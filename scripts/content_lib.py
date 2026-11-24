"""Shared helpers of the data pipeline: write a data file into content/ and register it in content/manifest.json
(version bump, SHA-256, entry count). content/ is what the web build, the Android app and the MCP server all use."""
import json, hashlib, os, datetime
C = 'content'
def _manifest():
    p = f'{C}/manifest.json'
    return json.load(open(p, encoding='utf8')) if os.path.exists(p) else {'schema': 1, 'version': 0, 'apk': {'versionCode': 0, 'url': '', 'notes': ''}, 'tabs': []}
def publish(tab_id, label, kind, obj, count, bump=True, extra=None):
    os.makedirs(C, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    name = f'{tab_id}.json'; open(f'{C}/{name}', 'wb').write(raw)
    m = _manifest(); t = next((x for x in m['tabs'] if x['id'] == tab_id), None)
    if not t: t = {'id': tab_id}; m['tabs'].append(t)
    t.update({'label': label, 'kind': kind, 'file': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'count': count})
    if extra: t.update(extra)
    if bump: m['version'] += 1
    m['updated'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(m, open(f'{C}/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); open(f'{C}/manifest.json', 'a').write('\n')
    print(f'{tab_id}: {count} entries, {len(raw)} bytes, manifest v{m["version"]}')

def publish_file(rel, obj, bump=True):
    """An extra file of the content (not a tab): content/<rel>, listed in the manifest's `files` with its SHA-256 (the app opens it on demand and updates it with the rest)."""
    return publish_bytes(rel, json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8'), bump)
def publish_bytes(rel, raw, bump=True):
    """the same for a file that is not JSON (a cover picture): its bytes are written as they are"""
    path = f'{C}/{rel}'
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'wb').write(raw)
    m = _manifest(); files = m.setdefault('files', []); e = next((x for x in files if x['file'] == rel), None)
    if not e: e = {'file': rel}; files.append(e)
    sha = hashlib.sha256(raw).hexdigest()
    changed = e.get('sha256') != sha; e.update({'sha256': sha, 'size': len(raw)})
    if bump and changed: m['version'] += 1
    m['updated'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(m, open(f'{C}/manifest.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); open(f'{C}/manifest.json', 'a').write('\n')
