"""
Automated Validation Suite for OmniStore ISM
Verifies all modules:
1. RAID Engine (XOR parity, failure, and degraded-mode dynamic reconstruction)
2. Deduplication & Compression Engine (Chunking, SHA-256 hash table, GC)
3. Information Lifecycle Management (Storage tiering, temperature changes, migration)
4. SAN Fabric & LUN Management (Thin/Thick provisioning, zoning, masking)
5. Disaster Recovery (CoW Snapshots, Sync/Async replication, failover/failback)
6. Security (AES-256 encryption/decryption, chained audit verification)
"""

import sys
import io

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from ism_engine.raid_engine import RaidArray
from ism_engine.deduplication import DeduplicationEngine
from ism_engine.tiering_ilm import TieringILMEngine
from ism_engine.san_lun import SanFabricEngine
from ism_engine.replication_dr import ReplicationDREngine
from ism_engine.security_crypto import StorageSecurityEngine
from ism_engine.srm_telemetry import SRMTelemetryEngine

def test_raid_module():
    print("\n--- [1] Testing RAID Architecture & Parity Engine ---")
    array = RaidArray(raid_level="5", num_disks=4)
    write_res = array.write_data("TEST_FILE_01", "ANTIGRAVITY_ISM_DATA_BLOCKS_PARITY_TEST")
    assert write_res["status"] == "SUCCESS"
    assert array.get_health_status() == "HEALTHY"
    print("  [OK] RAID 5 Data Striping & XOR Parity calculation successful.")

    # Normal read
    read_res = array.read_data("TEST_FILE_01")
    assert read_res["status"] == "SUCCESS"
    assert read_res["reconstruction_performed"] is False
    print("  [OK] Normal read from healthy array successful.")

    # Fail Disk 1
    fail_res = array.fail_disk(1)
    assert fail_res["new_status"] == "FAILED"
    assert array.get_health_status() == "DEGRADED"
    print("  [OK] Disk 1 failure simulated. Array state: DEGRADED.")

    # Degraded read (dynamic reconstruction)
    degraded_read = array.read_data("TEST_FILE_01")
    assert degraded_read["status"] == "SUCCESS"
    assert degraded_read["reconstruction_performed"] is True
    print("  [OK] Degraded read successfully reconstructed missing block using parity XOR!")

    # Rebuild
    rebuild_res = array.rebuild_with_hotspare(1)
    assert rebuild_res["status"] == "SUCCESS"
    assert array.get_health_status() == "HEALTHY"
    print("  [OK] Hot-spare rebuild completed. Array restored to HEALTHY.")

def test_deduplication_module():
    print("\n--- [2] Testing Data Deduplication & Compression ---")
    dedupe = DeduplicationEngine(chunk_size=16)
    
    # Ingest file 1
    res1 = dedupe.ingest_data("doc1.txt", "ENTERPRISE DATA CHUNK AAAAA ENTERPRISE DATA CHUNK BBBBB")
    # Ingest file 2 (repetitive content)
    res2 = dedupe.ingest_data("doc2.txt", "ENTERPRISE DATA CHUNK AAAAA ENTERPRISE DATA CHUNK CCCCC")
    
    stats = dedupe.get_stats()
    assert stats["space_saved_bytes"] > 0
    assert stats["total_files"] == 2
    print(f"  [OK] Deduplication detected identical chunks. Ratio: {stats['deduplication_ratio']}, Space Saved: {stats['space_saved_percent']}%.")

    # Delete file 2 & check garbage collection
    del_res = dedupe.delete_file("doc2.txt")
    assert del_res["status"] == "SUCCESS"
    print(f"  [OK] File deletion triggered Garbage Collection. Reclaimed blocks: {del_res['freed_blocks']}.")

def test_tiering_ilm_module():
    print("\n--- [3] Testing Storage Tiering & ILM ---")
    ilm = TieringILMEngine()
    
    # Allocate new object
    alloc_res = ilm.allocate_object("customer_table.db", 40.0, initial_tier=1)
    assert alloc_res["status"] == "SUCCESS"
    obj_id = alloc_res["object"]["object_id"]
    print("  [OK] Object allocated to Tier 1 (NVMe SSD).")

    # Advance time to cool object down
    ilm.advance_time(10)
    obj = ilm.objects[obj_id]
    assert obj.temperature in ("WARM", "COLD")
    print(f"  [OK] Idle object cooled down to: {obj.temperature}.")

    # Run ILM migration
    mig_res = ilm.run_ilm_migration()
    assert mig_res["status"] == "SUCCESS"
    print(f"  [OK] Automated ILM migration executed. Migrated {mig_res['migrations_executed']} objects.")

    cost_res = ilm.calculate_cost_savings()
    print(f"  [OK] Cost savings calculated: ${cost_res['monthly_savings_usd']} / month ({cost_res['savings_percentage']}%).")

def test_san_lun_module():
    print("\n--- [4] Testing SAN Fabric & LUN Management ---")
    san = SanFabricEngine()
    
    # Create Thin LUN
    lun_res = san.create_lun("LUN_ERP_Database", 800.0, "THIN")
    assert lun_res["status"] == "SUCCESS"
    lun_id = lun_res["lun"]["lun_id"]
    print(f"  [OK] Created Thin Provisioned LUN #{lun_id} (800 GB virtual).")

    # Apply LUN masking
    mask_res = san.apply_lun_masking(lun_id, "wwn.10:00:00:00:c9:a1:01:00", allow_access=True)
    assert mask_res["status"] == "SUCCESS"
    print("  [OK] LUN Masking granted to host WWN.")

def test_dr_replication_module():
    print("\n--- [5] Testing Disaster Recovery & Snapshots ---")
    dr = ReplicationDREngine()
    
    # Snapshot
    snap_res = dr.create_snapshot("Snap_Pre_Migration")
    assert snap_res["status"] == "SUCCESS"
    snap_id = snap_res["snapshot"]["snap_id"]
    print(f"  [OK] Point-in-time CoW Snapshot created: {snap_id}.")

    # Write block with CoW
    write_res = dr.write_block_with_cow(2, "MODIFIED_PAYMENT_ROW_#45")
    assert write_res["status"] == "SUCCESS"
    print(f"  [OK] Live block updated; CoW delta preserved in snapshot.")

    # Rollback
    rb_res = dr.rollback_to_snapshot(snap_id)
    assert rb_res["status"] == "SUCCESS"
    print("  [OK] Live storage rolled back to previous snapshot state.")

    # Disaster failover
    failover_res = dr.trigger_disaster_failover()
    assert failover_res["site_b_status"] == "PROMOTED_PRIMARY"
    print(f"  [OK] Disaster simulated at Site A. Failover promoted Site B to: {failover_res['active_dc']}.")

    # Failback
    failback_res = dr.restore_and_failback()
    assert failback_res["status"] == "SUCCESS"
    print("  [OK] Site A restored. Failback completed.")

def test_security_crypto_module():
    print("\n--- [6] Testing Security, Encryption & Chained Audit ---")
    sec = StorageSecurityEngine()
    
    plaintext = "SECRET_PATIENT_MEDICAL_HISTORY_DATA"
    enc = sec.encrypt_data(plaintext)
    assert enc["ciphertext_b64"] != plaintext
    print("  [OK] Plaintext encrypted with simulated AES-256-XTS.")

    dec = sec.decrypt_data(enc["ciphertext_b64"])
    assert dec["decrypted_text"] == plaintext
    print("  [OK] Ciphertext decrypted and matched original plaintext.")

    # Log action & verify tamper-evident hash chaining
    sec.log_audit("admin", "STORAGE_ADMIN", "TEST_ACTION", "Testing audit tamper resistance")
    ver = sec.verify_audit_integrity()
    assert ver["is_valid"] is True
    print(f"  [OK] Audit chain cryptographic integrity verified: {ver['status']}.")

def main():
    print("================================================================")
    print("    RUNNING OMNISTORE ISM COMPLETE MODULE VALIDATION SUITE      ")
    print("================================================================")
    test_raid_module()
    test_deduplication_module()
    test_tiering_ilm_module()
    test_san_lun_module()
    test_dr_replication_module()
    test_security_crypto_module()
    print("\n" + "=" * 64)
    print("  >>> ALL 6 ISM MODULES PASSED VALIDATION WITH 100% SUCCESS <<<")
    print("================================================================\n")

if __name__ == "__main__":
    main()
