NUM_SLOTS = 512
VIRTUAL_NODES_PER_SERVER = 9

def request_hash(i: int) -> int:
    # Hash function for client request -> slot
    return (i**2 + 2*i + 17) % NUM_SLOTS

def virtual_node_hash(i: int, j: int) -> int:
    # Hash function for server (i) and virtual node j -> slot
    return (i**2 + j + 2*j + 25) % NUM_SLOTS

class ConsistentHashRing:
    def __init__(self):
        self.slots = [None] * NUM_SLOTS  # Each slot holds (server_id, vnode_id)
        self.server_virtual_map = {}     # server_id -> list of slot indices

    def add_server(self, server_id: str):
        self.server_virtual_map[server_id] = []
        for j in range(VIRTUAL_NODES_PER_SERVER):
            slot = virtual_node_hash(int(server_id), j)
            original_slot = slot
            attempts = 0
            while self.slots[slot] is not None:
                attempts += 1
                if attempts > NUM_SLOTS:
                    raise RuntimeError("No free slots available for virtual node")
                slot = (original_slot + attempts**2) % NUM_SLOTS  # Quadratic probing
            self.slots[slot] = (server_id, j)
            self.server_virtual_map[server_id].append(slot)

    def remove_server(self, server_id: str):
        if server_id not in self.server_virtual_map:
            return
        for slot in self.server_virtual_map[server_id]:
            self.slots[slot] = None
        del self.server_virtual_map[server_id]

    def get_server_for_request(self, request_id: int) -> str:
        slot = request_hash(request_id)
        original = slot
        attempts = 0
        while self.slots[slot] is None:
            attempts += 1
            if attempts > NUM_SLOTS:
                raise RuntimeError("No available server to handle request")
            slot = (original + attempts) % NUM_SLOTS
        return self.slots[slot][0]  # Return only the server ID

    def print_ring(self):
        for i, val in enumerate(self.slots):
            if val:
                print(f"Slot {i}: Server {val[0]} (VNode {val[1]})")

# Example usage
if __name__ == "__main__":
    ring = ConsistentHashRing()
    ring.add_server("1")
    ring.add_server("2")
    ring.add_server("3")

    print("Request 10 handled by Server:", ring.get_server_for_request(10))
    print("Request 500 handled by Server:", ring.get_server_for_request(500))

    ring.print_ring()
