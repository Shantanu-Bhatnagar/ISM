"""
Storage Resource Management (SRM) & Performance Telemetry
Simulates real-time IOPS, Throughput (MB/s), Response Time / Latency (ms),
Cache Hit Ratios, and Capacity Forecasting / Exhaustion Runway.
"""

import random
import time
from typing import Dict, List, Any

class SRMTelemetryEngine:
    def __init__(self):
        self.workload_type = "OLTP_BALANCED"  # OLTP_BALANCED, HIGH_THROUGHPUT_STREAMING, BACKUP_STORM
        self.cache_hit_ratio = 88.5
        self.history_records: List[Dict[str, Any]] = []
        self.daily_growth_gb = 14.5
        self.total_pool_gb = 5000.0
        self.current_used_gb = 2850.0
        self._seed_history()

    def _seed_history(self):
        base_iops = 14200
        for i in range(12):
            point = self._generate_metric_point(base_iops)
            self.history_records.append(point)

    def _generate_metric_point(self, base_iops: int = 15000) -> Dict[str, Any]:
        if self.workload_type == "OLTP_BALANCED":
            iops = int(base_iops + random.randint(-1200, 1500))
            throughput_mb = round((iops * 8) / 1024, 2)  # 8KB avg block size
            latency_ms = round(random.uniform(0.8, 1.9), 2)
            cache_hit = round(random.uniform(86.0, 93.0), 1)
        elif self.workload_type == "HIGH_THROUGHPUT_STREAMING":
            iops = int(3500 + random.randint(-400, 600))
            throughput_mb = round(random.uniform(850.0, 1400.0), 2)  # Heavy MB/s
            latency_ms = round(random.uniform(3.5, 7.8), 2)
            cache_hit = round(random.uniform(62.0, 75.0), 1)
        else:  # BACKUP_STORM
            iops = int(6200 + random.randint(-800, 900))
            throughput_mb = round(random.uniform(450.0, 950.0), 2)
            latency_ms = round(random.uniform(4.0, 9.2), 2)
            cache_hit = round(random.uniform(45.0, 60.0), 1)

        return {
            "timestamp": time.strftime("%H:%M:%S"),
            "iops": iops,
            "throughput_mb_s": throughput_mb,
            "latency_ms": latency_ms,
            "cache_hit_ratio": cache_hit
        }

    def set_workload(self, workload_name: str) -> Dict[str, Any]:
        self.workload_type = workload_name.upper()
        return {"status": "SUCCESS", "current_workload": self.workload_type}

    def sample_telemetry(self) -> Dict[str, Any]:
        point = self._generate_metric_point()
        self.history_records.append(point)
        if len(self.history_records) > 20:
            self.history_records.pop(0)

        # Capacity runway forecast
        free_gb = max(0.0, self.total_pool_gb - self.current_used_gb)
        days_remaining = int(free_gb / self.daily_growth_gb) if self.daily_growth_gb > 0 else 999

        return {
            "current": point,
            "workload": self.workload_type,
            "history": self.history_records,
            "capacity_forecasting": {
                "total_capacity_gb": self.total_pool_gb,
                "current_used_gb": round(self.current_used_gb, 2),
                "free_capacity_gb": round(free_gb, 2),
                "usage_pct": round((self.current_used_gb / self.total_pool_gb) * 100, 1),
                "daily_growth_rate_gb": self.daily_growth_gb,
                "projected_exhaustion_days": days_remaining,
                "health_status": "NORMAL" if days_remaining > 60 else "WARNING_CAPACITY_NEAR"
            }
        }
