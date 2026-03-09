import logging
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoIPMessage:
    """
    Handles the Header and Payload for ISO 13400-2 (DoIP).

    Header structure (8 bytes):
    - Protocol Version: 1 byte (0x02)
    - Inverse Version:  1 byte (0xFD)
    - Payload Type:     2 bytes (Big Endian)
    - Payload Length:   4 bytes (Big Endian)
    """

    # Protocol Constants
    PROTOCOL_VERSION = 0x02
    INVERSE_VERSION = 0xFD

    def __init__(self, payload_type: int, payload: bytes = b''):
        self.payload_type = payload_type
        self.payload = payload

    def serialize(self) -> bytes:
        """
        Serialize: Converts DoIPMessage object to raw bytes.
        Uses '>BBHI' format: Big Endian, 2 Unsigned Chars, 1 Unsigned Short, 1 Unsigned Int (4 bytes)
        """
        payload_len = len(self.payload)

        # Pack the 8-byte header
        header = struct.pack(
            ">BBHI",
            self.PROTOCOL_VERSION,
            self.INVERSE_VERSION,
            self.payload_type,
            payload_len
        )
        return header + self.payload

    @classmethod
    def parse(cls, data: bytes):
        """
        Parse: Converts raw bytes into a DoIPMessage object.
        """
        if len(data) < 8:
            raise ValueError("Data too short to be a valid DoIP header")

        # Unpack the first 8 bytes
        version, inv_version, p_type, p_len = struct.unpack(">BBHI", data[:8])

        # Basic Validation
        if version != cls.PROTOCOL_VERSION:
            raise ValueError(f"Unsupported Protocol Version: {version}")

        if version ^ inv_version != 0xFF:
            raise ValueError("Invalid Inverse Version check failed")

        payload = data[8 : 8 + p_len]
        return cls(p_type, payload)

    def __repr__(self):
        return f"<DoIPMessage Type: 0x{self.payload_type:04X}, Length: {len(self.payload)}>"


class DoIPProtocolHandler:
    """
    Handles DoIP protocol layer operations - message serialization and deserialization.

    This handler wraps the DoIPMessage class and provides convenient methods for
    sending and receiving DoIP frames over sockets.
    """

    @staticmethod
    def send_frame(socket, payload_type: int, payload: bytes = b'') -> bool:
        """
        Serialize a DoIP message and send it over the socket.

        Args:
            socket: Socket object with a sendto() or sendall() method
            payload_type: 2-byte payload type identifier (e.g., 0x0001 for vehicle ID request)
            payload: Payload bytes (empty by default)

        Returns:
            True if send successful, False otherwise
        """
        try:
            # Create and serialize the DoIP message
            msg = DoIPMessage(payload_type, payload)
            frame = msg.serialize()

            # Send the frame (socket must be ready - either UDP with sendto or TCP with sendall)
            if hasattr(socket, 'sendall'):
                # TCP socket
                socket.sendall(frame)
            else:
                # UDP socket (requires tuple address)
                raise ValueError("Use send_frame_udp() for UDP sockets with explicit address")

            logger.info(f"Sent DoIP frame: Type=0x{payload_type:04X}, Length={len(payload)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send DoIP frame - {e}")
            return False

    @staticmethod
    def send_frame_udp(socket, payload_type: int, address: tuple, payload: bytes = b'') -> bool:
        """
        Serialize a DoIP message and send it via UDP to a specific address.

        Args:
            socket: UDP socket object with sendto() method
            payload_type: 2-byte payload type identifier
            address: Tuple of (ip, port) for UDP sendto()
            payload: Payload bytes (empty by default)

        Returns:
            True if send successful, False otherwise
        """
        try:
            # Create and serialize the DoIP message
            msg = DoIPMessage(payload_type, payload)
            frame = msg.serialize()

            # Send via UDP
            socket.sendto(frame, address)
            logger.info(f"Sent DoIP frame via UDP to {address[0]}:{address[1]}: Type=0x{payload_type:04X}, Length={len(payload)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send DoIP frame via UDP - {e}")
            return False

    @staticmethod
    def receive_frame(socket, timeout: float = None) -> tuple:
        """
        Receive and parse a DoIP frame from a socket.

        Args:
            socket: Socket object (TCP with recv() or UDP with recvfrom())
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (DoIPMessage, address) or (None, None) on error/timeout
            For TCP: address is None
            For UDP: address is (ip, port) tuple
        """
        try:
            # Receive raw data (socket must be set up)
            if hasattr(socket, 'recvfrom'):
                # UDP socket
                data, addr = socket.recvfrom(1024)
            else:
                # TCP socket
                data = socket.recv(1024)
                addr = None

            # Parse the DoIP message
            if len(data) < 8:
                logger.warning(f"Received data too short ({len(data)} bytes) to be a valid DoIP message")
                return None, None

            msg = DoIPMessage.parse(data)
            logger.info(f"Received DoIP frame: Type=0x{msg.payload_type:04X}, Length={len(msg.payload)}")

            return msg, addr

        except ValueError as e:
            logger.error(f"DoIP validation error - {e}")
            return None, None
        except Exception as e:
            logger.error(f"Failed to receive DoIP frame - {e}")
            return None, None

    @staticmethod
    def parse_frame(data: bytes) -> 'DoIPMessage':
        """
        Parse raw bytes into a DoIP message (without receiving from socket).

        Args:
            data: Raw bytes to parse

        Returns:
            DoIPMessage object or None on error
        """
        try:
            if len(data) < 8:
                logger.warning(f"Received data too short ({len(data)} bytes) to be a valid DoIP message")
                return None

            msg = DoIPMessage.parse(data)
            logger.info(f"Parsed DoIP frame: Type=0x{msg.payload_type:04X}, Length={len(msg.payload)}")
            return msg

        except ValueError as e:
            logger.error(f"DoIP validation error - {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse DoIP frame - {e}")
            return None

    @staticmethod
    def validate_frame(raw_bytes: bytes) -> bool:
        """
        Validate that raw bytes contain a valid DoIP frame header.

        Args:
            raw_bytes: Raw bytes to validate

        Returns:
            True if valid DoIP frame, False otherwise
        """
        if len(raw_bytes) < 8:
            logger.warning(f"Data too short ({len(raw_bytes)} bytes) for DoIP validation")
            return False

        try:
            DoIPMessage.parse(raw_bytes)
            return True
        except Exception as e:
            logger.warning(f"DoIP validation failed - {e}")
            return False
