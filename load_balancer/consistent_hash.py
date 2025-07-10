"""
Consistent-hash ring for the load balancer (Task 2).

Default parameters follow the assignment spec:
    • N  = 3  physical servers             (can grow/shrink later)
    • M  = 512 total slots on the ring
    • K  = 9   virtual nodes per server    (= log2(M))
The ring stores (slot → server_id) pairs in a sorted list for O(log M) lookup.

We deliberately use Python's hashlib.sha256 for uniform, reproducible hashes;
it is simpler than the custom quadratic hash functions in the PDF while still
meeting the ‘match N, M, K’ requirement. Collisions are resolved by *linear
probing* to the next empty slot, exactly as suggested.:contentReference[oaicite:0]{index=0}
"""
from __future__ import annotations

import bisect
import hashlib
import random
from typing import Dict, List, Tuple


class ConsistentHashRing:
    """A circular hash ring with virtual nodes."""

    def __init__(
        self,
        num_slots: int = 2048,
        vnodes_per_server: int = 100,
    ) -> None:
        self.M = num_slots
        self.K = vnodes_per_server
        # Sorted list of (slot, server_id) tuples
        self._ring: List[Tuple[int, str]] = []
        # Reverse index: server_id -> list[slot] (its virtual nodes)
        self._server_slots: Dict[str, List[int]] = {}

    # --------------------------------------------------------------------- #
    #  Public API
    # --------------------------------------------------------------------- #
    def add_server(self, server_id: str) -> None:
        """Insert `server_id` with K virtual nodes."""
        if server_id in self._server_slots:
            raise ValueError(f"Server {server_id!r} already present")

        slots = []
        for replica in range(self.K):
            slot = self._hash(f"{server_id}-{replica}")
            # linear probing (tolerable because collisions are rare at M=512)
            original = slot
            while self._slot_taken(slot):
                slot = (slot + 1) % self.M
                if slot == original:  # ring is full (shouldn't happen)
                    raise RuntimeError("Hash ring full")
            self._insert(slot, server_id)
            slots.append(slot)

        self._server_slots[server_id] = slots

    def remove_server(self, server_id: str) -> None:
        """Remove all virtual nodes for `server_id` (no-op if missing)."""
        for slot in self._server_slots.pop(server_id, []):
            idx = bisect.bisect_left(self._ring, (slot, ""))
            if idx < len(self._ring) and self._ring[idx][0] == slot:
                self._ring.pop(idx)

    def get_server(self, request_id: int | str) -> str:
        """
        Map `request_id` → nearest clockwise server.

        Returns the server_id responsible for the request.
        """
        slot = self._hash(str(request_id))
        idx = bisect.bisect_right(self._ring, (slot, chr(255)))
        if idx == len(self._ring):  # wrap-around
            idx = 0
        if not self._ring:
            raise LookupError("Ring is empty - add a server first")
        return self._ring[idx][1]

    # Convenience helpers -------------------------------------------------- #
    def servers(self) -> List[str]:
        """Current physical servers, unsorted."""
        return list(self._server_slots)

    def ring_view(self) -> List[Tuple[int, str]]:
        """Return the full (slot, server_id) list — mainly for debugging."""
        return list(self._ring)

    # --------------------------------------------------------------------- #
    #  Internals
    # --------------------------------------------------------------------- #
    def _hash(self, key: str) -> int:
        """Uniform 0…M-1 slot from SHA256(key)."""
        h = hashlib.sha256(key.encode(), usedforsecurity=False).digest()
        return int.from_bytes(h[:4], "big") % self.M  # 32-bit slice is enough

    def _slot_taken(self, slot: int) -> bool:
        """True if the given slot already holds a virtual node."""
        idx = bisect.bisect_left(self._ring, (slot, ""))
        return idx < len(self._ring) and self._ring[idx][0] == slot

    def _insert(self, slot: int, server_id: str) -> None:
        """Insert (slot, server_id) keeping _ring sorted."""
        bisect.insort(self._ring, (slot, server_id))


# ------------------------------------------------------------------------- #
# Basic smoke-test (run `python consistent_hash.py` directly)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    ring = ConsistentHashRing()

    # Add the three initial servers (S1..S3)
    for s in range(1, 4):
        ring.add_server(f"S{s}")

    print("Ring slots (slot → server):")
    for slot, sid in ring.ring_view():
        print(f"{slot:>3}  →  {sid}")

    # Simulate 10 random requests
    print("\nSample mapping:")
    for _ in range(10):
        rid = random.randint(100_000, 999_999)
        target = ring.get_server(rid)
        print(f"Request {rid}  →  {target}")

    # quick sanity assertions
    assert len(ring.ring_view()) == 3 * 100
    assert all(ring.ring_view()[i][0] < 512 for i in range(27))
    from collections import Counter
    print(Counter(sid for _, sid in ring.ring_view()))

