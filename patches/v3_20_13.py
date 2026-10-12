from pathlib import Path
import ast, os, re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def method_span(text, cls_name, name):
    pat=re.compile(r'(?m)^    (?:async\s+)?def\s+'+re.escape(name)+r'\s*\(')
    hits=list(pat.finditer(text))
    if len(hits)!=1: raise SystemExit(f'v3.20.13: expected one {cls_name}.{name}, found {len(hits)}')
    a=hits[0].start()
    nxt=re.search(r'(?m)^(?:    @|    (?:async\s+)?def\s+\w+\s*\(|class\s+\w+\b|def\s+\w+\s*\()',text[hits[0].end():])
    b=hits[0].end()+nxt.start() if nxt else len(text)
    return a,b


def replace_method(cls_name,name,new_src):
    global s
    a,b=method_span(s,cls_name,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def insert_before_method(cls_name,name,src):
    global s
    a,_=method_span(s,cls_name,name)
    s=s[:a]+src.rstrip()+"\n\n"+s[a:]


def top_def_span(text,name):
    pat=re.compile(r'(?m)^def\s+'+re.escape(name)+r'\s*\(')
    hits=list(pat.finditer(text))
    if len(hits)!=1: raise SystemExit(f'v3.20.13: expected one global {name}, found {len(hits)}')
    a=hits[0].start()
    nxt=re.search(r'(?m)^(?:def\s+\w+\s*\(|class\s+\w+\b)',text[hits[0].end():])
    b=hits[0].end()+nxt.start() if nxt else len(text)
    return a,b


def replace_global(name,new_src):
    global s
    a,b=top_def_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def replace_global_assignment(name,new_src):
    global s
    tree=ast.parse(s)
    node=None
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):
            node=n;break
        if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id==name:
            node=n;break
    if node is None: raise SystemExit(f'v3.20.13: global assignment {name} not found')
    lines=s.splitlines(True); starts=[0]; total=0
    for line in lines: total+=len(line); starts.append(total)
    a=starts[node.lineno-1]; b=starts[node.end_lineno]
    s=s[:a]+new_src.rstrip()+"\n"+s[b:]


if 'APP_VERSION = "3.20.12"' not in s: raise SystemExit('v3.20.13: expected v3.20.12 base')
s=s.replace('APP_VERSION = "3.20.12"','APP_VERSION = "3.20.13"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Robust ANI + 18 Distinct Audio Identities"',s,count=1)
if n!=1: raise SystemExit('v3.20.13: timestamp')

# AUDIO: 18 real identities. Spotify code is deliberately untouched.
replace_global_assignment('AUDIO_PACKS',r'''AUDIO_PACKS = {
    "VOID DRIVE": {"folder":"void_drive", "genre":"Phonk agressivo", "bpm":145, "desc":"Phonk agressivo • 145 BPM • cowbell, 808 saturado e bateria seca."},
    "NIGHT RUNNER": {"folder":"night_runner", "genre":"Drift Phonk", "bpm":170, "desc":"Drift Phonk • 170 BPM • cowbell veloz, bass distorcido e corrida noturna."},
    "NO SIGNAL": {"folder":"no_signal", "genre":"Dark Trap", "bpm":132, "desc":"Dark Trap • 132 BPM • 808 profundo, hats quebrados e atmosfera sem sinal."},
    "NEON HEART": {"folder":"neon_heart", "genre":"Trap Melódico", "bpm":138, "desc":"Trap melódico • 138 BPM • plucks emotivos, pads e 808 limpo."},
    "SYSTEM BREACH": {"folder":"system_breach", "genre":"Cyberpunk", "bpm":128, "desc":"Cyberpunk • 128 BPM • sequências mecânicas, bass pulse e glitches."},
    "OVERCLOCK": {"folder":"overclock", "genre":"Drum & Bass", "bpm":174, "desc":"Drum & Bass • 174 BPM • break rápido, reese bass e energia contínua."},
    "MIDNIGHT.exe": {"folder":"midnight_exe", "genre":"Synthwave", "bpm":105, "desc":"Synthwave • 105 BPM • synths analógicos, arpejo e bateria retrô."},
    "AFTER HOURS": {"folder":"after_hours", "genre":"Lo-fi", "bpm":82, "desc":"Lo-fi • 82 BPM • Rhodes, bateria macia e textura noturna."},
    "REDLINE": {"folder":"redline", "genre":"Electro Rock", "bpm":150, "desc":"Electro Rock • 150 BPM • riffs sintéticos, bateria pesada e bass agressivo."},
    "GLITCHED": {"folder":"glitched", "genre":"Hyperpop / Rage", "bpm":160, "desc":"Hyperpop/Rage • 160 BPM • leads brilhantes, 808 slides e cortes digitais."},
    "ABYSS": {"folder":"abyss", "genre":"Dark Ambient", "bpm":68, "desc":"Dark Ambient • 68 BPM • drones, sinos distantes e espaço profundo."},
    "FINAL PHASE": {"folder":"final_phase", "genre":"Boss Battle OST", "bpm":156, "desc":"Boss Battle OST • 156 BPM • ostinatos, impactos e clímax cinematográfico."},
    "PIXEL RUSH": {"folder":"pixel_rush", "genre":"Chiptune moderno", "bpm":165, "desc":"Chiptune moderno • 165 BPM • pulse leads, arpejos e drums digitais."},
    "ICE COLD": {"folder":"ice_cold", "genre":"Jersey Club", "bpm":140, "desc":"Jersey Club • 140 BPM • kick triplet, chops sintéticos e bounce gelado."},
    "LOW GRAVITY": {"folder":"low_gravity", "genre":"Future Garage", "bpm":134, "desc":"Future Garage • 134 BPM • drums espaçados, subs e pads aéreos."},
    "BLACKOUT": {"folder":"blackout", "genre":"Industrial", "bpm":120, "desc":"Industrial • 120 BPM • metal, ruído, kick pesado e sequências de fábrica."},
    "SUNSET MODE": {"folder":"sunset_mode", "genre":"Chillwave", "bpm":95, "desc":"Chillwave • 95 BPM • pads quentes, chorus synth e groove de pôr do sol."},
    "LAST ROUND": {"folder":"last_round", "genre":"Breakcore leve", "bpm":185, "desc":"Breakcore leve • 185 BPM • breaks fragmentados, bass curto e final acelerado."},
}''')
replace_global_assignment('DEFAULT_AUDIO_PACK','DEFAULT_AUDIO_PACK = "VOID DRIVE"')

anchor='DEFAULT_AUDIO_PACK = "VOID DRIVE"\n'
if anchor not in s: raise SystemExit('v3.20.13: default audio anchor')
alias_src=r'''
AUDIO_PACK_ALIASES = {
    "ZK Signature":"SUNSET MODE", "Neon Tech":"MIDNIGHT.exe", "Glass UI":"NEON HEART",
    "Tactical":"VOID DRIVE", "Deep Space":"ABYSS", "Arcade":"PIXEL RUSH",
    "Soft Clicks":"AFTER HOURS", "Cyber Pulse":"SYSTEM BREACH",
    "Retro Digital":"PIXEL RUSH", "Void Calm":"ABYSS",
}
def _normalize_audio_pack(name):
    name=str(name or "").strip()
    name=AUDIO_PACK_ALIASES.get(name,name)
    return name if name in AUDIO_PACKS else DEFAULT_AUDIO_PACK
'''
s=s.replace(anchor,anchor+alias_src,1)

pat=re.compile(r'(?m)^(\s{8}self\.sound_pack\s*=\s*[^\n]*config_data\.get\(["\']sound_pack["\'][^\n]*)$')
m=pat.search(s)
if m:
    line=m.group(1)
    s=s[:m.start()]+line+'\n        self.sound_pack=_normalize_audio_pack(self.sound_pack)'+s[m.end():]
else:
    print('v3.20.13: note: app sound_pack init line not found; using runtime normalization')

try:
    a,b=method_span(s,'ZKSoundManager','set_pack')
    old=s[a:b]
    old=old.replace('self.pack=pack','self.pack=_normalize_audio_pack(pack)')
    old=old.replace('self.pack = pack','self.pack = _normalize_audio_pack(pack)')
    s=s[:a]+old+s[b:]
except SystemExit:
    pass

replace_method('ZKSoundManager','_long_music_path',r'''    def _long_music_path(self, minimum_seconds=120.0):
        """Return the single long-form v3.20.13 composition for this identity."""
        try:
            self.pack=_normalize_audio_pack(getattr(self,"pack",DEFAULT_AUDIO_PACK))
            paths=[p for p in self.paths("ambient") if os.path.isfile(p)]
            preferred=[p for p in paths if "v3213_" in os.path.basename(p).lower()]
            return (preferred or paths)[0] if (preferred or paths) else ""
        except Exception:return ""
''')

a,b=method_span(s,'ModernConfigApp','_lazy_build_page_audio');chunk=s[a:b]
needle='''        t=TEMAS[self.tema_atual]\n        st=self._theme_style()'''
if needle not in chunk: raise SystemExit('v3.20.13: audio page start anchor')
chunk=chunk.replace(needle,'''        t=TEMAS[self.tema_atual]\n        self.sound_pack=_normalize_audio_pack(getattr(self,"sound_pack",DEFAULT_AUDIO_PACK))\n        st=self._theme_style()''',1)
chunk=chunk.replace('10 packs locais, 2 trilhas melódicas por pack e efeitos diferentes para navegação, scroll, sliders, tema, Combo Planner, avisos e carregamento.','18 músicas originais, cada uma com identidade, BPM, arranjo e atmosfera próprios. Os efeitos da interface continuam separados.')
chunk=chunk.replace('10 local packs, 2 melodic background tracks per pack and distinct effects for navigation, scroll, sliders, themes, Combo Planner, alerts and loading.','18 original tracks, each with its own identity, BPM, arrangement and atmosphere. Interface effects remain separate.')
chunk=chunk.replace('PACKS DE SOM','MÚSICAS // IDENTIDADES')
chunk=chunk.replace('SOUND PACKS','TRACKS // IDENTITIES')
chunk=chunk.replace('Cada pack usa composição, ritmo e harmonia próprios. Use TESTAR para ouvir a assinatura antes de trocar.','Cada faixa foi composta como música própria, não como variação de uma mesma base. Use TESTAR para ouvir antes de trocar.')
chunk=chunk.replace('Each pack uses its own composition, rhythm and harmony. Use TEST to hear its signature before switching.','Each track is composed as its own song, not a variation of the same base. Use TEST before switching.')
old='''            ctk.CTkLabel(pc,text=meta.get("desc",""),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x",padx=12,pady=(1,8))'''
new='''            meta_line=f"{meta.get('genre','')}  //  {meta.get('bpm','?')} BPM"\n            ctk.CTkLabel(pc,text=meta_line,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(fill="x",padx=12,pady=(1,2))\n            ctk.CTkLabel(pc,text=meta.get("desc",""),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x",padx=12,pady=(1,8))'''
if old not in chunk: raise SystemExit('v3.20.13: audio card description anchor')
chunk=chunk.replace(old,new,1)
s=s[:a]+chunk+s[b:]

replace_global('_cursor_overlay_decode_file',r'''def _cursor_overlay_decode_file(path,target_visible=24):
    from PIL import Image,ImageSequence
    import io,struct
    path=str(path or '');ext=os.path.splitext(path)[1].lower();frames=[];delays=[];hotspots=[]

    def _u32(blob,off=0):
        return struct.unpack_from('<I',blob,off)[0]

    def _decode_dib(dib,width_hint=0,height_hint=0):
        if len(dib)<16:return None
        try:
            hsize=_u32(dib,0)
            if hsize not in (12,40,52,56,64,108,124):return None
            if hsize==12:
                w,h=struct.unpack_from('<HH',dib,4);bit=struct.unpack_from('<H',dib,10)[0]
            else:
                w,h=struct.unpack_from('<ii',dib,4);bit=struct.unpack_from('<H',dib,14)[0]
            w=int(width_hint or abs(w) or 32); real_h=int(height_hint or max(1,abs(h)//2) or 32)
            wb=0 if w>=256 else max(1,min(255,w));hb=0 if real_h>=256 else max(1,min(255,real_h))
            ico=struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',wb,hb,0,0,1,max(1,int(bit or 32)),len(dib),22)+dib
            im=Image.open(io.BytesIO(ico));im.load();return im.convert('RGBA')
        except Exception:return None

    def _decode_cur_ico(blob):
        if len(blob)<22 or blob[:2]!=b'\x00\x00' or blob[2:4] not in (b'\x01\x00',b'\x02\x00'):return None
        try:
            typ,count=struct.unpack_from('<HH',blob,2);best=None
            for i in range(min(int(count),64)):
                off=6+i*16
                if off+16>len(blob):break
                w,h,cc,res,a,b,size,pos=struct.unpack_from('<BBBBHHII',blob,off)
                ww=256 if w==0 else w;hh=256 if h==0 else h
                if pos<0 or size<=0 or pos+size>len(blob):continue
                score=ww*hh
                if best is None or score>best[0]:best=(score,ww,hh,a,b,size,pos,typ)
            if best is None:return None
            _,ww,hh,a,b,size,pos,typ=best;raw=blob[pos:pos+size]
            if raw.startswith(b'\x89PNG\r\n\x1a\n'):
                im=Image.open(io.BytesIO(raw));im.load();im=im.convert('RGBA')
            else:
                im=_decode_dib(raw,ww,hh)
                if im is None:return None
            hotspot=(int(a),int(b)) if typ==2 else (0,0)
            return im,hotspot
        except Exception:return None

    def _decode_icon_payload(payload):
        got=_decode_cur_ico(payload)
        if got:return got
        if len(payload)>8:
            try:hx,hy=struct.unpack_from('<HH',payload,0)
            except Exception:hx=hy=0
            raw=payload[4:]
            if raw.startswith(b'\x89PNG\r\n\x1a\n'):
                try:
                    im=Image.open(io.BytesIO(raw));im.load();return im.convert('RGBA'),(int(hx),int(hy))
                except Exception:pass
            im=_decode_dib(raw)
            if im is not None:return im,(int(hx),int(hy))
        for sig in (b'\x00\x00\x02\x00',b'\x00\x00\x01\x00'):
            p=payload.find(sig,1,96)
            if p>=0:
                got=_decode_cur_ico(payload[p:])
                if got:return got
        p=payload.find(b'\x89PNG\r\n\x1a\n')
        if p>=0:
            try:
                im=Image.open(io.BytesIO(payload[p:]));im.load();return im.convert('RGBA'),(0,0)
            except Exception:pass
        for p in (0,4,8,12):
            if len(payload)>=p+4 and _u32(payload,p) in (12,40,52,56,64,108,124):
                im=_decode_dib(payload[p:])
                if im is not None:return im,(0,0)
        return None

    def _riff_chunks(data,start,end):
        pos=max(0,int(start));end=min(len(data),int(end))
        while pos+8<=end:
            cid=data[pos:pos+4];size=_u32(data,pos+4);ds=pos+8;de=min(end,ds+size)
            if de<ds:break
            payload=data[ds:de]
            yield cid,payload
            if cid in (b'LIST',b'RIFF') and len(payload)>=4:
                yield from _riff_chunks(data,ds+4,de)
            nxt=ds+size+(size&1)
            if nxt<=pos:break
            pos=nxt

    ani_meta={'frames':0,'steps':0,'jif':5,'flags':0};rates=[];seq=[]
    if ext=='.ani':
        data=Path(path).read_bytes()
        if len(data)<12 or data[:4]!=b'RIFF' or data[8:12]!=b'ACON':raise ValueError('invalid RIFF/ACON ANI')
        payloads=[]
        for cid,payload in _riff_chunks(data,12,min(len(data),8+_u32(data,4))):
            low=cid.lower()
            if low==b'anih' and len(payload)>=36:
                vals=struct.unpack_from('<9I',payload,0)
                ani_meta={'frames':int(vals[1]),'steps':int(vals[2]),'jif':max(1,int(vals[7] or 5)),'flags':int(vals[8])}
            elif low==b'rate' and len(payload)>=4:
                rates=[int(v) for v in struct.unpack('<'+'I'*(len(payload)//4),payload[:(len(payload)//4)*4])]
            elif low in (b'seq ',b'seq\x00') and len(payload)>=4:
                seq=[int(v) for v in struct.unpack('<'+'I'*(len(payload)//4),payload[:(len(payload)//4)*4])]
            elif low==b'icon':payloads.append(payload)
        base=[];base_hot=[]
        for payload in payloads:
            got=_decode_icon_payload(payload)
            if got:
                base.append(got[0]);base_hot.append(got[1])
        if base:
            requested=max(1,ani_meta.get('steps',0) or len(seq) or len(base));requested=min(256,requested)
            order=(seq[:requested] if seq else [i%len(base) for i in range(requested)])
            order=[i for i in order if 0<=int(i)<len(base)] or list(range(len(base)))
            default_jif=max(1,int(ani_meta.get('jif',5) or 5))
            for step,idx in enumerate(order):
                frames.append(base[int(idx)]);hotspots.append(base_hot[int(idx)] if int(idx)<len(base_hot) else (0,0))
                jif=int(rates[step] if step<len(rates) and rates[step] else default_jif)
                delays.append(max(16,min(1000,int(round(jif*1000.0/60.0)))))
        elif os.name=='nt':
            try:
                native=_cursor_overlay_native_ani_frames(path,max(1,ani_meta.get('steps',0) or ani_meta.get('frames',0) or len(rates) or 1),ani_meta.get('jif',5),rates)
                frames,delays,hotspots=native
            except Exception as exc:
                raise ValueError('no cursor frames (RIFF parsed; Windows fallback failed: '+str(exc)+')')
    elif ext=='.gif':
        im=Image.open(path)
        for fr in ImageSequence.Iterator(im):
            frames.append(fr.convert('RGBA').copy());delays.append(max(20,int(fr.info.get('duration',70) or 70)));hotspots.append((0,0))
    elif ext in ('.cur','.ico'):
        blob=Path(path).read_bytes();got=_decode_icon_payload(blob)
        if got:frames=[got[0]];delays=[250];hotspots=[got[1]]
    else:
        blob=Path(path).read_bytes();im=Image.open(io.BytesIO(blob)).convert('RGBA');frames=[im.copy()];delays=[250];hotspots=[(0,0)]
    if not frames:raise ValueError('no cursor frames')
    target_visible=max(8,min(96,int(target_visible or 24)));prepared=[];scaled_hot=[];out_delays=[]
    for idx,im in enumerate(frames[:256]):
        im=im.convert('RGBA');bbox=im.getchannel('A').getbbox() or (0,0,im.width,im.height);vw=max(1,bbox[2]-bbox[0]);vh=max(1,bbox[3]-bbox[1]);scale=target_visible/max(vw,vh)
        nw=max(1,int(round(im.width*scale)));nh=max(1,int(round(im.height*scale)))
        if (nw,nh)!=im.size:im=im.resize((nw,nh),Image.Resampling.LANCZOS)
        hx,hy=hotspots[idx] if idx<len(hotspots) else (0,0);prepared.append(im);scaled_hot.append((max(0,int(round(hx*scale))),max(0,int(round(hy*scale)))));out_delays.append(int(delays[idx] if idx<len(delays) else 85))
    return prepared,out_delays,scaled_hot
''')

insert_at=top_def_span(s,'_cursor_overlay_decode_file')[0]
native_src=r'''def _cursor_overlay_native_ani_frames(path,steps=1,default_jif=5,rates=None):
    if os.name!='nt':raise RuntimeError('Windows only')
    from PIL import Image
    import ctypes
    from ctypes import wintypes
    user32=ctypes.windll.user32;gdi32=ctypes.windll.gdi32
    IMAGE_CURSOR=2;LR_LOADFROMFILE=0x0010;DI_NORMAL=0x0003
    hcur=user32.LoadImageW(None,str(path),IMAGE_CURSOR,0,0,LR_LOADFROMFILE)
    if not hcur:raise OSError('LoadImageW rejected ANI')
    class ICONINFO(ctypes.Structure):
        _fields_=[('fIcon',wintypes.BOOL),('xHotspot',wintypes.DWORD),('yHotspot',wintypes.DWORD),('hbmMask',wintypes.HBITMAP),('hbmColor',wintypes.HBITMAP)]
    class BITMAP(ctypes.Structure):
        _fields_=[('bmType',wintypes.LONG),('bmWidth',wintypes.LONG),('bmHeight',wintypes.LONG),('bmWidthBytes',wintypes.LONG),('bmPlanes',wintypes.WORD),('bmBitsPixel',wintypes.WORD),('bmBits',ctypes.c_void_p)]
    class BMIH(ctypes.Structure):
        _fields_=[('biSize',wintypes.DWORD),('biWidth',wintypes.LONG),('biHeight',wintypes.LONG),('biPlanes',wintypes.WORD),('biBitCount',wintypes.WORD),('biCompression',wintypes.DWORD),('biSizeImage',wintypes.DWORD),('biXPelsPerMeter',wintypes.LONG),('biYPelsPerMeter',wintypes.LONG),('biClrUsed',wintypes.DWORD),('biClrImportant',wintypes.DWORD)]
    class BMI(ctypes.Structure):_fields_=[('bmiHeader',BMIH),('bmiColors',wintypes.DWORD*3)]
    info=ICONINFO();w=h=32;hx=hy=0
    try:
        if user32.GetIconInfo(hcur,ctypes.byref(info)):
            hx,hy=int(info.xHotspot),int(info.yHotspot);bm=BITMAP();hb=info.hbmColor or info.hbmMask
            if hb and gdi32.GetObjectW(hb,ctypes.sizeof(BITMAP),ctypes.byref(bm)):
                w=max(1,int(bm.bmWidth));h=max(1,int(bm.bmHeight if info.hbmColor else bm.bmHeight//2))
    finally:
        try:
            if info.hbmColor:gdi32.DeleteObject(info.hbmColor)
            if info.hbmMask:gdi32.DeleteObject(info.hbmMask)
        except Exception:pass
    steps=max(1,min(256,int(steps or 1)));out=[];delays=[];hots=[];rates=list(rates or []);default_jif=max(1,int(default_jif or 5))
    for step in range(steps):
        dc=gdi32.CreateCompatibleDC(0);bits=ctypes.c_void_p();bmi=BMI();bmi.bmiHeader.biSize=ctypes.sizeof(BMIH);bmi.bmiHeader.biWidth=w;bmi.bmiHeader.biHeight=-h;bmi.bmiHeader.biPlanes=1;bmi.bmiHeader.biBitCount=32;bmi.bmiHeader.biCompression=0
        hbmp=gdi32.CreateDIBSection(dc,ctypes.byref(bmi),0,ctypes.byref(bits),None,0)
        if not hbmp or not bits:
            if dc:gdi32.DeleteDC(dc)
            break
        old=gdi32.SelectObject(dc,hbmp)
        try:
            ctypes.memset(bits,0,w*h*4)
            ok=user32.DrawIconEx(dc,0,0,hcur,w,h,step,None,DI_NORMAL)
            if not ok:continue
            raw=ctypes.string_at(bits,w*h*4);im=Image.frombytes('RGBA',(w,h),raw,'raw','BGRA')
            alpha=im.getchannel('A')
            if alpha.getbbox() is None:
                px=bytearray(im.tobytes())
                for i in range(0,len(px),4):px[i+3]=255 if (px[i] or px[i+1] or px[i+2]) else 0
                im=Image.frombytes('RGBA',(w,h),bytes(px))
            out.append(im);hots.append((hx,hy));j=int(rates[step] if step<len(rates) and rates[step] else default_jif);delays.append(max(16,min(1000,int(round(j*1000.0/60.0)))))
        finally:
            if old:gdi32.SelectObject(dc,old)
            gdi32.DeleteObject(hbmp);gdi32.DeleteDC(dc)
    try:user32.DestroyCursor(hcur)
    except Exception:pass
    if not out:raise RuntimeError('DrawIconEx returned no frames')
    return out,delays,hots

'''
s=s[:insert_at]+native_src+s[insert_at:]

insert_before_method('ModernConfigApp','_cursor_overlay_refresh_ui',r'''    def _cursor_overlay_preview_stop(self):
        self._cursor_overlay_preview_token=int(getattr(self,'_cursor_overlay_preview_token',0) or 0)+1
        self._cursor_overlay_preview_images=[]

    def _cursor_overlay_preview_refresh(self):
        token=int(getattr(self,'_cursor_overlay_preview_token',0) or 0)+1;self._cursor_overlay_preview_token=token
        lab=getattr(self,'cursor_overlay_preview',None);path=str(getattr(self,'cursor_overlay_path','') or '')
        if lab is None:return
        try:
            if not lab.winfo_exists():return
        except Exception:return
        if not path or not os.path.isfile(path):
            try:lab.configure(image=None,text='◉')
            except Exception:pass
            return
        try:
            frames,delays,_=_cursor_overlay_decode_file(path,48)
            imgs=[ctk.CTkImage(light_image=im,dark_image=im,size=im.size) for im in frames[:96]]
            self._cursor_overlay_preview_images=imgs
            def tick(i=0):
                if token!=int(getattr(self,'_cursor_overlay_preview_token',0) or 0):return
                try:
                    if not lab.winfo_exists():return
                    j=i%len(imgs);lab.configure(image=imgs[j],text='');delay=max(20,min(1000,int(delays[j] if j<len(delays) else 85)));self.after(delay,lambda:tick(i+1))
                except Exception:return
            tick(0)
        except Exception:
            try:lab.configure(image=None,text=os.path.splitext(path)[1].lstrip('.').upper() or 'CUR')
            except Exception:pass
''')

a,b=method_span(s,'ModernConfigApp','_lazy_build_page_cursor');chunk=s[a:b]
old='''ctk.CTkLabel(icon,text="◉",text_color=t["accent"],font=ctk.CTkFont(size=28,weight="bold")).pack(fill="both",expand=True)'''
new='''self.cursor_overlay_preview=ctk.CTkLabel(icon,text="◉",text_color=t["accent"],font=ctk.CTkFont(size=18,weight="bold"));self.cursor_overlay_preview.pack(fill="both",expand=True)'''
if old not in chunk:raise SystemExit('v3.20.13: cursor overlay icon anchor')
chunk=chunk.replace(old,new,1)
anchor2='''        self._cursor_overlay_refresh_ui()'''
if anchor2 in chunk:chunk=chunk.replace(anchor2,anchor2+'''\n        self.after(40,self._cursor_overlay_preview_refresh)''',1)
s=s[:a]+chunk+s[b:]

a,b=method_span(s,'ModernConfigApp','_cursor_overlay_pick');chunk=s[a:b]
needle='''self.cursor_overlay_path=dst;self.salvar_config_app();self._play_ui_sound('select',0);self._cursor_overlay_refresh_ui()'''
if needle not in chunk:raise SystemExit('v3.20.13: cursor pick anchor')
chunk=chunk.replace(needle,needle+''';self._cursor_overlay_preview_refresh()''',1)
s=s[:a]+chunk+s[b:]

checks=(
    'APP_VERSION = "3.20.13"','"VOID DRIVE"','"LAST ROUND"','"bpm":185',
    'def _cursor_overlay_native_ani_frames','invalid RIFF/ACON ANI','b\'anih\'',
    "low==b'rate'","low in (b'seq '",'def _cursor_overlay_preview_refresh',
    'def _lazy_build_page_audio(self):','18 músicas originais',
)
for x in checks:
    if x not in s:raise SystemExit('v3.20.13: missing '+x)
if s.count('"folder":')<18:raise SystemExit('v3.20.13: expected 18 audio folders')
if 'RedrawWindow(' in s:raise SystemExit('v3.20.13: unsafe repaint returned')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.13 robust ANI + 18-audio-identity patch')
