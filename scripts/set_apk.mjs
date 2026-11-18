// Records the newest APK in content/manifest.json (apk.versionCode / apk.url). Installed apps older than that show a «new version» notice.
// usage: node scripts/set_apk.mjs <versionCode> <url> [notes]
import { readFileSync, writeFileSync } from 'node:fs';
const [vc, url, notes = ''] = process.argv.slice(2);
if (!vc || !url) { console.error('usage: set_apk.mjs <versionCode> <url> [notes]'); process.exit(1); }
const m = JSON.parse(readFileSync('content/manifest.json', 'utf8'));
m.apk = { versionCode: Number(vc), url, notes };
writeFileSync('content/manifest.json', JSON.stringify(m, null, 1) + '\n');
console.log('manifest.apk =', m.apk);
