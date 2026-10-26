/**
 * OmniStore ISM — Enterprise Client-Side Application Controller
 */

// Global State
let currentTab = 'tab-overview';
let telemetryInterval = null;
let selectedPipelineFile = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    loadOverview();
    loadRaidStatus();
    loadDedupeStatus();
    loadTieringStatus();
    loadSanStatus();
    loadDrStatus();
    loadSecurityStatus();

    // Start background telemetry polling
    telemetryInterval = setInterval(fetchTelemetrySample, 3000);
}

// ===================== NAVIGATION =====================

function switchTab(tabId) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const tabBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    const tabPane = document.getElementById(tabId);

    if (tabBtn) tabBtn.classList.add('active');
    if (tabPane) tabPane.classList.add('active');

    currentTab = tabId;

    // Refresh specific tab data on switch
    if (tabId === 'tab-raid') loadRaidStatus();
    if (tabId === 'tab-dedupe') loadDedupeStatus();
    if (tabId === 'tab-tiering') loadTieringStatus();
    if (tabId === 'tab-san') loadSanStatus();
    if (tabId === 'tab-dr') loadDrStatus();
    if (tabId === 'tab-security') loadSecurityStatus();
    if (tabId === 'tab-overview') loadOverview();
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;
    toast.textContent = message;
    toast.style.borderColor = type === 'error' ? 'var(--accent-red)' : (type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-cyan)');
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 4000);
}

// ===================== TELEMETRY & OVERVIEW =====================

async function loadOverview() {
    try {
        const res = await fetch('/api/overview');
        const data = await res.json();

        // Update Controller Status Pill
        const pill = document.getElementById('controllerStatusPill');
        const pillText = document.getElementById('controllerStatusText');
        if (data.raid.health === 'HEALTHY') {
            pill.className = 'status-pill status-healthy';
            pillText.textContent = 'ARRAY HEALTHY';
        } else if (data.raid.health === 'DEGRADED') {
            pill.className = 'status-pill status-degraded';
            pillText.textContent = 'ARRAY DEGRADED';
        } else {
            pill.className = 'status-pill status-failed';
            pillText.textContent = 'ARRAY CRITICAL';
        }

        // Active DC
        document.getElementById('activeDcText').textContent = data.dr_replication.active_site;

        // Telemetry counters
        document.getElementById('liveIops').textContent = data.telemetry.iops.toLocaleString();
        document.getElementById('liveThroughput').innerHTML = `${data.telemetry.throughput_mb_s} <span class="unit">MB/s</span>`;
        document.getElementById('liveLatency').innerHTML = `${data.telemetry.latency_ms} <span class="unit">ms</span>`;
        document.getElementById('liveCacheHit').innerHTML = `${data.telemetry.cache_hit_ratio}<span class="unit">%</span>`;

        // Overview Summary Badges
        document.getElementById('ovRaidLevel').textContent = `RAID ${data.raid.level}`;
        document.getElementById('ovRaidHealth').textContent = data.raid.health;
        document.getElementById('ovRaidHealth').className = data.raid.health === 'HEALTHY' ? 'text-success' : 'text-danger';
        document.getElementById('ovRaidDisks').textContent = `${data.raid.disks} Physical Drives + 1 Hot Spare`;

        document.getElementById('ovDedupRatio').textContent = data.deduplication.ratio;
        document.getElementById('ovDedupSaved').textContent = `${data.deduplication.space_saved_percent}%`;
        document.getElementById('ovDedupFiles').textContent = `${data.deduplication.files} Files Ingested`;

        document.getElementById('ovIlmSavings').textContent = `$${data.ilm_tiering.monthly_savings_usd} / Month Saved`;
        document.getElementById('ovIlmObjects').textContent = `${data.ilm_tiering.total_objects} Data Volumes Tracked`;

        document.getElementById('ovSanUsage').textContent = `${data.san_storage_pool.used_pct}% Allocated`;
        document.getElementById('ovSanPool').textContent = `${data.san_storage_pool.total_gb.toLocaleString()} GB`;
        document.getElementById('ovSanLuns').textContent = `${data.san_storage_pool.luns_count} Active LUNs`;

        document.getElementById('ovDrMode').textContent = data.dr_replication.mode;
        document.getElementById('ovDrRpo').textContent = `${data.dr_replication.rpo_seconds} sec ${data.dr_replication.rpo_seconds === 0 ? '(Zero Loss)' : ''}`;

    } catch (err) {
        console.error('Overview fetch error:', err);
    }
}

async function fetchTelemetrySample() {
    try {
        const res = await fetch('/api/telemetry/sample');
        const data = await res.json();
        const curr = data.current;
        const forecast = data.capacity_forecasting;

        document.getElementById('liveIops').textContent = curr.iops.toLocaleString();
        document.getElementById('liveThroughput').innerHTML = `${curr.throughput_mb_s} <span class="unit">MB/s</span>`;
        document.getElementById('liveLatency').innerHTML = `${curr.latency_ms} <span class="unit">ms</span>`;
        document.getElementById('liveCacheHit').innerHTML = `${curr.cache_hit_ratio}<span class="unit">%</span>`;

        document.getElementById('liveRunway').innerHTML = `${forecast.projected_exhaustion_days} <span class="unit">Days</span>`;
        document.getElementById('liveRunwaySub').textContent = `At ${forecast.daily_growth_rate_gb} GB / day consumption`;

    } catch (err) {
        console.error('Telemetry sampling error:', err);
    }
}

async function changeWorkload(workload) {
    const formData = new FormData();
    formData.append('workload', workload);
    await fetch('/api/telemetry/workload', { method: 'POST', body: formData });
    showToast(`Workload profile changed to ${workload}`);
    fetchTelemetrySample();
}

// ===================== RAID ENGINE =====================

async function loadRaidStatus() {
    try {
        const res = await fetch('/api/raid/status');
        const data = await res.json();

        // Level selector
        document.getElementById('raidLevelSelector').value = data.raid_level;

        // Health Badge
        const badge = document.getElementById('raidArrayStatusBadge');
        badge.textContent = data.health;
        badge.className = data.health === 'HEALTHY' ? 'badge badge-emerald' : (data.health === 'DEGRADED' ? 'badge badge-amber' : 'badge badge-red');

        // Render Disks
        const container = document.getElementById('raidDisksContainer');
        container.innerHTML = '';

        data.disks.forEach(d => {
            const isFailed = d.status === 'FAILED';
            const isRebuilding = d.status === 'REBUILDING';
            const statusClass = isFailed ? 'disk-failed' : (isRebuilding ? 'disk-rebuilding' : 'disk-online');
            const ledClass = isFailed ? 'led-red' : (isRebuilding ? 'led-amber' : 'led-green');

            const blocksHtml = Object.entries(d.blocks || {}).slice(-4).map(([idx, val]) => {
                const isParity = val.startsWith('[P:') || val.startsWith('[Q:');
                return `<span class="block-chip ${isParity ? 'block-parity' : ''}">${val}</span>`;
            }).join('');

            const card = document.createElement('div');
            card.className = `disk-slot ${statusClass}`;
            card.innerHTML = `
                <div class="disk-head">
                    <span class="disk-name">${d.name}</span>
                    <span class="disk-led ${ledClass}" title="${d.status}"></span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:6px;">Status: <strong>${d.status}</strong></div>
                <div class="disk-capacity-bar">
                    <div class="disk-capacity-fill" style="width: ${Math.min(100, (d.used_blocks / d.capacity_blocks) * 100)}%;"></div>
                </div>
                <div style="font-size:0.72rem; color:var(--text-secondary); display:flex; justify-content:space-between;">
                    <span>Blocks: ${d.used_blocks} / ${d.capacity_blocks}</span>
                    <span>I/O: ${d.io_writes} W / ${d.io_reads} R</span>
                </div>
                <div class="disk-blocks-strip">
                    ${blocksHtml || '<span style="font-size:0.68rem; color:var(--text-muted)">Empty disk blocks</span>'}
                </div>
                <div class="disk-actions">
                    ${isFailed ? 
                        `<button class="btn btn-secondary btn-xs" onclick="rebuildDisk(${d.disk_id})">Rebuild (Hot Spare)</button>` : 
                        `<button class="btn btn-danger-outline btn-xs" onclick="failDisk(${d.disk_id})">Simulate Failure</button>`
                    }
                </div>
            `;
            container.appendChild(card);
        });

        // Parity Equations
        const eqContainer = document.getElementById('parityEquationsList');
        if (data.parity_equations && data.parity_equations.length > 0) {
            eqContainer.innerHTML = data.parity_equations.map(eq => `
                <div class="parity-eq-item">
                    Stripe Row ${eq.row}: <span>${eq.equation}</span> <span class="eq-disk">[Written to ${eq.parity_disk}]</span>
                </div>
            `).join('');
        }

    } catch (err) {
        console.error('RAID status load error:', err);
    }
}

async function writeRaidData() {
    const fileId = document.getElementById('raidFileId').value.trim() || 'SAMPLE_FILE';
    const dataContent = document.getElementById('raidDataContent').value.trim() || 'SAMPLE DATA';

    try {
        const res = await fetch('/api/raid/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId, data_content: dataContent })
        });
        const result = await res.json();

        showToast(`Data striped across RAID ${result.raid_level} (${result.chunks} chunks written)`, 'success');
        
        // Show write trace
        const traceBox = document.getElementById('raidWriteTrace');
        traceBox.innerHTML = `
            <div style="font-size:0.8rem; font-weight:600; color:var(--accent-cyan); margin-bottom:6px;">Striping Trace (Controller Log):</div>
            ${result.trace.map(t => `
                <div style="font-size:0.75rem; font-family:var(--font-mono); padding:3px 0; color:var(--text-secondary);">
                    Block <strong>[${t.block}]</strong> on <strong>${t.disk}</strong>: <code>${t.chunk}</code> (${t.type})
                </div>
            `).join('')}
        `;

        loadRaidStatus();
        loadOverview();
    } catch (err) {
        showToast('Error writing to RAID array', 'error');
    }
}

async function readRaidData() {
    const fileId = document.getElementById('raidReadTarget').value.trim();
    if (!fileId) return;

    const formData = new FormData();
    formData.append('file_id', fileId);

    try {
        const res = await fetch('/api/raid/read', { method: 'POST', body: formData });
        const result = await res.json();

        const box = document.getElementById('raidReadResult');
        if (result.status === 'SUCCESS') {
            box.innerHTML = `
                <div style="color:var(--accent-emerald); font-weight:600; margin-bottom:4px;">Read Succeeded:</div>
                <div>Assembled Data: <strong>${result.data_preview}</strong></div>
                ${result.reconstruction_performed ? 
                    `<div style="color:var(--accent-amber); margin-top:6px;">⚠️ Dynamic In-Flight Parity Reconstruction Applied! (Degraded Drive recovered via XOR)</div>` : 
                    `<div style="color:var(--text-muted); margin-top:4px;">Direct read from healthy stripes (no parity rebuild needed).</div>`
                }
            `;
            showToast('File read and reconstructed successfully', 'success');
        } else {
            box.innerHTML = `<span style="color:var(--accent-red);">${result.message}</span>`;
            showToast(result.message, 'error');
        }
    } catch (err) {
        showToast('Read failed', 'error');
    }
}

async function failDisk(diskId) {
    try {
        const res = await fetch('/api/raid/fail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ disk_id: diskId })
        });
        const result = await res.json();
        showToast(`Disk ${diskId} failed! Array is now in DEGRADED mode.`, 'error');
        loadRaidStatus();
        loadOverview();
    } catch (err) {
        showToast('Failed to simulate disk failure', 'error');
    }
}

async function rebuildDisk(diskId) {
    try {
        const res = await fetch('/api/raid/rebuild', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ disk_id: diskId })
        });
        const result = await res.json();
        showToast(`Rebuilt disk ${diskId} from distributed parity hot spare!`, 'success');
        loadRaidStatus();
        loadOverview();
    } catch (err) {
        showToast('Rebuild failed', 'error');
    }
}

async function resetRaidArray() {
    const level = document.getElementById('raidLevelSelector').value;
    const disksCount = level === '0' || level === '1' ? 2 : (level === '6' || level === '10' ? 4 : 4);

    try {
        await fetch('/api/raid/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ raid_level: level, num_disks: disksCount })
        });
        showToast(`RAID array reconfigured to RAID ${level}`, 'success');
        loadRaidStatus();
        loadOverview();
    } catch (err) {
        showToast('Failed to reset RAID configuration', 'error');
    }
}

// ===================== DEDUPLICATION =====================

async function loadDedupeStatus() {
    try {
        const res = await fetch('/api/dedupe/status');
        const data = await res.json();

        document.getElementById('dedupeRatioDisplay').textContent = data.deduplication_ratio;
        document.getElementById('dedupeSavingsPercent').textContent = `${data.space_saved_percent}%`;
        document.getElementById('dedupeSavingsBytes').textContent = `Saved ${data.space_saved_bytes.toLocaleString()} Bytes`;
        document.getElementById('dedupeVirtualBytes').textContent = `${data.virtual_raw_bytes.toLocaleString()} B`;
        document.getElementById('dedupePhysicalBytes').textContent = `${data.physical_raw_bytes.toLocaleString()} B`;
        document.getElementById('dedupeCompressedBytes').textContent = `${data.physical_compressed_bytes.toLocaleString()} B`;
        document.getElementById('dedupeUniqueCount').textContent = `${data.total_unique_blocks} Unique Blocks`;

        // Render Ingested Files List
        const filesContainer = document.getElementById('dedupeFilesList');
        filesContainer.innerHTML = (data.files_list || []).map(f => `
            <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.06); padding:4px 10px; border-radius:999px; font-size:0.78rem;">
                <span>📄 ${f}</span>
                <button onclick="deleteDedupeFile('${f}')" style="background:none; border:none; color:var(--accent-red); cursor:pointer; font-weight:700;">×</button>
            </div>
        `).join('') || '<span style="font-size:0.78rem; color:var(--text-muted)">No files ingested yet.</span>';

        // Render Block Table
        const tbody = document.getElementById('dedupeBlockTableBody');
        tbody.innerHTML = (data.blocks_preview || []).map(b => `
            <tr>
                <td><strong>#${b.block_id}</strong></td>
                <td><code style="color:var(--accent-cyan); font-family:var(--font-mono);">${b.block_hash}</code></td>
                <td><span class="badge ${b.ref_count > 1 ? 'badge-purple' : 'badge-cyan'}">${b.ref_count}x Ref</span></td>
                <td>${b.size_bytes} B</td>
                <td>${b.compressed_size} B</td>
                <td><code style="font-size:0.75rem;">${b.sample_preview}</code></td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Dedupe load error:', err);
    }
}

async function ingestDedupeData() {
    const filename = document.getElementById('dedupeFilename').value.trim() || 'sample.txt';
    const content = document.getElementById('dedupeContent').value.trim() || 'sample text';

    try {
        const res = await fetch('/api/dedupe/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, content })
        });
        const result = await res.json();
        showToast(`Ingested ${filename}: ${result.chunks_total} chunks (${result.duplicate_blocks_referenced} duplicates detected)`, 'success');
        loadDedupeStatus();
        loadOverview();
    } catch (err) {
        showToast('Ingestion failed', 'error');
    }
}

function loadDuplicateSample() {
    document.getElementById('dedupeFilename').value = 'daily_backup_snapshot_v2.sql';
    document.getElementById('dedupeContent').value = 'ACME FINANCIAL Q1 2026: TOTAL REVENUE $48M. CONFIDENTIAL STORAGE DATA. ENTERPRISE REPEATED BLOCK DATA BLOCK DATA NEW EXTRA LINE';
}

async function deleteDedupeFile(filename) {
    const formData = new FormData();
    formData.append('filename', filename);
    try {
        const res = await fetch('/api/dedupe/delete', { method: 'POST', body: formData });
        const result = await res.json();
        showToast(result.message, 'info');
        loadDedupeStatus();
        loadOverview();
    } catch (err) {
        showToast('Delete failed', 'error');
    }
}

async function clearDedupeIndex() {
    await fetch('/api/dedupe/clear', { method: 'POST' });
    showToast('Deduplication index reset', 'info');
    loadDedupeStatus();
    loadOverview();
}

// ===================== STORAGE TIERING & ILM =====================

async function loadTieringStatus() {
    try {
        const res = await fetch('/api/tiering/status');
        const data = await res.json();

        document.getElementById('ilmCurrentTick').textContent = `Simulation Cycle: ${data.current_tick}`;

        // Render Tiers
        const container = document.getElementById('storageTiersContainer');
        container.innerHTML = data.tiers.map((t, idx) => `
            <div class="tier-card tier-${idx + 1}">
                <div class="tier-header">
                    <div>
                        <div class="tier-name">${t.name}</div>
                        <div class="tier-media">${t.media_type} • ${t.iops.toLocaleString()} IOPS</div>
                    </div>
                    <span class="badge ${idx === 0 ? 'badge-cyan' : (idx === 1 ? 'badge-blue' : 'badge-purple')}">${t.latency_ms} ms</span>
                </div>
                <div class="tier-cost">Media Cost: <strong>$${t.cost_per_gb} / GB / mo</strong></div>
                <div class="tier-gauge">
                    <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:4px;">
                        <span>Used: ${t.used_gb} GB (${t.usage_percent}%)</span>
                        <span>Total: ${t.total_gb} GB</span>
                    </div>
                    <div class="progress-bar-container" style="height:8px; margin:0;">
                        <div class="progress-bar" style="width:${t.usage_percent}%;"></div>
                    </div>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">Active Objects: <strong>${t.object_count}</strong></div>
            </div>
        `).join('');

        // Cost Savings Banner
        const savings = data.cost_savings;
        document.getElementById('costSavingsAmount').textContent = `$${savings.monthly_savings_usd.toFixed(2)}`;
        document.getElementById('costBannerExplanation').innerHTML = `
            Storing all ${savings.total_stored_gb} GB in Tier 1 NVMe would cost <strong>$${savings.cost_unoptimized_usd.toFixed(2)} / month</strong>.
            By placing cold and warm data in Tier 2 and Tier 3, your monthly cost is only <strong>$${savings.cost_tiered_ilm_usd.toFixed(2)} / month</strong>.
        `;

        // Render Objects Heatmap
        const objContainer = document.getElementById('objectsHeatmapGrid');
        objContainer.innerHTML = data.objects.map(o => {
            const tempClass = o.temperature === 'HOT' ? 'temp-badge-hot' : (o.temperature === 'WARM' ? 'temp-badge-warm' : 'temp-badge-cold');
            return `
                <div class="object-item-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <strong style="font-size:0.85rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:140px;">${o.name}</strong>
                        <span class="badge ${tempClass}">${o.temperature}</span>
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px;">
                        Size: <strong>${o.size_gb} GB</strong> • Currently on <strong>Tier ${o.tier_id}</strong><br>
                        Access Count: <strong>${o.access_count} I/Os</strong>
                    </div>
                    <button class="btn btn-secondary btn-xs" onclick="accessTierObject('${o.object_id}')">⚡ Access (Warm Up)</button>
                </div>
            `;
        }).join('');

        // Migrations Log
        const logContainer = document.getElementById('ilmMigrationsList');
        if (data.recent_migrations && data.recent_migrations.length > 0) {
            logContainer.innerHTML = data.recent_migrations.map(m => `
                <div style="font-size:0.78rem; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);">
                    <span style="color:var(--accent-cyan); font-weight:600;">${m.object_name}</span> (${m.size_gb} GB)
                    moved from <strong>${m.from_tier}</strong> ➔ <strong>${m.to_tier}</strong>
                    <div style="color:var(--text-muted); font-size:0.72rem;">${m.reason}</div>
                </div>
            `).join('');
        }

    } catch (err) {
        console.error('Tiering load error:', err);
    }
}

async function accessTierObject(objectId) {
    const formData = new FormData();
    formData.append('object_id', objectId);
    const res = await fetch('/api/tiering/access', { method: 'POST', body: formData });
    const data = await res.json();
    showToast(`Accessed object (Temperature: ${data.temperature}, served by ${data.served_by_tier} at ${data.latency_ms}ms)`);
    loadTieringStatus();
}

async function advanceIlmTime() {
    const formData = new FormData();
    formData.append('ticks', '3');
    await fetch('/api/tiering/tick', { method: 'POST', body: formData });
    showToast('Advanced simulation time by 3 cycles. Inactive objects are cooling down.');
    loadTieringStatus();
}

async function runIlmMigration() {
    const res = await fetch('/api/tiering/migrate', { method: 'POST' });
    const data = await res.json();
    showToast(`ILM Execution Complete: Migrated ${data.migrations_executed} objects to optimal tiers!`, 'success');
    loadTieringStatus();
    loadOverview();
}

async function allocateNewObject() {
    const name = document.getElementById('newObjName').value.trim() || 'new_data.bin';
    const size = parseFloat(document.getElementById('newObjSize').value) || 50;
    const tier = parseInt(document.getElementById('newObjTier').value) || 1;

    await fetch('/api/tiering/allocate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, size_gb: size, initial_tier: tier })
    });
    showToast(`Allocated ${name} (${size} GB) to Tier ${tier}`, 'success');
    loadTieringStatus();
}

// ===================== SAN FABRIC & LUNS =====================

async function loadSanStatus() {
    try {
        const res = await fetch('/api/san/status');
        const data = await res.json();

        document.getElementById('poolAllocatedVal').textContent = `${data.pool_allocated_gb.toLocaleString()} GB Allocated`;
        document.getElementById('poolTotalVal').textContent = `${data.pool_total_gb.toLocaleString()} GB Capacity`;
        document.getElementById('poolUsagePctVal').textContent = `${data.pool_usage_pct}%`;
        document.getElementById('poolProgressBar').style.width = `${Math.min(100, data.pool_usage_pct)}%`;

        document.getElementById('poolVirtualTotal').textContent = `${data.total_virtual_gb.toLocaleString()} GB`;
        document.getElementById('poolOversubRatio').textContent = `${data.oversubscription_ratio}:1`;
        document.getElementById('poolFreeGb').textContent = `${data.pool_free_gb.toLocaleString()} GB`;

        // LUNs table
        const tbody = document.getElementById('lunsTableBody');
        tbody.innerHTML = data.luns.map(l => `
            <tr>
                <td><strong>LUN #${l.lun_id}</strong></td>
                <td>${l.name}</td>
                <td><span class="badge ${l.provisioning_type === 'THIN' ? 'badge-cyan' : 'badge-purple'}">${l.provisioning_type}</span></td>
                <td>${l.size_gb.toLocaleString()} GB</td>
                <td>${l.allocated_gb.toLocaleString()} GB (${l.efficiency}% thin efficiency)</td>
                <td><code style="font-size:0.74rem;">${l.attached_initiators.join(', ') || 'No Initiator Attached'}</code></td>
            </tr>
        `).join('');

        // Zones
        const zonesContainer = document.getElementById('sanZonesList');
        zonesContainer.innerHTML = Object.entries(data.zones).map(([zName, members]) => `
            <div style="background:rgba(255,255,255,0.04); border:1px solid var(--border-color); padding:8px 12px; border-radius:var(--radius-sm); margin-bottom:8px;">
                <div style="font-weight:600; color:var(--accent-cyan); font-size:0.82rem;">${zName}</div>
                <div style="font-size:0.74rem; font-family:var(--font-mono); color:var(--text-secondary); margin-top:2px;">Members: ${members.join(' ↔ ')}</div>
            </div>
        `).join('');

        // Masking matrix
        const maskTbody = document.getElementById('maskingTableBody');
        const rows = [];
        data.luns.forEach(l => {
            data.hosts.forEach(h => {
                const isMaskedIn = l.attached_initiators.includes(h.initiator_id);
                rows.push(`
                    <tr>
                        <td><strong>${l.name}</strong> (LUN ${l.lun_id})</td>
                        <td>${h.host_name} <br><code style="font-size:0.72rem; color:var(--text-muted);">${h.initiator_id}</code></td>
                        <td>
                            <span class="badge ${isMaskedIn ? 'badge-emerald' : 'badge-amber'}">${isMaskedIn ? 'GRANTED' : 'MASKED'}</span>
                        </td>
                        <td>
                            <button class="btn ${isMaskedIn ? 'btn-danger-outline' : 'btn-outline'} btn-xs" onclick="toggleLunMasking(${l.lun_id}, '${h.initiator_id}', ${!isMaskedIn})">
                                ${isMaskedIn ? 'Mask Out (Deny)' : 'Mask In (Grant)'}
                            </button>
                        </td>
                    </tr>
                `);
            });
        });
        maskTbody.innerHTML = rows.join('');

    } catch (err) {
        console.error('SAN load error:', err);
    }
}

async function createLun() {
    const name = document.getElementById('lunName').value.trim() || 'LUN_New';
    const size = parseFloat(document.getElementById('lunSize').value) || 500;
    const provType = document.querySelector('input[name="lunProvType"]:checked').value;

    const res = await fetch('/api/san/lun/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, size_gb: size, provisioning_type: provType })
    });
    const result = await res.json();
    if (result.status === 'SUCCESS') {
        showToast(`Provisioned ${provType} LUN '${name}' (${size} GB) into SAN Storage Pool!`, 'success');
        loadSanStatus();
        loadOverview();
    } else {
        showToast(result.message, 'error');
    }
}

async function toggleLunMasking(lunId, initiatorId, allowAccess) {
    const res = await fetch('/api/san/lun/mask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lun_id: lunId, initiator_id: initiatorId, allow_access: allowAccess })
    });
    const data = await res.json();
    showToast(`LUN Masking: ${initiatorId} ${allowAccess ? 'granted access to' : 'masked out from'} LUN ${lunId}`);
    loadSanStatus();
}

// ===================== DISASTER RECOVERY & REPLICATION =====================

async function loadDrStatus() {
    try {
        const res = await fetch('/api/dr/status');
        const data = await res.json();

        // Active DC Indicator
        document.getElementById('drActiveDcVal').textContent = data.active_dc;
        document.getElementById('drRpoVal').innerHTML = `${data.rpo_seconds} <span class="unit">sec</span>`;
        document.getElementById('drRtoVal').innerHTML = `${data.rto_minutes} <span class="unit">min</span>`;

        // DC A & B Cards
        const cardA = document.getElementById('dcCardA');
        const cardB = document.getElementById('dcCardB');
        const badgeA = document.getElementById('siteAStatusBadge');
        const badgeB = document.getElementById('siteBStatusBadge');

        if (data.site_a_status === 'ONLINE') {
            cardA.className = 'dc-card active-primary';
            badgeA.textContent = 'ONLINE PRIMARY';
            badgeA.className = 'badge badge-emerald';
            document.getElementById('btnDisasterFailover').style.display = 'inline-block';
            document.getElementById('btnDisasterFailback').style.display = 'none';
        } else {
            cardA.className = 'dc-card disaster-failed';
            badgeA.textContent = 'DISASTER OUTAGE';
            badgeA.className = 'badge badge-red';
            document.getElementById('btnDisasterFailover').style.display = 'none';
            document.getElementById('btnDisasterFailback').style.display = 'inline-block';
        }

        if (data.site_b_status === 'PROMOTED_PRIMARY') {
            cardB.className = 'dc-card active-primary';
            badgeB.textContent = 'PROMOTED PRIMARY';
            badgeB.className = 'badge badge-emerald';
        } else {
            cardB.className = 'dc-card';
            badgeB.textContent = 'STANDBY REPLICA';
            badgeB.className = 'badge badge-blue';
        }

        // Replication link
        document.getElementById('repModeLabel').textContent = `${data.replication_mode} REPLICATION`;
        document.getElementById('drModeSelect').value = data.replication_mode;
        document.getElementById('linkLatencyVal').textContent = `${data.link_latency_ms} ms`;
        document.getElementById('repQueueVal').textContent = `${data.queue_pending_items} Blocks`;
        document.getElementById('flushQueueBtn').style.display = data.queue_pending_items > 0 ? 'inline-block' : 'none';

        // Render Blocks
        const renderBlocks = (blocks, targetId) => {
            const container = document.getElementById(targetId);
            container.innerHTML = Object.entries(blocks).map(([idx, val]) => `
                <div style="background:rgba(255,255,255,0.05); padding:6px; border-radius:4px; font-family:var(--font-mono); font-size:0.75rem; margin-bottom:4px;">
                    Block [${idx}]: <code style="color:var(--accent-cyan);">${val}</code>
                </div>
            `).join('');
        };
        renderBlocks(data.live_blocks, 'siteABlocksGrid');
        renderBlocks(data.site_b_blocks, 'siteBBlocksGrid');

        // Snapshots timeline
        const snapContainer = document.getElementById('snapshotsTimeline');
        snapContainer.innerHTML = data.snapshots.map(s => `
            <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border-color); padding:10px 14px; border-radius:var(--radius-sm); margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>📸 ${s.name}</strong> (${s.snap_id})
                    <div style="font-size:0.72rem; color:var(--text-muted);">${s.timestamp} • ${s.blocks_count} Blocks Saved • CoW Deltas: ${s.cow_delta_count}</div>
                </div>
                <button class="btn btn-outline btn-xs" onclick="rollbackSnapshot('${s.snap_id}')">Revert / Rollback</button>
            </div>
        `).join('');

        // DR Events log
        const eventsContainer = document.getElementById('drEventsList');
        eventsContainer.innerHTML = (data.dr_events || []).map(e => `
            <div style="font-size:0.76rem; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="color:var(--accent-amber); font-weight:600;">[${e.timestamp}]</span> ${e.event}: ${e.details}
            </div>
        `).join('') || '<div style="font-size:0.74rem; color:var(--text-muted);">No disaster events triggered yet.</div>';

    } catch (err) {
        console.error('DR load error:', err);
    }
}

async function changeReplicationMode(mode) {
    await fetch('/api/dr/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
    });
    showToast(`Replication protocol updated to ${mode}`);
    loadDrStatus();
    loadOverview();
}

async function writeDrBlock() {
    const blockIdx = parseInt(document.getElementById('drBlockIdx').value) || 0;
    const newVal = document.getElementById('drBlockData').value.trim() || 'DATA';

    const res = await fetch('/api/dr/write', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ block_idx: blockIdx, new_val: newVal })
    });
    const result = await res.json();
    if (result.status === 'SUCCESS') {
        showToast(`Block [${blockIdx}] written. Write Ack latency: ${result.write_ack_latency_ms}ms (${result.replication_status})`, 'success');
        loadDrStatus();
    } else {
        showToast(result.message, 'error');
    }
}

async function flushDrQueue() {
    await fetch('/api/dr/flush', { method: 'POST' });
    showToast('Asynchronous queue flushed to Site B (RPO synchronized to 0.0s)', 'success');
    loadDrStatus();
}

async function createSnapshot() {
    const snapName = document.getElementById('snapshotNameInput').value.trim() || 'Manual_Snapshot';
    const formData = new FormData();
    formData.append('snap_name', snapName);

    await fetch('/api/dr/snapshot', { method: 'POST', body: formData });
    showToast(`CoW Snapshot '${snapName}' successfully captured!`, 'success');
    document.getElementById('snapshotNameInput').value = '';
    loadDrStatus();
}

async function rollbackSnapshot(snapId) {
    const formData = new FormData();
    formData.append('snap_id', snapId);
    const res = await fetch('/api/dr/rollback', { method: 'POST', body: formData });
    const data = await res.json();
    showToast(data.message, 'success');
    loadDrStatus();
}

async function triggerDrFailover() {
    const res = await fetch('/api/dr/failover', { method: 'POST' });
    const data = await res.json();
    showToast('DISASTER AT SITE A! Automated failover promoted Site B to Active Master!', 'error');
    loadDrStatus();
    loadOverview();
}

async function triggerDrFailback() {
    const res = await fetch('/api/dr/failback', { method: 'POST' });
    const data = await res.json();
    showToast('Site A restored! Resynchronized deltas and restored Site A as Primary Master.', 'success');
    loadDrStatus();
    loadOverview();
}

// ===================== SECURITY & AUDIT =====================

async function loadSecurityStatus() {
    try {
        const res = await fetch('/api/security/status');
        const data = await res.json();

        document.getElementById('secKeyFingerprint').textContent = data.key_fingerprint;
        document.getElementById('auditIntegrityBadge').textContent = data.integrity_check.status;
        document.getElementById('auditIntegrityBadge').className = data.integrity_check.is_valid ? 'badge badge-emerald' : 'badge badge-red';

        const tbody = document.getElementById('auditTableBody');
        tbody.innerHTML = data.audit_chain.map(a => `
            <tr>
                <td>#${a.index}</td>
                <td><small>${a.timestamp}</small></td>
                <td><strong>${a.user}</strong> (${a.role})</td>
                <td><code style="color:var(--accent-cyan);">${a.action}</code></td>
                <td><small>${a.details}</small></td>
                <td><code style="color:var(--accent-purple); font-size:0.72rem;">${a.hash}</code></td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Security load error:', err);
    }
}

async function verifyAuditIntegrity() {
    const res = await fetch('/api/security/verify', { method: 'POST' });
    const data = await res.json();
    if (data.is_valid) {
        showToast(`Audit log cryptographic verification PASSED: All ${data.total_records} chained records tamper-free!`, 'success');
    } else {
        showToast('Audit log tampering detected!', 'error');
    }
    loadSecurityStatus();
}

async function testEncrypt() {
    const plaintext = document.getElementById('encryptInput').value.trim();
    const res = await fetch('/api/security/encrypt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plaintext })
    });
    const data = await res.json();

    const box = document.getElementById('encryptResultBox');
    box.style.display = 'block';
    document.getElementById('cipherOutputText').textContent = data.ciphertext_b64;
    document.getElementById('decryptOutputText').textContent = '';
}

async function testDecrypt() {
    const cipher = document.getElementById('cipherOutputText').textContent;
    const formData = new FormData();
    formData.append('ciphertext', cipher);

    const res = await fetch('/api/security/decrypt', { method: 'POST', body: formData });
    const data = await res.json();

    document.getElementById('decryptOutputText').innerHTML = `
        <span style="color:var(--accent-emerald);">Decrypted Verified:</span> <strong>${data.decrypted_text}</strong>
    `;
}

// ===================== END-TO-END PIPELINE LAB =====================

function handleFileSelected(input) {
    if (input.files && input.files[0]) {
        selectedPipelineFile = input.files[0];
        const banner = document.getElementById('selectedFileBanner');
        banner.style.display = 'inline-block';
        banner.textContent = `Selected File: ${selectedPipelineFile.name} (${(selectedPipelineFile.size / 1024).toFixed(1)} KB)`;
        document.getElementById('btnRunPipeline').disabled = false;
    }
}

function loadSampleTextFile() {
    const sampleContent = `CONFIDENTIAL ENTERPRISE QUARTERLY REPORT - FISCAL YEAR 2026.
OmniStore Information Storage Management Platform.
Total Transactions: 1,842,900 operations.
Storage Efficiency Ratio: 4.2:1 with inline compression.
Disaster Recovery RPO: 0.0s via synchronous WAN replication.
Data-at-rest encrypted with AES-256-XTS algorithm.`;

    const blob = new Blob([sampleContent], { type: 'text/plain' });
    selectedPipelineFile = new File([blob], 'enterprise_financial_q1.txt', { type: 'text/plain' });

    const banner = document.getElementById('selectedFileBanner');
    banner.style.display = 'inline-block';
    banner.textContent = `Selected File: ${selectedPipelineFile.name} (Built-in Enterprise Sample)`;
    document.getElementById('btnRunPipeline').disabled = false;
}

async function executePipelineUpload() {
    if (!selectedPipelineFile) {
        showToast('Please select or choose a file first', 'error');
        return;
    }

    const priority = document.getElementById('pipelinePriority').value;
    const stagesContainer = document.getElementById('pipelineStagesContainer');
    stagesContainer.style.display = 'grid';

    const cards = [
        document.getElementById('stage1Card'),
        document.getElementById('stage2Card'),
        document.getElementById('stage3Card'),
        document.getElementById('stage4Card'),
        document.getElementById('stage5Card')
    ];

    cards.forEach(c => {
        c.className = 'pipeline-stage-card';
    });

    // Step 1
    cards[0].classList.add('stage-active');
    await new Promise(r => setTimeout(r, 400));
    cards[0].classList.remove('stage-active');
    cards[0].classList.add('stage-done');

    // Step 2
    cards[1].classList.add('stage-active');
    await new Promise(r => setTimeout(r, 400));
    cards[1].classList.remove('stage-active');
    cards[1].classList.add('stage-done');

    // Perform actual API upload
    const formData = new FormData();
    formData.append('file', selectedPipelineFile);
    formData.append('priority', priority);

    try {
        const res = await fetch('/api/pipeline/upload', { method: 'POST', body: formData });
        const data = await res.json();

        // Step 3
        cards[2].classList.add('stage-active');
        await new Promise(r => setTimeout(r, 300));
        cards[2].classList.remove('stage-active');
        cards[2].classList.add('stage-done');

        // Step 4
        cards[3].classList.add('stage-active');
        await new Promise(r => setTimeout(r, 300));
        cards[3].classList.remove('stage-active');
        cards[3].classList.add('stage-done');

        // Step 5
        cards[4].classList.add('stage-active');
        await new Promise(r => setTimeout(r, 200));
        cards[4].classList.remove('stage-active');
        cards[4].classList.add('stage-done');

        // Show Results
        const resultCard = document.getElementById('pipelineResultCard');
        resultCard.style.display = 'block';
        document.getElementById('pipelineSummaryText').textContent = data.summary;

        const stages = data.pipeline_stages;
        document.getElementById('pipelineDetailsGrid').innerHTML = `
            <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                <strong style="color:var(--accent-purple);">1. Deduplication & Chunking</strong>
                <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                    Total Chunks: <strong>${stages.step_1_deduplication.chunks}</strong><br>
                    Unique Stored: <strong>${stages.step_1_deduplication.unique_stored}</strong><br>
                    Duplicates Reused: <strong>${stages.step_1_deduplication.duplicates_saved}</strong><br>
                    Dedupe Ratio: <strong class="text-accent">${stages.step_1_deduplication.dedup_ratio}</strong>
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                <strong style="color:var(--accent-cyan);">2. AES-256 Encryption</strong>
                <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                    Algorithm: <strong>${stages.step_2_encryption.algorithm}</strong><br>
                    KMS Key Fingerprint: <code>${stages.step_2_encryption.key_fingerprint}</code><br>
                    Sample Ciphertext: <br><code style="font-size:0.72rem;">${stages.step_2_encryption.sample_cipher}</code>
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                <strong style="color:var(--accent-amber);">3. Storage Tiering (ILM)</strong>
                <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                    Assigned Tier: <strong>${stages.step_3_ilm_tiering.assigned_tier}</strong><br>
                    Tier Name: <strong>${stages.step_3_ilm_tiering.tier_name}</strong><br>
                    SLA Priority: <strong>${priority}</strong>
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                <strong style="color:var(--accent-emerald);">4. RAID Parity Striping</strong>
                <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                    RAID Architecture: <strong>RAID ${stages.step_4_raid_striping.raid_level}</strong><br>
                    Striped Chunks: <strong>${stages.step_4_raid_striping.chunks_striped}</strong><br>
                    Parity Math: <strong>XOR Distributed</strong><br>
                    Array Health: <strong class="text-success">${stages.step_4_raid_striping.array_health}</strong>
                </p>
            </div>
        `;

        showToast('File stored successfully through all 6 ISM stages!', 'success');
        loadOverview();

    } catch (err) {
        showToast('Pipeline upload failed', 'error');
    }
}
