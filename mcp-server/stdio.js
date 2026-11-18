#!/usr/bin/env node
// Local MCP server over stdio (for Claude Desktop / Claude Code on your own computer). Same tools as the Worker.
// Env: GITHUB_TOKEN, GITHUB_REPO ("owner/name"), GITHUB_BRANCH (default main).
import { createInterface } from 'node:readline';
import { createServer, githubClient } from './core.js';
const { GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH } = process.env;
if (!GITHUB_TOKEN || !GITHUB_REPO) { console.error('Set GITHUB_TOKEN and GITHUB_REPO (owner/name)'); process.exit(1); }
const server = createServer({ gh: githubClient({ token: GITHUB_TOKEN, repo: GITHUB_REPO, branch: GITHUB_BRANCH || 'main' }) });
const rl = createInterface({ input: process.stdin });
rl.on('line', async (line) => {
  if (!line.trim()) return;
  let msg; try { msg = JSON.parse(line); } catch { process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } }) + '\n'); return; }
  const out = await server.handle(msg); if (out !== null) process.stdout.write(JSON.stringify(out) + '\n');
});
