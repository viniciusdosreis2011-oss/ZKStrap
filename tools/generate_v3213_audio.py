from __future__ import annotations
import hashlib, json, math, os, pathlib, wave
import numpy as np

ROOT = pathlib.Path(os.environ.get("ZK_SOURCE_DIR", "."))
SR = 12000
SECTIONS = ["intro", "A", "change", "B", "break", "final"]

TRACKS = [
    ("VOID DRIVE","void_drive","Phonk agressivo",145,132.0),
    ("NIGHT RUNNER","night_runner","Drift Phonk",170,126.0),
    ("NO SIGNAL","no_signal","Dark Trap",132,138.0),
    ("NEON HEART","neon_heart","Trap Melódico",138,144.0),
    ("SYSTEM BREACH","system_breach","Cyberpunk",128,136.0),
    ("OVERCLOCK","overclock","Drum & Bass",174,128.0),
    ("MIDNIGHT.exe","midnight_exe","Synthwave",105,150.0),
    ("AFTER HOURS","after_hours","Lo-fi",82,156.0),
    ("REDLINE","redline","Electro Rock",150,132.0),
    ("GLITCHED","glitched","Hyperpop / Rage",160,126.0),
    ("ABYSS","abyss","Dark Ambient",68,160.0),
    ("FINAL PHASE","final_phase","Boss Battle OST",156,140.0),
    ("PIXEL RUSH","pixel_rush","Chiptune moderno",165,124.0),
    ("ICE COLD","ice_cold","Jersey Club",140,130.0),
    ("LOW GRAVITY","low_gravity","Future Garage",134,148.0),
    ("BLACKOUT","blackout","Industrial",120,142.0),
    ("SUNSET MODE","sunset_mode","Chillwave",95,154.0),
    ("LAST ROUND","last_round","Breakcore leve",185,122.0),
]
META = {name: (slug, genre, bpm, dur) for name,slug,genre,bpm,dur in TRACKS}

def _osc(kind, phase):
    if kind == "square":
        return np.where(np.sin(phase) >= 0.0, 1.0, -1.0)
    if kind == "saw":
        return 2.0 * ((phase / (2*np.pi)) % 1.0) - 1.0
    if kind == "tri":
        x = (phase / (2*np.pi)) % 1.0
        return 4.0*np.abs(x-0.5)-1.0
    if kind == "pulse":
        return np.where(((phase/(2*np.pi))%1.0) < 0.27, 1.0, -1.0)
    return np.sin(phase)

def _note(buf, start, dur, freq, amp=0.1, wave_kind="sine", decay=2.0, detune=0.0):
    i0=max(0,int(start*SR)); i1=min(len(buf),i0+max(1,int(dur*SR)))
    if i1<=i0:return
    t=np.arange(i1-i0,dtype=np.float32)/SR
    ph=2*np.pi*freq*t
    y=_osc(wave_kind,ph)
    if detune:
        y=(y+0.55*_osc(wave_kind,2*np.pi*freq*(1.0+detune)*t))/1.55
    env=np.minimum(1.0,t/0.012)*np.exp(-decay*t/max(dur,0.05))
    buf[i0:i1]+=amp*y*env

def _kick(buf, t0, amp=0.5, tone=55.0):
    n=int(0.22*SR); i=int(t0*SR)
    if i>=len(buf):return
    n=min(n,len(buf)-i); t=np.arange(n,dtype=np.float32)/SR
    f=tone+90*np.exp(-18*t)
    ph=2*np.pi*np.cumsum(f)/SR
    env=np.exp(-18*t)
    buf[i:i+n]+=amp*np.sin(ph)*env

def _snare(buf,t0,rng,amp=0.23):
    n=int(0.16*SR);i=int(t0*SR)
    if i>=len(buf):return
    n=min(n,len(buf)-i);t=np.arange(n,dtype=np.float32)/SR
    noise=rng.standard_normal(n).astype(np.float32)
    env=np.exp(-24*t)
    buf[i:i+n]+=amp*(0.78*noise+0.22*np.sin(2*np.pi*185*t))*env

def _hat(buf,t0,rng,amp=0.075,open_hat=False):
    dur=0.15 if open_hat else 0.045
    n=int(dur*SR);i=int(t0*SR)
    if i>=len(buf):return
    n=min(n,len(buf)-i);t=np.arange(n,dtype=np.float32)/SR
    noise=rng.standard_normal(n).astype(np.float32)
    noise=np.concatenate(([0.0],np.diff(noise))).astype(np.float32)
    env=np.exp((-28 if open_hat else -75)*t)
    buf[i:i+n]+=amp*noise*env

def _impact(buf,t0,rng,amp=0.22):
    n=int(1.1*SR);i=int(t0*SR)
    if i>=len(buf):return
    n=min(n,len(buf)-i);t=np.arange(n,dtype=np.float32)/SR
    noise=rng.standard_normal(n).astype(np.float32)
    env=np.exp(-3.8*t)
    buf[i:i+n]+=amp*(0.6*noise+0.4*np.sin(2*np.pi*(48+16*np.exp(-3*t))*t))*env

def _pad(buf,start,dur,root,intervals=(0,3,7),amp=0.035,wave_kind="sine"):
    for k,semi in enumerate(intervals):
        f=root*(2**(semi/12))
        _note(buf,start,dur,f,amp/(1+k*0.1),wave_kind,decay=0.32,detune=0.003*(k+1))

def _scale(root, semis):
    return [root*(2**(s/12)) for s in semis]

def _base(name, seed):
    slug,genre,bpm,duration=META[name]
    rng=np.random.default_rng(seed)
    buf=np.zeros(int(duration*SR),dtype=np.float32)
    return buf,rng,slug,genre,bpm,duration

def _beat_times(duration,bpm,step=1.0):
    beat=60.0/bpm
    return np.arange(0.0,duration,beat*step,dtype=np.float32),beat

def _arrangement_gain(buf,duration,shape=(0.72,1.0,0.84,1.0,0.58,1.0)):
    edges=np.array([0,.12,.37,.50,.76,.88,1.0],dtype=np.float32)*duration
    gain=np.ones(len(buf),dtype=np.float32)
    for i,g in enumerate(shape):
        a=int(edges[i]*SR); b=min(len(buf),int(edges[i+1]*SR))
        gain[a:b]*=g
    n=min(int(1.5*SR),len(buf)//4)
    if n>1:
        gain[:n]*=np.linspace(0,1,n,dtype=np.float32)
        gain[-n:]*=np.linspace(1,0,n,dtype=np.float32)
    buf*=gain

def _finish(buf, drive=1.0, noise_floor=0.0, rng=None):
    if noise_floor and rng is not None:
        buf += noise_floor*rng.standard_normal(len(buf)).astype(np.float32)
    if drive!=1.0:
        buf=np.tanh(buf*drive)/np.tanh(drive)
    peak=float(np.max(np.abs(buf)) or 1.0)
    buf=np.clip(buf*(0.88/peak),-1,1)
    return (buf*32767.0).astype("<i2")

def compose_void_drive():
    b,r,slug,g,bpm,d=_base("VOID DRIVE",101)
    ts,beat=_beat_times(d,bpm)
    scale=_scale(55,[0,3,5,7,10,12])
    for j,t in enumerate(ts):
        if j%4 in (0,2):_kick(b,float(t),0.58,52)
        if j%4 in (1,3):_snare(b,float(t),r,0.20)
        _hat(b,float(t+beat*.5),r,0.055)
        f=scale[(j*3+j//8)%len(scale)]*2
        _note(b,float(t),beat*.72,f,0.085,"square",4.4)
        if j%2==0:_note(b,float(t),beat*1.7,scale[(j//2)%4]/2,0.19,"saw",1.8)
    _arrangement_gain(b,d);return _finish(b,1.9,0.0012,r)

def compose_night_runner():
    b,r,slug,g,bpm,d=_base("NIGHT RUNNER",202);ts,beat=_beat_times(d,bpm,.5)
    scale=_scale(65,[0,3,5,7,10,12,15])
    for j,t in enumerate(ts):
        if j%4 in (0,3):_kick(b,float(t),0.44,58)
        if j%8 in (2,6):_snare(b,float(t),r,0.15)
        _hat(b,float(t),r,0.045,j%8==7)
        f=scale[(j*5)%len(scale)]*2
        _note(b,float(t),beat*.32,f,0.07,"pulse",6.0)
        if j%4==0:_note(b,float(t),beat*1.8,scale[(j//4)%5]/2,0.16,"saw",1.4)
    _arrangement_gain(b,d,(.55,1,.8,1,.62,1));return _finish(b,1.7,.0007,r)

def compose_no_signal():
    b,r,slug,g,bpm,d=_base("NO SIGNAL",303);ts,beat=_beat_times(d,bpm)
    roots=_scale(46,[0,1,3,6,8,10])
    for j,t in enumerate(ts):
        if j%4==0:_kick(b,float(t),0.62,44)
        if j%4==2:_snare(b,float(t),r,0.28)
        if j%2==1:_hat(b,float(t+beat*.5),r,0.045)
        if j%8 in (0,3,7):_note(b,float(t),beat*2.8,roots[(j//2)%len(roots)]/2,0.22,"sine",1.5)
        if j%16==15:_impact(b,float(t),r,.10)
    for t in np.arange(2,d,3.37):
        _note(b,float(t),.045,950+r.uniform(-180,180),.04,"square",10)
    _arrangement_gain(b,d);return _finish(b,1.35,.002,r)

def compose_neon_heart():
    b,r,slug,g,bpm,d=_base("NEON HEART",404);ts,beat=_beat_times(d,bpm)
    scale=_scale(110,[0,2,3,7,10,12,14,15])
    bassroot=scale[0]/2
    for bar in range(int(d/(beat*4))+1):
        t=bar*beat*4; root=scale[(bar//2)%4]/2; bassroot=root
        _pad(b,t,beat*4,root,(0,3,7,10),.026,"tri")
    for j,t in enumerate(ts):
        if j%4 in (0,3):_kick(b,float(t),.38,58)
        if j%4==2:_snare(b,float(t),r,.16)
        _hat(b,float(t+beat*.5),r,.035)
        f=scale[(j*2+j//4)%len(scale)]
        _note(b,float(t),beat*.78,f,.105,"tri",3.5,.004)
        if j%4==0:_note(b,float(t),beat*2.5,bassroot/2,.11,"sine",1.0)
    _arrangement_gain(b,d);return _finish(b,1.1,.00035,r)

def compose_system_breach():
    b,r,slug,g,bpm,d=_base("SYSTEM BREACH",505);ts,beat=_beat_times(d,bpm,.5)
    seq=_scale(58,[0,1,6,7,10,13])
    for j,t in enumerate(ts):
        if j%8 in (0,5):_kick(b,float(t),.42,50)
        if j%8==4:_snare(b,float(t),r,.14)
        if j%2==0:_hat(b,float(t),r,.038)
        f=seq[(j*7+j//16)%len(seq)]
        _note(b,float(t),beat*.31,f,.08,"saw",8.0)
        if j%16==0:_pad(b,float(t),beat*8,f/2,(0,6,7),.022,"pulse")
        if j%23==0:_impact(b,float(t),r,.08)
    _arrangement_gain(b,d);return _finish(b,1.65,.001,r)

def compose_overclock():
    b,r,slug,g,bpm,d=_base("OVERCLOCK",606);ts,beat=_beat_times(d,bpm,.5)
    bass=_scale(49,[0,3,5,7,10])
    for j,t in enumerate(ts):
        if j%8 in (0,3,6):_kick(b,float(t),.42,55)
        if j%8 in (2,6):_snare(b,float(t),r,.19)
        _hat(b,float(t),r,.04,j%16 in (7,15))
        if j%2==0:_note(b,float(t),beat*.85,bass[(j//2)%len(bass)]/2,.18,"saw",2.6,.006)
        if j%8 in (1,5):_note(b,float(t),beat*.4,bass[(j+2)%len(bass)]*2,.055,"tri",5)
    _arrangement_gain(b,d,(.65,1,.72,1,.5,1));return _finish(b,1.55,.0006,r)

def compose_midnight_exe():
    b,r,slug,g,bpm,d=_base("MIDNIGHT.exe",707);ts,beat=_beat_times(d,bpm,.5)
    chords=[55,65.41,73.42,49.0];arp=[0,7,12,15,12,7,3,7]
    for j,t in enumerate(ts):
        root=chords[(j//16)%4]
        _note(b,float(t),beat*.44,root*2**(arp[j%8]/12),.065,"saw",3.4,.004)
        if j%8==0:_kick(b,float(t),.40,52)
        if j%8==4:_snare(b,float(t),r,.15)
        if j%4==2:_hat(b,float(t),r,.032,True)
        if j%16==0:_pad(b,float(t),beat*8,root,(0,4,7,11),.026,"saw")
        if j%8==0:_note(b,float(t),beat*3.5,root/2,.13,"square",1.1)
    _arrangement_gain(b,d);return _finish(b,1.08,.00025,r)

def compose_after_hours():
    b,r,slug,g,bpm,d=_base("AFTER HOURS",808);ts,beat=_beat_times(d,bpm)
    chords=[65.41,73.42,82.41,58.27]
    for bar in range(int(d/(beat*4))+1):
        t=bar*beat*4;root=chords[bar%4]
        _pad(b,t,beat*3.8,root,(0,3,7,10),.042,"sine")
        _note(b,t+.08,beat*.9,root*2,.05,"tri",2.8)
    for j,t in enumerate(ts):
        if j%4==0:_kick(b,float(t),.30,48)
        if j%4==2:_snare(b,float(t),r,.10)
        if j%2==1:_hat(b,float(t),r,.02)
        if j%8 in (3,7):_note(b,float(t),beat*.7,chords[(j//4)%4]*2**(7/12),.04,"sine",3)
    _arrangement_gain(b,d,(.78,.9,.72,.92,.58,.82));return _finish(b,1.0,.0045,r)

def compose_redline():
    b,r,slug,g,bpm,d=_base("REDLINE",909);ts,beat=_beat_times(d,bpm,.5)
    riff=_scale(82.41,[0,0,3,5,7,5,3,10])
    for j,t in enumerate(ts):
        if j%8 in (0,2,5):_kick(b,float(t),.48,58)
        if j%8 in (4,7):_snare(b,float(t),r,.20)
        _hat(b,float(t),r,.035)
        f=riff[j%len(riff)]
        _note(b,float(t),beat*.42,f,.13,"saw",6,.008)
        _note(b,float(t),beat*.40,f/2,.09,"square",5)
        if j%16==0:_impact(b,float(t),r,.11)
    _arrangement_gain(b,d);return _finish(b,2.0,.0007,r)

def compose_glitched():
    b,r,slug,g,bpm,d=_base("GLITCHED",1001);ts,beat=_beat_times(d,bpm,.5)
    sc=_scale(123.47,[0,2,4,7,9,12,14,16])
    for j,t in enumerate(ts):
        if j%8 in (0,3,7):_kick(b,float(t),.43,62)
        if j%8==4:_snare(b,float(t),r,.18)
        if j%3!=1:_hat(b,float(t),r,.045)
        f=sc[(j*3+j//8)%len(sc)]
        _note(b,float(t),beat*.27,f,.095,"square",8)
        if j%8 in (0,6):_note(b,float(t),beat*1.4,sc[(j//8)%4]/2,.18,"sine",2)
        if j%19==0:_note(b,float(t),.06,1700+r.uniform(-400,500),.045,"pulse",14)
    _arrangement_gain(b,d);out=_finish(b,1.8,.0005,r)
    return ((out.astype(np.int32)//64)*64).astype("<i2")

def compose_abyss():
    b,r,slug,g,bpm,d=_base("ABYSS",1102);roots=[36.71,41.20,32.70,46.25]
    for k,t in enumerate(np.arange(0,d,8.0)):
        root=roots[k%4]
        _pad(b,float(t),10.5,root,(0,1,7,12),.052,"sine")
        _note(b,float(t+2.7),5.5,root*4*2**(([0,3,7,10][k%4])/12),.025,"sine",.6)
        if k%3==0:_impact(b,float(t),r,.035)
    for t in np.arange(0,d,60/bpm*4):_note(b,float(t),2.4,roots[int(t)%4]/2,.06,"sine",.55)
    _arrangement_gain(b,d,(.45,.7,.65,.78,.38,.62));return _finish(b,1.0,.0018,r)

def compose_final_phase():
    b,r,slug,g,bpm,d=_base("FINAL PHASE",1203);ts,beat=_beat_times(d,bpm,.5);ost=_scale(55,[0,3,7,8,10,12,15,19])
    for j,t in enumerate(ts):
        if j%8 in (0,2,5,7):_kick(b,float(t),.48,48)
        if j%8 in (4,6):_snare(b,float(t),r,.17)
        if j%2==0:_hat(b,float(t),r,.028)
        f=ost[(j*3)%8]
        _note(b,float(t),beat*.36,f,.095,"tri",5);_note(b,float(t),beat*.38,f/2,.07,"saw",4)
        if j%32==0:_impact(b,float(t),r,.18);_pad(b,float(t),beat*12,f/2,(0,3,7,12),.03,"saw")
    _arrangement_gain(b,d,(.55,.85,.74,1,.48,1));return _finish(b,1.6,.0007,r)

def compose_pixel_rush():
    b,r,slug,g,bpm,d=_base("PIXEL RUSH",1304);ts,beat=_beat_times(d,bpm,.5);sc=_scale(130.81,[0,2,4,7,9,12,14,16,19])
    for j,t in enumerate(ts):
        if j%8 in (0,4):_kick(b,float(t),.34,64)
        if j%8 in (2,6):_snare(b,float(t),r,.105)
        _hat(b,float(t),r,.02);_note(b,float(t),beat*.38,sc[(j*5)%len(sc)],.10,"square",7)
        if j%4==0:_note(b,float(t),beat*1.7,sc[(j//4)%5]/4,.13,"pulse",2.1)
    _arrangement_gain(b,d);return _finish(b,1.3,.00015,r)

def compose_ice_cold():
    b,r,slug,g,bpm,d=_base("ICE COLD",1405);ts,beat=_beat_times(d,bpm);sc=_scale(73.42,[0,3,5,7,10,12])
    for j,t in enumerate(ts):
        _kick(b,float(t),.43,58)
        if j%2==1:_kick(b,float(t+beat/3),.30,62);_kick(b,float(t+2*beat/3),.25,66)
        if j%4==2:_snare(b,float(t),r,.14)
        _hat(b,float(t+beat*.5),r,.034)
        if j%2==0:_note(b,float(t),beat*.48,sc[(j*2)%len(sc)]*2,.07,"tri",5)
        if j%4==0:_note(b,float(t),beat*2.4,sc[(j//4)%4]/2,.16,"sine",1.3)
    _arrangement_gain(b,d);return _finish(b,1.45,.0005,r)

def compose_low_gravity():
    b,r,slug,g,bpm,d=_base("LOW GRAVITY",1506);ts,beat=_beat_times(d,bpm,.5);sc=_scale(61.74,[0,2,3,7,10,12,14])
    for j,t in enumerate(ts):
        if j%16 in (0,5,11):_kick(b,float(t),.35,50)
        if j%16 in (7,15):_snare(b,float(t),r,.12)
        if j%4 in (1,3):_hat(b,float(t),r,.025,True)
        if j%8 in (0,3,6):_note(b,float(t),beat*2.2,sc[(j//3)%len(sc)]/2,.13,"sine",1.1)
        if j%16==0:_pad(b,float(t),beat*8,sc[(j//16)%4],(0,3,7,14),.028,"tri")
    _arrangement_gain(b,d,(.55,.82,.68,.9,.4,.78));return _finish(b,1.08,.0012,r)

def compose_blackout():
    b,r,slug,g,bpm,d=_base("BLACKOUT",1607);ts,beat=_beat_times(d,bpm,.5);roots=_scale(46.25,[0,1,6,7,10])
    for j,t in enumerate(ts):
        if j%8 in (0,3,6):_kick(b,float(t),.58,43)
        if j%8 in (4,7):_snare(b,float(t),r,.16)
        if j%2==0:_hat(b,float(t),r,.055)
        f=roots[(j//4)%len(roots)];_note(b,float(t),beat*.75,f,.18,"saw",2.3)
        if j%8 in (1,5):_note(b,float(t),.10,650+90*(j%5),.055,"square",10)
        if j%24==0:_impact(b,float(t),r,.15)
    _arrangement_gain(b,d);return _finish(b,2.2,.0025,r)

def compose_sunset_mode():
    b,r,slug,g,bpm,d=_base("SUNSET MODE",1708);ts,beat=_beat_times(d,bpm);roots=[82.41,98.0,110.0,73.42]
    for bar in range(int(d/(beat*4))+1):
        t=bar*beat*4;root=roots[bar%4];_pad(b,t,beat*5,root,(0,4,7,11),.040,"tri");_note(b,t+beat*.5,beat*1.6,root*2,.036,"sine",1.5,.006)
    for j,t in enumerate(ts):
        if j%4==0:_kick(b,float(t),.25,52)
        if j%4==2:_snare(b,float(t),r,.085)
        if j%2==1:_hat(b,float(t),r,.017,True)
        if j%8==6:_note(b,float(t),beat*.9,roots[(j//8)%4]*2**(7/12),.045,"tri",2.4)
    _arrangement_gain(b,d,(.65,.8,.72,.88,.5,.72));return _finish(b,1.0,.0015,r)

def compose_last_round():
    b,r,slug,g,bpm,d=_base("LAST ROUND",1809);ts,beat=_beat_times(d,bpm,.25);sc=_scale(55,[0,1,3,6,7,10,12])
    for j,t in enumerate(ts):
        if j%16 in (0,3,6,10,13):_kick(b,float(t),.38,54+r.uniform(-4,4))
        if j%16 in (4,7,12,15):_snare(b,float(t),r,.17)
        if j%2==0:_hat(b,float(t),r,.03,j%16 in (7,15))
        if j%8 in (0,2,5):_note(b,float(t),beat*.22,sc[(j*3+j//16)%len(sc)]*2,.055,"pulse",10)
        if j%32==0:_note(b,float(t),beat*5,sc[(j//32)%4]/2,.15,"saw",1.8)
    _arrangement_gain(b,d,(.62,.95,.7,1,.42,1));return _finish(b,1.65,.0015,r)

COMPOSERS = {
    "VOID DRIVE": compose_void_drive, "NIGHT RUNNER": compose_night_runner,
    "NO SIGNAL": compose_no_signal, "NEON HEART": compose_neon_heart,
    "SYSTEM BREACH": compose_system_breach, "OVERCLOCK": compose_overclock,
    "MIDNIGHT.exe": compose_midnight_exe, "AFTER HOURS": compose_after_hours,
    "REDLINE": compose_redline, "GLITCHED": compose_glitched, "ABYSS": compose_abyss,
    "FINAL PHASE": compose_final_phase, "PIXEL RUSH": compose_pixel_rush,
    "ICE COLD": compose_ice_cold, "LOW GRAVITY": compose_low_gravity,
    "BLACKOUT": compose_blackout, "SUNSET MODE": compose_sunset_mode,
    "LAST ROUND": compose_last_round,
}

def _write_wav(path, pcm):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())

def main():
    packroot=ROOT/"zkstrap_assets"/"sounds"/"packs";report=[]
    for name,slug,genre,bpm,duration in TRACKS:
        folder=packroot/slug;folder.mkdir(parents=True,exist_ok=True)
        for old in folder.glob("ambient*.wav"):old.unlink()
        pcm=COMPOSERS[name]();out=folder/f"ambient_v3213_{slug}.wav";_write_wav(out,pcm)
        digest=hashlib.sha256(out.read_bytes()).hexdigest();actual=len(pcm)/SR
        report.append({"name":name,"slug":slug,"genre":genre,"bpm":bpm,"duration":round(actual,3),"sections":SECTIONS,"file":str(out.relative_to(ROOT)).replace("\\","/"),"sha256":digest})
        print(f"{name}: {actual:.1f}s {digest[:12]} {out}")
    (ROOT/"v3213_audio_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Generated 18 independent v3.20.13 tracks.")

if __name__=="__main__":main()
