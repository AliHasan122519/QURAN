// MCP server for the content of «الباحث القرآني» (Qur'an / hadith / poem / any added reference).
// It edits the files in the repository's content/ folder through the GitHub API; every installed app downloads the new content by itself.
// Pure JavaScript with no dependencies (fetch + crypto only), so the same code runs as a Cloudflare Worker (worker.js) and as a local stdio server (stdio.js).

export const SERVER_INFO = { name: 'quran-search-content', version: '1.0.0' };
const INSTRUCTIONS = [
  'Edits the content of the Quran-search app: tabs (quran, jami = hadith, alfiya = poem, amthal, and any tab you add) stored in content/ of the GitHub repository.',
  'Every change is one commit that updates the data file and content/manifest.json (version +1, SHA-256, entry count); installed apps pick it up on their next launch.',
  'Entry numbers are 0-based positions in the tab (see search_entries). Use add_tab / add_entries to add a new reference; use update_entry to correct a text.',
  'Never invent texts: add only what the user supplied or what a source the user named says.',
].join('\n');

// How each tab kind stores a row (arrays, to keep the files small) and the field names the tools use.
const KINDS = {
  quran: { list: 'a', fields: { surah: 0, ayah: 1, text: 2 }, make: (o) => [o.surah ?? 0, o.ayah ?? 0, o.text ?? ''] },
  hadith: { list: 'h', fields: { page: 0, letter: 1, text: 2, takhrij: 3, symbols: 4, grade: 5, tier: 6, mahla: 7, number: 8, printed: 9 }, make: (o) => [o.page ?? 0, o.letter ?? '', o.text ?? '', o.takhrij ?? '', o.symbols ?? [], o.grade ?? '', o.tier ?? 'v', o.mahla ?? 0, o.number ?? 0] },
  poem: { list: 'h', fields: { number: 0, page: 1, chapter: 2, shatr1: 3, shatr2: 4 }, make: (o) => [o.number ?? 0, o.page ?? 0, o.chapter ?? '', o.shatr1 ?? '', o.shatr2 ?? ''] },
  generic: { list: 'h', fields: { ref: 0, text: 1, explanation: 2, source: 3 }, make: (o) => (o.source ? [o.ref ?? '', o.text ?? '', o.explanation ?? '', o.source] : [o.ref ?? '', o.text ?? '', o.explanation ?? '']) },
};
const NEW_TAB_KINDS = ['generic', 'poem'];
const ID_RE = /^[a-z][a-z0-9_-]{1,30}$/;
const DIAC = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
export const norm = (s) => String(s).replace(DIAC, '').replace(/[إأآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه').replace(/\s+/g, ' ').trim();
const sha256 = async (text) => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map((b) => b.toString(16).padStart(2, '0')).join('');
const isoNow = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');

const toObj = (kind, row, index) => { const o = { index }; for (const [k, i] of Object.entries(KINDS[kind].fields)) o[k] = row[i]; return o; };
const textOf = (kind, row) => Object.entries(KINDS[kind].fields).filter(([, i]) => typeof row[i] === 'string').map(([, i]) => row[i]).join(' ');
class ToolError extends Error {}
const need = (cond, msg) => { if (!cond) throw new ToolError(msg); };

// ---------------------------------------------------------------------------------------------------------------------------------------
// GitHub access: read a file, and commit several files (or deletions) as ONE commit through the Git Data API.
export function githubClient({ token, repo, branch = 'main', fetchImpl = fetch }) {
  const api = `https://api.github.com/repos/${repo}`;
  const call = async (path, init = {}, accept = 'application/vnd.github+json') => {
    const res = await fetchImpl(api + path, { ...init, headers: { Authorization: `Bearer ${token}`, Accept: accept, 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'quran-search-mcp', ...(init.body ? { 'Content-Type': 'application/json' } : {}) } });
    return res;
  };
  const json = async (path, init) => { const r = await call(path, init); if (!r.ok) throw new ToolError(`GitHub ${r.status}: ${(await r.text()).slice(0, 300)}`); return r.json(); };
  return {
    async getText(path) {
      const r = await call(`/contents/${path}?ref=${encodeURIComponent(branch)}`, {}, 'application/vnd.github.raw+json');
      if (r.status === 404) return null;
      if (!r.ok) throw new ToolError(`GitHub ${r.status} reading ${path}`);
      return r.text();
    },
    async commit(files, message) {
      const ref = await json(`/git/ref/heads/${branch}`); const head = ref.object.sha;
      const base = (await json(`/git/commits/${head}`)).tree.sha;
      const tree = await json('/git/trees', { method: 'POST', body: JSON.stringify({ base_tree: base, tree: files.map((f) => (f.content === null ? { path: f.path, mode: '100644', type: 'blob', sha: null } : { path: f.path, mode: '100644', type: 'blob', content: f.content })) }) });
      const c = await json('/git/commits', { method: 'POST', body: JSON.stringify({ message, tree: tree.sha, parents: [head] }) });
      await json(`/git/refs/heads/${branch}`, { method: 'PATCH', body: JSON.stringify({ sha: c.sha, force: false }) });
      return { sha: c.sha, url: `https://github.com/${repo}/commit/${c.sha}` };
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------------------------------
export function createServer({ gh }) {
  const readManifest = async () => { const t = await gh.getText('content/manifest.json'); need(t, 'content/manifest.json was not found in the repository'); return JSON.parse(t); };
  const tabOf = (m, id) => { const t = m.tabs.find((x) => x.id === id); need(t, `unknown tab «${id}». Tabs: ${m.tabs.map((x) => x.id).join(', ')}`); return t; };
  const readTab = async (t) => {
    if (!t.file) return { [KINDS[t.kind].list]: [] };
    const txt = await gh.getText('content/' + t.file); need(txt, `data file content/${t.file} is missing`); return JSON.parse(txt);
  };
  // Re-serialise the changed tabs, update their hash and count, bump the version and commit everything at once.
  const save = async (m, changes, message, { bump = true } = {}) => {
    const files = [];
    for (const { tab, data, remove } of changes) {
      if (remove) { files.push({ path: 'content/' + tab.file, content: null }); continue; }
      const kind = KINDS[tab.kind]; const text = JSON.stringify(data);
      tab.file = tab.file || `${tab.id}.json`; tab.sha256 = await sha256(text); tab.count = data[kind.list].length;
      files.push({ path: 'content/' + tab.file, content: text });
    }
    if (bump) m.version += 1;
    m.updated = isoNow();
    files.push({ path: 'content/manifest.json', content: JSON.stringify(m, null, 1) + '\n' });
    const c = await gh.commit(files, message);
    return { ...c, version: m.version };
  };
  const rowsOf = (t, data) => data[KINDS[t.kind].list];
  const fieldCheck = (kind, obj) => { for (const k of Object.keys(obj)) need(k in KINDS[kind].fields, `unknown field «${k}» for kind ${kind}. Fields: ${Object.keys(KINDS[kind].fields).join(', ')}`); };
  const ok = (o) => (typeof o === 'string' ? o : JSON.stringify(o, null, 1));

  const TOOLS = [
    { name: 'content_status', description: 'Shows the content version, the tabs (id, label, kind, entry count) and the newest APK notice.', inputSchema: { type: 'object', properties: {} },
      run: async () => { const m = await readManifest(); return { version: m.version, updated: m.updated, apk: m.apk, tabs: m.tabs.map(({ id, label, kind, count, file }) => ({ id, label, kind, count, file })) }; } },
    { name: 'search_entries', description: 'Finds entries of a tab whose text contains the query (diacritics and alef/ya/ta-marbuta variants are ignored). Returns the entry index, which the other tools use.',
      inputSchema: { type: 'object', properties: { tab: { type: 'string' }, query: { type: 'string' }, limit: { type: 'integer', default: 20 } }, required: ['tab', 'query'] },
      run: async ({ tab, query, limit = 20 }) => { const m = await readManifest(); const t = tabOf(m, tab); const d = await readTab(t); const q = norm(query); need(q, 'empty query');
        const out = []; let total = 0; rowsOf(t, d).forEach((row, i) => { if (norm(textOf(t.kind, row)).includes(q)) { total++; if (out.length < Math.min(limit, 100)) out.push({ ...toObj(t.kind, row, i), text: undefined, preview: String(textOf(t.kind, row)).slice(0, 200) }); } });
        return { tab, total, shown: out.length, results: out }; } },
    { name: 'get_entry', description: 'Returns one entry with all its fields.', inputSchema: { type: 'object', properties: { tab: { type: 'string' }, index: { type: 'integer' } }, required: ['tab', 'index'] },
      run: async ({ tab, index }) => { const m = await readManifest(); const t = tabOf(m, tab); const rows = rowsOf(t, await readTab(t)); need(rows[index], `no entry ${index} in ${tab} (0..${rows.length - 1})`); return toObj(t.kind, rows[index], index); } },
    { name: 'update_entry', description: 'Corrects fields of one entry (e.g. {"text": "..."}). Committed to GitHub; installed apps update automatically.',
      inputSchema: { type: 'object', properties: { tab: { type: 'string' }, index: { type: 'integer' }, fields: { type: 'object' } }, required: ['tab', 'index', 'fields'] },
      run: async ({ tab, index, fields }) => { const m = await readManifest(); const t = tabOf(m, tab); const data = await readTab(t); const rows = rowsOf(t, data); need(rows[index], `no entry ${index} in ${tab}`);
        fieldCheck(t.kind, fields); need(Object.keys(fields).length, 'no fields given'); const before = toObj(t.kind, rows[index], index);
        for (const [k, v] of Object.entries(fields)) rows[index][KINDS[t.kind].fields[k]] = v;
        const c = await save(m, [{ tab: t, data }], `content: update ${tab} #${index}`); return { updated: toObj(t.kind, rows[index], index), before, ...c }; } },
    { name: 'add_entries', description: 'Appends entries to a tab (up to 500 per call). Each entry is an object with the tab kind\'s fields: generic {ref,text,explanation,source?} (source = the name of the book, shown under the result in the books tab); poem {number,page,chapter,shatr1,shatr2}; hadith {text,takhrij,number,page,grade,...}; quran {surah,ayah,text}. Creates the data file if the tab was empty.',
      inputSchema: { type: 'object', properties: { tab: { type: 'string' }, entries: { type: 'array', items: { type: 'object' } } }, required: ['tab', 'entries'] },
      run: async ({ tab, entries }) => { need(Array.isArray(entries) && entries.length && entries.length <= 500, 'entries must be 1..500 objects'); const m = await readManifest(); const t = tabOf(m, tab); const data = await readTab(t); const rows = rowsOf(t, data);
        const K = KINDS[t.kind]; const first = rows.length;
        for (const e of entries) { fieldCheck(t.kind, e); need(typeof e.text === 'string' ? e.text.trim() : (t.kind === 'poem' ? e.shatr1 && e.shatr2 : false), 'every entry needs text (poem: shatr1 and shatr2)'); rows.push(K.make(e)); }
        const c = await save(m, [{ tab: t, data }], `content: add ${entries.length} entries to ${tab}`); return { added: entries.length, firstIndex: first, total: rows.length, ...c }; } },
    { name: 'delete_entries', description: 'Deletes entries by index (indexes of the tab are renumbered afterwards).', inputSchema: { type: 'object', properties: { tab: { type: 'string' }, indexes: { type: 'array', items: { type: 'integer' } } }, required: ['tab', 'indexes'] },
      run: async ({ tab, indexes }) => { const m = await readManifest(); const t = tabOf(m, tab); const data = await readTab(t); const rows = rowsOf(t, data);
        const set = [...new Set(indexes)].sort((a, b) => b - a); need(set.length && set.every((i) => rows[i]), 'some indexes do not exist'); for (const i of set) rows.splice(i, 1);
        const c = await save(m, [{ tab: t, data }], `content: delete ${set.length} entries from ${tab}`); return { deleted: set.length, total: rows.length, ...c }; } },
    { name: 'add_tab', description: 'Adds a new reference as a new tab of the app (kind generic = entries with ref/text/explanation; poem = verses with two hemistichs). id: latin letters/digits/-/_.',
      inputSchema: { type: 'object', properties: { id: { type: 'string' }, label: { type: 'string' }, kind: { type: 'string', enum: NEW_TAB_KINDS, default: 'generic' }, placeholder: { type: 'string' }, hint: { type: 'string' }, entries: { type: 'array', items: { type: 'object' } } }, required: ['id', 'label'] },
      run: async ({ id, label, kind = 'generic', placeholder, hint, entries = [] }) => { need(ID_RE.test(id), 'id must match [a-z][a-z0-9_-]{1,30}'); need(NEW_TAB_KINDS.includes(kind), `kind must be one of ${NEW_TAB_KINDS.join(', ')}`); need(String(label).trim(), 'label is required');
        const m = await readManifest(); need(!m.tabs.some((x) => x.id === id), `tab «${id}» already exists`); need(entries.length <= 500, 'at most 500 entries per call (add more with add_entries)');
        const K = KINDS[kind]; const t = { id, label: String(label).trim(), kind, file: `${id}.json`, sha256: null, count: 0 }; if (placeholder) t.placeholder = placeholder; if (hint) t.hint = hint;
        const rows = entries.map((e) => { fieldCheck(kind, e); return K.make(e); }); const data = { [K.list]: rows }; m.tabs.push(t);
        const c = await save(m, [{ tab: t, data }], `content: add tab ${id}`); return { tab: id, entries: rows.length, ...c }; } },
    { name: 'update_tab', description: 'Changes a tab\'s label, search placeholder or hint text.', inputSchema: { type: 'object', properties: { id: { type: 'string' }, label: { type: 'string' }, placeholder: { type: 'string' }, hint: { type: 'string' } }, required: ['id'] },
      run: async ({ id, label, placeholder, hint }) => { const m = await readManifest(); const t = tabOf(m, id); if (label) t.label = label; if (placeholder !== undefined) t.placeholder = placeholder; if (hint !== undefined) t.hint = hint;
        const c = await save(m, [], `content: update tab ${id}`); return { tab: id, ...c }; } },
    { name: 'reorder_tabs', description: 'Sets the order of the tabs (all tab ids, in the new order).', inputSchema: { type: 'object', properties: { ids: { type: 'array', items: { type: 'string' } } }, required: ['ids'] },
      run: async ({ ids }) => { const m = await readManifest(); need(ids.length === m.tabs.length && m.tabs.every((t) => ids.includes(t.id)), `give all ${m.tabs.length} tab ids`); m.tabs = ids.map((i) => tabOf(m, i)); const c = await save(m, [], 'content: reorder tabs'); return { order: ids, ...c }; } },
    { name: 'remove_tab', description: 'Removes a tab and its data file. Requires confirm=true.', inputSchema: { type: 'object', properties: { id: { type: 'string' }, confirm: { type: 'boolean' } }, required: ['id', 'confirm'] },
      run: async ({ id, confirm }) => { need(confirm === true, 'pass confirm=true to remove a tab'); const m = await readManifest(); const t = tabOf(m, id); need(!['quran', 'jami'].includes(id), 'the core tabs quran and jami cannot be removed'); m.tabs = m.tabs.filter((x) => x.id !== id);
        const c = await save(m, t.file ? [{ tab: t, remove: true }] : [], `content: remove tab ${id}`); return { removed: id, ...c }; } },
    { name: 'set_apk_notice', description: 'Announces a newer APK: apps older than versionCode show a download notice with this url.', inputSchema: { type: 'object', properties: { versionCode: { type: 'integer' }, url: { type: 'string' }, notes: { type: 'string' } }, required: ['versionCode', 'url'] },
      run: async ({ versionCode, url, notes = '' }) => { need(/^https:\/\//.test(url), 'url must be https'); const m = await readManifest(); m.apk = { versionCode, url, notes }; const c = await save(m, [], 'content: announce APK', { bump: false }); return { apk: m.apk, ...c }; } },
  ];
  const byName = new Map(TOOLS.map((t) => [t.name, t]));

  async function handleOne(msg) {
    const { id, method, params } = msg; const isNote = id === undefined || id === null;
    const reply = (result) => (isNote ? null : { jsonrpc: '2.0', id, result });
    const fail = (code, message) => (isNote ? null : { jsonrpc: '2.0', id, error: { code, message } });
    try {
      switch (method) {
        case 'initialize': return reply({ protocolVersion: params?.protocolVersion ?? '2025-03-26', capabilities: { tools: { listChanged: false } }, serverInfo: SERVER_INFO, instructions: INSTRUCTIONS });
        case 'notifications/initialized': case 'notifications/cancelled': return null;
        case 'ping': return reply({});
        case 'tools/list': return reply({ tools: TOOLS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })) });
        case 'tools/call': {
          const tool = byName.get(params?.name); if (!tool) return fail(-32602, `unknown tool ${params?.name}`);
          try { const out = await tool.run(params.arguments ?? {}); return reply({ content: [{ type: 'text', text: ok(out) }] }); }
          catch (e) { return reply({ isError: true, content: [{ type: 'text', text: e instanceof ToolError ? e.message : `error: ${e?.message ?? e}` }] }); }
        }
        default: return fail(-32601, `method not found: ${method}`);
      }
    } catch (e) { return fail(-32603, String(e?.message ?? e)); }
  }
  return {
    tools: TOOLS,
    /** one JSON-RPC message or a batch → the response (or null when there is nothing to send back) */
    async handle(body) {
      if (Array.isArray(body)) { const r = (await Promise.all(body.map(handleOne))).filter(Boolean); return r.length ? r : null; }
      if (!body || typeof body !== 'object' || body.jsonrpc !== '2.0') return { jsonrpc: '2.0', id: null, error: { code: -32600, message: 'invalid request' } };
      return handleOne(body);
    },
  };
}
