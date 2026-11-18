"""A small line-OCR model (CNN + BiLSTM + CTC) trained on the typeface of al-Jami' al-Saghir from the hand-verified pages.
Lines are mirrored horizontally so that the reading direction (right to left) becomes the scanning direction, and the label is the logical text.
Modes:  train DATA_DIR MODEL.pt [epochs]   |   eval DATA_DIR MODEL.pt   |   predict MODEL.pt IMAGE.png...
DATA_DIR holds train/ and eval/ with NAME.png + NAME.gt.txt (see scripts/make_train_data.py)."""
import sys, glob, os, random, re, math, json, time
import numpy as np, torch, torch.nn as nn
from PIL import Image, ImageFilter
H = 44; SCALE_W = 0.42; MAXW = 900
torch.set_num_threads(4)
def label_of(gt): return open(gt, encoding='utf8').read().strip()
def load_img(path, aug=False):
    im = Image.open(path).convert('L'); w, h = im.size
    sc = H / h; nw = max(32, min(MAXW, int(w * sc * SCALE_W * (h / H) ** 0 * 2.0)))      # keep line aspect; compress width by ~2x
    if aug:
        sc2 = random.uniform(0.9, 1.1); nw = max(32, min(MAXW, int(nw * sc2)))
        im = im.rotate(random.uniform(-0.8, 0.8), fillcolor=255, resample=Image.BILINEAR)
        if random.random() < 0.3: im = im.filter(ImageFilter.MinFilter(3))
        elif random.random() < 0.3: im = im.filter(ImageFilter.MaxFilter(3))
    im = im.resize((nw, H), Image.LANCZOS)
    a = 1.0 - np.asarray(im, dtype=np.float32) / 255.0                                       # ink = 1
    if aug: a = np.clip(a + np.random.normal(0, 0.03, a.shape).astype(np.float32), 0, 1)
    return torch.from_numpy(a[:, ::-1].copy())[None]                                       # mirror: reading order -> left to right
class Net(nn.Module):
    def __init__(self, ncls):
        super().__init__()
        def blk(i, o, pool): return [nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(pool)]
        self.cnn = nn.Sequential(*blk(1, 32, (2, 2)), *blk(32, 64, (2, 2)), *blk(64, 128, (2, 1)), *blk(128, 128, (2, 1)))      # H: 44 -> 2 ; W: /4
        self.rnn = nn.LSTM(128 * 2, 192, num_layers=2, bidirectional=True, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(384, ncls + 1)
    def forward(self, x):
        f = self.cnn(x); b, c, h, w = f.shape
        f = f.permute(0, 3, 1, 2).reshape(b, w, c * h); o, _ = self.rnn(f); return self.fc(o).log_softmax(2)      # B,T,C
def batchify(items):
    ws = [x.shape[2] for x in items]; W = max(ws); W += (-W) % 4
    out = torch.zeros(len(items), 1, H, W)
    for i, x in enumerate(items): out[i, :, :, :x.shape[2]] = x
    return out, torch.tensor([math.ceil(w / 4) for w in ws])
def decode(logp, chars):
    best = logp.argmax(2).cpu().numpy(); res = []
    for seq in best:
        s, prev = [], 0
        for k in seq:
            if k != prev and k != 0: s.append(chars[k - 1])
            prev = k
        res.append(''.join(s))
    return res
def edit(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1]
def data(dirp): return [(f, label_of(f[:-4] + '.gt.txt')) for f in sorted(glob.glob(dirp + '/*.png')) if os.path.exists(f[:-4] + '.gt.txt')]
def evaluate(model, chars, items):
    model.eval(); err = tot = werr = wtot = 0
    with torch.no_grad():
        for i in range(0, len(items), 16):
            chunk = items[i:i + 16]; x, _ = batchify([load_img(f) for f, _ in chunk]); out = decode(model(x), chars)
            for (f, lab), hyp in zip(chunk, out):
                lab = re.sub(r'\s+', ' ', lab); err += edit(hyp, lab); tot += len(lab)
                lw, hw = lab.split(), hyp.split(); werr += edit(hw, lw); wtot += len(lw)
    return err / max(1, tot), werr / max(1, wtot)
if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'train':
        d, mp = sys.argv[2], sys.argv[3]; epochs = int(sys.argv[4]) if len(sys.argv) > 4 else 40
        tr, ev = data(d + '/train'), data(d + '/eval'); chars = sorted(set(''.join(re.sub(r'\s+', ' ', l) for _, l in tr + ev)))
        print('lines', len(tr), len(ev), 'chars', len(chars), flush=True)
        net = Net(len(chars)); opt = torch.optim.Adam(net.parameters(), 1.5e-3); sched = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-3, total_steps=epochs * math.ceil(len(tr) / 16))
        ctc = nn.CTCLoss(blank=0, zero_infinity=True); cid = {c: i + 1 for i, c in enumerate(chars)}; best = 9
        for ep in range(epochs):
            net.train(); random.shuffle(tr); t0 = time.time(); tl = 0
            for i in range(0, len(tr), 16):
                chunk = tr[i:i + 16]; x, il = batchify([load_img(f, True) for f, _ in chunk])
                labs = [torch.tensor([cid[c] for c in re.sub(r'\s+', ' ', l)]) for _, l in chunk]
                loss = ctc(net(x).permute(1, 0, 2), torch.cat(labs), il, torch.tensor([len(l) for l in labs]))
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 5); opt.step(); sched.step(); tl += loss.item()
            cer, wer = evaluate(net, chars, ev)
            print(f'epoch {ep + 1}/{epochs} loss {tl / math.ceil(len(tr) / 16):.3f} held-out CER {cer:.3f} WER {wer:.3f} ({time.time() - t0:.0f}s)', flush=True)
            if cer < best: best = cer; torch.save({'chars': chars, 'state': net.state_dict(), 'cer': cer, 'wer': wer}, mp)
        print('best held-out CER', best)
    elif mode == 'eval':
        ck = torch.load(sys.argv[3]); net = Net(len(ck['chars'])); net.load_state_dict(ck['state']); print(evaluate(net, ck['chars'], data(sys.argv[2] + '/eval')))
