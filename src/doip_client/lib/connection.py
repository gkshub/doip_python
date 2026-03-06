import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import socket

class DoIPConnection:
    """Class to manage DoIP connection and communication."""
    def __init__(self, target_ip, target_port=13400):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = None

    def connect(self):
        """Establish a TCP connection to the DoIP server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)  # Set a timeout for connection attempts
            self.sock.connect((self.target_ip, self.target_port))
            logger.info(f"Connected to DoIP server at {self.target_ip}:{self.target_port}")
        except Exception as e:
            logger.error(f"Failed to connect to DoIP server: {e}")
            raise

    def send(self, data: bytes):
        """Send data to the DoIP server."""
        if not self.sock:
            raise ConnectionError("Not connected to DoIP server.")
        try:
            self.sock.sendall(data)
            logger.info(f"Sent data: {data.hex()}")
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            raise

    def receive(self, buffer_size=1024) -> bytes:
        """Receive data from the DoIP server."""
        if not self.sock:
            raise ConnectionError("Not connected to DoIP server.")
        try:
            data = self.sock.recv(buffer_size)
            logger.info(f"Received data: {data.hex()}")
            return data
        except Exception as e:
            logger.error(f"Failed to receive data: {e}")
            raise

    def close(self):
        """Close the connection to the DoIP server."""
        if self.sock:
            self.sock.close()
            logger.info("Connection closed.")

def create_doip_header(payload_type, payload_len):
    """Create a DoIP header based on the given payload type and length."""
    protocol_version = 0x02
    inverse_protocol_version = 0xFD
    reserved = 0x00
    header = bytearray(8)
    header[0] = protocol_version
    header[1] = inverse_protocol_version
    header[2] = reserved
    header[3] = reserved
    header[4] = (payload_type >> 8) & 0xFF
    header[5] = payload_type & 0xFF
    header[6] = (payload_len >> 8) & 0xFF
    header[7] = payload_len & 0xFF
    return header

def setup_doip_connection(target_ip, target_port=13400):
    """Set up a TCP connection to the DoIP server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Set a timeout for connection attempts
    sock.connect((target_ip, target_port))
    return sock