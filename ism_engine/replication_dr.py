"""
Backup, Snapshots & Disaster Recovery (DR) Engine
Simulates Copy-on-Write (CoW) Snapshots, Synchronous vs Asynchronous Replication,
RPO / RTO calculations, and automated site failover / failback.
"""

import time
from typing import Dict, List, Any, Optional

class SnapshotPoint:
    def __init__(self, snap_id: str, name: str, timestamp_str: str, base_blocks: Dict[int, str]):
        self.snap_id = snap_id
        self.name = name
        self.timestamp_str = timestamp_str
        # Copy-on-Write snapshot saves initial block state
        self.frozen_blocks = dict(base_blocks)
        self.cow_delta_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snap_id": self.snap_id,
            "name": self.name,
            "timestamp": self.timestamp_str,
            "blocks_count": len(self.frozen_blocks),
            "cow_delta_count": self.cow_delta_count
        }


class ReplicationDREngine:
    def __init__(self):
        # Primary Production Site (Site A - New York)
        self.site_a_status = "ONLINE"
        self.active_dc = "Site A (Primary DC - NY)"
        
        # Disaster Recovery Remote Site (Site B - Frankfurt / Texas)
        self.site_b_status = "STANDBY"
        
        # Replication Mode: SYNCHRONOUS or ASYNCHRONOUS
        self.replication_mode = "SYNCHRONOUS"
        self.link_latency_ms = 4.2  # ms over WAN
        self.link_bandwidth_mbps = 1000
        
        # Primary Storage Blocks
        self.live_storage_blocks: Dict[int, str] = {
            0: "INIT_BOOT_SECTOR",
            1: "SYS_KERNEL_DATA",
            2: "DB_TRANSACTIONS_01",
            3: "USER_ACCOUNTS_TBL"
        }
        
        # Site B Mirror Storage Blocks
        self.site_b_blocks: Dict[int, str] = dict(self.live_storage_blocks)
        self.replication_queue: List[Dict[str, Any]] = []

        # Snapshots
        self.snapshots: List[SnapshotPoint] = []
        self._create_initial_snapshot()

        # Telemetry & Metrics
        self.last_sync_timestamp = time.time()
        self.rpo_seconds = 0.0
        self.rto_minutes = 2.5
        self.dr_events_log: List[Dict[str, Any]] = []

    def _create_initial_snapshot(self):
        snap = SnapshotPoint("snap_001", "Baseline_Gold_Image", "10:00:00 AM", self.live_storage_blocks)
        self.snapshots.append(snap)

    def set_replication_mode(self, mode: str) -> Dict[str, Any]:
        self.replication_mode = mode.upper()
        if self.replication_mode == "SYNCHRONOUS":
            self.link_latency_ms = 3.8
            self.rpo_seconds = 0.0
        else:
            self.link_latency_ms = 0.5  # Local write is immediate
            self.rpo_seconds = 180.0  # 3 minutes buffer

        return {
            "status": "SUCCESS",
            "replication_mode": self.replication_mode,
            "rpo_seconds": self.rpo_seconds,
            "rto_minutes": self.rto_minutes
        }

    def write_block_with_cow(self, block_idx: int, new_val: str) -> Dict[str, Any]:
        """Performs write with Copy-On-Write snapshot preservation and Site replication."""
        if self.site_a_status != "ONLINE" and self.active_dc.startswith("Site A"):
            return {"status": "ERROR", "message": "Primary Site A is OFFLINE! Initiate DR Failover first."}

        old_val = self.live_storage_blocks.get(block_idx, "[EMPTY]")
        
        # Copy-on-Write: If block being written is in a snapshot, verify preservation
        for snap in self.snapshots:
            if block_idx in snap.frozen_blocks:
                snap.cow_delta_count += 1

        self.live_storage_blocks[block_idx] = new_val

        # Replication to Site B
        ack_latency = 0.2
        if self.replication_mode == "SYNCHRONOUS":
            # Direct synchronous commit
            self.site_b_blocks[block_idx] = new_val
            self.last_sync_timestamp = time.time()
            self.rpo_seconds = 0.0
            ack_latency = 0.2 + self.link_latency_ms
            rep_status = "COMMITTED_BOTH_SITES"
        else:
            # Asynchronous queue
            self.replication_queue.append({"block": block_idx, "val": new_val, "ts": time.time()})
            self.rpo_seconds = round(min(300.0, len(self.replication_queue) * 15.0), 1)
            rep_status = "QUEUED_FOR_ASYNC_FLUSH"

        return {
            "status": "SUCCESS",
            "block_idx": block_idx,
            "old_val": old_val,
            "new_val": new_val,
            "replication_status": rep_status,
            "write_ack_latency_ms": round(ack_latency, 2),
            "rpo_seconds": self.rpo_seconds
        }

    def flush_async_replication(self) -> Dict[str, Any]:
        """Flushes asynchronous replication queue to Site B."""
        flushed_count = len(self.replication_queue)
        for item in self.replication_queue:
            self.site_b_blocks[item["block"]] = item["val"]
        self.replication_queue.clear()
        self.last_sync_timestamp = time.time()
        self.rpo_seconds = 0.0

        return {
            "status": "SUCCESS",
            "flushed_items": flushed_count,
            "rpo_seconds": self.rpo_seconds,
            "message": "Site B synchronized with Primary Site."
        }

    def create_snapshot(self, snap_name: str) -> Dict[str, Any]:
        """Creates a new point-in-time CoW Snapshot."""
        ts = time.strftime("%H:%M:%S")
        snap_id = f"snap_{len(self.snapshots) + 1:03d}"
        snap = SnapshotPoint(snap_id, snap_name, ts, self.live_storage_blocks)
        self.snapshots.append(snap)

        return {
            "status": "SUCCESS",
            "snapshot": snap.to_dict()
        }

    def rollback_to_snapshot(self, snap_id: str) -> Dict[str, Any]:
        """Reverts live storage blocks to the chosen historical snapshot."""
        target_snap = None
        for s in self.snapshots:
            if s.snap_id == snap_id:
                target_snap = s
                break

        if not target_snap:
            return {"status": "ERROR", "message": "Snapshot ID not found"}

        self.live_storage_blocks = dict(target_snap.frozen_blocks)
        # Resync to Site B
        self.site_b_blocks = dict(self.live_storage_blocks)
        self.replication_queue.clear()

        return {
            "status": "SUCCESS",
            "message": f"Storage successfully rolled back to snapshot {target_snap.name}",
            "restored_blocks": self.live_storage_blocks
        }

    def trigger_disaster_failover(self) -> Dict[str, Any]:
        """Simulates catastrophic disaster at Site A and initiates automated DR failover to Site B."""
        self.site_a_status = "DISASTER_OFFLINE"
        self.site_b_status = "PROMOTED_PRIMARY"
        self.active_dc = "Site B (Disaster Recovery DC - Promoted)"

        event = {
            "timestamp": time.strftime("%H:%M:%S"),
            "event": "DISASTER_FAILOVER",
            "details": f"Site A failed. Site B promoted to Active Primary. Actual RTO: {self.rto_minutes} min, RPO data loss: {self.rpo_seconds} sec."
        }
        self.dr_events_log.append(event)

        return {
            "status": "SUCCESS",
            "event": event,
            "active_dc": self.active_dc,
            "site_a_status": self.site_a_status,
            "site_b_status": self.site_b_status
        }

    def restore_and_failback(self) -> Dict[str, Any]:
        """Restores Site A and performs failback delta synchronization."""
        self.site_a_status = "ONLINE"
        self.site_b_status = "STANDBY"
        self.active_dc = "Site A (Primary DC - NY)"
        
        # Delta sync from B back to A
        self.live_storage_blocks = dict(self.site_b_blocks)

        event = {
            "timestamp": time.strftime("%H:%M:%S"),
            "event": "FAILBACK_RESTORED",
            "details": "Site A operational again. Delta synchronized from Site B. Site A restored as Primary."
        }
        self.dr_events_log.append(event)

        return {
            "status": "SUCCESS",
            "event": event,
            "active_dc": self.active_dc
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_a_status": self.site_a_status,
            "site_b_status": self.site_b_status,
            "active_dc": self.active_dc,
            "replication_mode": self.replication_mode,
            "link_latency_ms": self.link_latency_ms,
            "rpo_seconds": self.rpo_seconds,
            "rto_minutes": self.rto_minutes,
            "queue_pending_items": len(self.replication_queue),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "live_blocks": self.live_storage_blocks,
            "site_b_blocks": self.site_b_blocks,
            "dr_events": self.dr_events_log[-5:]
        }
