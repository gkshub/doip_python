
class DoIPDiscover:
    def __init__(self, config):
        self.config = config

    def discover_vehicles(self):
        # Simulate discovery of vehicles based on the configuration
        discovered_vehicles = []
        for vehicle in self.config["vehicles"]:
            discovered_vehicles.append({
                "vehicle_id": vehicle["vehicle_id"],
                "logical_address": vehicle["logical_address"],
                "eid": vehicle["eid"],
                "gid": vehicle["gid"],
                "max_tcp_connections": vehicle.get("max_tcp_connections", 0),
                "uds_profile": vehicle.get("uds_profile", "unknown")
            })
        return discovered_vehicles
