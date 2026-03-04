"""
DoIP Socket Connection Module

Handles TCP connection establishment to DoIP servers based on configuration.
Implements DoIP vehicle connection logic with routing activation, frame handling,
and timeout/retry management.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DoIPFrame:
    """DoIP protocol frame with length-prefixed payload."""

    payload: bytes

    def encode(self) -> bytes:
        """Encode frame as 4-byte length prefix + payload."""
        return len(self.payload).to_bytes(4, "big") + self.payload

    @staticmethod
    async def recv_from(reader: asyncio.StreamReader) -> Optional["DoIPFrame"]:
        """Receive and decode a frame from a stream reader."""
        try:
            hdr = await reader.readexactly(4)
            if not hdr:
                return None
            length = int.from_bytes(hdr, "big")
            if length == 0:
                return DoIPFrame(b"")
            payload = await reader.readexactly(length)
            return DoIPFrame(payload)
        except asyncio.IncompleteReadError:
            return None


class DoIPConnection:
    """Manages a single TCP connection to a DoIP server."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: Dict[str, Any],
    ):
        self.reader = reader
        self.writer = writer
        self.config = config
        self.is_connected = False
        self.is_activated = False

    @classmethod
    async def connect(
        cls, host: str, port: int, config: Dict[str, Any]
    ) -> "DoIPConnection":
        """Establish a TCP connection to a DoIP server."""
        timeout = config.get("doip_client", {}).get("timeouts", {}).get(
            "tcp_connect_timeout_ms", 3000
        )
        timeout_s = timeout / 1000.0

        logger.info(f"Connecting to {host}:{port} (timeout: {timeout_s}s)")
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout_s
            )
            conn = cls(reader, writer, config)
            conn.is_connected = True
            logger.info(f"Connected to {host}:{port}")
            return conn
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {host}:{port}")
            raise
        except Exception as e:
            logger.error(f"Connection failed to {host}:{port}: {e}")
            raise

    async def send(self, payload: bytes) -> None:
        """Send a DoIP frame."""
        frame = DoIPFrame(payload)
        self.writer.write(frame.encode())
        await self.writer.drain()
        logger.debug(f"Sent {len(payload)} bytes")

    async def recv(self) -> Optional[bytes]:
        """Receive a DoIP frame payload."""
        try:
            frame = await DoIPFrame.recv_from(self.reader)
            if frame is not None:
                logger.debug(f"Received {len(frame.payload)} bytes")
                return frame.payload
            return None
        except (asyncio.IncompleteReadError, ConnectionResetError) as e:
            logger.error(f"Receive error: {e}")
            return None

    async def routing_activation(self) -> bool:
        """Perform DoIP routing activation handshake.
        
        Builds and sends a routing activation request based on target config,
        and waits for a positive response.
        """
        config = self.config.get("doip_client", {})
        target = config.get("target", {})
        source_addr = int(target.get("source_logical_address", "0x0E80"), 16)
        routing_type = target.get("routing_activation_type", 0)

        # Simple routing activation frame: [source_addr (2 bytes), routing_type (1 byte)]
        activation_req = source_addr.to_bytes(2, "big") + bytes([routing_type])

        logger.info("Sending routing activation request")
        await self.send(activation_req)

        timeout = config.get("timeouts", {}).get("routing_activation_timeout_ms", 2000)
        timeout_s = timeout / 1000.0

        try:
            response = await asyncio.wait_for(self.recv(), timeout_s)
            if response and len(response) > 0:
                self.is_activated = True
                logger.info("Routing activation successful")
                return True
            logger.warning("Routing activation failed: empty response")
            return False
        except asyncio.TimeoutError:
            logger.error("Routing activation timeout")
            return False

    def close(self) -> None:
        """Close the connection."""
        if self.writer:
            try:
                self.writer.close()
                self.is_connected = False
                self.is_activated = False
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DoIPClient:
    """DoIP client for connecting to vehicles based on config."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.connection: Optional[DoIPConnection] = None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path) as f:
            config = json.load(f)
        logger.info(f"Loaded config from {self.config_path}")
        return config

    async def connect_to_target(self) -> DoIPConnection:
        """Connect to the target vehicle specified in config."""
        client_config = self.config.get("doip_client", {})
        target_config = client_config.get("target", {})
        network_config = client_config.get("network", {})

        target_ip = target_config.get("target_ip")
        tcp_port = network_config.get("tcp_port", 13400)

        if not target_ip:
            raise ValueError("target_ip not found in config")

        self.connection = await DoIPConnection.connect(target_ip, tcp_port, self.config)
        return self.connection

    async def connect_with_activation(self) -> DoIPConnection:
        """Connect and perform routing activation."""
        conn = await self.connect_to_target()
        success = await conn.routing_activation()
        if not success:
            conn.close()
            raise RuntimeError("Routing activation failed")
        return conn

    async def send_uds(self, data: bytes, wait_response: bool = True) -> Optional[bytes]:
        """Send UDS data after connection is established and activated."""
        if not self.connection or not self.connection.is_activated:
            raise RuntimeError("Connection not established or not activated")

        await self.connection.send(data)

        if wait_response:
            client_config = self.config.get("doip_client", {})
            timeout = client_config.get("timeouts", {}).get("uds_response_timeout_ms", 5000)
            timeout_s = timeout / 1000.0
            try:
                response = await asyncio.wait_for(self.connection.recv(), timeout_s)
                return response
            except asyncio.TimeoutError:
                logger.error("UDS response timeout")
                return None

        return None

    def close(self) -> None:
        """Close the connection."""
        if self.connection:
            self.connection.close()


async def establish_connection(config_path: str) -> DoIPConnection:
    """Convenience function to establish a connection with config.
    
    Args:
        config_path: Path to the DoIP client config JSON file.
        
    Returns:
        An activated DoIPConnection instance.
    """
    client = DoIPClient(config_path)
    conn = await client.connect_with_activation()
    return conn


__all__ = [
    "DoIPFrame",
    "DoIPConnection",
    "DoIPClient",
    "establish_connection",
]
