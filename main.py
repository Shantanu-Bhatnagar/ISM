"""
OmniStore ISM — Enterprise Information Storage & Management Platform
FastAPI Server & REST API Gateway
"""

import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ism_engine.raid_engine import RaidArray
from ism_engine.deduplication import DeduplicationEngine
from ism_engine.tiering_ilm import TieringILMEngine
from ism_engine.san_lun import SanFabricEngine
from ism_engine.replication_dr import ReplicationDREngine
from ism_engine.security_crypto import StorageSecurityEngine
from ism_engine.srm_telemetry import SRMTelemetryEngine

app = FastAPI(
    title="OmniStore ISM Platform",
    description="Enterprise Information Storage & Management Simulation & Lab System",
    version="1.0.0"
)

# Engine Singletons
raid_array = RaidArray(raid_level="5", num_disks=4)
dedupe_engine = DeduplicationEngine(chunk_size=16)
tiering_engine = TieringILMEngine()
san_engine = SanFabricEngine()
dr_engine = ReplicationDREngine()
security_engine = StorageSecurityEngine()
srm_engine = SRMTelemetryEngine()

# Seed initial dedupe files
dedupe_engine.ingest_data("financial_report_v1.docx", "ACME FINANCIAL Q1 2026: TOTAL REVENUE $45M. CONFIDENTIAL STORAGE DATA.")
dedupe_engine.ingest_data("financial_report_v2.docx", "ACME FINANCIAL Q1 2026: TOTAL REVENUE $48M. CONFIDENTIAL STORAGE DATA.")
dedupe_engine.ingest_data("backup_db_schema.sql", "CREATE TABLE users (id INT, name VARCHAR); CREATE TABLE orders (id INT);")

# Seed initial RAID data
raid_array.write_data("SYS_CONFIG", "Enterprise SAN Configuration Data Block Array Ready 2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# ===================== UI ROUTES =====================

@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ===================== OVERVIEW API =====================

@app.get("/api/overview")
async def get_overview():
    telemetry = srm_engine.sample_telemetry()
    dedupe_stats = dedupe_engine.get_stats()
    san_stats = san_engine.to_dict()
    tiering_stats = tiering_engine.to_dict()
    raid_stats = raid_array.to_dict()

    return {
        "status": "ONLINE",
        "system_name": "OmniStore ISM Enterprise Controller",
        "raid": {
            "level": raid_stats["raid_level"],
            "health": raid_stats["health"],
            "disks": len(raid_stats["disks"])
        },
        "deduplication": {
            "ratio": dedupe_stats["deduplication_ratio"],
            "space_saved_percent": dedupe_stats["space_saved_percent"],
            "files": dedupe_stats["total_files"]
        },
        "ilm_tiering": {
            "total_objects": len(tiering_stats["objects"]),
            "monthly_savings_usd": tiering_stats["cost_savings"]["monthly_savings_usd"]
        },
        "san_storage_pool": {
            "total_gb": san_stats["pool_total_gb"],
            "used_pct": san_stats["pool_usage_pct"],
            "luns_count": len(san_stats["luns"])
        },
        "dr_replication": {
            "active_site": dr_engine.active_dc,
            "mode": dr_engine.replication_mode,
            "rpo_seconds": dr_engine.rpo_seconds
        },
        "telemetry": telemetry["current"]
    }

# ===================== RAID API =====================

class RaidResetReq(BaseModel):
    raid_level: str
    num_disks: int

class RaidWriteReq(BaseModel):
    file_id: str
    data_content: str

class RaidFailReq(BaseModel):
    disk_id: int

@app.get("/api/raid/status")
async def get_raid_status():
    return raid_array.to_dict()

@app.post("/api/raid/reset")
async def reset_raid(req: RaidResetReq):
    raid_array.reset_array(req.raid_level, req.num_disks)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "RECONFIGURE_RAID", f"Reset array to RAID {req.raid_level} with {req.num_disks} disks")
    return {"status": "SUCCESS", "raid": raid_array.to_dict()}

@app.post("/api/raid/write")
async def write_raid(req: RaidWriteReq):
    res = raid_array.write_data(req.file_id, req.data_content)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "RAID_STRIPE_WRITE", f"Striped file '{req.file_id}' across RAID array")
    return res

@app.post("/api/raid/read")
async def read_raid(file_id: str = Form(...)):
    res = raid_array.read_data(file_id)
    security_engine.log_audit("operator", "OPERATOR", "RAID_READ", f"Read file '{file_id}', degraded: {res.get('reconstruction_performed')}")
    return res

@app.post("/api/raid/fail")
async def fail_raid_disk(req: RaidFailReq):
    res = raid_array.fail_disk(req.disk_id)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "SIMULATE_DISK_FAILURE", f"Disk {req.disk_id} marked as FAILED")
    return res

@app.post("/api/raid/rebuild")
async def rebuild_raid_disk(req: RaidFailReq):
    res = raid_array.rebuild_with_hotspare(req.disk_id)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "HOTSPARE_REBUILD", f"Disk {req.disk_id} rebuilt from distributed parity")
    return res

# ===================== DEDUPLICATION API =====================

class DedupeIngestReq(BaseModel):
    filename: str
    content: str

@app.get("/api/dedupe/status")
async def get_dedupe_status():
    return dedupe_engine.get_stats()

@app.post("/api/dedupe/ingest")
async def dedupe_ingest(req: DedupeIngestReq):
    res = dedupe_engine.ingest_data(req.filename, req.content)
    security_engine.log_audit("operator", "OPERATOR", "DEDUPE_INGEST", f"Ingested {req.filename}, ratio: {res['dedup_ratio']}")
    return res

@app.post("/api/dedupe/delete")
async def dedupe_delete(filename: str = Form(...)):
    res = dedupe_engine.delete_file(filename)
    security_engine.log_audit("operator", "OPERATOR", "DEDUPE_DELETE_GC", f"Deleted {filename}, GC reclaimed orphaned blocks")
    return res

@app.post("/api/dedupe/clear")
async def dedupe_clear():
    dedupe_engine.clear()
    return {"status": "SUCCESS", "message": "Deduplication index cleared."}

# ===================== TIERING & ILM API =====================

class TierObjectReq(BaseModel):
    name: str
    size_gb: float
    initial_tier: int = 1

@app.get("/api/tiering/status")
async def get_tiering_status():
    return tiering_engine.to_dict()

@app.post("/api/tiering/allocate")
async def tiering_allocate(req: TierObjectReq):
    res = tiering_engine.allocate_object(req.name, req.size_gb, req.initial_tier)
    security_engine.log_audit("operator", "OPERATOR", "ILM_OBJECT_ALLOCATE", f"Allocated {req.name} ({req.size_gb}GB) to Tier {req.initial_tier}")
    return res

@app.post("/api/tiering/access")
async def tiering_access(object_id: str = Form(...)):
    return tiering_engine.access_object(object_id)

@app.post("/api/tiering/tick")
async def tiering_tick(ticks: int = Form(3)):
    return tiering_engine.advance_time(ticks)

@app.post("/api/tiering/migrate")
async def tiering_migrate():
    res = tiering_engine.run_ilm_migration()
    security_engine.log_audit("admin", "STORAGE_ADMIN", "ILM_POLICY_EXECUTE", f"Migrated {res['migrations_executed']} objects across tiers")
    return res

# ===================== SAN & LUN API =====================

class LunCreateReq(BaseModel):
    name: str
    size_gb: float
    provisioning_type: str = "THIN"

class LunMaskReq(BaseModel):
    lun_id: int
    initiator_id: str
    allow_access: bool

@app.get("/api/san/status")
async def get_san_status():
    return san_engine.to_dict()

@app.post("/api/san/lun/create")
async def create_lun(req: LunCreateReq):
    res = san_engine.create_lun(req.name, req.size_gb, req.provisioning_type)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "SAN_LUN_PROVISION", f"Created {req.provisioning_type} LUN '{req.name}' ({req.size_gb}GB)")
    return res

@app.post("/api/san/lun/mask")
async def mask_lun(req: LunMaskReq):
    res = san_engine.apply_lun_masking(req.lun_id, req.initiator_id, req.allow_access)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "LUN_MASKING_CHANGE", f"LUN {req.lun_id} masking updated for {req.initiator_id}")
    return res

@app.post("/api/san/lun/write_growth")
async def write_lun_growth(lun_id: int = Form(...), growth_gb: float = Form(...)):
    return san_engine.write_io_to_thin_lun(lun_id, growth_gb)

# ===================== REPLICATION & DR API =====================

class ReplicationModeReq(BaseModel):
    mode: str

class DRWriteReq(BaseModel):
    block_idx: int
    new_val: str

@app.get("/api/dr/status")
async def get_dr_status():
    return dr_engine.to_dict()

@app.post("/api/dr/mode")
async def set_dr_mode(req: ReplicationModeReq):
    res = dr_engine.set_replication_mode(req.mode)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "REPLICATION_MODE_CHANGE", f"Replication set to {req.mode}")
    return res

@app.post("/api/dr/write")
async def write_dr_block(req: DRWriteReq):
    return dr_engine.write_block_with_cow(req.block_idx, req.new_val)

@app.post("/api/dr/flush")
async def flush_dr_queue():
    return dr_engine.flush_async_replication()

@app.post("/api/dr/snapshot")
async def create_snapshot(snap_name: str = Form(...)):
    res = dr_engine.create_snapshot(snap_name)
    security_engine.log_audit("operator", "OPERATOR", "SNAPSHOT_CREATE", f"Created CoW snapshot '{snap_name}'")
    return res

@app.post("/api/dr/rollback")
async def rollback_snapshot(snap_id: str = Form(...)):
    res = dr_engine.rollback_to_snapshot(snap_id)
    security_engine.log_audit("admin", "STORAGE_ADMIN", "SNAPSHOT_ROLLBACK", f"Rolled back live storage to snapshot {snap_id}")
    return res

@app.post("/api/dr/failover")
async def trigger_failover():
    res = dr_engine.trigger_disaster_failover()
    security_engine.log_audit("admin", "STORAGE_ADMIN", "DISASTER_FAILOVER", "Site A failed; promoted Site B to primary")
    return res

@app.post("/api/dr/failback")
async def trigger_failback():
    res = dr_engine.restore_and_failback()
    security_engine.log_audit("admin", "STORAGE_ADMIN", "FAILBACK_RESTORE", "Site A restored; delta synchronized")
    return res

# ===================== SECURITY & AUDIT API =====================

class CryptoReq(BaseModel):
    plaintext: str

@app.get("/api/security/status")
async def get_security_status():
    return security_engine.to_dict()

@app.post("/api/security/verify")
async def verify_audit():
    return security_engine.verify_audit_integrity()

@app.post("/api/security/encrypt")
async def encrypt_text(req: CryptoReq):
    return security_engine.encrypt_data(req.plaintext)

@app.post("/api/security/decrypt")
async def decrypt_text(ciphertext: str = Form(...)):
    return security_engine.decrypt_data(ciphertext)

# ===================== SRM TELEMETRY API =====================

@app.get("/api/telemetry/sample")
async def sample_telemetry():
    return srm_engine.sample_telemetry()

@app.post("/api/telemetry/workload")
async def switch_workload(workload: str = Form(...)):
    return srm_engine.set_workload(workload)

# ===================== END-TO-END PIPELINE API =====================

@app.post("/api/pipeline/upload")
async def upload_file_pipeline(
    file: UploadFile = File(...),
    priority: str = Form("HIGH")
):
    """
    End-to-End Enterprise ISM Pipeline:
    1. Reads incoming raw stream
    2. Hashes & chunk deduplication
    3. Compression
    4. AES-256 Volume Encryption
    5. ILM Tiering Placement
    6. RAID 5/6 Striping & XOR Parity calculation
    7. Storage Pool & Audit logging
    """
    content_bytes = await file.read()
    raw_text = content_bytes.decode('utf-8', errors='replace')
    filename = file.filename or "uploaded_data.txt"
    file_size_bytes = len(content_bytes)

    # 1. Deduplication & Compression
    dedupe_res = dedupe_engine.ingest_data(filename, raw_text)

    # 2. AES Encryption
    crypto_res = security_engine.encrypt_data(raw_text[:128])

    # 3. ILM Tier Assignment based on priority
    tier_target = 1 if priority == "HIGH" else (2 if priority == "MEDIUM" else 3)
    size_in_gb = max(0.01, round(file_size_bytes / (1024 * 1024), 2))
    tier_res = tiering_engine.allocate_object(filename, size_in_gb, initial_tier=tier_target)

    # 4. RAID Striping with Parity
    raid_file_id = f"FILE_{filename}"
    raid_res = raid_array.write_data(raid_file_id, raw_text)

    # 5. Cryptographic Audit Entry
    security_engine.log_audit("operator", "OPERATOR", "INGEST_ISM_PIPELINE", f"Stored '{filename}' ({file_size_bytes}B) through full ISM pipeline")

    return {
        "status": "SUCCESS",
        "pipeline_stages": {
            "step_1_deduplication": {
                "chunks": dedupe_res["chunks_total"],
                "unique_stored": dedupe_res["unique_blocks_stored"],
                "duplicates_saved": dedupe_res["duplicate_blocks_referenced"],
                "dedup_ratio": dedupe_res["dedup_ratio"]
            },
            "step_2_encryption": {
                "algorithm": "AES-256-XTS",
                "key_fingerprint": crypto_res["key_fingerprint"],
                "sample_cipher": crypto_res["ciphertext_b64"][:24] + "..."
            },
            "step_3_ilm_tiering": {
                "assigned_tier": f"Tier {tier_target}",
                "virtual_gb": size_in_gb,
                "tier_name": tier_res.get("tier_placed")
            },
            "step_4_raid_striping": {
                "raid_level": raid_array.raid_level,
                "chunks_striped": raid_res["chunks"],
                "array_health": raid_res["array_health"],
                "trace_preview": raid_res["trace"][:5]
            }
        },
        "summary": f"File '{filename}' safely stored across simulated RAID array with parity, deduplicated, encrypted, and tiered."
    }
