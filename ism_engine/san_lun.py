"""
Storage Area Network (SAN) & LUN Management Simulator
Simulates FC / iSCSI SAN fabric, Thin vs Thick LUN Provisioning,
Storage Pools, Fabric Zoning, and LUN Masking.
"""

from typing import Dict, List, Any, Optional

class LUN:
    def __init__(self, lun_id: int, name: str, size_gb: float, provisioning_type: str = "THIN"):
        self.lun_id = lun_id
        self.name = name
        self.size_gb = size_gb
        self.provisioning_type = provisioning_type.upper()  # THIN or THICK
        # Thick uses full allocated size immediately; Thin starts near 0 and grows
        self.allocated_gb = size_gb if self.provisioning_type == "THICK" else round(size_gb * 0.15, 2)
        self.status = "ONLINE"
        self.attached_initiators: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lun_id": self.lun_id,
            "name": self.name,
            "size_gb": self.size_gb,
            "allocated_gb": self.allocated_gb,
            "provisioning_type": self.provisioning_type,
            "status": self.status,
            "attached_initiators": self.attached_initiators,
            "efficiency": round((1 - (self.allocated_gb / self.size_gb)) * 100, 1) if self.provisioning_type == "THIN" else 0.0
        }


class HostInitiator:
    def __init__(self, host_name: str, initiator_id: str, protocol: str = "FC"):
        self.host_name = host_name
        self.initiator_id = initiator_id  # WWN or IQN
        self.protocol = protocol.upper()  # FC (Fibre Channel) or ISCSI
        self.zone_group: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host_name": self.host_name,
            "initiator_id": self.initiator_id,
            "protocol": self.protocol,
            "zone_group": self.zone_group
        }


class SanFabricEngine:
    def __init__(self):
        self.pool_total_gb = 5000.0  # 5 TB Raw Pool
        self.luns: Dict[int, LUN] = {}
        self.hosts: Dict[str, HostInitiator] = {}
        self.zones: Dict[str, List[str]] = {
            "Zone_DB_Production": ["wwn.10:00:00:00:c9:a1:01:00", "target.array_port_1"],
            "Zone_VMware_Cluster": ["iqn.1998-01.com.vmware:esxi-01", "target.array_port_2"]
        }
        self.target_ports = ["target.array_port_1", "target.array_port_2"]
        self._initialize_defaults()

    def _initialize_defaults(self):
        # Hosts
        self.hosts["wwn.10:00:00:00:c9:a1:01:00"] = HostInitiator("Oracle-DB-Server-01", "wwn.10:00:00:00:c9:a1:01:00", "FC")
        self.hosts["wwn.10:00:00:00:c9:a1:01:00"].zone_group = "Zone_DB_Production"

        self.hosts["iqn.1998-01.com.vmware:esxi-01"] = HostInitiator("ESXi-VirtualHost-Node1", "iqn.1998-01.com.vmware:esxi-01", "ISCSI")
        self.hosts["iqn.1998-01.com.vmware:esxi-01"].zone_group = "Zone_VMware_Cluster"

        self.hosts["iqn.1998-01.com.test:dev-box"] = HostInitiator("Dev-Test-Server", "iqn.1998-01.com.test:dev-box", "ISCSI")

        # Initial LUNs
        lun1 = LUN(1, "LUN_DB_Datafiles", 1500.0, "THICK")
        lun1.attached_initiators.append("wwn.10:00:00:00:c9:a1:01:00")
        self.luns[1] = lun1

        lun2 = LUN(2, "LUN_VMFS_Datastore", 2500.0, "THIN")
        lun2.attached_initiators.append("iqn.1998-01.com.vmware:esxi-01")
        self.luns[2] = lun2

    def create_lun(self, name: str, size_gb: float, provisioning_type: str = "THIN") -> Dict[str, Any]:
        """Creates a new LUN (Thin or Thick Provisioned)."""
        lun_id = max(self.luns.keys(), default=0) + 1
        new_lun = LUN(lun_id, name, size_gb, provisioning_type)

        current_pool_used = sum(l.allocated_gb for l in self.luns.values())
        if current_pool_used + new_lun.allocated_gb > self.pool_total_gb:
            return {"status": "ERROR", "message": "Storage Pool Capacity Exceeded!"}

        self.luns[lun_id] = new_lun
        return {"status": "SUCCESS", "lun": new_lun.to_dict()}

    def apply_lun_masking(self, lun_id: int, initiator_id: str, allow_access: bool = True) -> Dict[str, Any]:
        """Controls LUN Masking: grants or denies initiator access to this LUN."""
        lun = self.luns.get(lun_id)
        if not lun:
            return {"status": "ERROR", "message": "LUN not found"}
        if initiator_id not in self.hosts:
            return {"status": "ERROR", "message": "Host Initiator not recognized in SAN fabric"}

        if allow_access:
            if initiator_id not in lun.attached_initiators:
                lun.attached_initiators.append(initiator_id)
            action = "MASKED_IN (Allowed)"
        else:
            if initiator_id in lun.attached_initiators:
                lun.attached_initiators.remove(initiator_id)
            action = "MASKED_OUT (Revoked)"

        return {
            "status": "SUCCESS",
            "lun_id": lun_id,
            "initiator_id": initiator_id,
            "action": action,
            "attached_initiators": lun.attached_initiators
        }

    def write_io_to_thin_lun(self, lun_id: int, write_gb: float) -> Dict[str, Any]:
        """Simulates data growth on a Thin Provisioned LUN."""
        lun = self.luns.get(lun_id)
        if not lun:
            return {"status": "ERROR", "message": "LUN not found"}

        if lun.allocated_gb + write_gb > lun.size_gb:
            write_gb = max(0.0, lun.size_gb - lun.allocated_gb)

        lun.allocated_gb = round(lun.allocated_gb + write_gb, 2)
        return {
            "status": "SUCCESS",
            "lun_id": lun_id,
            "new_allocated_gb": lun.allocated_gb,
            "virtual_size_gb": lun.size_gb
        }

    def to_dict(self) -> Dict[str, Any]:
        total_virtual_gb = sum(l.size_gb for l in self.luns.values())
        total_allocated_gb = sum(l.allocated_gb for l in self.luns.values())
        oversubscription_ratio = round(total_virtual_gb / self.pool_total_gb, 2) if self.pool_total_gb > 0 else 1.0

        return {
            "pool_total_gb": self.pool_total_gb,
            "pool_allocated_gb": round(total_allocated_gb, 2),
            "pool_free_gb": round(max(0.0, self.pool_total_gb - total_allocated_gb), 2),
            "pool_usage_pct": round((total_allocated_gb / self.pool_total_gb) * 100, 1),
            "total_virtual_gb": round(total_virtual_gb, 2),
            "oversubscription_ratio": oversubscription_ratio,
            "luns": [l.to_dict() for l in self.luns.values()],
            "hosts": [h.to_dict() for h in self.hosts.values()],
            "zones": self.zones,
            "target_ports": self.target_ports
        }
