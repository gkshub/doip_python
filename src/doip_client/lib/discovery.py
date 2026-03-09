import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import socket

# Import the new layers
from lib.connection import UDPConnection
from lib.doip_protocol import DoIPProtocolHandler
from lib.doip_messages import VehicleIdentificationRequest, VehicleAnnouncement, DoIPMessageType


class DoIPDiscovery:
    """
    DoIP Discovery handler using the 3-tier architecture:
    - Socket Layer: UDPConnection
    - Protocol Layer: DoIPProtocolHandler
    - Message Layer: VehicleIdentificationRequest, VehicleAnnouncement
    """

    def __init__(self, config):
        self.config = config

    def listen_for_vehicle_announcements(self, port: int = 13400, timeout: float = 5.0) -> list:
        """
        Passively listen for unsolicited Vehicle Announcements from vehicles.

        Uses the 3-tier architecture:
        - Socket Layer (UDPConnection): Creates listening socket and receives data
        - Protocol Layer (DoIPProtocolHandler): Parses DoIP frames
        - Message Layer (VehicleAnnouncement): Extracts announcement data

        Args:
            port: Port to listen on (default DoIP port is 13400)
            timeout: How long to listen in seconds

        Returns:
            List of vehicle announcements received (each as dict)
        """
        logger.info(f"Listening for Vehicle Announcements on port {port} for {timeout}s...")

        udp_conn = UDPConnection(timeout=timeout)
        announcements = []

        try:
            # Socket Layer: Bind to the port for listening
            if not udp_conn.bind(port):
                logger.error("Failed to bind to announcement port")
                return announcements

            # Set timeout for listening
            udp_conn.sock.settimeout(timeout)

            # Listen for announcements
            while True:
                try:
                    # Socket Layer: Receive raw data via UDP
                    data, addr = udp_conn.receive(timeout)

                    if data is None:
                        break

                    # Protocol Layer: Parse DoIP frame
                    msg = DoIPProtocolHandler.parse_frame(data)

                    if msg and msg.payload_type == DoIPMessageType.VEHICLE_ANNOUNCEMENT:
                        # Message Layer: Extract announcement information
                        vehicle_info = VehicleAnnouncement.parse(msg.payload)
                        vehicle_info['source_ip'] = addr[0] if addr else None
                        announcements.append(vehicle_info)
                        logger.info(f"Received announcement from {addr[0] if addr else 'unknown'}")
                except socket.timeout:
                    break
                except Exception as e:
                    logger.warning(f"Error processing announcement - {e}")
                    continue

        finally:
            udp_conn.close()

        logger.info(f"Received {len(announcements)} vehicle announcements")
        return announcements

    def send_vehicle_identification_request(self,
                                           broadcast_address: str = '255.255.255.255',
                                           port: int = 13400) -> bool:
        """
        Send a Vehicle Identification Request via UDP broadcast.

        Uses the 3-tier architecture:
        - Socket Layer (UDPConnection): Creates and manages the socket
        - Protocol Layer (DoIPProtocolHandler): Serializes the DoIP frame
        - Message Layer (VehicleIdentificationRequest): Builds the payload

        Args:
            broadcast_address: Broadcast address (default 255.255.255.255)
            port: Target port (default DoIP port 13400)

        Returns:
            True if send successful, False otherwise
        """
        logger.info(f"Sending Vehicle Identification Request to {broadcast_address}:{port}")

        udp_conn = UDPConnection()
        success = False

        try:
            # Socket Layer: Initialize UDP socket with broadcast capability
            if not udp_conn.init_broadcast():
                logger.error("Failed to initialize broadcast socket")
                return False

            # Message Layer: Build the Vehicle Identification Request payload
            payload = VehicleIdentificationRequest.build()

            # Protocol Layer: Send DoIP frame using protocol handler
            success = DoIPProtocolHandler.send_frame_udp(
                udp_conn.sock,
                VehicleIdentificationRequest.PAYLOAD_TYPE,
                (broadcast_address, port),
                payload
            )

            if success:
                logger.info("Vehicle Identification Request sent successfully")

        except Exception as e:
            logger.error(f"Failed to send Vehicle Identification Request - {e}")
        finally:
            udp_conn.close()

        return success

    def receive_vehicle_identification_response(self, timeout: float = 5.0):
        """
        Wait for and parse a Vehicle Identification Response.

        Uses the 3-tier architecture:
        - Socket Layer (UDPConnection): Creates and manages the listening socket
        - Protocol Layer (DoIPProtocolHandler): Parses the DoIP frame
        - Message Layer (VehicleAnnouncement): Extracts vehicle information

        Args:
            timeout: How long to wait for response in seconds

        Returns:
            Tuple of (vehicle_ip, vehicle_info) or (None, None) if no response
        """
        logger.info(f"Waiting for Vehicle Identification Response (timeout={timeout}s)...")

        udp_conn = UDPConnection(timeout=timeout)
        vehicle_ip = None
        vehicle_info = None

        try:
            # Socket Layer: Initialize UDP socket for receiving
            if not udp_conn.init_for_receiving():
                logger.error("Failed to initialize receiving socket")
                return None, None

            # Socket Layer: Receive raw data via UDP
            data, addr = udp_conn.receive(timeout)

            if data:
                # Protocol Layer: Parse DoIP frame
                msg = DoIPProtocolHandler.parse_frame(data)

                if msg and msg.payload_type == DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE:
                    # Message Layer: Extract vehicle information from response
                    vehicle_info = VehicleAnnouncement.parse(msg.payload)
                    vehicle_ip = addr[0]
                    logger.info(f"Received Vehicle Identification Response from {vehicle_ip}")

        except socket.timeout:
            logger.warning("No response received within the timeout period.")
        except Exception as e:
            logger.error(f"Error receiving Vehicle Identification Response - {e}")
        finally:
            udp_conn.close()

        return vehicle_ip, vehicle_info

    def find_vehicle(self, timeout: float = 2.0) -> str:
        """
        Orchestrate the complete vehicle discovery process.

        1. Send Vehicle Identification Request via broadcast
        2. Wait for and parse the response
        3. Return the IP address of the responding vehicle

        Args:
            timeout: Timeout for discovery in seconds (will be converted from milliseconds in callers)

        Returns:
            Vehicle IP address string, or None if discovery fails
        """
        logger.info(f"Starting vehicle discovery (timeout={timeout}s)")

        # Send the identification request
        if not self.send_vehicle_identification_request():
            logger.error("Failed to send vehicle identification request")
            return None

        # Wait for response
        vehicle_ip, vehicle_info = self.receive_vehicle_identification_response(timeout)

        if vehicle_ip:
            logger.info(f"Vehicle discovered at IP: {vehicle_ip}")
            return vehicle_ip
        else:
            logger.warning("No vehicle found within the timeout period")
            return None

    def find_vehicle_hybrid(self, timeout: float = 2.0, try_announcements_first: bool = True) -> str:
        """
        Hybrid discovery: Try both passive and active discovery mechanisms.

        Uses the 3-tier architecture with two strategies:
        1. (Optional) Listen for unsolicited Vehicle Announcements (passive)
        2. Send Vehicle Identification Request and wait for response (active)
        3. Return the first vehicle found via either method

        Args:
            timeout: Total timeout for discovery in seconds
            try_announcements_first: If True, listen for announcements before active discovery

        Returns:
            Vehicle IP address string, or None if discovery fails
        """
        logger.info(f"Starting hybrid vehicle discovery (timeout={timeout}s, announcements_first={try_announcements_first})")

        vehicle_ip = None

        # Strategy 1: Try passive discovery (announcements) if configured
        if try_announcements_first:
            announcement_timeout = min(10.0, timeout) # Use a reasonable timeout for announcements (e.g., 10 seconds or total timeout if shorter)
            logger.info(f"Attempting passive discovery via announcements ({announcement_timeout}s)...")

            announcements = self.listen_for_vehicle_announcements(
                port=13400,
                timeout=announcement_timeout
            )

            if announcements:
                vehicle_ip = announcements[0].get('source_ip')
                logger.info(f"Vehicle found via announcement: {vehicle_ip}")
                return vehicle_ip

        # Strategy 2: Fall back to active discovery (request-response)
        remaining_timeout = timeout
        logger.info(f"Attempting active discovery via identification request ({remaining_timeout}s)...")

        vehicle_ip = self.find_vehicle(timeout=remaining_timeout)

        if vehicle_ip:
            return vehicle_ip
        else:
            logger.warning("No vehicle found via hybrid discovery")
            return None

