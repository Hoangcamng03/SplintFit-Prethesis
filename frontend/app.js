import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ==================== Application State ====================
const state = {
  step: 1,
  sessionId: null,
  sourceName: '',
  scanCenter: new THREE.Vector3(0, 0, 0),
  scanSize: 200,
  suggestedLandmarks: null,
  safeFrame: null,
  landmarks: { proximal: null, distal: null, side: null },
  reliefs: [],
  pickMode: null,
  buildData: null,
  lastExportId: null,
  exportDirHandle: null,
  userFolders: null,
};

// Clinical Presets Mapping (Doctor-friendly -> Verified Engineering Values)
const CLINICAL_PRESETS = {
  fit: {
    swollen: { clearance: 2.5, padding: 1.0 },
    standard: { clearance: 1.5, padding: 0.5 },
    snug: { clearance: 1.3, padding: 0.0 },
  },
  rigidity: {
    light: { thickness: 2.8 },
    medium: { thickness: 3.2 },
    rigid: { thickness: 4.0 },
  },
  vent: {
    honeycomb: { ventilation: true, hole_pitch: 20, hole_ratio: 0.58 },
    moderate: { ventilation: true, hole_pitch: 25, hole_ratio: 0.48 },
    solid: { ventilation: false, hole_pitch: 24, hole_ratio: 0.48 },
  },
  notch: {
    wide: { depth: 22 },
    mild: { depth: 14 },
    straight: { depth: 0 },
  },
};

// ==================== DOM Helpers ====================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function showToast(msg, type = 'info', duration = 4500) {
  const el = $('#toast-box');
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add('hidden'), duration);
}

function setLoading(active, text = 'Đang xử lý hình học 3D…') {
  $('#loading-text').textContent = text;
  $('#loading-overlay').classList.toggle('hidden', !active);
}

// ==================== Three.js 3D Studio ====================
const canvasWrap = $('#viewport-canvas');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeef2f6);

const camera = new THREE.PerspectiveCamera(42, 1, 0.5, 5000);
camera.position.set(220, 180, 260);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
canvasWrap.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

// Clinical Studio Lighting
scene.add(new THREE.HemisphereLight(0xffffff, 0xcbd5e1, 1.0));
const keyLight = new THREE.DirectionalLight(0xffffff, 0.95);
keyLight.position.set(260, 320, 240);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xe0f2fe, 0.55);
fillLight.position.set(-240, -140, -180);
scene.add(fillLight);

// Scene Groups
const scanGroup = new THREE.Group();
const boundaryGroup = new THREE.Group();
const markerGroup = new THREE.Group();
const splintShellGroup = new THREE.Group();
const splintQuadGroup = new THREE.Group();
const splintHeatmapGroup = new THREE.Group();
scene.add(scanGroup, boundaryGroup, markerGroup, splintShellGroup, splintQuadGroup, splintHeatmapGroup);

let activeScanMesh = null;
let pieceShellObjects = [];
let pieceQuadObjects = [];
let pieceHeatObjects = [];

function resizeViewport() {
  const w = canvasWrap.clientWidth || 800;
  const h = canvasWrap.clientHeight || 600;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
window.addEventListener('resize', resizeViewport);
resizeViewport();

(function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
})();

function clearGroup(group) {
  while (group.children.length > 0) {
    const child = group.children[0];
    group.remove(child);
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
      else child.material.dispose();
    }
  }
}

function buildGeometryFromJson(meshJson, useVertexColors = false) {
  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(meshJson.positions), 3));
  geom.setIndex(meshJson.indices);
  geom.computeVertexNormals();

  if (useVertexColors && meshJson.scalars && meshJson.scalars.length) {
    const lo = meshJson.scalar_min ?? 0;
    const hi = Math.max(meshJson.scalar_max ?? 1, lo + 0.01);
    const colors = new Float32Array(meshJson.scalars.length * 3);
    const c = new THREE.Color();
    for (let i = 0; i < meshJson.scalars.length; i++) {
      const t = Math.max(0, Math.min(1, (meshJson.scalars[i] - lo) / (hi - lo)));
      c.setHSL(0.62 - t * 0.52, 0.85, 0.5);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  }
  return geom;
}

function fitCamera(view = 'fit') {
  const c = state.scanCenter;
  const dist = Math.max(state.scanSize * 1.65, 160);
  controls.target.copy(c);
  if (view === 'front') camera.position.set(c.x, c.y - dist, c.z);
  else if (view === 'side') camera.position.set(c.x + dist, c.y, c.z);
  else if (view === 'top') camera.position.set(c.x, c.y, c.z + dist);
  else camera.position.set(c.x + dist * 0.72, c.y - dist * 0.65, c.z + dist * 0.55);
  camera.lookAt(c);
  controls.update();
}

function clearSplintVisuals() {
  clearGroup(splintShellGroup);
  clearGroup(splintQuadGroup);
  clearGroup(splintHeatmapGroup);
  pieceShellObjects = [];
  pieceQuadObjects = [];
  pieceHeatObjects = [];
  state.buildData = null;
  $$('.splint-only').forEach((el) => el.classList.add('hidden'));
  $('#rng-explode').value = 0;
}

function renderScan(data) {
  clearGroup(scanGroup);
  clearGroup(boundaryGroup);
  clearSplintVisuals();

  const geom = buildGeometryFromJson(data.mesh);
  const mat = new THREE.MeshStandardMaterial({
    color: 0xe6d6c7,
    roughness: 0.65,
    metalness: 0.03,
    transparent: true,
    opacity: parseFloat($('#rng-scan-opacity').value),
    side: THREE.DoubleSide,
  });
  activeScanMesh = new THREE.Mesh(geom, mat);
  scanGroup.add(activeScanMesh);

  if (data.boundary_segments && data.boundary_segments.length) {
    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(data.boundary_segments, 3));
    boundaryGroup.add(new THREE.LineSegments(lineGeom, new THREE.LineBasicMaterial({ color: 0xdc2626 })));
  }

  const b = data.mesh.bounds;
  state.scanCenter.set((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2);
  state.scanSize = Math.hypot(b[1] - b[0], b[3] - b[2], b[5] - b[4]);
  fitCamera('fit');

  $('#empty-overlay').classList.add('hidden');
  $('#layer-bar').classList.remove('hidden');
  $('#scene-badge').textContent = `${data.source_name} • ${data.stats.triangles.toLocaleString('vi-VN')} mặt`;
}

function renderMarkers() {
  clearGroup(markerGroup);
  const r = Math.max(state.scanSize * 0.014, 3.2);
  [
    { key: 'proximal', color: 0x2563eb },
    { key: 'distal', color: 0xea580c },
    { key: 'side', color: 0x9333ea },
  ].forEach(({ key, color }) => {
    const pt = state.landmarks[key];
    if (!pt) return;
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(r, 20, 20),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.25, roughness: 0.3 })
    );
    sphere.position.set(pt[0], pt[1], pt[2]);
    markerGroup.add(sphere);
  });

  if (state.landmarks.proximal && state.landmarks.distal) {
    const a = new THREE.Vector3(...state.landmarks.proximal);
    const b = new THREE.Vector3(...state.landmarks.distal);
    const dir = new THREE.Vector3().subVectors(b, a);
    const len = dir.length();
    if (len > 5) {
      markerGroup.add(
        new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]), new THREE.LineBasicMaterial({ color: 0x0f766e }))
      );
      const ringR = state.safeFrame ? Math.max(state.safeFrame.radius_est_mm * 1.28, 28) : Math.max(state.scanSize * 0.14, 34);
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir.clone().normalize());
      [
        { pos: a, color: 0x2563eb },
        { pos: b, color: 0xea580c },
      ].forEach(({ pos, color }) => {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(ringR, 1.1, 10, 48),
          new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.65 })
        );
        ring.position.copy(pos);
        ring.quaternion.copy(q);
        markerGroup.add(ring);
      });
      $('#span-preview').classList.remove('hidden');
      $('#span-preview-val').textContent = `${len.toFixed(1)} mm`;
    }
  } else {
    $('#span-preview').classList.add('hidden');
  }

  state.reliefs.forEach((rel) => {
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(rel.radius_mm, 18, 18),
      new THREE.MeshBasicMaterial({ color: 0xe11d48, transparent: true, opacity: 0.22, wireframe: true })
    );
    sphere.position.set(...rel.point);
    markerGroup.add(sphere);
  });
}

function renderSplint(buildData) {
  clearSplintVisuals();
  state.buildData = buildData;

  const pieceColors = [0x0d9488, 0x0284c7];
  buildData.pieces.forEach((piece, idx) => {
    const col = pieceColors[idx % pieceColors.length];
    if (piece.shell) {
      const mesh = new THREE.Mesh(
        buildGeometryFromJson(piece.shell),
        new THREE.MeshStandardMaterial({ color: col, roughness: 0.34, metalness: 0.06, side: THREE.DoubleSide })
      );
      splintShellGroup.add(mesh);
      pieceShellObjects.push(mesh);
    }
    if (piece.quad_wireframe && piece.quad_wireframe.length) {
      const qGeom = new THREE.BufferGeometry();
      qGeom.setAttribute('position', new THREE.Float32BufferAttribute(piece.quad_wireframe, 3));
      const lines = new THREE.LineSegments(qGeom, new THREE.LineBasicMaterial({ color: idx === 0 ? 0xf59e0b : 0x7c3aed }));
      splintQuadGroup.add(lines);
      pieceQuadObjects.push(lines);
    }
    if (piece.inner) {
      const hMesh = new THREE.Mesh(
        buildGeometryFromJson(piece.inner, true),
        new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.5, side: THREE.DoubleSide })
      );
      splintHeatmapGroup.add(hMesh);
      pieceHeatObjects.push(hMesh);
    }
  });

  $$('.splint-only').forEach((el) => el.classList.remove('hidden'));
  $('#chk-shell').checked = true;
  $('#chk-quad').checked = false;
  $('#chk-heatmap').checked = false;
  syncLayerVisibility();
}

function syncLayerVisibility() {
  scanGroup.visible = $('#chk-scan').checked;
  boundaryGroup.visible = $('#chk-boundaries').checked;
  splintShellGroup.visible = $('#chk-shell').checked;
  splintQuadGroup.visible = $('#chk-quad').checked;
  splintHeatmapGroup.visible = $('#chk-heatmap').checked;
  if (activeScanMesh) activeScanMesh.material.opacity = parseFloat($('#rng-scan-opacity').value);
}

function applyExplode(distMm) {
  if (pieceShellObjects.length < 2 || !state.landmarks.proximal || !state.landmarks.distal || !state.landmarks.side) return;
  const a = new THREE.Vector3(...state.landmarks.proximal);
  const b = new THREE.Vector3(...state.landmarks.distal);
  const s = new THREE.Vector3(...state.landmarks.side);
  const z = new THREE.Vector3().subVectors(b, a).normalize();
  const mid = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5);
  const x = new THREE.Vector3().subVectors(s, mid);
  x.addScaledVector(z, -x.dot(z));
  if (x.lengthSq() < 1e-4) x.set(1, 0, 0);
  x.normalize();

  [pieceShellObjects, pieceQuadObjects, pieceHeatObjects].forEach((arr) => {
    if (arr.length >= 2) {
      arr[0].position.copy(x).multiplyScalar(distMm);
      arr[1].position.copy(x).multiplyScalar(-distMm);
    }
  });
}

// ==================== Raycasting for 3D Picking ====================
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerDownPos = { x: 0, y: 0 };

renderer.domElement.addEventListener('pointerdown', (e) => {
  pointerDownPos = { x: e.clientX, y: e.clientY };
});

renderer.domElement.addEventListener('pointerup', (e) => {
  if (!state.pickMode || !activeScanMesh) return;
  if (Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y) > 5) return;

  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObject(activeScanMesh, false);
  if (!hits.length) {
    showToast('Hãy nhấp trúng trực tiếp lên bề mặt chi 3D.', 'info', 2500);
    return;
  }
  const p = hits[0].point;
  const coords = [Number(p.x.toFixed(2)), Number(p.y.toFixed(2)), Number(p.z.toFixed(2))];

  if (state.pickMode === 'relief') {
    const radius = parseFloat($('#relief-radius').value) || 18;
    const extra = parseFloat($('#relief-extra').value) || 2.0;
    state.reliefs.push({ name: `Tránh tỳ đè #${state.reliefs.length + 1}`, point: coords, radius_mm: radius, extra_mm: extra });
    updateReliefUI();
    showToast(`Đã thêm vùng tránh tỳ đè (+${extra} mm).`, 'success', 2500);
  } else {
    state.landmarks[state.pickMode] = coords;
    updateLandmarksUI();
  }
  setPickMode(null);
  renderMarkers();
});

function setPickMode(mode) {
  state.pickMode = mode;
  const banner = $('#pick-banner');
  if (!mode) {
    banner.classList.add('hidden');
    renderer.domElement.style.cursor = 'grab';
    return;
  }
  const labels = {
    proximal: 'Đầu phía khuỷu tay — Nhấp lên mô hình 3D',
    distal: 'Đầu phía bàn tay — Nhấp lên mô hình 3D',
    side: 'Mặt đặt nẹp (Mu / Lòng) — Nhấp lên mô hình 3D',
    relief: 'Tâm vùng tránh tỳ đè — Nhấp lên mô hình 3D',
  };
  $('#pick-banner-text').textContent = labels[mode];
  banner.classList.remove('hidden');
  renderer.domElement.style.cursor = 'crosshair';
}

// ==================== Consistent 1-Primary-Button Wizard ====================
const PRIMARY_BTN_LABELS = {
  1: 'Tiếp tục chọn vùng →',
  2: 'Tiếp tục thiết kế →',
  3: 'Tạo mô hình nẹp 3D',
  4: 'Sang bước xuất Fusion 360 →',
  5: 'Xuất lưới cho Fusion 360 Form',
};

function goToStep(stepNum) {
  if (stepNum > 1 && !state.sessionId) {
    showToast('Hãy nạp file scan hoặc mở mẫu thử ở Bước 1 trước.', 'info');
    return;
  }
  state.step = Math.max(1, Math.min(5, stepNum));
  $$('.wizard-step').forEach((el) => el.classList.toggle('active', Number(el.dataset.step) === state.step));
  $$('.step-pill').forEach((el) => {
    const s = Number(el.dataset.step);
    el.classList.toggle('active', s === state.step);
    el.classList.toggle('done', s < state.step);
  });

  $('#btn-prev').style.visibility = state.step === 1 ? 'hidden' : 'visible';
  $('#btn-primary-action').textContent = PRIMARY_BTN_LABELS[state.step];

  if (state.step === 4 && state.buildData) {
    $('#inspect-content').classList.remove('hidden');
    $('#build-empty-notice').classList.add('hidden');
  }
  setPickMode(null);
}

$('#btn-primary-action').addEventListener('click', () => {
  if (state.step === 1) goToStep(2);
  else if (state.step === 2) goToStep(3);
  else if (state.step === 3) buildSplint();
  else if (state.step === 4) goToStep(5);
  else if (state.step === 5) exportBundle();
});

// ==================== Clinical Presets & Summary ====================
function updateClinicalSummary() {
  const mode = $('#p-splint-mode').value === 'bivalve' ? 'Nẹp 2 mảnh' : 'Nẹp 1 mảnh';
  const cl = Number($('#p-clearance').value).toFixed(1);
  const pad = Number($('#p-padding').value).toFixed(1);
  const th = Number($('#p-thickness').value).toFixed(1);
  const fl = Number($('#p-rim-flare').value).toFixed(1);
  $('#clinical-summary-pill').textContent = `${mode} • Hở da ${cl} mm • Lót ${pad} mm • Dày ${th} mm • Loe mép ${fl} mm`;
}

function setInputValue(id, value) {
  const el = $(id);
  if (!el) return;
  if (el.type === 'checkbox') el.checked = Boolean(value);
  else el.value = value;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

$$('.preset-grid').forEach((grid) => {
  const group = grid.dataset.presetGroup;
  grid.querySelectorAll('.preset-card').forEach((card) => {
    card.addEventListener('click', () => {
      grid.querySelectorAll('.preset-card').forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
      const val = card.dataset.value;
      const cfg = CLINICAL_PRESETS[group]?.[val];
      if (!cfg) return;
      if (group === 'fit') {
        setInputValue('#p-clearance', cfg.clearance);
        setInputValue('#p-padding', cfg.padding);
      } else if (group === 'rigidity') {
        setInputValue('#p-thickness', cfg.thickness);
      } else if (group === 'vent') {
        setInputValue('#p-ventilation', cfg.ventilation);
        setInputValue('#p-hole-pitch', cfg.hole_pitch);
        setInputValue('#p-hole-ratio', cfg.hole_ratio);
      } else if (group === 'notch') {
        setInputValue('#p-notch-depth', cfg.depth);
      }
      updateClinicalSummary();
    });
  });
});

function initSafeZoneSliders(sf) {
  state.safeFrame = sf;
  if (!sf) return;
  const span = Math.max(30, Math.round(sf.safe_max_mm - sf.safe_min_mm));
  const slProx = $('#sl-prox-pos');
  const slDist = $('#sl-dist-pos');
  const slAng = $('#sl-seam-angle');

  slProx.min = 0;
  slProx.max = Math.max(0, span - 30);
  slProx.value = 0;

  slDist.min = 30;
  slDist.max = span;
  slDist.value = span;

  slAng.value = 0;
  $('#safe-zone-span').textContent = `dài tối đa ${span} mm`;
  syncLandmarksFromSliders();
}

function syncLandmarksFromSliders(changed = null) {
  const sf = state.safeFrame;
  if (!sf) return;
  const slProx = $('#sl-prox-pos');
  const slDist = $('#sl-dist-pos');
  const slAng = $('#sl-seam-angle');
  let pRel = parseFloat(slProx.value);
  let dRel = parseFloat(slDist.value);
  const minLen = 30;

  // Enforce minimum splint length of 30 mm inside safe bounds
  if (dRel - pRel < minLen) {
    if (changed === 'prox') {
      pRel = Math.max(0, dRel - minLen);
      slProx.value = pRel;
    } else {
      dRel = Math.min(parseFloat(slDist.max), pRel + minLen);
      slDist.value = dRel;
    }
  }

  const zStart = sf.safe_min_mm + pRel;
  const zEnd = sf.safe_min_mm + dRel;
  const zMid = 0.5 * (zStart + zEnd);
  const angRad = (parseFloat(slAng.value) * Math.PI) / 180.0;
  const rSide = (sf.radius_est_mm || 30) + 6.0;

  const o = sf.origin;
  const z = sf.axis_z;
  const x = sf.axis_x;
  const y = sf.axis_y;
  const ca = Math.cos(angRad);
  const sa = Math.sin(angRad);

  state.landmarks.proximal = [o[0] + z[0] * zStart, o[1] + z[1] * zStart, o[2] + z[2] * zStart];
  state.landmarks.distal = [o[0] + z[0] * zEnd, o[1] + z[1] * zEnd, o[2] + z[2] * zEnd];
  state.landmarks.side = [
    o[0] + z[0] * zMid + (ca * x[0] + sa * y[0]) * rSide,
    o[1] + z[1] * zMid + (ca * x[1] + sa * y[1]) * rSide,
    o[2] + z[2] * zMid + (ca * x[2] + sa * y[2]) * rSide,
  ];

  $('#val-prox-pos').textContent = `+${Math.round(pRel)} mm`;
  $('#val-dist-pos').textContent = `${Math.round(dRel)} mm`;
  $('#val-seam-angle').textContent = `${Math.round(parseFloat(slAng.value))}°`;

  updateLandmarksUI();
  renderMarkers();
}

// ==================== UI Updates ====================
function updateScanUI(data) {
  state.sessionId = data.session_id;
  state.sourceName = data.source_name;
  state.suggestedLandmarks = data.suggested_landmarks;
  state.landmarks = {
    proximal: [...data.suggested_landmarks.proximal],
    distal: [...data.suggested_landmarks.distal],
    side: [...data.suggested_landmarks.side],
  };
  state.reliefs = [];
  updateLandmarksUI();
  updateReliefUI();
  renderScan(data);
  if (data.safe_frame) {
    initSafeZoneSliders(data.safe_frame);
  } else {
    renderMarkers();
  }

  const st = data.stats;
  $('#scan-summary-card').classList.remove('hidden');
  $('#scan-stats-grid').innerHTML = `
    <div class="stat-box"><div class="stat-label">Độ chi tiết lưới</div><div class="stat-value">${st.triangles.toLocaleString('vi-VN')} mặt</div></div>
    <div class="stat-box"><div class="stat-label">Chiều dài mẫu</div><div class="stat-value">${data.suggested_landmarks.span_mm} mm</div></div>
    <div class="stat-box"><div class="stat-label">Cạnh biên hở</div><div class="stat-value">${st.boundary_edges}</div></div>
    <div class="stat-box"><div class="stat-label">Số khối bề mặt</div><div class="stat-value">${data.total_pieces}</div></div>
  `;

  const pieceWrap = $('#piece-selector-wrap');
  const pieceSel = $('#scan-piece-select');
  if (data.pieces && data.pieces.length > 1) {
    pieceWrap.classList.remove('hidden');
    pieceSel.innerHTML =
      data.pieces
        .map((p, idx) => `<option value="${p.id}" ${p.id === data.active_piece_id ? 'selected' : ''}>Khối #${idx + 1} (${p.triangles.toLocaleString('vi-VN')} mặt)</option>`)
        .join('') + `<option value="all" ${data.active_piece_id === 'all' ? 'selected' : ''}>Giữ tất cả</option>`;
  } else {
    pieceWrap.classList.add('hidden');
  }
}

function updateLandmarksUI() {
  const fmt = (pt) => (pt ? 'Đã đặt vị trí ✓' : 'Chưa chọn');
  $('#lm-proximal-val').textContent = fmt(state.landmarks.proximal);
  $('#lm-distal-val').textContent = fmt(state.landmarks.distal);
  $('#lm-side-val').textContent = fmt(state.landmarks.side);
}

function updateReliefUI() {
  const wrap = $('#relief-list');
  if (!state.reliefs.length) {
    wrap.innerHTML = '';
    return;
  }
  wrap.innerHTML = state.reliefs
    .map(
      (r, idx) => `
      <div class="relief-chip">
        <span>${r.name} (+${r.extra_mm} mm)</span>
        <button class="btn-link" style="color:#be123c;" data-del-relief="${idx}">Xóa</button>
      </div>`
    )
    .join('');
  $$('[data-del-relief]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.reliefs.splice(Number(btn.dataset.delRelief), 1);
      updateReliefUI();
      renderMarkers();
    });
  });
}

function updateInspectUI(data) {
  const r = data.report;
  $('#build-empty-notice').classList.add('hidden');
  $('#inspect-content').classList.remove('hidden');
  $('#result-metrics').innerHTML = `
    <div class="stat-box"><div class="stat-label">Chiều dài nẹp</div><div class="stat-value">${(r.length_mm || 0).toFixed(1)} mm</div></div>
    <div class="stat-box"><div class="stat-label">Lưới Quad (Fusion)</div><div class="stat-value">${(r.quad_faces || 0).toLocaleString('vi-VN')} ô</div></div>
    <div class="stat-box"><div class="stat-label">Lỗ tổ ong / Khe đai</div><div class="stat-value">${r.ventilation_holes || 0} lỗ • ${r.strap_slots || 0} khe</div></div>
    <div class="stat-box"><div class="stat-label">Độ hở mặt trong</div><div class="stat-value">${(r.nominal_clearance_min_mm || 0).toFixed(1)}–${(r.nominal_clearance_max_mm || 0).toFixed(1)} mm</div></div>
  `;

  const badgeMap = {
    PASSED: ['Đạt', 'st-pass'],
    PASSED_SAMPLED: ['Đạt', 'st-pass'],
    FAILED: ['Cần chỉnh', 'st-fail'],
    NOT_ENTERED: ['Chưa đo', 'st-muted'],
    NOT_VALIDATED: ['Chưa thử lâm sàng', 'st-warn'],
  };
  $('#checks-list').innerHTML = (r.technical_checks || [])
    .map((c) => {
      const [label, cls] = badgeMap[c.status] || [c.status, 'st-muted'];
      return `<div class="check-row"><span>${c.name}</span><span class="status-badge ${cls}">${label}</span></div>`;
    })
    .join('');

  const uniqueMsgs = Array.from(new Set(r.messages || []));
  $('#messages-list').innerHTML = uniqueMsgs.map((m) => `<li>${m}</li>`).join('');
}

// ==================== API Calls ====================
function friendlyError(err) {
  const msg = String(err?.message || err || 'Lỗi không xác định');
  if (msg.toLowerCase().includes('failed to fetch')) {
    return 'Mất kết nối tới server SplintFit (127.0.0.1:8765). Hãy mở lại file START_STUDIO.bat rồi thử lại.';
  }
  return msg;
}

async function loadDemo(kind = 'hand_forearm') {
  setLoading(true, 'Đang nạp mẫu giải phẫu cẳng tay–bàn tay…');
  try {
    const res = await fetch('/api/scan/demo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không thể nạp mẫu thử.');
    updateScanUI(data);
    showToast('Đã nạp mẫu tay chuẩn & tự gợi ý 3 mốc. Nhấn "Tiếp tục chọn vùng →" để xem.', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
}

async function uploadScanFile(file) {
  setLoading(true, `Đang đọc file ${file.name}…`);
  try {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('scale_mm', $('#scan-unit').value);
    const res = await fetch('/api/scan/upload', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không đọc được file quét.');
    updateScanUI(data);
    showToast(`Đã nạp ${file.name} thành công.`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
}

async function buildSplint() {
  if (!state.sessionId) return showToast('Chưa nạp file scan.', 'error');
  if (!state.landmarks.proximal || !state.landmarks.distal || !state.landmarks.side) {
    goToStep(2);
    return showToast('Hãy chọn đủ 3 mốc ở Bước 2.', 'error');
  }
  setLoading(true, 'Đang dựng nẹp 2 mảnh lưới tổ ong, loe mép & lưới Quad cho Fusion Form…');
  try {
    const params = {
      proximal_point: state.landmarks.proximal,
      distal_point: state.landmarks.distal,
      side_point: state.landmarks.side,
      start_adjust_mm: parseFloat($('#p-start-adj').value) || 0,
      end_adjust_mm: parseFloat($('#p-end-adj').value) || 0,
      reliefs: state.reliefs,
      splint_mode: $('#p-splint-mode').value,
      cast_template: true,
      clearance_mm: parseFloat($('#p-clearance').value),
      padding_mm: parseFloat($('#p-padding').value),
      thickness_mm: parseFloat($('#p-thickness').value),
      rim_flare_mm: parseFloat($('#p-rim-flare').value),
      seam_gap_mm: parseFloat($('#p-seam-gap').value),
      coverage_deg: parseFloat($('#p-coverage').value),
      ventilation: $('#p-ventilation').checked,
      hole_pitch_mm: parseFloat($('#p-hole-pitch').value),
      hole_ratio: parseFloat($('#p-hole-ratio').value),
      hand_notch_depth_mm: parseFloat($('#p-notch-depth').value),
      hand_notch_width_deg: parseFloat($('#p-notch-width').value) || 75,
      hand_notch_angle_deg: parseFloat($('#p-notch-angle').value) || 0,
      circumference_proximal_mm: parseFloat($('#p-circ-prox').value) || 0,
      circumference_mid_mm: parseFloat($('#p-circ-mid').value) || 0,
      circumference_distal_mm: parseFloat($('#p-circ-dist').value) || 0,
    };
    const res = await fetch('/api/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId, params }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không tạo được mô hình nẹp.');
    renderSplint(data);
    updateInspectUI(data);
    goToStep(4);
    showToast('Đã tạo xong nẹp 3D lưới tổ ong & lưới Quad cho Fusion 360 Form!', 'success');
  } catch (err) {
    showToast(friendlyError(err), 'error', 6500);
  } finally {
    setLoading(false);
  }
}

async function exportBundle() {
  if (!state.sessionId || !state.buildData) {
    goToStep(3);
    return showToast('Hãy tạo mô hình nẹp 3D ở Bước 3 trước khi xuất.', 'error');
  }
  const exportMode = $('#chk-export-full')?.checked ? 'full' : 'fusion_only';
  const outputDir = ($('#export-output-dir')?.value || '').trim();
  if (outputDir) localStorage.setItem('splintfit_output_dir', outputDir);
  setLoading(true, exportMode === 'full' ? 'Đang xuất gói đầy đủ…' : 'Đang xuất 5 file mesh cho Fusion 360 Form…');
  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        case_id: $('#case-id').value,
        side: $('#hand-side').value,
        export_mode: exportMode,
        output_dir: outputDir,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Xuất gói thất bại.');
    state.lastExportId = data.export_id;
    let savedLocationText = data.folder_path;

    // If user picked a native folder via Browser File System Access API, write files directly into it!
    if (state.exportDirHandle) {
      setLoading(true, `Đang ghi trực tiếp vào thư mục "${state.exportDirHandle.name}"…`);
      const subDir = await state.exportDirHandle.getDirectoryHandle(data.folder_name, { create: true });
      for (const f of data.files) {
        const parts = f.path.split('/');
        let targetDir = subDir;
        for (let i = 0; i < parts.length - 1; i++) {
          targetDir = await targetDir.getDirectoryHandle(parts[i], { create: true });
        }
        const fileHandle = await targetDir.getFileHandle(parts[parts.length - 1], { create: true });
        const writable = await fileHandle.createWritable();
        const fRes = await fetch(`/api/export/${data.export_id}/file/${encodeURI(f.path)}`);
        const blob = await fRes.blob();
        await writable.write(blob);
        await writable.close();
      }
      savedLocationText = `${state.exportDirHandle.name}\\${data.folder_name} (đã ghi trực tiếp vào thư mục bạn chọn!)`;
    }

    $('#export-success-box').classList.remove('hidden');
    $('#export-folder-path').textContent = savedLocationText;
    $('#btn-download-zip').href = data.download_url;
    $('#export-files-list').innerHTML = data.files
      .map((f) => {
        const isQuad = f.path.endsWith('_quad.obj');
        return `<div class="file-item ${isQuad ? 'highlight' : ''}"><span>${isQuad ? '⭐ ' : ''}${f.path}</span><span>${f.size_kb} KB</span></div>`;
      })
      .join('');
    showToast(
      state.exportDirHandle
        ? `Đã lưu trực tiếp ${data.files.length} file vào "${state.exportDirHandle.name}\\${data.folder_name}"!`
        : 'Đã xuất gói Fusion 360 Form thành công!',
      'success'
    );
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
}

// ==================== Event Bindings ====================
$$('.step-pill').forEach((btn) => btn.addEventListener('click', () => goToStep(Number(btn.dataset.step))));
$('#btn-prev').addEventListener('click', () => goToStep(state.step - 1));

$('#btn-open-folder').addEventListener('click', async () => {
  if (!state.lastExportId) return;
  try {
    const res = await fetch(`/api/export/${state.lastExportId}/open-folder`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.opened) throw new Error(data.error || 'Không mở được Explorer.');
    showToast('Đã gọi Windows Explorer (kiểm tra thanh taskbar nếu cửa sổ nằm phía sau).', 'info', 3500);
  } catch (err) {
    showToast('Không mở tự động được — hãy bấm "Sao chép đường dẫn" hoặc "Tải gói .ZIP".', 'error', 4500);
  }
});

$('#btn-copy-path').addEventListener('click', async () => {
  const pathText = $('#export-folder-path').textContent.trim();
  if (!pathText) return;
  try {
    await navigator.clipboard.writeText(pathText);
    showToast('Đã sao chép đường dẫn! Dán (Ctrl+V) vào thanh địa chỉ File Explorer.', 'success', 3500);
  } catch {
    showToast(pathText, 'info', 5000);
  }
});

// Restore saved export directory & bind native Browser Directory Picker + quick folder presets
const savedDir = localStorage.getItem('splintfit_output_dir');
if (savedDir && $('#export-output-dir')) $('#export-output-dir').value = savedDir;

fetch('/api/user-folders')
  .then((r) => r.json())
  .then((d) => (state.userFolders = d))
  .catch(() => {});

$$('.quick-dir-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.dirKey;
    const p = state.userFolders?.[key];
    if (!p) return;
    state.exportDirHandle = null;
    $('#native-dir-status').classList.add('hidden');
    $('#export-output-dir').value = p;
    localStorage.setItem('splintfit_output_dir', p);
    showToast(`Đã chọn thư mục lưu: ${p}`, 'success', 2800);
  });
});

$('#btn-pick-native-dir').addEventListener('click', async () => {
  if (typeof window.showDirectoryPicker === 'function') {
    try {
      const handle = await window.showDirectoryPicker({ mode: 'readwrite' });
      state.exportDirHandle = handle;
      const statusEl = $('#native-dir-status');
      statusEl.innerHTML = `✓ Đã chọn thư mục trực tiếp: <strong>${handle.name}</strong>`;
      statusEl.classList.remove('hidden');
      showToast(`Đã chọn thư mục "${handle.name}". Khi bấm Xuất, file sẽ lưu thẳng vào đây!`, 'success', 3500);
      return;
    } catch (err) {
      if (err?.name === 'AbortError') return;
    }
  }
  showToast('Trình duyệt hiện tại không hỗ trợ chọn thư mục trực tiếp. Hãy dùng nút Desktop / Downloads / Documents bên dưới.', 'info', 4500);
});

$('#btn-quick-demo').addEventListener('click', () => loadDemo('hand_forearm'));
$('#btn-demo-hand').addEventListener('click', () => loadDemo('hand_forearm'));
$('#btn-demo-forearm').addEventListener('click', () => loadDemo('simple_forearm'));

const dropzone = $('#dropzone');
$('#file-input').addEventListener('change', (e) => {
  if (e.target.files && e.target.files[0]) uploadScanFile(e.target.files[0]);
});
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) uploadScanFile(e.dataTransfer.files[0]);
});

$('#scan-piece-select').addEventListener('change', async (e) => {
  if (!state.sessionId) return;
  setLoading(true, 'Đang chuyển khối lưới…');
  try {
    const res = await fetch('/api/scan/select-piece', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId, piece_id: e.target.value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    updateScanUI(data);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
});

$$('[data-pick]').forEach((btn) => btn.addEventListener('click', () => setPickMode(btn.dataset.pick)));
$('#btn-cancel-pick').addEventListener('click', () => setPickMode(null));
$('#btn-auto-landmarks').addEventListener('click', () => {
  if (state.safeFrame) {
    initSafeZoneSliders(state.safeFrame);
    showToast('Đã đặt lại vùng nẹp an toàn mặc định.', 'info', 2200);
    return;
  }
  if (!state.suggestedLandmarks) return;
  state.landmarks = {
    proximal: [...state.suggestedLandmarks.proximal],
    distal: [...state.suggestedLandmarks.distal],
    side: [...state.suggestedLandmarks.side],
  };
  updateLandmarksUI();
  renderMarkers();
  showToast('Đã đặt lại 3 mốc gợi ý tự động.', 'info', 2500);
});

$('#sl-prox-pos').addEventListener('input', () => syncLandmarksFromSliders('prox'));
$('#sl-dist-pos').addEventListener('input', () => syncLandmarksFromSliders('dist'));
$('#sl-seam-angle').addEventListener('input', () => syncLandmarksFromSliders('ang'));

$$('.cam-btn').forEach((btn) => btn.addEventListener('click', () => fitCamera(btn.dataset.cam)));

['#chk-scan', '#chk-boundaries', '#chk-shell', '#chk-quad', '#chk-heatmap', '#rng-scan-opacity'].forEach((id) => {
  $(id).addEventListener('input', syncLayerVisibility);
});
$('#rng-explode').addEventListener('input', (e) => applyExplode(parseFloat(e.target.value)));

const bindRange = (id, outId, fmt) => {
  const el = $(id);
  const out = $(outId);
  const sync = () => {
    out.textContent = fmt(el.value);
    updateClinicalSummary();
  };
  el.addEventListener('input', sync);
  sync();
};
bindRange('#p-clearance', '#val-clearance', (v) => `${Number(v).toFixed(2)} mm`);
bindRange('#p-padding', '#val-padding', (v) => `${Number(v).toFixed(2)} mm`);
bindRange('#p-thickness', '#val-thickness', (v) => `${Number(v).toFixed(1)} mm`);
bindRange('#p-rim-flare', '#val-flare', (v) => `${Number(v).toFixed(1)} mm`);
bindRange('#p-seam-gap', '#val-seam', (v) => `${Number(v).toFixed(1)} mm`);
bindRange('#p-coverage', '#val-coverage', (v) => `${v}°`);
bindRange('#p-hole-pitch', '#val-pitch', (v) => `${v} mm`);
bindRange('#p-hole-ratio', '#val-ratio', (v) => Number(v).toFixed(2));
bindRange('#p-notch-depth', '#val-notch-depth', (v) => `${v} mm`);

$('#p-splint-mode').addEventListener('change', (e) => {
  const isBivalve = e.target.value === 'bivalve';
  $('#wrap-seam-gap').classList.toggle('hidden', !isBivalve);
  $('#wrap-coverage').classList.toggle('hidden', isBivalve);
  updateClinicalSummary();
});

$('#p-ventilation').addEventListener('change', (e) => {
  $('#vent-controls').classList.toggle('hidden', !e.target.checked);
});

updateClinicalSummary();
goToStep(1);
