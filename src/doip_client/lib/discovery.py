import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import socket

class DoIPDiscovery:
    def __init__(self, config):
        self.config = config

    def handle_vehicle_identification_request(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send Vehicle Identification Request (Header + No Payload)
            request = b'\x02\xFD\x00\x01\x00\x00\x00\x00'
            sock.sendto(request, ('255.255.255.255', 13400))
            return sock
        
    def handle_vehicle_identification_response(self, sock):
        try:
            data, addr = sock.recvfrom(1024)
            logger.info(f"Vehicle found at {addr[0]}")
            return addr[0] # Return the IP to be used for TCP
        except socket.timeout:
            logger.warning("No vehicle found within the timeout period.")
            return None

    def find_vehicle(self, timeout=2.0):
        sock = self.vehicle_identification_request() 
        sock.settimeout(timeout)
        return self.handle_vehicle_identification_response(sock)    
            
    
