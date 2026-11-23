// Tests scripts/content.mjs in a throw-away git checkout with a local bare «origin»: the change must be committed, valid and pushed.
import { execFileSync as ex } from 'node:child_process';
import { mkdtempSync, cpSync, readFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
const src = resolve('.'); const tmp = mkdtempSync(join(tmpdir(), 'cc-')); const origin = join(tmp, 'origin.git'); const work = join(tmp, 'work');
const sh = (cwd, ...a) => ex('git', a, { cwd, encoding: 'utf8' });
sh(tmp, 'init', '-q', '--bare', '-b', 'main', origin); mkdirSync(work); sh(work, 'init', '-q', '-b', 'main'); sh(work, 'config', 'user.email', 't@t'); sh(work, 'config', 'user.name', 't');
cpSync(join(src, 'content'), join(work, 'content'), { recursive: true }); cpSync(join(src, 'scripts', 'validate_content.mjs'), join(work, 'scripts', 'validate_content.mjs'), { recursive: true }); for (const f of ['build_ruaa.py', 'content_lib.py']) cpSync(join(src, 'scripts', f), join(work, 'scripts', f));
sh(work, 'add', '-A'); sh(work, 'commit', '-q', '-m', 'seed'); sh(work, 'remote', 'add', 'origin', origin); sh(work, 'push', '-q', 'origin', 'main');
const cli = (...a) => ex('node', [join(src, 'scripts', 'content.mjs'), ...a], { cwd: work, encoding: 'utf8', env: { ...process.env, COMMIT_TRAILER: 'Co-Authored-By: test' } });
let pass = 0, fail = 0; const check = (n, c, d = '') => { c ? pass++ : fail++; console.log(`${c ? 'PASS' : 'FAIL'} | ${n}${d ? ' — ' + d : ''}`); };
check('list shows the tools', cli('list').includes('update_entry'));
check('content_status works', JSON.parse(cli('content_status', '{}').split('\ncontent OK')[0]).tabs.length === 13);
const before = JSON.parse(readFileSync(join(work, 'content', 'manifest.json'), 'utf8')); const am0 = before.tabs.find((t) => t.id === 'amthal').count, v0 = before.version;
const out = cli('add_entries', JSON.stringify({ tab: 'amthal', entries: [{ ref: 'مثل', text: 'الصبر مفتاح الفرج' }] }));
check('add_entries commits and validation passes', out.includes(`content OK: version ${v0 + 1}`));
const log = sh(work, 'log', '--format=%s%n%b', '-1'); check('commit message has the trailer', log.includes('content: add 1 entries to amthal') && log.includes('Co-Authored-By: test'));
check('the commit reached origin', sh(origin, 'log', '-1', '--format=%s', 'main').trim() === 'content: add 1 entries to amthal');
const m = JSON.parse(readFileSync(join(work, 'content', 'manifest.json'), 'utf8')); check('manifest version bumped, amthal has one more entry', m.version === v0 + 1 && m.tabs.find((t) => t.id === 'amthal').count === am0 + 1);
let bad = false; try { cli('update_entry', '{"tab":"zzz","index":0,"fields":{"text":"x"}}'); } catch { bad = true; } check('a bad request fails without committing', bad && sh(work, 'log', '--oneline').trim().split('\n').length === 2);
// a new reference added to the books: the dreams it interprets reach «رؤى وتعبيرها» in a second commit
const r0 = JSON.parse(readFileSync(join(work, 'content', 'manifest.json'), 'utf8')).tabs.find((t) => t.id === 'ruaa').count;
const out2 = cli('add_entries', JSON.stringify({ tab: 'books', entries: [{ ref: 'مرجع تجريبي', text: 'جاء رجل إلى ابن سيرين فقال: رأيت كأني أمسك طائرا أبيض في يدي فقال: تنال خيرا من جهة امرأة صالحة فكان كذلك', explanation: '', source: 'كتاب تجريبي' }] }));
const r1 = JSON.parse(readFileSync(join(work, 'content', 'manifest.json'), 'utf8')).tabs.find((t) => t.id === 'ruaa').count;
check('a dream interpreted in a new book reaches «رؤى وتعبيرها»', r1 === r0 + 1 && out2.includes('refreshed and pushed') && sh(origin, 'log', '-1', '--format=%s', 'main').includes('رؤى وتعبيرها'), `${r0} -> ${r1}`);
console.log(`\nSUMMARY: ${pass}/${pass + fail} passed`); process.exit(fail ? 1 : 0);
