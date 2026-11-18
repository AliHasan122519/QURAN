// Netlify Function entry: the same MCP server as worker.js, served at /mcp/<MCP_SECRET> on a Netlify site.
// Site settings (Netlify → Site configuration → Environment variables): GITHUB_TOKEN, MCP_SECRET, GITHUB_REPO, GITHUB_BRANCH.
import worker from '../worker.js';

export default async (req) => worker.fetch(req, {
  MCP_SECRET: process.env.MCP_SECRET,
  GITHUB_TOKEN: process.env.GITHUB_TOKEN,
  GITHUB_REPO: process.env.GITHUB_REPO,
  GITHUB_BRANCH: process.env.GITHUB_BRANCH,
});

export const config = { path: ['/mcp', '/mcp/*'] };
