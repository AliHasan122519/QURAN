// Local «GitHub» for the content tools: reads and writes the files of a git checkout and commits + pushes them.
// Lets a Claude session that has the repository checked out edit the content with the very same tools as the MCP server — no hosting needed.
import { readFile, writeFile, rm, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';

export function localClient({ root = '.', push = true, trailer = process.env.COMMIT_TRAILER ?? '' } = {}) {
  const git = (...a) => execFileSync('git', a, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  return {
    async getText(path) { try { return await readFile(join(root, path), 'utf8'); } catch { return null; } },
    async commit(files, message) {
      for (const f of files) {
        const p = join(root, f.path);
        if (f.content === null) await rm(p, { force: true }); else { await mkdir(dirname(p), { recursive: true }); await writeFile(p, f.content); }
      }
      git('add', '-A', 'content');
      git('commit', '-q', '-m', trailer ? `${message}\n\n${trailer}` : message);
      const sha = git('rev-parse', 'HEAD');
      if (push) { try { git('pull', '-q', '--rebase', 'origin', 'HEAD'); } catch { /* nothing to rebase onto */ } git('push', '-q', 'origin', 'HEAD'); }
      return { sha, url: push ? `pushed ${sha.slice(0, 7)}` : `committed ${sha.slice(0, 7)} (not pushed)` };
    },
  };
}
