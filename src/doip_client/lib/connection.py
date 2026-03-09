import logging
import socket   

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseConnection:
    def __init__(self, timeout=5.0):
        self.sock = None
        self.timeout = timeout

    def is_active(self):
        return self.sock is not None
    
    def close(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno != 107:  # ENOTCONN - socket not connected
                    logger.warning(f"Error shutting down socket: {e}")
            except Exception as e:
                logger.warning(f"Error shutting down socket: {e}")
            self.sock.close()
            self.sock = None
            logger.info("Connection closed successfully.")
        else:
            logger.error("No active connection to close.")

class UDPConnection(BaseConnection):
    def __init__(self, timeout=5.0):
        super().__init__(timeout)
        self.broadcast_enabled = False

    def close(self):
        """Close UDP socket without shutdown (UDP is connectionless)"""
        if self.sock:
            self.sock.close()
            self.sock = None
            logger.info("UDP connection closed.")

    def init_broadcast(self) -> bool:
        """
        Initialize UDP socket with broadcast capability for sending.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.sock:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.settimeout(self.timeout)
            self.broadcast_enabled = True
            logger.info("UDP socket initialized with broadcast capability")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize broadcast socket - {e}")
            return False

    def init_for_receiving(self) -> bool:
        """
        Initialize UDP socket for receiving broadcast messages.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.sock:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.settimeout(self.timeout)
            logger.info("UDP socket initialized for receiving")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize receiving socket - {e}")
            return False

    def send(self, data: bytes, address: tuple) -> bool:
        """
        Send raw bytes to a specific address.

        Args:
            data: Raw bytes to send
            address: Tuple of (ip, port)

        Returns:
            True if send successful, False otherwise
        """
        if not self.sock:
            logger.error("Cannot send: No active UDP socket.")
            return False

        try:
            self.sock.sendto(data, address)
            logger.info(f"Sent {len(data)} bytes to {address[0]}:{address[1]}")
            return True
        except Exception as e:
            logger.error(f"Failed to send UDP data to {address} - {e}")
            self.close()
            return False

    def receive(self, timeout: float = None) -> tuple:
        """
        Receive raw bytes from socket.

        Args:
            timeout: Optional timeout in seconds. Uses self.timeout if not specified.

        Returns:
            Tuple of (data, address) or (None, None) on timeout/error
        """
        if not self.sock:
            logger.error("Cannot receive: No active UDP socket.")
            return None, None

        try:
            if timeout:
                self.sock.settimeout(timeout)
            data, addr = self.sock.recvfrom(1024)
            logger.info(f"Received {len(data)} bytes from {addr[0]}:{addr[1]}")
            return data, addr
        except socket.timeout:
            logger.warning("No data received within the timeout period.")
            return None, None
        except Exception as e:
            logger.error(f"Failed to receive UDP data - {e}")
            self.close()
            return None, None

    def bind(self, port: int) -> bool:
        """
        Bind UDP socket to a port for listening.

        Args:
            port: Port number to bind to

        Returns:
            True if bind successful, False otherwise
        """
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.settimeout(self.timeout)

        try:
            self.sock.bind(('', port))
            logger.info(f"Bound UDP socket to port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to bind to port {port} - {e}")
            self.close()
            return False

    def discover_vehicle(self,
                         request_data: bytes,
                         broadcast_address='255.255.255.255',
                         port=13400):
        """
        Legacy method for vehicle discovery. Use send/receive methods instead.
        Kept for backward compatibility.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(self.timeout)

        try:
            self.sock.sendto(request_data, (broadcast_address, port))
            logger.info(f"Sent discovery request to {broadcast_address}:{port}")
            data, addr = self.sock.recvfrom(1024)
            logger.info(f"Received response from {addr[0]}:{addr[1]}")
            return addr[0]  # Return the IP address of the responding vehicle
        except socket.timeout:
            logger.warning("No response received within the timeout period.")
            return None
        finally:
            # Ensure the socket is closed after discovery attempt
            self.close()

class TCPConnection(BaseConnection):
    def __init__(self, ip: str, port: int, timeout=5.0):
        super().__init__(timeout)
        self.ip = ip
        self.port = port

    def close(self):
        """Close TCP socket with proper shutdown"""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno != 107:  # ENOTCONN - socket not connected
                    logger.warning(f"Error shutting down socket: {e}")
            except Exception as e:
                logger.warning(f"Error shutting down socket: {e}")
            self.sock.close()
            self.sock = None
            logger.info("TCP connection closed.")

    def connect(self):
        # Create a TCP socket and attempt to connect to the specified IP and port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect((self.ip, self.port))
            logger.info(f"Successfully connected to {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.ip}:{self.port} - {e}")
            self.close()
            return False
        
    def send(self, data: bytes) -> bool:
        """
        Send raw bytes over TCP connection.

        Args:
            data: Raw bytes to send

        Returns:
            True if send successful, False otherwise
        """
        if not self.is_active():
            logger.error("Cannot send: No active TCP connection.")
            return False

        try:
            self.sock.sendall(data)
            logger.info(f"Sent {len(data)} bytes to {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to send TCP data to {self.ip}:{self.port} - {e}")
            self.close()
            return False

    def receive(self, timeout: float = None) -> bytes:
        """
        Receive raw bytes from TCP connection.

        Args:
            timeout: Optional timeout in seconds. Uses self.timeout if not specified.

        Returns:
            Received bytes or None on error/timeout
        """
        if not self.is_active():
            logger.error("Cannot receive: No active TCP connection.")
            return None

        try:
            if timeout:
                self.sock.settimeout(timeout)
            data = self.sock.recv(1024)
            if data:
                logger.info(f"Received {len(data)} bytes from {self.ip}:{self.port}")
            return data
        except socket.timeout:
            logger.warning("No data received within the timeout period.")
            return None
        except Exception as e:
            logger.error(f"Failed to receive TCP data from {self.ip}:{self.port} - {e}")
            self.close()
            return None

    def send_doip_message(self, message: bytes):
        """
        Legacy method to send DoIP message. Use send() method instead.
        Kept for backward compatibility.
        """
        if not self.is_active():
            logger.error("Cannot send message: No active connection.")
            return False
        try:
            self.sock.sendall(message)
            logger.info(f"Sent DoIP message to {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to send DoIP message - {e}")
            self.close()
            return False
