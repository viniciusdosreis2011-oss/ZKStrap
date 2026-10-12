from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import random
import wave

import numpy as np

SR = 22050
TARGET_SECONDS = 126.0
VERSION_SALT = "ZKStrap-v3.20.12-original-audio"


def hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def env_adsr(n: int, attack=.05, release=.2) -> np.ndarray:
    e = np.ones(n, dtype=np.float32)
    a = min(n, max(1, int(n * attack)))
    r = min(n, max(1, int(n * release)))
    e[:a] = np.linspace(0.0, 1.0, a, endpoint=False, dtype=np.float32)
    e[-r:] *= np.linspace(1.0, 0.0, r, endpoint=True, dtype=np.float32)
    return e


def oscillator(kind: int, freq: float, t: np.ndarray, phase=0.0) -> np.ndarray:
    x = 2.0 * np.pi * (freq * t + phase)
    if kind % 4 == 0:
        return np.sin(x)
    if kind % 4 == 1:
        return (2.0 / np.pi) * np.arcsin(np.sin(x))
    if kind % 4 == 2:
        return .68*np.sin(x) + .22*np.sin(2*x) + .10*np.sin(3*x)
    return .74*np.sin(x) + .18*np.sin(1.5*x + .3) + .08*np.sin(3*x + .7)


def add_tone(buf, start, length, freq, amp, kind, phase=0.0, attack=.05, release=.20):
    if length <= 2 or start >= len(buf):
        return
    end = min(len(buf), start + length)
    n = end - start
    t = np.arange(n, dtype=np.float32) / SR
    sig = oscillator(kind, freq, t, phase).astype(np.float32)
    sig *= env_adsr(n, attack, release)
    buf[start:end] += sig * float(amp)


def add_kick(buf, start, amp, flavor):
    n = min(int(SR * .28), len(buf) - start)
    if n <= 2:
        return
    t = np.arange(n, dtype=np.float32) / SR
    f0 = 74.0 + flavor * 15.0
    phase = 2*np.pi*(f0*t - 30.0*t*t)
    env = np.exp(-t * (14.0 + flavor*2.0))
    click = np.sin(2*np.pi*980.0*t) * np.exp(-t*70.0)
    buf[start:start+n] += (np.sin(phase)*env + .07*click) * amp


def add_snare(buf, start, amp, rng):
    n = min(int(SR * .20), len(buf) - start)
    if n <= 2:
        return
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    body = np.sin(2*np.pi*188.0*t)
    buf[start:start+n] += (noise*.52 + body*.28) * np.exp(-t*22.0) * amp


def add_hat(buf, start, amp, rng, open_hat=False):
    n = min(int(SR * (.15 if open_hat else .065)), len(buf) - start)
    if n <= 2:
        return
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    hp = np.empty_like(noise)
    hp[0] = noise[0]
    hp[1:] = noise[1:] - noise[:-1]
    buf[start:start+n] += hp * np.exp(-t*(22.0 if open_hat else 58.0)) * amp


def choose_scale(seed):
    scales = [
        [0,2,3,5,7,9,10],
        [0,2,4,7,9],
        [0,3,5,7,10],
        [0,2,4,6,7,9,11],
        [0,2,3,5,7,8,10],
    ]
    return scales[seed % len(scales)]


def degree_note(root, scale, degree):
    octv, idx = divmod(degree, len(scale))
    return root + scale[idx] + octv*12


def chord(root, scale, degree):
    return [degree_note(root, scale, degree+k) for k in (0,2,4)]


def compose(pack_name: str, out_path: Path):
    digest = hashlib.sha256((VERSION_SALT + '|' + pack_name).encode('utf-8')).digest()
    seed = int.from_bytes(digest[:8], 'little')
    py = random.Random(seed)
    rg = np.random.default_rng(seed)

    bpm = py.choice([80,84,88,92,96,100,104])
    beat = 60.0 / bpm
    bar_seconds = beat * 4.0
    bars = int(math.ceil(TARGET_SECONDS / bar_seconds))
    total_seconds = bars * bar_seconds
    total = int(total_seconds * SR)
    buf = np.zeros(total, dtype=np.float32)

    root = py.choice([38,40,41,43,45,47])
    scale = choose_scale(seed)
    synth = seed % 4
    progressions = [
        [0,3,4,2,5,1,4,3],
        [0,4,2,5,3,1,6,4],
        [0,2,5,3,1,4,6,2],
        [0,5,3,4,1,6,2,5],
    ]
    prog = progressions[(seed >> 5) % len(progressions)]
    spb = SR * beat
    drum_fps = []
    last_fp = None

    for bar in range(bars):
        s0 = int(round(bar * spb * 4.0))
        s1 = min(total, int(round((bar+1) * spb * 4.0)))
        section = bar // 8
        local = bar % 8
        deg = prog[(bar + section) % len(prog)] % len(scale)

        # Arrangement changes every 8 bars: pad voicing, density and octave all move.
        ch = chord(root + (12 if section % 5 == 4 else 0), scale, deg)
        inv = (bar + section + seed) % 3
        ch = ch[inv:] + [x+12 for x in ch[:inv]]
        pad_amp = .060 + .010*((section+local) % 4)
        if section % 6 == 0 and local < 2:
            pad_amp *= .60
        for j,m in enumerate(ch):
            add_tone(buf, s0, max(1,s1-s0), hz(m+12), pad_amp/(1+j*.12), synth+j, phase=.08*(bar+j), attack=.15, release=.22)

        # Bass groove changes every bar.
        bass_patterns = [
            [0.0,1.5,2.75], [0.0,1.0,2.5,3.5], [0.0,1.75,3.0],
            [0.0,.75,2.0,3.25], [0.0,2.0,3.0], [0.0,1.25,2.25,3.75]
        ]
        bp = bass_patterns[(bar + section + (seed % 7)) % len(bass_patterns)]
        bass_midi = degree_note(root-12, scale, deg)
        for i,b in enumerate(bp):
            st = s0 + int(b*spb)
            ln = int(spb * (.62 if i%2 else .82))
            add_tone(buf, st, ln, hz(bass_midi + (12 if (bar+i)%13==0 else 0)), .11, synth+2, attack=.01, release=.28)

        # Per-bar drum pattern. Reject exact consecutive repeats.
        for _ in range(24):
            kick = tuple(i for i in range(16) if i in (0,8) or py.random() < (.10 + .025*(section%4)))
            snare = tuple(i for i in range(16) if i in (4,12) or (i in (10,14) and py.random() < .24))
            hat = tuple(i for i in range(16) if py.random() < (.44 + .05*((bar+section)%4)))
            fp = (kick,snare,hat)
            if fp != last_fp:
                break
        last_fp = fp
        drum_fps.append(repr(fp))
        step = spb/4.0
        dg = .080 + .010*((section+1)%3)
        if section % 6 == 0 and local == 0:
            dg *= .32
        for i in kick: add_kick(buf, s0+int(i*step), dg*1.35, (seed%17)/17.0)
        for i in snare: add_snare(buf, s0+int(i*step), dg*.55, rg)
        for i in hat: add_hat(buf, s0+int(i*step), dg*.12, rg, open_hat=((i+bar)%13==0))

        # Melody phrases mutate every two bars and disappear in sparse sections.
        if section % 4 != 0 or local >= 4:
            mr = random.Random((seed ^ ((bar//2)+1)*0x9E3779B1) & 0xFFFFFFFF)
            for slot in range(8):
                if mr.random() < (.34 + .07*(section%3)):
                    md = (deg + mr.choice([-2,-1,0,1,2,3])) % len(scale)
                    midi = root + scale[md] + 24 + 12*((slot+section)%2)
                    st = s0 + int(slot*(spb/2.0))
                    ln = int(spb * mr.choice([.28,.40,.56,.70]))
                    add_tone(buf, st, ln, hz(midi), .040+.007*(section%4), synth+1, phase=.15*slot, attack=.025, release=.30)

        # Section transition swell.
        if local == 7 and bar+1 < bars:
            n = min(int(SR*.9), s1-s0)
            st = s1-n
            t = np.arange(n,dtype=np.float32)/SR
            env = np.linspace(0,1,n,dtype=np.float32)**2
            noise = rg.standard_normal(n).astype(np.float32)
            smooth = np.cumsum(noise)/18.0
            smooth = np.tanh(smooth)*env*.010
            tone = np.sin(2*np.pi*hz(root+24+scale[(deg+2)%len(scale)])*t)*env*.016
            buf[st:s1] += smooth + tone

    t = np.arange(total,dtype=np.float32)/SR
    buf *= (0.94 + 0.06*np.sin(2*np.pi*(.006+(seed%7)*.0006)*t + (seed%19))).astype(np.float32)
    buf = np.tanh(buf*1.34)
    peak = float(np.max(np.abs(buf)) or 1.0)
    if peak > .92:
        buf *= .92/peak
    fade = min(int(SR*2.0), total//4)
    buf[:fade] *= np.linspace(0,1,fade,dtype=np.float32)
    buf[-fade:] *= np.linspace(1,0,fade,dtype=np.float32)

    pcm = np.clip(buf*32767,-32768,32767).astype('<i2')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

    unique = len(set(drum_fps))
    return {
        'pack': pack_name,
        'seconds': round(len(pcm)/SR,3),
        'bpm': bpm,
        'bars': bars,
        'unique_drum_bars': unique,
        'drum_bar_count': len(drum_fps),
        'sha256': hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }


def main():
    source = Path(os.environ.get('ZK_SOURCE_DIR') or os.environ.get('ZK_SOURCE') or '.')
    root = source / 'zkstrap_assets' / 'sounds'
    if not root.is_dir():
        raise SystemExit(f'sounds root missing: {root}')
    dirs = sorted({p.parent for p in root.rglob('ambient*.wav')}, key=lambda p: str(p).lower())
    if not dirs:
        raise SystemExit('no ambient pack directories found')

    report=[]
    for d in dirs:
        old=list(d.glob('ambient*.wav'))
        pack=str(d.relative_to(root)).replace('\\','/') or d.name
        out=d/'ambient_v3212_original.wav'
        meta=compose(pack,out)
        for p in old:
            if p.resolve()!=out.resolve():
                try:p.unlink()
                except OSError:pass
        report.append(meta)
        print(pack,meta)

    if any(x['seconds'] < 120.0 for x in report):
        raise SystemExit('a generated track is shorter than 2 minutes')
    if any(x['unique_drum_bars'] < max(10,int(x['drum_bar_count']*.45)) for x in report):
        raise SystemExit('arrangement diversity validation failed')
    if len({x['sha256'] for x in report}) != len(report):
        raise SystemExit('duplicate music generated across packs')

    report_path=source/'zkstrap_assets'/'sounds'/'v3212_music_report.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated',len(report),'new original tracks; all >=120s')

if __name__=='__main__':
    main()
