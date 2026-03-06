import struct

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
        The 'Opposite of Parsing': Converts object to raw bytes.
        Uses '>BBHH' format: Big Endian, 2 Unsigned Chars, 1 Unsigned Short, 1 Unsigned Int (4 bytes)
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
        The 'Parsing' logic: Converts raw bytes into a DoIPMessage object.
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