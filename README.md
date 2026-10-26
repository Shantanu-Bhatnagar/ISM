# 🗄️ OmniStore ISM: Enterprise Information Storage & Management Platform

> **An End-to-End Enterprise Storage Area Network (SAN), RAID, Deduplication, ILM Tiering, and Disaster Recovery Simulator & Management Console.**

Designed specifically for **Information Storage and Management (ISM)** academic curricula, lab evaluations, and technical project presentations.

---

## ⚡ Quick Start (Under 1 Minute)

### Option 1: 1-Click Launch (Windows)
Double-click `run.bat` in this folder. It will install dependencies, launch the server, and automatically open the interactive dashboard in your default browser.

### Option 2: Command Line Launch
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application (Automatically opens browser at http://127.0.0.1:8000)
python run.py
```

### Option 3: Automated Validation Suite
To verify all 6 ISM modules before your presentation:
```bash
python test_system.py
```

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |   OmniStore ISM Web Console           |
                                  |   (Glassmorphic Dark Mode Dashboard)  |
                                  +-------------------+-------------------+
                                                      |  REST API / WebSockets
                                                      v
                                  +---------------------------------------+
                                  |   FastAPI Central Storage Controller  |
                                  +---+-------+-------+-------+-------+---+
                                      |       |       |       |       |
                 +--------------------+   +---+---+   |   +---+---+   +--------------------+
                 |                        |       |   |   |       |                        |
                 v                        v       v   v   v       v                        v
        +-----------------+       +----------------+ +-----------------+       +-----------------+
        |  Module 1: RAID |       |  Module 2: ILM | | Module 3: Dedupe|       |  Module 4: SAN  |
        |  Parity Engine  |       | 3-Tier Storage | | SHA-256 Chunks  |       |  Fabric & LUNs  |
        |  (0, 1, 5, 6, 10|       | NVMe/SAS/Cloud | | GC Reclaim      |       |  Thin/Thick LUN |
        +-----------------+       +----------------+ +-----------------+       +-----------------+
                 |                                                                      |
                 +------------------------+                      +----------------------+
                                          v                      v
                                  +---------------------------------------+
                                  |   Module 5: DR & Multi-Site WAN Link  |
                                  |   CoW Snapshots & RPO/RTO Simulator   |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |   Module 6: KMS Security & Audit Log  |
                                  |   AES-256-XTS & Tamper-Evident Chaining|
                                  +---------------------------------------+
```

---

## 📦 Core Modules Breakdown

### 1. RAID Architecture & Fault Tolerance Engine (`raid_engine.py`)
- **Supported Levels**: RAID 0 (Striping), RAID 1 (Mirroring), RAID 5 (Block striping with distributed parity), RAID 6 (Dual distributed parity $P+Q$), and RAID 10 (Striped mirrors).
- **Parity Calculations**: Bitwise XOR math:
  $$P = D_1 \oplus D_2 \oplus D_3$$
- **Dynamic Reconstruction**: When a disk is marked `FAILED`, the controller continues serving read requests by computing missing data on the fly:
  $$D_{\text{missing}} = P \oplus \sum D_{\text{surviving}}$$
- **Online Hot Spare Rebuild**: Automated rebuild into a dedicated spare drive.

### 2. Information Lifecycle Management (ILM) & Storage Tiering (`tiering_ilm.py`)
- **Tier 1 (Performance)**: NVMe SSD (75,000 IOPS, 0.2 ms latency, $1.20/GB/mo).
- **Tier 2 (Capacity)**: Enterprise SAS HDD (1,200 IOPS, 6.5 ms latency, $0.25/GB/mo).
- **Tier 3 (Archive)**: Cloud Deep Archive / Tape (100 IOPS, 45 ms latency, $0.02/GB/mo).
- **Dynamic Temperature Tracking**: Classifies data volumes as **HOT**, **WARM**, or **COLD** based on access count and recency.
- **Cost Optimizer**: Calculates exact dollar savings per month achieved through ILM tiering vs storing everything on expensive NVMe.

### 3. Content-Addressable Deduplication & Compression (`deduplication.py`)
- **Block Chunking**: Fixed-size chunking with cryptographic SHA-256 fingerprinting.
- **Reference-Counted Hash Table**: Stores unique physical blocks once; duplicate blocks point to existing hashes.
- **Garbage Collection (GC)**: When files are deleted, reference counts decrement; unreferenced blocks are reclaimed.
- **Analytics**: Real-time Deduplication Ratio ($Raw : Physical$), Space Saved %, and compression statistics.

### 4. Storage Area Network (SAN) & LUN Management (`san_lun.py`)
- **Storage Virtualization**: Aggregates raw storage disks into an enterprise Storage Pool.
- **Thin vs Thick Provisioning**: Demonstrates oversubscription ratio where thin LUNs advertise large virtual sizes while consuming physical blocks only on demand.
- **SAN Fabric Zoning & LUN Masking**: Simulates Fibre Channel (FC) WWN and iSCSI IQN host initiators, access permissions, and fabric switch zones.

### 5. Disaster Recovery (DR) & Multi-Site Replication (`replication_dr.py`)
- **Multi-Site Architecture**: Primary DC (New York) to Remote DR DC (Frankfurt) WAN link.
- **Synchronous vs Asynchronous Replication**:
  - *Synchronous*: Zero RPO (no data loss), adds WAN round-trip latency to writes.
  - *Asynchronous*: Buffered queue, minimal application latency, small RPO window.
- **Copy-on-Write (CoW) Snapshots**: Freezes point-in-time state without cloning all data. Supports instant point-in-time rollback.
- **Disaster Injection**: Click to fail Site A -> Automated DR failover promotes Site B to active master -> Failback delta sync restores Site A.

### 6. Storage Security & Cryptographic Audit (`security_crypto.py`)
- **Data-at-Rest Encryption**: AES-256-XTS volume encryption with KMS master key vault.
- **Role-Based Access Control (RBAC)**: Storage Admin, Operator, and Auditor roles.
- **Tamper-Evident Chained Audit Log**: Cryptographically chained audit records ($H_n = \text{SHA256}(H_{n-1} + \text{data})$). Tampering with any historical record breaks the chain.

### 7. Storage Resource Management (SRM) & Telemetry (`srm_telemetry.py`)
- Real-time simulation of:
  - **IOPS** (Random vs Sequential)
  - **Throughput / Bandwidth** (MB/s)
  - **Response Time / Latency** (ms)
  - **Array Controller Cache Hit Ratio** (%)
  - **Capacity Forecasting Runway** (Days until exhaustion based on daily consumption velocity).

---

## 🎯 Step-by-Step Demo Walkthrough (For College Evaluation)

When showing this project to an evaluator or professor, follow this 5-minute presentation script:

1. **Dashboard Overview**:
   - Point out the top telemetry ribbon showing live IOPS (14,000+), sub-millisecond latency, and cache hit ratio.
   - Show how changing the Workload Profile (OLTP -> Streaming Data -> Backup Storm) dynamically shifts throughput and latency.

2. **RAID Engine Tab**:
   - Write a data string like `"STUDENT_EXAM_GRADE_DATA"`.
   - Point to the **Parity Calculation Inspector** showing the exact XOR equation $D_0 \oplus D_1 \oplus D_2 = P$.
   - Click **"Simulate Failure"** on Disk 1. The status LED turns pulsing red, and the array enters **DEGRADED** mode.
   - Click **"Read / Reconstruct"**: Point out how the controller reconstructed the missing block in real-time from the surviving blocks and parity!
   - Click **"Rebuild (Hot Spare)"** to show online disk reconstruction.

3. **Deduplication Tab**:
   - Ingest a file, then click **"Insert Similar Duplicate Version"**.
   - Watch the **Deduplication Ratio** increase to > 3:1 and space savings exceed 65%!
   - Show the **SHA-256 block table** where `ref_count` increments without creating new physical blocks.
   - Delete a file and show how the **Garbage Collector** reclaims orphaned blocks.

4. **Storage Tiering Tab**:
   - Show the 3 tiers (NVMe SSD, SAS HDD, Cloud Archive) and the **Cost Savings Banner** ($700+ saved/mo).
   - Click **"Access"** on a cold object to heat it up to HOT.
   - Click **"Execute Automated ILM Policies"** and watch the system automatically promote it to NVMe SSD!

5. **Disaster Recovery Tab**:
   - Toggle between **Synchronous** ($RPO = 0.0s$) and **Asynchronous** mode.
   - Take a point-in-time **CoW Snapshot**.
   - Click **"⚡ Simulate Disaster at Site A"**: Site A turns red, and Site B is automatically promoted to active primary master.
   - Click **"Restore & Failback"** to bring Site A back online.

6. **End-to-End Ingestion Lab Tab**:
   - Click **"Use Built-in Enterprise Sample"** or upload any file.
   - Click **"🚀 Run Full ISM Pipeline"** and watch all 5 stages animate sequentially.

---

## 🎓 Viva Questions & Answers (Quick Reference)

**Q1: What is the difference between DAS, NAS, and SAN?**  
- **DAS (Direct Attached Storage)**: Block-level storage connected directly to a host via SAS/SATA without a network.
- **NAS (Network Attached Storage)**: File-level storage accessible over LAN via CIFS/SMB or NFS.
- **SAN (Storage Area Network)**: Dedicated high-speed network (Fibre Channel or iSCSI) providing block-level access to consolidated storage pools.

**Q2: What is the storage efficiency and fault tolerance of RAID 5 vs RAID 6?**  
- **RAID 5**: Uses $N-1$ disks for data and 1 disk worth of distributed parity ($P$). Can survive **1** disk failure. Usable capacity: $(N-1)/N$.
- **RAID 6**: Uses dual parity ($P$ and $Q$). Can survive **2** simultaneous disk failures. Usable capacity: $(N-2)/N$.

**Q3: What are RPO and RTO in Disaster Recovery?**  
- **RPO (Recovery Point Objective)**: The maximum acceptable age of data that can be lost (in time: seconds/hours).
- **RTO (Recovery Time Objective)**: The maximum duration of downtime permitted to restore operations after a disaster.

**Q4: Explain Thin vs Thick Provisioning.**  
- **Thick Provisioning**: Physical storage is 100% committed and allocated upfront at LUN creation.
- **Thin Provisioning**: Storage is allocated on-demand as blocks are written, allowing storage oversubscription and higher utilization.

---

## 📁 File Structure

```
c:\Users\swati\Desktop\ISM Project\
├── run.bat                     # Windows 1-click batch launcher
├── run.py                      # Python startup script (opens browser)
├── main.py                     # FastAPI REST server & controller
├── requirements.txt            # Python dependencies
├── test_system.py              # Automated test suite (all 6 modules)
├── README.md                   # Complete documentation & demo guide
├── ISM_PROJECT_REPORT.md       # Comprehensive ready-to-submit project report
├── ism_engine/
│   ├── __init__.py
│   ├── raid_engine.py          # RAID 0, 1, 5, 6, 10 + XOR parity math
│   ├── deduplication.py        # SHA-256 chunking, dedupe & GC
│   ├── tiering_ilm.py          # 3-tier ILM policy & cost savings
│   ├── san_lun.py              # SAN pool, Thin/Thick LUNs, zoning & masking
│   ├── replication_dr.py       # CoW snapshots, sync/async DR failover
│   ├── security_crypto.py      # AES-256 encryption & tamper-evident audit
│   └── srm_telemetry.py        # Real-time IOPS, throughput, latency, runway
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphic dark theme design system
│   └── js/
│       └── app.js              # Interactive UI controller & animations
└── templates/
    └── index.html              # Operations console dashboard
```
