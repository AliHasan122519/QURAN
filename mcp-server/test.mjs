// Tests the MCP server end to end against an in-memory fake of the GitHub API (contents + git data endpoints), seeded with the real content/ folder.
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createServer, githubClient } from './core.js';
import worker from './worker.js';

const files = new Map(); for (const f of readdirSync('content')) if (f.endsWith('.json')) files.set('content/' + f, readFileSync('content/' + f, 'utf8'));
let commits = 0; const head = { sha: 'c0' }; const pending = new Map();
const fakeFetch = async (url, init = {}) => {
  const u = new URL(url); const p = u.pathname.replace('/repos/o/r', ''); const method = init.method ?? 'GET'; const body = init.body ? JSON.parse(init.body) : null;
  const send = (o, s = 200) => new Response(JSON.stringify(o), { status: s });
  if (!init.headers?.Authorization?.startsWith('Bearer ')) return send({ message: 'no auth' }, 401);
  let m;
  if ((m = p.match(/^\/contents\/(.+)$/))) { const t = files.get(decodeURIComponent(m[1])); return t === undefined ? send({ message: 'Not Found' }, 404) : new Response(t, { status: 200 }); }
  if (p === '/git/ref/heads/main') return send({ object: { sha: head.sha } });
  if ((m = p.match(/^\/git\/commits\/(.+)$/))) return send({ tree: { sha: 'tree-' + m[1] } });
  if (p === '/git/trees' && method === 'POST') { const id = 'tree' + Math.random(); pending.set(id, body.tree); return send({ sha: id }); }
  if (p === '/git/commits' && method === 'POST') { if (body.parents[0] !== head.sha) return send({ message: 'stale' }, 409); const id = 'c' + (++commits); pending.set(id, pending.get(body.tree)); return send({ sha: id }); }
  if (p === '/git/refs/heads/main' && method === 'PATCH') { for (const e of pending.get(body.sha)) { if (e.sha === null) files.delete(e.path); else files.set(e.path, e.content); } head.sha = body.sha; return send({ ref: 'ok' }); }
  return send({ message: 'unrouted ' + p }, 404);
};
const server = createServer({ gh: githubClient({ token: 't', repo: 'o/r', fetchImpl: fakeFetch }) });
let id = 0; const rpc = async (method, params) => server.handle({ jsonrpc: '2.0', id: ++id, method, params });
const call = async (name, args = {}) => { const r = await rpc('tools/call', { name, arguments: args }); const t = r.result.content[0].text; return { err: !!r.result.isError, text: t, json: (() => { try { return JSON.parse(t); } catch { return null; } })() }; };
let pass = 0, fail = 0; const check = (n, c, d = '') => { c ? pass++ : fail++; console.log(`${c ? 'PASS' : 'FAIL'} | ${n}${d ? ' — ' + d : ''}`); };
const manifest = () => JSON.parse(files.get('content/manifest.json'));
const consistent = () => { const m = manifest(); return m.tabs.every((t) => !t.file || (files.has('content/' + t.file) && createHash('sha256').update(files.get('content/' + t.file)).digest('hex') === t.sha256 && (() => { const j = JSON.parse(files.get('content/' + t.file)); return (j.a ?? j.h).length === t.count; })())); };

// protocol
const init = await rpc('initialize', { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 't', version: '1' } });
check('initialize returns server info and tools capability', init.result.serverInfo.name === 'quran-search-content' && !!init.result.capabilities.tools);
check('notifications get no reply', (await server.handle({ jsonrpc: '2.0', method: 'notifications/initialized' })) === null);
const list = await rpc('tools/list'); const names = list.result.tools.map((t) => t.name);
check('tools/list has the content tools', ['content_status', 'search_entries', 'get_entry', 'update_entry', 'add_entries', 'delete_entries', 'add_tab', 'update_tab', 'reorder_tabs', 'remove_tab', 'set_apk_notice'].every((n) => names.includes(n)), names.length + ' tools');
check('unknown method is a JSON-RPC error', (await rpc('nope')).error.code === -32601);

// reading
const st = await call('content_status'); check('content_status: 4 tabs, version 1', st.json.version === 1 && st.json.tabs.length === 4, st.json.tabs.map((t) => `${t.id}:${t.count}`).join(' '));
const s1 = await call('search_entries', { tab: 'jami', query: 'إنما الأعمال بالنيات' }); check('search_entries finds the hadith «إنما الأعمال بالنيات»', s1.json.total >= 1, 'index ' + s1.json.results[0]?.index);
const s2 = await call('search_entries', { tab: 'alfiya', query: 'والليث سلطان' }); const lion = s2.json.results[0]; check('search_entries finds alfiya verse 521', s2.json.total === 1 && lion.number === 521, 'index ' + lion?.index);
check('get_entry returns the fields', (await call('get_entry', { tab: 'alfiya', index: lion.index })).json.shatr1.includes('والليث'));
check('bad tab → tool error', (await call('get_entry', { tab: 'zzz', index: 0 })).err);

// writing
let v = manifest().version;
const up = await call('update_entry', { tab: 'alfiya', index: lion.index, fields: { shatr2: 'يحذر من السلطان في عقابه (اختبار)' } });
check('update_entry commits and bumps the version', !up.err && manifest().version === v + 1 && up.json.sha, 'v' + manifest().version);
check('the edited text is in the data file', JSON.parse(files.get('content/alfiya.json')).h[lion.index][4].includes('(اختبار)'));
check('manifest hash and counts stay consistent', consistent());
check('update_entry rejects unknown fields', (await call('update_entry', { tab: 'alfiya', index: 0, fields: { bogus: 1 } })).err);
v = manifest().version;
const ad = await call('add_entries', { tab: 'amthal', entries: [{ ref: 'مثل', text: 'الصبر مفتاح الفرج', explanation: 'اختبار' }, { text: 'الجار قبل الدار' }] });
check('add_entries creates the file of an empty tab (amthal)', !ad.err && files.has('content/amthal.json') && manifest().tabs.find((t) => t.id === 'amthal').count === 2 && manifest().version === v + 1);
check('consistent after add_entries', consistent());
check('add_entries needs text', (await call('add_entries', { tab: 'amthal', entries: [{ ref: 'x' }] })).err);
const nt = await call('add_tab', { id: 'adhkar', label: 'الأذكار', kind: 'generic', entries: [{ ref: 'ذكر', text: 'سبحان الله وبحمده' }] });
check('add_tab adds a new tab with entries', !nt.err && manifest().tabs.some((t) => t.id === 'adhkar' && t.count === 1 && t.kind === 'generic'));
check('add_tab rejects a bad id / duplicate / bad kind', (await call('add_tab', { id: 'Bad Id', label: 'x' })).err && (await call('add_tab', { id: 'adhkar', label: 'x' })).err && (await call('add_tab', { id: 'abc', label: 'x', kind: 'quran' })).err);
check('search in the new tab works', (await call('search_entries', { tab: 'adhkar', query: 'وبحمده' })).json.total === 1);
check('update_tab changes the label', !(await call('update_tab', { id: 'adhkar', label: 'الأذكار والأدعية', hint: 'اكتب لفظاً' })).err && manifest().tabs.find((t) => t.id === 'adhkar').label === 'الأذكار والأدعية');
const order = manifest().tabs.map((t) => t.id).reverse(); check('reorder_tabs', !(await call('reorder_tabs', { ids: order })).err && manifest().tabs.map((t) => t.id).join() === order.join());
check('delete_entries removes entries', !(await call('delete_entries', { tab: 'amthal', indexes: [1] })).err && manifest().tabs.find((t) => t.id === 'amthal').count === 1);
check('remove_tab needs confirm and refuses core tabs', (await call('remove_tab', { id: 'adhkar', confirm: false })).err && (await call('remove_tab', { id: 'quran', confirm: true })).err);
check('remove_tab deletes the tab and its file', !(await call('remove_tab', { id: 'adhkar', confirm: true })).err && !files.has('content/adhkar.json') && !manifest().tabs.some((t) => t.id === 'adhkar'));
v = manifest().version; check('set_apk_notice does not bump the content version', !(await call('set_apk_notice', { versionCode: 9, url: 'https://example.com/a.apk', notes: 'x' })).err && manifest().apk.versionCode === 9 && manifest().version === v);
check('consistent at the end', consistent());
check('every change is one commit (no half-written state)', commits === 8, commits + ' commits');

// Worker: authentication and transport
const env = { MCP_SECRET: 'x'.repeat(32), GITHUB_TOKEN: 't', GITHUB_REPO: 'o/r' };
const post = (path, body, headers = {}) => worker.fetch(new Request('https://w.example' + path, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) }), env);
check('worker: wrong secret → 404', (await post('/mcp/wrong', { jsonrpc: '2.0', id: 1, method: 'ping' })).status === 404);
const pr = await post('/mcp/' + env.MCP_SECRET, { jsonrpc: '2.0', id: 1, method: 'ping' }); check('worker: correct path secret → JSON-RPC result', pr.status === 200 && (await pr.json()).result !== undefined);
check('worker: bearer token also accepted', (await post('/mcp', { jsonrpc: '2.0', id: 1, method: 'ping' }, { Authorization: 'Bearer ' + env.MCP_SECRET })).status === 200);
check('worker: notification → 202', (await post('/mcp/' + env.MCP_SECRET, { jsonrpc: '2.0', method: 'notifications/initialized' })).status === 202);
check('worker: GET → 405', (await worker.fetch(new Request('https://w.example/mcp/' + env.MCP_SECRET), env)).status === 405);
check('worker: short secret refused', (await worker.fetch(new Request('https://w.example/mcp/abc', { method: 'POST', body: '{}' }), { MCP_SECRET: 'abc' })).status === 500);
console.log(`\nSUMMARY: ${pass}/${pass + fail} passed`); process.exit(fail ? 1 : 0);
