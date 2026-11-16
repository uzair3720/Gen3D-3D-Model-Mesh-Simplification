// Gen3D front end: talks to server.py and draws the mesh with three.js.
import * as THREE from 'three';
import { OrbitControls } from '/static/vendor/OrbitControls.js';

const $ = (id) => document.getElementById(id);
const state = { id: null, original: null, simplified: null, show: 'original', view: 'solid', edgeTab: 'cheapest_edges' };

// ---------- viewport ----------
const view = $('view');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
view.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x16181b);
const camera = new THREE.PerspectiveCamera(40, 1, 0.001, 1000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x555a63, 1.5));
const headlight = new THREE.DirectionalLight(0xffffff, 1.6);
scene.add(headlight);
const group = new THREE.Group();   // the mesh and its edge overlay
const floor = new THREE.Group();   // the ground grid
scene.add(group, floor);

function resize() {
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(view);
renderer.setAnimationLoop(() => {
  controls.update();
  headlight.position.copy(camera.position);
  renderer.render(scene, camera);
});

const LOW = new THREE.Color(0x3b6fd4), MID = new THREE.Color(0x9aa3ad), HIGH = new THREE.Color(0xe0483c);
const costColour = (r) => (r < 0.5 ? LOW.clone().lerp(MID, r * 2) : MID.clone().lerp(HIGH, (r - 0.5) * 2));
const SHARP = new THREE.Color(0xf0a030), BOUNDARY = new THREE.Color(0x35c9d6), WIRE = new THREE.Color(0x14161a);

function empty(g) {
  for (const child of [...g.children]) { child.geometry.dispose(); child.material.dispose(); g.remove(child); }
}

function edgeLines(data, pick) {
  // pick(i) returns the colour of edge i, or null to leave that edge out
  const pos = [], col = [];
  const p = data.positions, e = data.edges;
  for (let i = 0; i < e.length / 2; i++) {
    const c = pick(i);
    if (!c) continue;
    for (const v of [e[2 * i], e[2 * i + 1]]) {
      pos.push(p[3 * v], p[3 * v + 1], p[3 * v + 2]);
      col.push(c.r, c.g, c.b);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ vertexColors: true }));
}

function draw(refit) {
  const data = state[state.show];
  empty(group);
  $('empty').hidden = !!data;
  if (!data) return;

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(data.positions, 3));
  geo.setIndex(data.faces);
  geo.computeVertexNormals();
  const overlay = state.view === 'cost' || state.view === 'feat';
  group.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    color: overlay ? 0x3a3e45 : 0xa9afb8, roughness: 0.8, metalness: 0.05, flatShading: true, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  })));
  if (state.view === 'wire') group.add(edgeLines(data, () => WIRE));
  if (state.view === 'cost') group.add(edgeLines(data, (i) => costColour(data.edge_cost_rank[i])));
  if (state.view === 'feat') group.add(edgeLines(data, (i) => (data.edge_boundary[i] ? BOUNDARY : data.edge_sharp[i] ? SHARP : null)));

  if (refit) {
    geo.computeBoundingBox();
    geo.computeBoundingSphere();
    const s = geo.boundingSphere;
    controls.target.copy(s.center);
    camera.position.copy(s.center).add(new THREE.Vector3(0.8, 0.45, 1.3).normalize().multiplyScalar(s.radius * 3.1));
    camera.near = s.radius / 100;
    camera.far = s.radius * 100;
    camera.updateProjectionMatrix();
    empty(floor);
    const grid = new THREE.GridHelper(s.radius * 6, 24, 0x3a3f47, 0x26292e);
    grid.position.set(s.center.x, geo.boundingBox.min.y, s.center.z);
    floor.add(grid);
  }
  drawLegend();
}

function drawLegend() {
  const el = $('legend');
  el.replaceChildren();
  const text = (t) => { const s = document.createElement('span'); s.textContent = t; return s; };
  const swatch = (c, t) => { const s = text(t); const b = document.createElement('span'); b.className = 'sw'; b.style.background = c; s.prepend(b); return s; };
  if (state.view === 'cost') {
    const ramp = document.createElement('span'); ramp.className = 'ramp';
    el.append(text('low cost'), ramp, text('high cost'));
  } else if (state.view === 'feat') {
    el.append(swatch('#f0a030', 'sharp (> 30°)'), swatch('#35c9d6', 'boundary'));
  }
}

// ---------- side panel ----------
const int = (n) => Number(n).toLocaleString('en-US');
const num = (x) => (x === 0 ? '0' : Math.abs(x) < 0.001 ? x.toExponential(2) : x.toFixed(4));

function row(table, cells, header) {
  const tr = document.createElement('tr');
  for (const c of cells) { const td = document.createElement(header ? 'th' : 'td'); td.textContent = c; tr.append(td); }
  table.append(tr);
}

function drawStats() {
  const t = $('stats'), a = state.original?.stats, b = state.simplified?.stats;
  if (!a) return;
  t.replaceChildren();
  if (b) row(t, ['', 'Original', 'Simplified'], true);
  const lines = [
    ['Vertices', 'vertices', int], ['Faces', 'faces', int], ['Edges', 'edges', int],
    ['Sharp edges', 'sharp_edges', int], ['Boundary edges', 'boundary_edges', int], ['Components', 'parts', int],
    ['Watertight', 'watertight', (v) => (v ? 'yes' : 'no')],
    ['Mean edge length', 'edge_length_mean', num], ['Median QEM cost', 'qem_cost_median', num],
  ];
  for (const [label, key, f] of lines) row(t, b ? [label, f(a[key]), f(b[key])] : [label, f(a[key])]);
}

function drawQuality() {
  const t = $('quality'), q = state.simplified?.quality;
  t.replaceChildren();
  if (!q) { row(t, ['Not simplified yet']); t.rows[0].cells[0].className = 'muted'; return; }
  const a = state.original.stats, b = state.simplified.stats;
  row(t, ['Face reduction', (100 * (1 - b.faces / a.faces)).toFixed(1) + ' %']);
  row(t, ['Chamfer distance', num(q.chamfer)]);
  row(t, ['Hausdorff distance', num(q.hausdorff)]);
  row(t, ['Normal consistency', q.normal_consistency.toFixed(4)]);
}

function drawEdges() {
  const t = $('edges'), d = state[state.show];
  if (!d) return;
  t.replaceChildren();
  row(t, ['Vertices', 'Length', 'Dihedral', 'Cost'], true);
  for (const e of d[state.edgeTab]) row(t, [e.edge.join(' – '), num(e.length), e.angle_deg.toFixed(1) + '°', num(e.qem_cost)]);
}

function status(text, isError) {
  $('status').textContent = text;
  $('status').className = isError ? 'err' : '';
}

function updateTarget() {
  const faces = state.original?.stats.faces;
  $('target').textContent = faces ? '→ ' + int(Math.max(4, Math.round(faces * $('keep').value / 100))) + ' faces' : '';
}

function refresh(refit) {
  for (const [attr, key] of [['show', 'show'], ['view', 'view'], ['edges', 'edgeTab']])
    document.querySelectorAll(`[data-${attr}]`).forEach((b) => b.classList.toggle('on', b.dataset[attr] === state[key]));
  document.querySelector('[data-show=simplified]').disabled = !state.simplified;
  $('run').disabled = !state.id;
  draw(refit); drawStats(); drawQuality(); drawEdges(); updateTarget();
}

// ---------- server calls ----------
async function call(url, options) {
  const res = await fetch(url, options);
  let body = null;
  try { body = await res.json(); } catch { /* not JSON */ }
  if (!res.ok || !body) throw new Error(body?.error || `Server error (${res.status})`);
  return body;
}

async function load(url, options, label) {
  status('Loading ' + label + '...');
  try {
    const data = await call(url, options);
    Object.assign(state, { id: data.id, original: data, simplified: null, show: 'original' });
    $('name').textContent = data.source;
    status(`${int(data.stats.vertices)} vertices, ${int(data.stats.faces)} faces, ${int(data.stats.edges)} edges`);
    refresh(true);
  } catch (err) { status(err.message, true); }
}

function openFile(file) {
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  load('/api/upload', { method: 'POST', body: form }, file.name);
}

$('sample').onclick = () => load('/api/sample', { method: 'POST' }, 'sample');
$('file').onchange = (ev) => { openFile(ev.target.files[0]); ev.target.value = ''; };
view.addEventListener('dragover', (ev) => { ev.preventDefault(); view.classList.add('drag'); });
view.addEventListener('dragleave', () => view.classList.remove('drag'));
view.addEventListener('drop', (ev) => { ev.preventDefault(); view.classList.remove('drag'); openFile(ev.dataTransfer.files[0]); });

$('keep').oninput = () => { $('keepNum').value = $('keep').value; updateTarget(); };
$('keepNum').onchange = () => {
  const v = Math.min(95, Math.max(1, Math.round(Number($('keepNum').value) || 25)));
  $('keepNum').value = v; $('keep').value = v; updateTarget();
};

$('run').onclick = async () => {
  $('run').disabled = true;
  status('Simplifying...');
  const started = performance.now();
  try {
    state.simplified = await call('/api/simplify', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: state.id, keep: Number($('keep').value) / 100 }),
    });
    state.show = 'simplified';
    const a = state.original.stats.faces, b = state.simplified.stats.faces;
    status(`QEM: ${int(a)} → ${int(b)} faces in ${((performance.now() - started) / 1000).toFixed(1)} s`);
  } catch (err) { status(err.message, true); }
  refresh(false);
};

for (const [attr, key] of [['show', 'show'], ['view', 'view'], ['edges', 'edgeTab']])
  document.querySelectorAll(`[data-${attr}]`).forEach((b) => { b.onclick = () => { state[key] = b.dataset[attr]; refresh(false); }; });

resize();
