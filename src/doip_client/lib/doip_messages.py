import logging
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoIPMessageType:
    """Constants for DoIP payload types according to ISO 13400-2"""
    VEHICLE_IDENTIFICATION_REQUEST = 0x0001
    VEHICLE_IDENTIFICATION_RESPONSE = 0x0002
    VEHICLE_ANNOUNCEMENT = 0x0004
    VEHICLE_IDENTIFICATION_REQUEST_WITH_EID = 0x0003
    VEHICLE_IDENTIFICATION_RESPONSE_WITH_EID = 0x0005


class VehicleIdentificationRequest:
    """
    DoIP Vehicle Identification Request (Payload Type 0x0001)

    Used to discover vehicles on the network via UDP broadcast.
    Payload is empty for basic identification request.
    """
    PAYLOAD_TYPE = DoIPMessageType.VEHICLE_IDENTIFICATION_REQUEST

    @staticmethod
    def build() -> bytes:
        """
        Build the payload for a Vehicle Identification Request.

        Returns:
            Empty bytes since basic VID request has no payload
        """
        logger.debug("Built Vehicle Identification Request payload (empty)")
        return b''


class VehicleIdentificationResponse:
    """
    DoIP Vehicle Identification Response (Payload Type 0x0002)

    Response from a vehicle to a Vehicle Identification Request.
    Contains vehicle information like VIN, hardware/software versions.
    """
    PAYLOAD_TYPE = DoIPMessageType.VEHICLE_IDENTIFICATION_RESPONSE

    @staticmethod
    def parse(payload: bytes) -> dict:
        """
        Parse a Vehicle Identification Response payload.

        Response format (min 6 bytes):
        - Bytes 0: VIN (17 bytes) - if present
        - Bytes 17: Hardware Version (6 bytes)
        - Bytes 23: Software Version (6 bytes)
        - Bytes 29: ExID (Exhaust ID, 4 bytes) - optional
        - Bytes 33: EDID (Equipment ID, 4 bytes) - optional

        Returns:
            Dictionary with parsed vehicle information
        """
        try:
            if len(payload) < 6:
                logger.warning(f"Vehicle Identification Response payload too short: {len(payload)} bytes")
                return {'error': 'Payload too short'}

            info = {}

            # Check if we have VIN (minimum 17 bytes)
            if len(payload) >= 17:
                info['vin'] = payload[0:17].decode('ascii', errors='replace').strip('\x00')

            # Hardware version at byte 17 (6 bytes if present)
            if len(payload) >= 23:
                info['hardware_version'] = payload[17:23].hex()

            # Software version at byte 23 (6 bytes if present)
            if len(payload) >= 29:
                info['software_version'] = payload[23:29].hex()

            # Optional: ExID at byte 29
            if len(payload) >= 33:
                info['exhaust_id'] = payload[29:33].hex()

            # Optional: EDID at byte 33
            if len(payload) >= 37:
                info['equipment_id'] = payload[33:37].hex()

            logger.info(f"Parsed Vehicle Identification Response: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to parse Vehicle Identification Response - {e}")
            return {'error': str(e)}


class VehicleAnnouncement:
    """
    DoIP Vehicle Announcement (Payload Type 0x0004)

    Unsolicited message sent by vehicles to announce their presence.
    Contains similar information to Vehicle Identification Response.
    """
    PAYLOAD_TYPE = DoIPMessageType.VEHICLE_ANNOUNCEMENT

    @staticmethod
    def parse(payload: bytes) -> dict:
        """
        Parse a Vehicle Announcement payload.

        Format is similar to Vehicle Identification Response:
        - VIN (17 bytes)
        - Hardware Version (6 bytes)
        - Software Version (6 bytes)
        - ExID (4 bytes) - optional
        - EDID (4 bytes) - optional

        Returns:
            Dictionary with parsed announcement information
        """
        try:
            if len(payload) < 6:
                logger.warning(f"Vehicle Announcement payload too short: {len(payload)} bytes")
                return {'error': 'Payload too short'}

            info = {'type': 'announcement'}

            # Check if we have VIN (minimum 17 bytes)
            if len(payload) >= 17:
                info['vin'] = payload[0:17].decode('ascii', errors='replace').strip('\x00')

            # Hardware version at byte 17 (6 bytes if present)
            if len(payload) >= 23:
                info['hardware_version'] = payload[17:23].hex()

            # Software version at byte 23 (6 bytes if present)
            if len(payload) >= 29:
                info['software_version'] = payload[23:29].hex()

            # Optional: ExID at byte 29
            if len(payload) >= 33:
                info['exhaust_id'] = payload[29:33].hex()

            # Optional: EDID at byte 33
            if len(payload) >= 37:
                info['equipment_id'] = payload[33:37].hex()

            logger.info(f"Parsed Vehicle Announcement: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to parse Vehicle Announcement - {e}")
            return {'error': str(e)}


class VehicleIdentificationRequestWithEID:
    """
    DoIP Vehicle Identification Request with EID (Payload Type 0x0003)

    Extended identification request that includes filtering by Exhaust ID.
    """
    PAYLOAD_TYPE = DoIPMessageType.VEHICLE_IDENTIFICATION_REQUEST_WITH_EID

    @staticmethod
    def build(exhaust_id: bytes = None) -> bytes:
        """
        Build the payload for a Vehicle Identification Request with EID.

        Args:
            exhaust_id: 4-byte Exhaust ID for filtering (optional)

        Returns:
            Payload bytes containing optional EID
        """
        if exhaust_id:
            if len(exhaust_id) != 4:
                logger.warning(f"ExID should be 4 bytes, got {len(exhaust_id)}")
                return exhaust_id[:4] if len(exhaust_id) > 4 else exhaust_id
            logger.debug(f"Built Vehicle Identification Request with EID: {exhaust_id.hex()}")
            return exhaust_id
        logger.debug("Built Vehicle Identification Request with EID (empty)")
        return b''
