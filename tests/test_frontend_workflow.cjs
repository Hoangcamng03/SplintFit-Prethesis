// Execute real workflow functions with a minimal DOM adapter, without a browser.
// This verifies guards/state transitions, not WebGL, layout or directory dialogs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../frontend/index.html'), 'utf8');
const elements = new Map();
const nodes = [];
function element(id) {
  if (!elements.has(id)) {
    const attrs = html.match(new RegExp('<(?:input|select)[^>]*id="' + id.slice(1) + '"[^>]*>'))?.[0] || '';
    const classes = new Set();
    const el = { value: attrs.match(/value="([^"]*)"/)?.[1] ?? '0', checked: /\schecked[\s>]/.test(attrs),
      disabled: false, dataset: {}, style: {}, textContent: '',
      classList: { add: v => classes.add(v), remove: v => classes.delete(v),
        toggle(v, flag) { flag ? classes.add(v) : classes.delete(v); } },
      hasAttribute: name => name === 'data-was-disabled' && Object.hasOwn(el.dataset, 'wasDisabled'),
      removeAttribute(name) { this[name] = undefined; },
    };
    elements.set(id, el);
  }
  return elements.get(id);
}
element('#p-splint-mode').value = 'bivalve';
const state = { step: 3, busy: false, sessionId: 'session',
  landmarks: { proximal: [0, 0, 0], distal: [0, 0, 200], side: [30, 0, 100] },
  reliefs: [], buildData: null, builtParams: null };
const messages = [];
const context = vm.createContext({ state, $: element, $$: () => nodes,
  showToast: msg => messages.push(msg), clearSplintVisuals: () => { state.buildData = null; },
  setPickMode() {}, console });
const between = (a, b) => source.slice(source.indexOf(a), source.indexOf(b, source.indexOf(a)));
vm.runInContext(between('function setLoading(', '// ==================== Three.js'), context);
vm.runInContext(between('function collectParameters()', 'async function exportBundle()'), context);
vm.runInContext(between('const PRIMARY_BTN_LABELS', "$('#btn-primary-action').addEventListener"), context);
function run(code) { return vm.runInContext(code, context); }

element('#confirm-scale').checked = false;
element('#confirm-region').checked = false;
run('goToStep(5)');
assert.equal(state.step, 3, 'Cannot skip scale confirmation');
element('#confirm-scale').checked = true;
run('goToStep(5)');
assert.equal(state.step, 3, 'Cannot skip region confirmation');
element('#confirm-region').checked = true;
run('goToStep(5)');
assert.equal(state.step, 3, 'Cannot export without current model');
run('state.buildData = {export_ready: true, build_id: "current"}; state.builtParams = JSON.parse(JSON.stringify(collectParameters()));');
assert.equal(run('Boolean(currentBuildMatches())'), true);
run('goToStep(5)');
assert.equal(state.step, 5);
element('#p-thickness').value = '4';
assert.equal(run('Boolean(currentBuildMatches())'), false, 'Edited parameters invalidate match even if an input event was missed');
run('invalidateDesign()');
assert.equal(state.buildData, null);
assert.equal(state.lastExportId, null);
assert.equal(element('#btn-download-zip').href, undefined);
assert.equal(element('#build-empty-notice').textContent.includes('Tạo lại'), true);
const normal = element('#btn-primary-action');
const alreadyDisabled = element('#disabled-control'); alreadyDisabled.disabled = true;
nodes.push(normal, alreadyDisabled);
run('setLoading(true)');
assert.equal(state.busy, true); assert.equal(normal.disabled, true);
state.step = 3; run('goToStep(1)'); assert.equal(state.step, 3, 'No navigation during request');
run('setLoading(true); setLoading(false)');
assert.equal(normal.disabled, false); assert.equal(alreadyDisabled.disabled, true);
assert.equal(state.busy, false);
context.localStorage = {setItem() {}};
context.fetch = async () => ({ok: true, json: async () => ({
  export_id: 'export-current', folder_name: 'CASE_123', folder_path: '/exports/CASE_123',
  download_url: '/api/export/export-current/download', files: [],
})});
state.exportDirHandle = {name: 'chosen', getDirectoryHandle: async () => { throw new Error('Permission denied'); }};
run('state.buildData = {export_ready: true, build_id: "current"}; state.builtParams = JSON.parse(JSON.stringify(collectParameters()));');
vm.runInContext(between('async function exportBundle()', '// ==================== Event Bindings'), context);
(async () => {
  await run('exportBundle()');
  assert.equal(state.lastExportId, 'export-current');
  assert.equal(element('#btn-download-zip').href, '/api/export/export-current/download');
  assert.equal(element('#export-folder-path').textContent.includes('tải ZIP'), true);
  assert.equal(state.busy, false);
  console.log('Frontend workflow guards and directory-failure ZIP fallback: PASS (DOM adapter; not a browser/WebGL test).');
})().catch(error => { console.error(error); process.exitCode = 1; });
