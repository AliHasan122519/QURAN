// Command-line access to the content tools (same tools as the MCP server) for a Claude session that has this repository checked out.
//   node scripts/content.mjs list                          → tools and what they do
//   node scripts/content.mjs <tool> '<json arguments>'     → run one, e.g.  content_status '{}'   or   update_entry '{"tab":"jami","index":0,"fields":{"text":"…"}}'
// Each change is one commit (data file + manifest.json: version +1, SHA-256, count) that is pushed to GitHub; installed apps then update themselves.
// Options: --no-push  (commit only).
import { createServer } from '../mcp-server/core.js';
import { localClient } from '../mcp-server/local.js';
import { execFileSync } from 'node:child_process';

const args = process.argv.slice(2); const noPush = args.includes('--no-push'); const rest = args.filter((a) => a !== '--no-push');
const [tool, json] = rest;
const server = createServer({ gh: localClient({ root: process.cwd(), push: !noPush }) });
if (!tool || tool === 'list') {
  const r = await server.handle({ jsonrpc: '2.0', id: 1, method: 'tools/list' });
  for (const t of r.result.tools) console.log(`${t.name}\n   ${t.description}\n   args: ${JSON.stringify(Object.keys(t.inputSchema.properties ?? {}))} required: ${JSON.stringify(t.inputSchema.required ?? [])}`);
  process.exit(0);
}
let params; try { params = json ? JSON.parse(json) : {}; } catch { console.error('the arguments must be valid JSON'); process.exit(2); }
const r = await server.handle({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: tool, arguments: params } });
if (r.error) { console.error(r.error.message); process.exit(1); }
console.log(r.result.content[0].text);
if (r.result.isError) process.exit(1);
try { console.log(execFileSync('node', ['scripts/validate_content.mjs'], { encoding: 'utf8' }).trim()); } catch (e) { console.error(e.stdout || e.message); process.exit(1); }
