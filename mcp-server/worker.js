// Cloudflare Worker entry: a remote MCP server (Streamable HTTP, JSON responses) that edits the app's content on GitHub.
// Secrets (wrangler secret put …): GITHUB_TOKEN (fine-grained, Contents: read+write on the repo), MCP_SECRET (a long random string).
// Vars (wrangler.toml): GITHUB_REPO = "owner/name", GITHUB_BRANCH = "main".
// Add to Claude as a custom connector with the URL  https://<worker>.workers.dev/mcp/<MCP_SECRET>
import { createServer, githubClient } from './core.js';

const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, DELETE', 'Access-Control-Allow-Headers': '*', 'Access-Control-Expose-Headers': 'Mcp-Session-Id' };
const json = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...cors } });
const same = (a, b) => { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; };

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(req.url); const secret = env.MCP_SECRET ?? '';
    if (secret.length < 24) return json({ error: 'MCP_SECRET is not set (use at least 24 random characters)' }, 500);
    const m = url.pathname.match(/^\/mcp(?:\/(.+))?$/);
    const given = m?.[1] ?? (req.headers.get('authorization') ?? '').replace(/^Bearer\s+/i, '');
    if (!m || !same(given, secret)) return json({ error: 'not found' }, 404);
    if (req.method === 'GET' || req.method === 'DELETE') return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST', ...cors } });
    if (req.method !== 'POST') return new Response('Method Not Allowed', { status: 405, headers: cors });
    let body; try { body = await req.json(); } catch { return json({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } }, 400); }
    const server = createServer({ gh: githubClient({ token: env.GITHUB_TOKEN, repo: env.GITHUB_REPO, branch: env.GITHUB_BRANCH || 'main' }) });
    const out = await server.handle(body);
    return out === null ? new Response(null, { status: 202, headers: cors }) : json(out);
  },
};
