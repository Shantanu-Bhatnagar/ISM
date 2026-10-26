"""
Information Lifecycle Management (ILM) & Automated Storage Tiering Engine
Simulates Tier 1 (NVMe SSD), Tier 2 (SAS HDD), Tier 3 (Cold Archive),
dynamic access frequency tracking, automatic demotion/promotion policies, and cost savings.
"""

import time
from typing import Dict, List, Any, Optional

class StorageTier:
    def __init__(self, tier_id: int, name: str, media_type: str, total_gb: float, iops: int, latency_ms: float, cost_per_gb: float):
        self.tier_id = tier_id
        self.name = name
        self.media_type = media_type
        self.total_gb = total_gb
        self.used_gb = 0.0
        self.iops = iops
        self.latency_ms = latency_ms
        self.cost_per_gb = cost_per_gb
        self.objects: Dict[str, "StorageObject"] = {}

    def available_gb(self) -> float:
        return max(0.0, self.total_gb - self.used_gb)

    def usage_percent(self) -> float:
        return round((self.used_gb / self.total_gb) * 100, 1) if self.total_gb > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier_id": self.tier_id,
            "name": self.name,
            "media_type": self.media_type,
            "total_gb": self.total_gb,
            "used_gb": round(self.used_gb, 2),
            "free_gb": round(self.available_gb(), 2),
            "usage_percent": self.usage_percent(),
            "iops": self.iops,
            "latency_ms": self.latency_ms,
            "cost_per_gb": self.cost_per_gb,
            "object_count": len(self.objects)
        }


class StorageObject:
    def __init__(self, object_id: str, name: str, size_gb: float, tier_id: int):
        self.object_id = object_id
        self.name = name
        self.size_gb = size_gb
        self.tier_id = tier_id
        self.access_count = 1
        self.last_access_tick = 0
        self.created_at = time.time()
        self.temperature = "HOT"  # HOT, WARM, COLD

    def record_access(self, current_tick: int):
        self.access_count += 1
        self.last_access_tick = current_tick
        self._update_temperature(current_tick)

    def _update_temperature(self, current_tick: int):
        age_in_ticks = current_tick - self.last_access_tick
        if age_in_ticks <= 3 and self.access_count >= 5:
            self.temperature = "HOT"
        elif age_in_ticks <= 8 or self.access_count >= 2:
            self.temperature = "WARM"
        else:
            self.temperature = "COLD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "size_gb": self.size_gb,
            "tier_id": self.tier_id,
            "access_count": self.access_count,
            "temperature": self.temperature,
            "last_access_tick": self.last_access_tick
        }


class TieringILMEngine:
    def __init__(self):
        self.tiers: Dict[int, StorageTier] = {
            1: StorageTier(1, "Tier 1 - Extreme Performance", "NVMe SSD", total_gb=500.0, iops=75000, latency_ms=0.2, cost_per_gb=1.20),
            2: StorageTier(2, "Tier 2 - Capacity Enterprise", "SAS HDD", total_gb=2000.0, iops=1200, latency_ms=6.5, cost_per_gb=0.25),
            3: StorageTier(3, "Tier 3 - Cold Archive", "Cloud Tape / Blob", total_gb=10000.0, iops=100, latency_ms=45.0, cost_per_gb=0.02)
        }
        self.objects: Dict[str, StorageObject] = {}
        self.current_tick = 0
        self.migration_history: List[Dict[str, Any]] = []
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        samples = [
            ("obj_db_oltp", "customer_orders_active.db", 45.0, 1, 18),
            ("obj_web_cache", "redis_session_cache.dump", 20.0, 1, 24),
            ("obj_crm_monthly", "crm_analytics_2026.parquet", 120.0, 2, 7),
            ("obj_hr_records", "employee_tax_records.pdf", 80.0, 2, 3),
            ("obj_sec_audit", "firewall_logs_2025.tar.gz", 350.0, 3, 0),
            ("obj_media_vault", "training_video_master.mp4", 450.0, 3, 1),
        ]
        for oid, name, size, tier, initial_access in samples:
            obj = StorageObject(oid, name, size, tier)
            obj.access_count = initial_access
            obj.last_access_tick = 0 if tier == 1 else (5 if tier == 2 else 15)
            obj._update_temperature(self.current_tick)
            self.objects[oid] = obj
            self.tiers[tier].objects[oid] = obj
            self.tiers[tier].used_gb += size

    def allocate_object(self, name: str, size_gb: float, initial_tier: int = 1) -> Dict[str, Any]:
        """Places a new data object into a specified tier, with fallback if full."""
        tier = self.tiers.get(initial_tier)
        if not tier or tier.available_gb() < size_gb:
            # Fallback to next tier
            for fallback_id in sorted(self.tiers.keys()):
                if self.tiers[fallback_id].available_gb() >= size_gb:
                    tier = self.tiers[fallback_id]
                    initial_tier = fallback_id
                    break

        if not tier or tier.available_gb() < size_gb:
            return {"status": "ERROR", "message": "Storage capacity exhausted across all tiers"}

        oid = f"obj_{int(time.time()*1000) % 100000}"
        obj = StorageObject(oid, name, size_gb, initial_tier)
        self.objects[oid] = obj
        tier.objects[oid] = obj
        tier.used_gb += size_gb

        return {
            "status": "SUCCESS",
            "object": obj.to_dict(),
            "tier_placed": tier.name
        }

    def access_object(self, object_id: str) -> Dict[str, Any]:
        """Simulates read/write access to an object, increasing temperature."""
        obj = self.objects.get(object_id)
        if not obj:
            return {"status": "ERROR", "message": "Object not found"}

        self.current_tick += 1
        obj.record_access(self.current_tick)
        tier = self.tiers[obj.tier_id]

        return {
            "status": "SUCCESS",
            "object_id": object_id,
            "access_count": obj.access_count,
            "temperature": obj.temperature,
            "served_by_tier": tier.name,
            "latency_ms": tier.latency_ms
        }

    def advance_time(self, ticks: int = 3) -> Dict[str, Any]:
        """Advances simulation time ticks without access, cooling down objects."""
        self.current_tick += ticks
        for obj in self.objects.values():
            obj._update_temperature(self.current_tick)
        return {"status": "SUCCESS", "current_tick": self.current_tick}

    def run_ilm_migration(self) -> Dict[str, Any]:
        """Executes Information Lifecycle Management policies:
        - Demotes COLD data from Tier 1 -> Tier 2 -> Tier 3
        - Promotes HOT data from Tier 3 / Tier 2 -> Tier 1
        """
        migrations = []

        for obj in list(self.objects.values()):
            old_tier_id = obj.tier_id
            new_tier_id = old_tier_id

            if obj.temperature == "COLD":
                if old_tier_id == 1:
                    new_tier_id = 2
                elif old_tier_id == 2:
                    new_tier_id = 3
            elif obj.temperature == "HOT":
                if old_tier_id == 3:
                    new_tier_id = 2
                elif old_tier_id == 2:
                    new_tier_id = 1

            if new_tier_id != old_tier_id:
                # Perform physical move
                old_tier = self.tiers[old_tier_id]
                new_tier = self.tiers[new_tier_id]
                
                if new_tier.available_gb() >= obj.size_gb:
                    del old_tier.objects[obj.object_id]
                    old_tier.used_gb = max(0.0, old_tier.used_gb - obj.size_gb)

                    new_tier.objects[obj.object_id] = obj
                    new_tier.used_gb += obj.size_gb
                    obj.tier_id = new_tier_id

                    entry = {
                        "object_name": obj.name,
                        "size_gb": obj.size_gb,
                        "from_tier": old_tier.name,
                        "to_tier": new_tier.name,
                        "reason": f"Temperature changed to {obj.temperature} (Access Count: {obj.access_count})",
                        "tick": self.current_tick
                    }
                    migrations.append(entry)
                    self.migration_history.append(entry)

        return {
            "status": "SUCCESS",
            "migrations_executed": len(migrations),
            "migrations": migrations,
            "cost_analysis": self.calculate_cost_savings()
        }

    def calculate_cost_savings(self) -> Dict[str, Any]:
        """Computes financial optimization: All Tier 1 vs Tiered ILM Architecture."""
        total_used = sum(t.used_gb for t in self.tiers.values())
        cost_if_all_tier1 = total_used * self.tiers[1].cost_per_gb
        actual_tiered_cost = sum(t.used_gb * t.cost_per_gb for t in self.tiers.values())
        monthly_savings = max(0.0, cost_if_all_tier1 - actual_tiered_cost)
        savings_pct = round((monthly_savings / cost_if_all_tier1) * 100, 1) if cost_if_all_tier1 > 0 else 0.0

        return {
            "total_stored_gb": round(total_used, 2),
            "cost_unoptimized_usd": round(cost_if_all_tier1, 2),
            "cost_tiered_ilm_usd": round(actual_tiered_cost, 2),
            "monthly_savings_usd": round(monthly_savings, 2),
            "savings_percentage": savings_pct
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_tick": self.current_tick,
            "tiers": [t.to_dict() for t in self.tiers.values()],
            "objects": [o.to_dict() for o in self.objects.values()],
            "recent_migrations": self.migration_history[-8:],
            "cost_savings": self.calculate_cost_savings()
        }
