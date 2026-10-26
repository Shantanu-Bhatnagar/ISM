# 🎓 OmniStore ISM: Student Project Explanation & Presentation Guide

> **How to Explain This Project to Your Teacher / Evaluator / External Examiner**  
> *Written in simple, clear, student-friendly language with live demo steps and ready-made answers.*

---

## 📌 Table of Contents
1. [The 30-Second Elevator Pitch (Start Here)](#1-the-30-second-elevator-pitch)
2. [Why We Built This Project (The Problem We Are Solving)](#2-why-we-built-this-project)
3. [High-Level Architecture (What is inside the project?)](#3-high-level-architecture)
4. [Deep Dive into the 6 Core Modules (How each part works)](#4-deep-dive-into-the-6-core-modules)
   - [Module 1: RAID & Parity Engine (Fault Tolerance)](#module-1-raid--parity-engine)
   - [Module 2: Deduplication & Compression (Storage Efficiency)](#module-2-deduplication--compression)
   - [Module 3: Information Lifecycle Management (Storage Tiering & Cost Savings)](#module-3-storage-tiering--ilm)
   - [Module 4: Storage Area Network & LUNs (Storage Virtualization)](#module-4-san-fabric--lun-management)
   - [Module 5: Disaster Recovery & Replication (Business Continuity)](#module-5-disaster-recovery--replication)
   - [Module 6: Storage Security & Audit Trail (Encryption & Compliance)](#module-6-storage-security--audit-trail)
5. [Bonus Highlights: SRM Telemetry & End-to-End Ingestion Lab](#5-bonus-highlights)
6. [Step-by-Step Live Demo Script (What to click and what to say)](#6-step-by-step-live-demo-script)
7. [Teacher / Viva Q&A (Anticipated questions & winning answers)](#7-teacher--viva-qa)
8. [Technology Stack & File Structure](#8-technology-stack--file-structure)

---

## 1. The 30-Second Elevator Pitch

> 🗣️ **Say this to your teacher when they say: *"Tell me briefly what you have made"***:
>
> *"Good morning/afternoon Ma'am/Sir. My project is called **OmniStore ISM**. It is an interactive, enterprise-grade simulation platform for **Information Storage and Management (ISM)**.*  
> *In the real world, big companies like banks, hospitals, and cloud providers deal with petabytes of critical data. They face hard drive crashes, skyrocketing storage costs, data duplication, disaster risks, and cyber threats.*  
> *Instead of just studying the textbook theory of SAN, RAID, Deduplication, and Disaster Recovery, **we built a working software platform that simulates and visualizes all 6 core pillars of enterprise storage in real-time** — complete with mathematical XOR parity recovery, SHA-256 deduplication, 3-tier cost optimization, multi-site disaster failover, and a live dark-mode operations dashboard."*

---

## 2. Why We Built This Project

### The Real-World Problem:
In standard computer science courses, storage is usually treated as a simple black box (like reading or writing to a local hard drive or simple database). But in real enterprise data centers:
1. **Drives fail all the time:** A drive can die at 2 AM. The system cannot stop serving customers.
2. **Storage is extremely expensive:** Storing everything on ultra-fast solid-state drives (NVMe SSDs) burns millions of dollars unnecessarily.
3. **Huge data redundancy:** 60% to 80% of data across corporate servers is identical duplicate copies (e.g., the same email attachment sent to 500 employees).
4. **Disasters happen:** Earthquakes, fiber cuts, or power grid failures can wipe out an entire city's data center.
5. **Regulations require proof:** Laws like HIPAA, GDPR, and Sarbanes-Oxley require companies to prove that data was never altered or tampered with.

### What We Are Doing Here:
We designed **OmniStore ISM** to take the concepts directly from the **EMC / Dell Information Storage and Management curriculum** and implement them as working algorithms in Python with an interactive web UI. Evaluators can directly click buttons, simulate hardware failures, inject disasters, watch mathematical data recovery happen in real-time, and see storage cost graphs update instantly.

---

## 3. High-Level Architecture

Here is how our entire system is arranged from top to bottom:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                   ENTERPRISE WEB CONSOLE (Glassmorphic Dark UI)        │
 │              Live IOPS, Latency, Bandwidth, Module Visualizers         │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ REST API & Real-time Telemetry
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │               FASTAPI CENTRAL STORAGE CONTROLLER (main.py)             │
 └───────┬──────────────┬─────────────┬─────────────┬─────────────┬───────┘
         │              │             │             │             │
 ┌───────▼──────┐┌──────▼──────┐┌─────▼──────┐┌─────▼──────┐┌─────▼──────┐
 │   MODULE 1   ││   MODULE 2   ││  MODULE 3  ││  MODULE 4  ││  MODULE 5  │
 │  RAID Engine ││ Deduplication││ILM Tiering ││ SAN & LUNs ││Disaster Rec│
 │  XOR Parity  ││SHA-256 Chunks││Hot/Warm/Cld││Thin/Thick  ││Sync/Async  │
 │ Degraded Read││  Garbage Col ││$ Savings   ││Zoning/Mask ││CoW Snapshot│
 └───────┬──────┘└──────────────┘└────────────┘└────────────┘└─────┬──────┘
         │                                                         │
         └───────────────────────────┬─────────────────────────────┘
                                     │
                             ┌───────▼──────┐
                             │   MODULE 6   │
                             │   Security   │
                             │AES-256 + KMS │
                             │ Chained Audit│
                             └──────────────┘
```

---

## 4. Deep Dive into the 6 Core Modules

---

### Module 1: RAID & Parity Engine (`raid_engine.py`)
*Theme: "Never lose data even if a physical hard drive explodes."*

#### 💡 Simple Everyday Analogy:
Imagine three friends write numbers on a board: Friend 1 writes `5`, Friend 2 writes `7`. Together they calculate the total: `5 + 7 = 12`.  
If Friend 2 wipes out their number, you don't panic! You simply subtract: `12 - 5 = 7`. You recovered the lost number without needing a complete second copy!

#### ⚙️ How It Works in Our Project:
1. **Striping:** We take incoming data (e.g., `"ENTERPRISE_DATABASE"`) and break it into chunks across multiple disks for faster read/write speeds.
2. **RAID 5 XOR Parity:** In RAID 5, we use the bitwise XOR operator ($\oplus$) across data disks to create a Parity block ($P$):
   $$P = D_0 \oplus D_1 \oplus D_2$$
   XOR has a magical mathematical property: $A \oplus A = 0$ and $A \oplus 0 = A$.
3. **Simulated Failure:** In our dashboard, you can click **"Simulate Failure"** on Disk 1. The status LED turns blinking red, and the array enters **DEGRADED mode**.
4. **Degraded In-Flight Reconstruction:** When a user requests data while Disk 1 is dead, the storage controller does NOT throw an error! It reads the surviving disks and the parity disk, XORs them together on the fly:
   $$D_{\text{missing}} = P \oplus D_0 \oplus D_2$$
   The customer gets their data back in microseconds!
5. **Hot-Spare Rebuild:** Click **"Rebuild with Hot Spare"**, and a standby spare drive automatically receives the calculated reconstructed data, returning the array to **HEALTHY**.

---

### Module 2: Deduplication & Compression (`deduplication.py`)
*Theme: "Store identical data once, save 70% storage space."*

#### 💡 Simple Everyday Analogy:
If 50 students in a class submit the exact same 100-page textbook PDF as an assignment, the school server doesn't need to save 5,000 pages. It saves **one single copy** of the book and gives each student a digital "pointer/shortcut" to it.

#### ⚙️ How It Works in Our Project:
1. **Fixed-Size Chunking:** Ingested files are split into small 16-byte blocks.
2. **SHA-256 Fingerprinting:** Every block gets a unique cryptographic hash fingerprint.
3. **Reference Counter Index:**
   - If the hash is new $\rightarrow$ save the block physically to storage, set `ref_count = 1`.
   - If the hash already exists $\rightarrow$ do NOT save another block! Just increment `ref_count = ref_count + 1`.
4. **Live Deduplication Metrics:** The dashboard shows:
   $$\text{Deduplication Ratio} = \frac{\text{Virtual Raw Ingested Bytes}}{\text{Actual Physical Bytes Consumed}}$$
   $$\text{Space Saved \%} = \left(1 - \frac{\text{Physical Bytes}}{\text{Raw Bytes}}\right) \times 100\%$$
   Typical savings in our simulator reach **65% to 75%** (a 3.4:1 ratio)!
5. **Garbage Collection (GC):** When a file is deleted, we decrement the reference counts of its blocks. If a block's `ref_count` drops to `0`, our Garbage Collector reclaims the physical block and frees up disk space.

---

### Module 3: Storage Tiering & ILM (`tiering_ilm.py`)
*Theme: "Put active data on super-fast expensive drives, move old data to cheap archive."*

#### 💡 Simple Everyday Analogy:
The notebook you use every single day sits directly on your study desk (Tier 1). Textbooks from last semester are kept in a bookshelf (Tier 2). Old kindergarten notebooks are packed away in boxes in the attic (Tier 3). You don't buy an expensive desk big enough to hold every book you've ever owned in your life!

#### ⚙️ How It Works in Our Project:
Our engine models a 3-tier enterprise storage hierarchy:
- **Tier 1 (Performance):** NVMe SSD — Super fast (75,000 IOPS, 0.2 ms latency), but expensive ($1.20 per GB/month).
- **Tier 2 (Capacity):** Enterprise SAS HDD — Balanced (1,200 IOPS, 6.5 ms latency, $0.25 per GB/month).
- **Tier 3 (Archive):** Cloud Deep Archive / Tape — Slower (100 IOPS, 45 ms latency), but dirt cheap ($0.02 per GB/month).

1. **Temperature Tracking:** Every data object has a temperature:
   - **HOT:** Accessed frequently within recent cycles $\rightarrow$ Tier 1.
   - **WARM:** Moderate access $\rightarrow$ Tier 2.
   - **COLD:** Rarely or never accessed $\rightarrow$ Tier 3.
2. **Automated ILM Policy Migration:** The controller scans storage periodically. Cold data on expensive NVMe SSD is automatically demoted to Cloud Archive.
3. **Cost Savings Calculator:** The dashboard calculates the exact company dollar savings:
   $$\text{Savings} = (\text{Total GB} \times \text{Tier 1 Price}) - (\text{Actual Multi-Tier Cost})$$
   It demonstrates how companies save **80%+ on monthly storage bills** without losing access to any data.

---

### Module 4: SAN Fabric & LUN Management (`san_lun.py`)
*Theme: "Virtualize all physical drives into one giant pool and assign slices safely to servers."*

#### 💡 Simple Everyday Analogy:
Instead of giving each apartment in a building its own tiny water tank that might overflow or run dry, the building has one giant master water reservoir (Storage Pool). Each apartment gets a pipe with a valve and meter (LUN), and security keys prevent Apartment A from tapping into Apartment B's pipe (LUN Masking & Zoning).

#### ⚙️ How It Works in Our Project:
1. **Storage Pool Virtualization:** We pool raw disk drives into a unified 10,000 GB shared storage pool.
2. **Thin vs. Thick Provisioning:**
   - **Thick LUN:** If you ask for 500 GB, the storage controller immediately locks and reserves 500 GB of physical space upfront, even if you only write 10 GB of data.
   - **Thin LUN (Smart Oversubscription):** If you ask for 800 GB, the controller tells your server *"Yes, you have 800 GB"*, but physically only allocates blocks as you actually write data (e.g., 50 GB). This lets data centers over-commit capacity safely!
3. **SAN Fabric Zoning & LUN Masking:** In an enterprise SAN, servers connect via Fibre Channel switches. We simulate **WWN (World Wide Name)** and **iSCSI IQN** identifiers. LUN masking ensures only authorized servers (like an ERP database server) can access specific sensitive LUNs, while web servers are locked out.

---

### Module 5: Disaster Recovery & Replication (`replication_dr.py`)
*Theme: "If a natural disaster destroys the main data center, business continues in seconds."*

#### 💡 Simple Everyday Analogy:
Think of typing in Google Docs. When you type, your words are automatically synced to cloud servers. If your laptop suddenly catches fire, your document is safe because an exact copy was already sent to another location.

#### ⚙️ How It Works in Our Project:
1. **Multi-Site Architecture:**
   - **Site A (Primary DC):** Located in New York (Active Master).
   - **Site B (Remote DR DC):** Located in Frankfurt (Standby Target).
2. **Synchronous vs. Asynchronous Replication:**
   - **Synchronous:** A write is acknowledged to the application only after it is saved at BOTH Site A and Site B. **$RPO = 0$ seconds** (Zero data loss), but adds slight network round-trip delay.
   - **Asynchronous:** Writes are acknowledged locally at Site A immediately and queued for background transmission to Site B. Faster performance, but tiny $RPO$ window (a few seconds).
3. **Copy-on-Write (CoW) Snapshots:**
   - A snapshot takes a point-in-time "frozen picture" of storage instantly without copying all gigabytes.
   - When a block is modified, the original untouched block is copied to snapshot delta storage first (*Copy-on-Write*), then new data is written.
   - If an accidental deletion or ransomware attack occurs, click **"Rollback to Snapshot"** to instantly revert the storage state!
4. **Live Disaster Injection & Automated Failover:**
   - Click **"⚡ Simulate Disaster at Site A"**.
   - Site A goes down (red warning).
   - The system automatically triggers failover: **Site B is promoted to Active Primary Master**.
   - Business operations continue with a Recovery Time Objective (**$RTO$**) of under 3 minutes!
   - Click **"Restore & Failback"** to bring Site A back online and delta-sync the newest changes.

---

### Module 6: Storage Security & Audit Trail (`security_crypto.py`)
*Theme: "Keep data encrypted at rest and create a tamper-proof audit trail that cannot be hacked."*

#### 💡 Simple Everyday Analogy:
Think of an official bank passbook where every single transaction is stamped with a serial number and a seal that depends on the previous page's seal. If a rogue employee tries to rip out a page or change a number, the mathematical seal breaks, and the fraud is immediately caught.

#### ⚙️ How It Works in Our Project:
1. **AES-256-XTS Volume Encryption:**
   - We simulate an enterprise Key Management Service (KMS).
   - Sensitive data (like patient health records or credit card numbers) is encrypted before being written to physical blocks. Even if a thief physically steals a hard drive from the rack, the data is unreadable gibberish.
2. **Cryptographically Chained Audit Trail (Hash Chain):**
   - Every administrative action (formatting a LUN, failing a disk, snapshotting, changing permissions) is recorded in an immutable ledger.
   - Each audit record $n$ is hashed with SHA-256 containing the hash of the previous record $n-1$:
     $$H_n = \text{SHA256}(n \parallel \text{Timestamp} \parallel \text{User} \parallel \text{Action} \parallel H_{n-1})$$
   - If anyone modifies or deletes an old log entry, the chain breaks.
   - Click **"Verify Audit Chain Cryptographic Integrity"** in the UI: the system verifies every link and outputs `TAMPER_FREE (100% VALID)`.

---

## 5. Bonus Highlights

### A. Live SRM Telemetry & Workload Simulator (`srm_telemetry.py`)
At the very top of the dashboard, you will see a real-time enterprise telemetry ribbon:
- **IOPS (Input/Output Operations Per Second):** Shows live I/O speed.
- **Throughput / Bandwidth:** Measures transfer rate (e.g., 116 MB/s).
- **Latency / Response Time:** Shows sub-millisecond response time ($1.2\text{ ms}$).
- **Cache Hit Ratio:** Percentage of reads served directly from controller DRAM cache ($85\% - 95\%$).
- **Dynamic Workload Switching:** In the top header dropdown, you can switch between:
  1. *OLTP Balanced* (typical e-commerce / banking random 8KB reads/writes)
  2. *Streaming Data* (video streaming / analytics 1MB sequential transfers)
  3. *Backup Burst Storm* (heavy write saturation)
  Watch the telemetry metrics shift in real-time as the workload profile changes!

### B. End-to-End Enterprise Ingestion Lab (Tab 8)
This is the ultimate showstopper for your presentation:
- You can drag-and-drop or select **any real file** from your computer (e.g., a `.txt`, `.json`, `.csv`, `.pdf`, `.sql`).
- Click **"🚀 Run Full ISM Pipeline"**.
- The screen visually animates the data flowing through **all 5 stages sequentially**:
  1. *Chunking & SHA-256 Deduplication*
  2. *AES-256 At-Rest Encryption*
  3. *ILM Tiering Placement (NVMe / SAS / Cloud)*
  4. *RAID 5 Striping & XOR Parity calculation*
  5. *Cryptographic Audit Chain Sealing*

---

## 6. Step-by-Step Live Demo Script

Follow this exact 5-minute script when demonstrating the project to your teacher:

| Time | Tab to Open | Action to Perform on Screen | What to Say to Your Teacher |
|---|---|---|---|
| **0:00 - 0:45** | **Tab 1: Overview** | Open `http://localhost:8000`. Point out the top telemetry cards (IOPS, Latency, Cache Hit). Change Workload dropdown to "Backup Storm". | *"Sir/Ma'am, this is our main storage operations center. Here we monitor real-time Storage Resource Management (SRM) telemetry like IOPS and cache hit ratio. When enterprise workloads change from OLTP to backup storms, our telemetry immediately reflects the shift."* |
| **0:45 - 1:45** | **Tab 2: RAID Engine** | 1. Show the XOR formula on screen.<br>2. Type `"ISM_EXAM_GRADE_DATA"` and click Write.<br>3. Click **"Simulate Failure"** on Disk 1 (LED turns blinking red).<br>4. Click **"Read / Reconstruct"**.<br>5. Click **"Rebuild with Hot Spare"**. | *"Here is our RAID 5 engine. Data is striped across 4 disks with distributed XOR parity. When I simulate a sudden failure on Disk 1, the array enters Degraded mode. Notice that when I read the file, the controller does NOT fail — it reconstructs the missing data in real-time using XOR parity! Now I click Rebuild, and our hot spare restores the array back to Healthy."* |
| **1:45 - 2:30** | **Tab 3: Deduplication** | 1. Point to the Deduplication Ratio (e.g., 3.4 : 1).<br>2. Click **"Insert Similar Duplicate Version"**.<br>3. Show the SHA-256 block table.<br>4. Click **"Delete File"** to trigger Garbage Collection. | *"In enterprise storage, storing duplicate files wastes money. Here, our deduplication engine breaks files into 16-byte chunks and hashes them with SHA-256. When duplicate data is ingested, we only increment reference counters without consuming new physical blocks. This gives us over 65% space savings. When files are deleted, our garbage collector reclaims orphaned blocks automatically."* |
| **2:30 - 3:15** | **Tab 4: Storage Tiering** | 1. Show the 3 tiers (NVMe SSD, SAS HDD, Cloud Archive).<br>2. Point to the **Cost Savings Banner** ($700+ saved/mo).<br>3. Click **"Access"** on a cold object to heat it up.<br>4. Click **"Execute Automated ILM Policies"**. | *"This is Information Lifecycle Management (ILM). NVMe SSD is ultra-fast but costs $1.20/GB/month. Cloud Archive is cheap at $0.02/GB/month. Our engine dynamically tracks data temperature based on access frequency. Cold data is automatically demoted to cheap tiers, saving over 85% in monthly data center costs."* |
| **3:15 - 4:00** | **Tab 5: SAN & LUNs** | 1. Point out the 10,000 GB shared Storage Pool.<br>2. Point to the Thin LUN comparison.<br>3. Point to the WWN and IQN host masking table. | *"Here we virtualize storage using a SAN Storage Pool. We support Thin Provisioning, which allows oversubscribing virtual capacity to servers while only allocating physical blocks on-demand. We also implement LUN Masking using Fibre Channel WWN addresses so only authorized database hosts can access specific volumes."* |
| **4:00 - 4:45** | **Tab 6: Disaster Recovery** | 1. Toggle between Synchronous and Asynchronous mode.<br>2. Click **"Create Snapshot"**.<br>3. Click **"⚡ Simulate Disaster at Site A"**.<br>4. Point out Site B being promoted to Active Primary.<br>5. Click **"Restore & Failback"**. | *"For business continuity, we simulate multi-site replication between New York and Frankfurt. We support Synchronous (Zero RPO) and Asynchronous modes. When I simulate a catastrophic disaster at Site A, our automated failover immediately promotes Site B to active primary with an RTO under 3 minutes. We also support Copy-on-Write (CoW) point-in-time snapshots for instant rollbacks."* |
| **4:45 - 5:15** | **Tab 7: Security & Audit** | 1. Encrypt sample text with AES-256.<br>2. Click **"Verify Audit Chain Cryptographic Integrity"**. | *"For security, all data at rest is encrypted with AES-256. Every admin action is recorded in a cryptographically chained audit log where each entry contains the SHA-256 hash of the previous one. Clicking verify proves that no historical log entry has been altered or tampered with."* |

---

## 7. Teacher / Viva Q&A

Here are the exact questions teachers commonly ask during ISM project evaluations, along with the crisp answers you should give:

### Q1: "Why did you use RAID 5 instead of RAID 0 or RAID 1?"
> **Answer:**  
> *"RAID 0 offers speed through striping but has zero fault tolerance—if one drive fails, everything is lost. RAID 1 provides 100% redundancy through mirroring, but wastes 50% of your disk capacity on duplicate copies.  
> **RAID 5 strikes the optimal balance**: it gives high performance and tolerates a single disk failure using distributed XOR parity, while only using $(N-1)/N$ capacity (75% usable capacity in a 4-disk array instead of just 50%)."*

### Q2: "How does XOR parity reconstruct lost data without storing a full copy?"
> **Answer:**  
> *"XOR has a mathematical property where $A \oplus A = 0$ and $A \oplus 0 = A$.  
> When writing, parity is calculated as $P = D_0 \oplus D_1 \oplus D_2$.  
> If Drive 1 fails, we don't have $D_1$. But if we XOR the surviving data drives with the parity drive:  
> $P \oplus D_0 \oplus D_2 = (D_0 \oplus D_1 \oplus D_2) \oplus D_0 \oplus D_2 = D_1$.  
> The matching terms cancel out to zero, leaving the exact missing data block!"*

### Q3: "What is the difference between Thin Provisioning and Thick Provisioning?"
> **Answer:**  
> *"In **Thick Provisioning**, the full storage capacity is physically reserved from the storage pool immediately upon LUN creation, whether the server uses it or not. This leads to stranded, wasted capacity.  
> In **Thin Provisioning**, the storage controller advertises a large virtual size (e.g., 500 GB) to the operating system, but only allocates physical storage blocks incrementally as actual data is written. This allows storage pooling and oversubscription."*

### Q4: "What do RPO and RTO mean in Disaster Recovery?"
> **Answer:**  
> - *"**RPO (Recovery Point Objective):** The maximum acceptable amount of data loss measured in time. With Synchronous replication, $RPO = 0$ (no lost data). With Asynchronous replication, $RPO$ is a few seconds of queued data.  
> - **RTO (Recovery Time Objective):** The time it takes to get the system back up and running after a disaster strikes. In our automated failover, Site B is promoted to primary within a few minutes ($RTO < 3\text{ minutes}$)."*

### Q5: "How does Copy-on-Write (CoW) snapshot work?"
> **Answer:**  
> *"Instead of duplicating the entire storage volume (which takes hours), a CoW snapshot takes zero seconds. It freezes metadata pointers. When a write request comes in to modify an existing block, the original baseline data block is first copied to a snapshot delta area before the live block is overwritten. This allows instant point-in-time recovery with minimal storage overhead."*

### Q6: "How is Deduplication different from standard Zip or Gzip compression?"
> **Answer:**  
> *"Zip/Gzip compression works within a single file by finding repeating byte sequences (like Lempel-Ziv algorithm).  
> **Deduplication operates across the entire storage system globally**: it identifies identical blocks across completely different files, volumes, and virtual machines using cryptographic hash fingerprints (SHA-256). They complement each other: deduplication eliminates identical blocks across files, and compression shrinks the remaining unique blocks."*

### Q7: "How does your audit log prevent tampering?"
> **Answer:**  
> *"It uses cryptographic hash chaining, similar to a blockchain. Each audit log entry includes the SHA-256 hash of the record that came before it. If an attacker or rogue administrator modifies even a single character in record #2, its hash changes, which invalidates record #3, #4, and so on. The cryptographic chain breaks, immediately exposing the tampering."*

---

## 8. Technology Stack & File Structure

If the teacher asks how the code is organized:

```text
ISM Project/
│
├── run.py / run.bat            # 1-Click launcher (starts server & opens browser)
├── main.py                     # FastAPI backend controller & REST API gateway
├── test_system.py              # Automated 6-module validation test suite
├── requirements.txt            # Lightweight dependencies (FastAPI, Uvicorn, Jinja2)
│
├── ism_engine/                 # Pure Python implementation of core ISM algorithms
│   ├── raid_engine.py          # RAID 0/1/5/6/10, XOR parity math, degraded recovery
│   ├── deduplication.py        # 16-byte chunking, SHA-256 hash table, GC engine
│   ├── tiering_ilm.py          # 3-Tier storage hierarchy, temperature, cost optimizer
│   ├── san_lun.py              # Virtual storage pool, Thin/Thick LUNs, WWN zoning
│   ├── replication_dr.py       # Multi-site sync/async replication, CoW snapshots, failover
│   ├── security_crypto.py      # AES-256 encryption, KMS vault, chained audit trail
│   └── srm_telemetry.py        # Live IOPS, latency, bandwidth, workload simulator
│
├── templates/
│   └── index.html              # Responsive dark-theme dashboard with 8 module tabs
└── static/
    ├── css/style.css           # Premium glassmorphic styling, responsive layout
    └── js/app.js               # Dynamic UI updates, REST API connectors, live charts
```

### Key Technical Merits:
- **Zero Heavy Framework Bloat:** Fast native Python algorithms with asynchronous FastAPI and pure Vanilla HTML/CSS/JS frontend.
- **Scientifically Accurate:** Parity calculations, hash algorithms, tiering metrics, and RPO/RTO calculations follow standard enterprise storage hardware specifications.
- **Verified by Automated Tests:** Running `python test_system.py` executes 6 automated test suites that confirm all modules pass with 100% success.

---

## 💡 Quick Tips for Presentation Day
1. **Keep `run.py` running in your terminal** so the website opens instantly at `http://127.0.0.1:8000`.
2. **Open the browser in full-screen (`F11`)** so the dark glassmorphic dashboard looks sleek and professional.
3. **Keep this guide handy on your phone or printed out** to glance at the "What to Say" script and Viva Q&A before you begin!
