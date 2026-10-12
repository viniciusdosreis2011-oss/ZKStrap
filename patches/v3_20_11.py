from pathlib import Path
import ast, os, re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def lines_pos(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos


def method_span(text,cls_name,name):
    # Fast lexical method locator. All patched methods are regular 4-space class methods;
    # avoiding a full AST parse for every edit makes this patch apply in seconds.
    pat=re.compile(r'(?m)^    (?:async\s+)?def\s+'+re.escape(name)+r'\s*\(')
    hits=list(pat.finditer(text))
    if len(hits)!=1:
        raise SystemExit(f'v3.20.11: expected one {cls_name}.{name}, found {len(hits)}')
    a=hits[0].start()
    nxt=re.search(r'(?m)^(?:    @|    (?:async\s+)?def\s+\w+\s*\(|class\s+\w+\b|def\s+\w+\s*\()',text[hits[0].end():])
    b=(hits[0].end()+nxt.start()) if nxt else len(text)
    return None,a,b


def replace_method(cls_name,name,new_src):
    global s
    _,a,b=method_span(s,cls_name,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def insert_before_method(cls_name,name,src):
    global s
    _,a,_=method_span(s,cls_name,name)
    s=s[:a]+src.rstrip()+"\n\n"+s[a:]


if 'APP_VERSION = "3.20.10"' not in s: raise SystemExit('v3.20.11: expected v3.20.10 base')
s=s.replace('APP_VERSION = "3.20.10"','APP_VERSION = "3.20.11"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Roblox Cursor Overlay + Audio Refresh + UX Density"',s,count=1)
if n!=1: raise SystemExit('v3.20.11: timestamp')

# -----------------------------------------------------------------------------
# AUDIO ENGINE: no immediate repeated SFX variant + minimum 3 minute music session.
# The bundled packs have two ~26s ambient stems. Rather than looping a single stem
# every 26s, build a lightweight temporary session from half-stems and crossfades.
# This keeps the package small while every playback cycle is >= 195 seconds.
# -----------------------------------------------------------------------------
old='''        self._scaled_music_temp=None
        self._scaled_sfx_cache={}'''
new='''        self._scaled_music_temp=None
        self._scaled_sfx_cache={}
        self._last_path_by_name={}
        self._long_music_temp=None
        self._long_music_key=None'''
if old not in s: raise SystemExit('v3.20.11: sound manager init anchor')
s=s.replace(old,new,1)

replace_method('ZKSoundManager','path',r'''    def path(self, name):
        paths=self.paths(name)
        if not paths:return ""
        last=str(getattr(self,"_last_path_by_name",{}).get(name,"") or "")
        choices=[p for p in paths if p!=last] if len(paths)>1 else list(paths)
        pick=random.choice(choices or paths)
        try:self._last_path_by_name[name]=pick
        except Exception:pass
        return pick
''')

insert_before_method('ZKSoundManager','_scaled_music_path',r'''    def _long_music_path(self, minimum_seconds=195.0):
        """Build one evolving ambient session (>=3 min) from the pack stems.

        Source stems remain untouched. The session is assembled in TEMP using
        shuffled half-stems and short PCM crossfades, so the exact same 26s WAV
        never hard-loops back-to-back.
        """
        try:
            import wave, array
            sources=[p for p in self.paths("ambient") if os.path.isfile(p) and "ambient_start" not in os.path.basename(p).lower()]
            if not sources:return ""
            key=tuple((p,os.path.getsize(p),int(os.path.getmtime(p))) for p in sources)
            cached=str(getattr(self,"_long_music_temp","") or "")
            if key==getattr(self,"_long_music_key",None) and cached and os.path.isfile(cached):return cached

            params=None; chunks=[]
            for source_index,p in enumerate(sources):
                try:
                    with wave.open(p,'rb') as w:
                        cur=(w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())
                        if cur[1]!=2 or cur[3]!='NONE':continue
                        if params is None:params=cur
                        if cur!=params:continue
                        frames=w.readframes(w.getnframes());frame_bytes=cur[0]*cur[1]
                        total_frames=len(frames)//frame_bytes
                        if total_frames<cur[2]*4:continue
                        cut=(total_frames//2)*frame_bytes
                        a=frames[:cut];b=frames[cut:]
                        if a:chunks.append((source_index,0,a))
                        if b:chunks.append((source_index,1,b))
                except Exception:continue
            if not params or not chunks:return self.path("ambient")

            channels,width,rate,_=params;frame_bytes=channels*width
            target_frames=max(int(float(minimum_seconds)*rate),rate*181)
            fade_frames=max(1,int(rate*.72));fade_bytes=fade_frames*frame_bytes
            rng=random.Random((time.time_ns() ^ os.getpid() ^ hash(self.pack)) & 0xFFFFFFFFFFFFFFFF)
            output=bytearray();last_id=None;last_source=None

            def append_chunk(raw):
                nonlocal output
                if not output:
                    output.extend(raw);return
                n=min(fade_bytes,len(output),len(raw));n-=n%frame_bytes
                if n<=0:output.extend(raw);return
                tail_start=len(output)-n
                aa=array.array('h');bb=array.array('h')
                aa.frombytes(bytes(output[tail_start:]));bb.frombytes(raw[:n])
                sample_frames=max(1,n//frame_bytes)
                for i in range(min(len(aa),len(bb))):
                    frame=i//channels;alpha=frame/max(1,sample_frames-1)
                    aa[i]=max(-32768,min(32767,int(aa[i]*(1.0-alpha)+bb[i]*alpha)))
                output[tail_start:]=aa.tobytes();output.extend(raw[n:])

            safety=0
            while len(output)//frame_bytes < target_frames and safety<128:
                safety+=1
                pool=[c for c in chunks if (c[0],c[1])!=last_id and (len(chunks)<=2 or c[0]!=last_source)]
                if not pool:pool=[c for c in chunks if (c[0],c[1])!=last_id] or chunks
                chosen=rng.choice(pool);append_chunk(chosen[2]);last_source=chosen[0];last_id=(chosen[0],chosen[1])

            if len(output)//frame_bytes < rate*181:return self.path("ambient")
            dst=os.path.join(tempfile.gettempdir(),f"zkstrap_longmix_{os.getpid()}_{uuid.uuid4().hex}.wav")
            with wave.open(dst,'wb') as out:
                out.setnchannels(channels);out.setsampwidth(width);out.setframerate(rate);out.writeframes(bytes(output))
            old=str(getattr(self,"_long_music_temp","") or "");self._long_music_temp=dst;self._long_music_key=key
            if old and old!=dst and os.path.isfile(old):
                try:os.remove(old)
                except Exception:pass
            _startup_log(f"AUDIO: long session built pack={self.pack!r} seconds={len(output)/frame_bytes/rate:.1f}")
            return dst
        except Exception as exc:
            _startup_log("AUDIO: long session failed "+repr(exc));return self.path("ambient")
''')

replace_method('ZKSoundManager','start_music',r'''    def start_music(self, force_restart=False):
        if not (self.enabled and self.music_enabled) or os.name != "nt": return False
        path=self._long_music_path(195.0)
        if not path or not os.path.isfile(path):
            _startup_log(f"AUDIO: ambient missing for pack {self.pack!r}"); return False
        if float(getattr(self,"music_volume",0.22)) <= 0.001:
            self.stop_music(); return False
        if force_restart:self.stop_music()
        path=self._scaled_music_path(path)
        if self._mci_active:return True
        try:
            if self._music_proc is not None and self._music_proc.poll() is None:return True
        except Exception:self._music_proc=None
        if self._start_music_mci(path):return True
        return self._start_music_helper(path)
''')

replace_method('ZKSoundManager','shutdown',r'''    def shutdown(self):
        self.stop_music()
        for temp_path in list(getattr(self,"_scaled_sfx_cache",{}).values()):
            try:
                if temp_path and os.path.isfile(temp_path):os.remove(temp_path)
            except Exception:pass
        self._scaled_sfx_cache={}
        long_temp=str(getattr(self,"_long_music_temp","") or "")
        try:
            if long_temp and os.path.isfile(long_temp):os.remove(long_temp)
        except Exception:pass
        self._long_music_temp=None;self._long_music_key=None
''')

# -----------------------------------------------------------------------------
# Standalone Roblox cursor overlay helper. It runs in a separate process so the
# overlay keeps its low-latency position loop even while the main ZKStrap is
# minimized. It never injects into Roblox; it is a click-through topmost window.
# -----------------------------------------------------------------------------
overlay_global=r'''
def _cursor_overlay_restore_state_file(state_path):
    try:
        if not state_path or not os.path.isfile(state_path):return
        with open(state_path,'r',encoding='utf-8') as f:state=json.load(f)
        for item in list((state or {}).get('entries',[])):
            dst=str(item.get('dst','') or '');backup=str(item.get('backup','') or '');existed=bool(item.get('existed',False))
            if not dst:continue
            try:
                if existed and backup and os.path.isfile(backup):
                    os.makedirs(os.path.dirname(dst),exist_ok=True);shutil.copy2(backup,dst)
                elif not existed and os.path.isfile(dst):os.remove(dst)
            except Exception:pass
        try:os.remove(state_path)
        except Exception:pass
    except Exception:pass


def _cursor_overlay_decode_file(path,target_visible=24):
    from PIL import Image,ImageSequence
    import io,struct
    path=str(path or '');ext=os.path.splitext(path)[1].lower();frames=[];delays=[];hotspots=[]
    def cur_hotspot(blob,im):
        try:
            if len(blob)>=22 and blob[:2]==b'\x00\x00' and blob[2:4]==b'\x02\x00':
                return tuple(int(v) for v in struct.unpack_from('<HH',blob,10))
        except Exception:pass
        return (0,0)
    if ext=='.ani':
        data=Path(path).read_bytes();rates=[]
        if data[:4]!=b'RIFF' or data[8:12]!=b'ACON':raise ValueError('invalid ANI')
        pos=12
        while pos+8<=len(data):
            cid=data[pos:pos+4];size=struct.unpack_from('<I',data,pos+4)[0];payload=data[pos+8:pos+8+size]
            if cid==b'rate' and len(payload)>=4:
                rates=[max(1,int(v))*1000//60 for v in struct.unpack('<'+'I'*(len(payload)//4),payload[:(len(payload)//4)*4])]
            pos+=8+size+(size&1)
        pos=0
        while True:
            i=data.find(b'icon',pos)
            if i<0 or i+8>len(data):break
            size=struct.unpack_from('<I',data,i+4)[0];payload=data[i+8:i+8+size];pos=i+8+size+(size&1)
            try:
                im=Image.open(io.BytesIO(payload)).convert('RGBA');frames.append(im.copy());hotspots.append(cur_hotspot(payload,im))
            except Exception:pass
        delays=[rates[i] if i<len(rates) else 85 for i in range(len(frames))]
    elif ext=='.gif':
        im=Image.open(path)
        for fr in ImageSequence.Iterator(im):
            frames.append(fr.convert('RGBA').copy());delays.append(max(20,int(fr.info.get('duration',70) or 70)));hotspots.append((0,0))
    else:
        blob=Path(path).read_bytes();im=Image.open(io.BytesIO(blob)).convert('RGBA');frames=[im.copy()];delays=[250];hotspots=[cur_hotspot(blob,im)]
    if not frames:raise ValueError('no cursor frames')
    target_visible=max(8,min(96,int(target_visible or 24)));prepared=[];scaled_hot=[]
    for idx,im in enumerate(frames[:96]):
        bbox=im.getchannel('A').getbbox() or (0,0,im.width,im.height);vw=max(1,bbox[2]-bbox[0]);vh=max(1,bbox[3]-bbox[1]);scale=target_visible/max(vw,vh)
        nw=max(1,int(round(im.width*scale)));nh=max(1,int(round(im.height*scale)))
        if (nw,nh)!=im.size:im=im.resize((nw,nh),Image.Resampling.LANCZOS)
        hx,hy=hotspots[idx] if idx<len(hotspots) else (0,0);prepared.append(im);scaled_hot.append((max(0,int(round(hx*scale))),max(0,int(round(hy*scale)))))
    return prepared,delays[:len(prepared)],scaled_hot


def _run_cursor_overlay_helper():
    """Click-through animated cursor visible only while Roblox is foreground."""
    path=_audio_cli_arg('--cursor-file','');stop_file=_audio_cli_arg('--cursor-stop','');state_path=_audio_cli_arg('--cursor-state','');parent=_audio_cli_arg('--parent-pid','0');size=_audio_cli_arg('--cursor-size','24')
    try:parent=int(parent or 0)
    except Exception:parent=0
    try:size=int(size or 24)
    except Exception:size=24
    if os.name!='nt' or not path or not os.path.isfile(path):
        _cursor_overlay_restore_state_file(state_path);raise SystemExit(0)
    win=None
    try:
        from PIL import ImageTk
        frames,delays,hotspots=_cursor_overlay_decode_file(path,size)
        win=tk.Tk();win.withdraw();win.overrideredirect(True);win.configure(bg='#010203')
        try:win.wm_attributes('-transparentcolor','#010203');win.attributes('-topmost',True)
        except Exception:pass
        photos=[ImageTk.PhotoImage(fr,master=win) for fr in frames]
        maxw=max(fr.width for fr in frames);maxh=max(fr.height for fr in frames)
        lab=tk.Label(win,bg='#010203',bd=0,highlightthickness=0);lab.place(x=0,y=0,width=maxw,height=maxh)
        win.geometry(f'{maxw}x{maxh}-10000-10000');win.update_idletasks();win.deiconify();win.update_idletasks()
        hwnd=int(win.winfo_id());user32=ctypes.windll.user32
        GWL_EXSTYLE=-20;WS_EX_LAYERED=0x00080000;WS_EX_TRANSPARENT=0x20;WS_EX_TOOLWINDOW=0x80;WS_EX_NOACTIVATE=0x08000000
        try:
            getter=getattr(user32,'GetWindowLongPtrW',user32.GetWindowLongW);setter=getattr(user32,'SetWindowLongPtrW',user32.SetWindowLongW)
            ex=int(getter(hwnd,GWL_EXSTYLE));setter(hwnd,GWL_EXSTYLE,ex|WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE)
        except Exception:pass
        SW_HIDE=0;HWND_TOPMOST=-1;SWP_NOSIZE=0x0001;SWP_NOACTIVATE=0x0010;SWP_SHOWWINDOW=0x0040
        user32.ShowWindow(hwnd,SW_HIDE)
        shared={'hotspot':hotspots[0] if hotspots else (0,0),'alive':True,'shown':False}
        try:ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:pass

        def is_roblox_foreground():
            fg=user32.GetForegroundWindow()
            if not fg:return (False,0,None)
            pid=wintypes.DWORD();user32.GetWindowThreadProcessId(fg,ctypes.byref(pid))
            try:name=str(psutil.Process(int(pid.value)).name() or '').lower()
            except Exception:name=''
            active=('roblox' in name and 'studio' not in name)
            return active,int(fg),pid.value

        def mover():
            point=wintypes.POINT();rect=wintypes.RECT()
            while shared['alive'] and (not stop_file or not os.path.exists(stop_file)) and (not parent or _windows_pid_alive(parent)):
                try:
                    active,fg,_=is_roblox_foreground()
                    if active and user32.GetCursorPos(ctypes.byref(point)):
                        inside=True
                        if user32.GetWindowRect(fg,ctypes.byref(rect)):
                            inside=(rect.left<=point.x<rect.right and rect.top<=point.y<rect.bottom)
                        if inside:
                            hx,hy=shared['hotspot'];user32.SetWindowPos(hwnd,HWND_TOPMOST,int(point.x-hx),int(point.y-hy),0,0,SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW);shared['shown']=True
                        elif shared['shown']:
                            user32.ShowWindow(hwnd,SW_HIDE);shared['shown']=False
                    elif shared['shown']:
                        user32.ShowWindow(hwnd,SW_HIDE);shared['shown']=False
                except Exception:pass
                time.sleep(.002)
            shared['alive']=False
            try:win.after(0,win.destroy)
            except Exception:pass
        threading.Thread(target=mover,name='ZKCursorOverlayPosition',daemon=True).start()

        def frame_tick(i=0):
            if not shared['alive']:return
            try:
                j=i%len(photos);lab.configure(image=photos[j]);lab.image=photos[j];shared['hotspot']=hotspots[j] if j<len(hotspots) else (0,0)
                delay=max(20,min(500,int(delays[j] if j<len(delays) else 85)));win.after(delay,lambda:frame_tick(i+1))
            except Exception:pass
        frame_tick();win.mainloop()
    except Exception as exc:
        _startup_log('CURSOR OVERLAY helper: '+repr(exc))
    finally:
        try:ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:pass
        _cursor_overlay_restore_state_file(state_path)
        try:
            if stop_file and os.path.isfile(stop_file):os.remove(stop_file)
        except Exception:pass
    raise SystemExit(0)

'''
anchor='class ZKSoundManager:'
if anchor not in s:raise SystemExit('v3.20.11: ZKSoundManager anchor')
s=s.replace(anchor,overlay_global+anchor,1)

# -----------------------------------------------------------------------------
# Config/state additions.
# -----------------------------------------------------------------------------
old='''        self._sound_manager = ZKSoundManager(self, self.sounds_enabled, self.sound_pack, self.music_enabled, self.sfx_enabled, self.music_volume, self.sfx_volume)
        self._last_hover_sound = 0.0'''
new='''        self._sound_manager = ZKSoundManager(self, self.sounds_enabled, self.sound_pack, self.music_enabled, self.sfx_enabled, self.music_volume, self.sfx_volume)
        self.first_run_intro_audio = bool(self.config_data.get("first_run_intro_audio", True))
        self._first_run_intro_active = False
        self._last_hover_sound = 0.0'''
if old not in s:raise SystemExit('v3.20.11: sound app init anchor')
s=s.replace(old,new,1)

old='''        self.cursor_anchor_mode = str(self.config_data.get("cursor_anchor_mode", "Ponta no centro") or "Ponta no centro")'''
new='''        self.cursor_anchor_mode = str(self.config_data.get("cursor_anchor_mode", "Ponta no centro") or "Ponta no centro")
        self.cursor_overlay_enabled = bool(self.config_data.get("cursor_overlay_enabled", False))
        self.cursor_overlay_path = str(self.config_data.get("cursor_overlay_path", self.config_data.get("ani_preview_path", "")) or "")
        self._cursor_overlay_proc = None
        self._cursor_overlay_stop_file = ""
        self._cursor_overlay_state_path = ""'''
if old not in s:raise SystemExit('v3.20.11: cursor init anchor')
s=s.replace(old,new,1)

old='''                "sfx_volume": float(getattr(self, "sfx_volume", 1.0)),
                "spotify_web_volume_optin": bool(getattr(self, "spotify_web_volume_optin", False)),'''
new='''                "sfx_volume": float(getattr(self, "sfx_volume", 1.0)),
                "first_run_intro_audio": bool(getattr(self, "first_run_intro_audio", True)),
                "cursor_overlay_enabled": bool(getattr(self, "cursor_overlay_enabled", False)),
                "cursor_overlay_path": str(getattr(self, "cursor_overlay_path", "")),
                "spotify_web_volume_optin": bool(getattr(self, "spotify_web_volume_optin", False)),'''
if old not in s:raise SystemExit('v3.20.11: config save anchor')
s=s.replace(old,new,1)

old='''        self.after(1050, self._start_ambient_if_enabled)
        self.after(1800, self._secret_music_tick)'''
new='''        self.after(1050, self._start_ambient_if_enabled)
        self.after(2600, self._cursor_overlay_autostart)
        self.after(1800, self._secret_music_tick)'''
if old not in s:raise SystemExit('v3.20.11: startup schedule anchor')
s=s.replace(old,new,1)

# -----------------------------------------------------------------------------
# First-run soundscape.
# -----------------------------------------------------------------------------
insert_before_method('ModernConfigApp','_play_ui_sound',r'''    def _first_run_audio_start(self):
        try:
            if bool(getattr(self,"sound_prompted",False)):
                if bool(getattr(self,"sounds_enabled",False)):self._start_ambient_if_enabled()
                return
            if not bool(getattr(self,"first_run_intro_audio",True)):return
            mgr=getattr(self,"_sound_manager",None)
            if mgr is None:return
            if bool(getattr(self,"_first_run_intro_active",False)):return
            mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK);mgr.enabled=True;mgr.music_enabled=True;mgr.sfx_enabled=True
            mgr.music_volume=min(.18,max(.08,float(getattr(self,"music_volume",.22) or .22)))
            mgr.start_music(force_restart=True);self._first_run_intro_active=True
        except Exception as exc:_startup_log('FIRST RUN AUDIO start: '+repr(exc))

    def _first_run_audio_event(self,name="select"):
        try:
            if bool(getattr(self,"sound_prompted",False)):
                return self._play_ui_sound(name,0)
            if not bool(getattr(self,"first_run_intro_audio",True)):return
            self._first_run_audio_start();mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:mgr.play(name,throttle=0)
        except Exception:pass

    def _first_run_audio_toggle(self):
        self.first_run_intro_audio=not bool(getattr(self,"first_run_intro_audio",True))
        try:self.salvar_config_app()
        except Exception:pass
        mgr=getattr(self,"_sound_manager",None)
        if self.first_run_intro_audio:
            self._first_run_intro_active=False;self._first_run_audio_start();self._first_run_audio_event('enable')
        else:
            self._first_run_intro_active=False
            if mgr is not None and not bool(getattr(self,"sounds_enabled",False)):mgr.stop_music();mgr.enabled=False
        btn=getattr(self,'_first_run_audio_btn',None)
        try:
            if btn is not None and btn.winfo_exists():btn.configure(text=("♫  INTRO ON" if self.first_run_intro_audio else "♫  INTRO OFF"))
        except Exception:pass
''')

_,a,b=method_span(s,'ModernConfigApp','_sound_choice');chunk=s[a:b]
needle='''        self.sound_prompted=True
        self.sounds_enabled=bool(enabled)'''
if needle not in chunk:raise SystemExit('v3.20.11: sound choice anchor')
chunk=chunk.replace(needle,'''        self.sound_prompted=True
        self._first_run_intro_active=False
        self.sounds_enabled=bool(enabled)''',1);s=s[:a]+chunk+s[b:]

# Language screen: start intro music, add a visible intro mute button, SFX on selection.
_,a,b=method_span(s,'ModernConfigApp','_maybe_show_first_run_language');chunk=s[a:b]
needle='''        t=TEMAS[self.tema_atual]
        rev=6'''
if needle not in chunk:raise SystemExit('v3.20.11: language start anchor')
chunk=chunk.replace(needle,'''        t=TEMAS[self.tema_atual]
        self._first_run_audio_start()
        rev=6''',1)
needle='''        def choose(code):
            self.idioma=code'''
if needle not in chunk:raise SystemExit('v3.20.11: language choose anchor')
chunk=chunk.replace(needle,'''        def choose(code):
            self._first_run_audio_event("select")
            self.idioma=code''',1)
needle='''        ctk.CTkLabel(right,text="ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(anchor="e",padx=8,pady=(8,2))'''
if needle not in chunk:raise SystemExit('v3.20.11: language footer anchor')
chunk=chunk.replace(needle,'''        footer=ctk.CTkFrame(right,fg_color="transparent");footer.pack(fill="x",padx=8,pady=(8,2))
        ctk.CTkLabel(footer,text="ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(side="right")
        self._first_run_audio_btn=ctk.CTkButton(footer,text=("♫  INTRO ON" if self.first_run_intro_audio else "♫  INTRO OFF"),width=112,height=28,corner_radius=9,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],command=self._first_run_audio_toggle,font=ctk.CTkFont(family="Consolas",size=7,weight="bold"));self._first_run_audio_btn.pack(side="left")''',1)
s=s[:a]+chunk+s[b:]

# Roblox onboarding: visually distinct search and confirmation states.
replace_method('ModernConfigApp','_abrir_onboarding_username_ui_3205',r'''    def _abrir_onboarding_username_ui_3205(self, primeiro_acesso=True):
        t=TEMAS[self.tema_atual];L=self._L
        if primeiro_acesso:self._first_run_ensure_maximized()
        self._first_run_audio_start();self._first_run_audio_event('open')
        old=getattr(self,"_tutorial_panel",None)
        try:
            if old is not None:old.destroy()
        except Exception:pass
        cover=self._zk_blur_cover(self,radius=13,brightness=.43);self._tutorial_panel=cover
        panel=ctk.CTkFrame(cover,width=1100,height=625,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.62));panel.place(relx=.5,rely=.5,anchor="center");panel.pack_propagate(False)
        ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        body=ctk.CTkFrame(panel,fg_color="transparent");body.pack(fill="both",expand=True,padx=22,pady=22)

        left=ctk.CTkFrame(body,width=350,fg_color=self._mix_hex(t["card"],t["accent"],.07),corner_radius=20,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.28));left.pack(side="left",fill="y",padx=(0,18));left.pack_propagate(False)
        ctk.CTkLabel(left,text="02 / 03   //   ROBLOX LINK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=24,pady=(25,15))
        avatar_shell=ctk.CTkFrame(left,width=154,height=154,corner_radius=77,fg_color=t["card_active"],border_width=2,border_color=t["accent"]);avatar_shell.pack(pady=(8,14));avatar_shell.pack_propagate(False)
        avatar=ctk.CTkLabel(avatar_shell,text="@",text_color=t["accent"],font=ctk.CTkFont(size=49,weight="bold"));avatar.place(relx=.5,rely=.5,anchor="center")
        profile_name=ctk.CTkLabel(left,text=L("Seu perfil aparece aqui","Your profile appears here","Tu perfil aparece aquí","你的资料会显示在这里","Votre profil apparaît ici"),text_color=t["text"],font=ctk.CTkFont(size=15,weight="bold"));profile_name.pack(padx=20,pady=(3,4))
        profile_user=ctk.CTkLabel(left,text="@username",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=10));profile_user.pack()
        confirm_badge=ctk.CTkLabel(left,text=L("AGUARDANDO BUSCA","WAITING FOR SEARCH","ESPERANDO BÚSQUEDA","等待搜索","EN ATTENTE DE RECHERCHE"),height=27,corner_radius=8,fg_color=t["card_active"],text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));confirm_badge.pack(padx=22,pady=(16,8),fill="x")
        ctk.CTkLabel(left,text=L("Só usamos o perfil público. Sem senha, cookie ou e-mail.","Public profile only. No password, cookie or email.","Solo perfil público. Sin contraseña, cookie ni correo.","仅使用公开资料，不需要密码、Cookie 或邮箱。","Profil public uniquement. Aucun mot de passe, cookie ou e-mail."),wraplength=285,justify="center",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(padx=24,pady=(8,8))

        right=ctk.CTkFrame(body,fg_color="transparent");right.pack(side="left",fill="both",expand=True)
        search_state=ctk.CTkFrame(right,fg_color="transparent");search_state.pack(fill="both",expand=True)
        ctk.CTkLabel(search_state,text=L("Encontre sua conta do Roblox","Find your Roblox account","Encuentra tu cuenta de Roblox","找到你的 Roblox 账号","Trouvez votre compte Roblox"),text_color=t["text"],font=ctk.CTkFont(size=27,weight="bold"),anchor="w").pack(fill="x",padx=7,pady=(14,4))
        ctk.CTkLabel(search_state,text=L("Digite seu @username. Primeiro mostramos a conta; você decide se é ela antes de vincular.","Enter your @username. We show the account first; you decide if it is correct before linking.","Escribe tu @usuario. Primero mostramos la cuenta; tú confirmas antes de vincular.","输入 @用户名。我们会先显示账号，由你确认后再绑定。","Entrez votre @pseudo. Le compte est d’abord affiché, puis vous confirmez avant de le lier."),wraplength=625,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(fill="x",padx=7,pady=(2,18))
        entry=ctk.CTkEntry(search_state,placeholder_text="@username",height=57,corner_radius=14,border_width=2,border_color=t["card_active"],font=ctk.CTkFont(size=14,weight="bold"));entry.pack(fill="x",padx=7)
        status=ctk.CTkLabel(search_state,text=L("Digite o username e pressione Enter.","Enter the username and press Enter.","Escribe el usuario y presiona Enter.","输入用户名并按 Enter。","Entrez le pseudo puis appuyez sur Entrée."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w");status.pack(fill="x",padx=8,pady=(8,12))
        search_btn=ctk.CTkButton(search_state,text=L("BUSCAR PERFIL  →","SEARCH PROFILE  →","BUSCAR PERFIL  →","搜索资料  →","RECHERCHER LE PROFIL  →"),height=48,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=10,weight="bold"));search_btn.pack(fill="x",padx=7,pady=(4,7))
        fallback=ctk.CTkButton(search_state,text=L("CONTINUAR SÓ COM O NICK","CONTINUE WITH NICK ONLY","CONTINUAR SOLO CON EL NICK","仅使用昵称继续","CONTINUER AVEC LE PSEUDO"),height=38,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"));fallback.pack(fill="x",padx=7)

        confirm_state=ctk.CTkFrame(right,fg_color=self._mix_hex(t["card"],t["accent"],.055),corner_radius=20,border_width=2,border_color=t["accent"])
        ctop=ctk.CTkFrame(confirm_state,fg_color="transparent");ctop.pack(fill="x",padx=25,pady=(23,6));ctk.CTkLabel(ctop,text="?",width=48,height=48,corner_radius=15,fg_color=t["accent"],text_color="#050505",font=ctk.CTkFont(size=25,weight="bold")).pack(side="left");ct=ctk.CTkFrame(ctop,fg_color="transparent");ct.pack(side="left",fill="x",expand=True,padx=(14,0));confirm_title=ctk.CTkLabel(ct,text=L("ESSA É SUA CONTA?","IS THIS YOUR ACCOUNT?","¿ESTA ES TU CUENTA?","这是你的账号吗？","EST-CE VOTRE COMPTE ?"),text_color=t["text"],font=ctk.CTkFont(size=25,weight="bold"),anchor="w");confirm_title.pack(fill="x");ctk.CTkLabel(ct,text=L("Confere o avatar, nome e @username antes de continuar.","Check the avatar, name and @username before continuing.","Comprueba avatar, nombre y @usuario antes de continuar.","继续前请核对头像、名称和 @用户名。","Vérifiez l’avatar, le nom et le @pseudo avant de continuer."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w").pack(fill="x")
        identity=ctk.CTkFrame(confirm_state,fg_color=t["card_active"],corner_radius=14,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.45));identity.pack(fill="x",padx=25,pady=(15,17));ctk.CTkLabel(identity,text=L("PERFIL ENCONTRADO","PROFILE FOUND","PERFIL ENCONTRADO","已找到资料","PROFIL TROUVÉ"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(fill="x",padx=14,pady=(10,2));confirm_identity=ctk.CTkLabel(identity,text="@username",text_color=t["text"],font=ctk.CTkFont(size=17,weight="bold"),anchor="w");confirm_identity.pack(fill="x",padx=14,pady=(1,11))
        crow=ctk.CTkFrame(confirm_state,fg_color="transparent");crow.pack(fill="x",padx=25,pady=(4,20));yes_btn=ctk.CTkButton(crow,text=L("SIM, É MINHA CONTA  ✓","YES, THAT'S MY ACCOUNT  ✓","SÍ, ES MI CUENTA  ✓","是，这是我的账号  ✓","OUI, C'EST MON COMPTE  ✓"),height=50,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=10,weight="bold"));yes_btn.pack(side="left",fill="x",expand=True,padx=(0,6));no_btn=ctk.CTkButton(crow,text=L("NÃO — PESQUISAR OUTRA","NO — SEARCH AGAIN","NO — BUSCAR OTRA","不是 — 重新搜索","NON — RECHERCHER"),height=50,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],font=ctk.CTkFont(size=9,weight="bold"));no_btn.pack(side="left",fill="x",expand=True,padx=(6,0))

        pending={"profile":None,"avatar":None}
        def begin_tutorial():
            try:cover.destroy()
            except Exception:pass
            self._tutorial_panel=None;self._first_run_active_stage="";self.after(20,lambda:self._abrir_tutorial_ui_3205(primeiro_acesso=bool(primeiro_acesso)))
        def set_avatar(data=None):
            if not data:
                try:avatar.configure(image=None,text="@")
                except Exception:pass
                return
            try:
                import io
                from PIL import Image
                im=Image.open(io.BytesIO(data)).convert('RGBA');im.thumbnail((140,140),Image.Resampling.LANCZOS);self._onboarding_avatar_img=ctk.CTkImage(light_image=im,dark_image=im,size=(140,140));avatar.configure(image=self._onboarding_avatar_img,text='')
            except Exception:pass
        def refresh_top_profile():
            try:self._render_profile_button()
            except Exception:pass
            try:self._refresh_home_profile_card()
            except Exception:pass
        def show_search(clear=True):
            pending["profile"]=None;pending["avatar"]=None;self._onboarding_profile_busy=False
            confirm_state.pack_forget();search_state.pack(fill="both",expand=True)
            try:
                entry.configure(state="normal");search_btn.configure(state="normal",text=L("BUSCAR PERFIL  →","SEARCH PROFILE  →","BUSCAR PERFIL  →","搜索资料  →","RECHERCHER LE PROFIL  →"));fallback.configure(state="normal")
                if clear:entry.delete(0,"end")
                profile_name.configure(text=L("Seu perfil aparece aqui","Your profile appears here","Tu perfil aparece aquí","你的资料会显示在这里","Votre profil apparaît ici"));profile_user.configure(text="@username");set_avatar(None);confirm_badge.configure(text=L("AGUARDANDO BUSCA","WAITING FOR SEARCH","ESPERANDO BÚSQUEDA","等待搜索","EN ATTENTE DE RECHERCHE"),text_color=t.get("muted","gray"));status.configure(text=L("Digite outro username e pesquise novamente.","Enter another username and search again.","Escribe otro usuario y vuelve a buscar.","输入另一个用户名并重新搜索。","Entrez un autre pseudo et recommencez."),text_color=t.get("muted","gray"));entry.focus_force()
            except Exception:pass
        def confirm_profile():
            profile=pending.get('profile')
            if not profile:return
            self._first_run_audio_event('success')
            try:
                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":str(profile.get("avatar_url","") or "")}
                self._mark_roblox_onboarding_done(self.linked_profile['name']);refresh_top_profile();self.after(60,refresh_top_profile)
                confirm_title.configure(text=L("CONTA VINCULADA  ✓","ACCOUNT LINKED  ✓","CUENTA VINCULADA  ✓","账号已绑定  ✓","COMPTE LIÉ  ✓"),text_color=t["accent"]);confirm_identity.configure(text='@'+self.linked_profile['name']);yes_btn.configure(state='disabled',text=L("PRONTO  ✓","DONE  ✓","LISTO  ✓","完成  ✓","PRÊT  ✓"));no_btn.configure(state='disabled');confirm_badge.configure(text=L("CONFIRMADO  ✓","CONFIRMED  ✓","CONFIRMADO  ✓","已确认  ✓","CONFIRMÉ  ✓"),text_color=t["accent"]);self.after(430,begin_tutorial)
            except Exception as exc:confirm_title.configure(text=str(exc),text_color="#FF6B7A")
        def link_result(profile,error='',avatar_bytes=None):
            self._onboarding_profile_busy=False;search_btn.configure(state='normal')
            if error:
                status.configure(text=error,text_color="#FF6B7A");search_btn.configure(text=L("TENTAR NOVAMENTE","TRY AGAIN","INTENTAR DE NUEVO","重试","RÉESSAYER"));fallback.configure(state='normal');return
            pending['profile']=profile;pending['avatar']=avatar_bytes;self._first_run_audio_event('notify')
            profile_name.configure(text=str(profile.get('displayName') or profile.get('name') or ''));profile_user.configure(text='@'+str(profile.get('name') or ''));set_avatar(avatar_bytes);confirm_badge.configure(text=L("PERFIL ENCONTRADO","PROFILE FOUND","PERFIL ENCONTRADO","已找到资料","PROFIL TROUVÉ"),text_color=t["accent"]);confirm_identity.configure(text=f"{profile.get('displayName') or profile.get('name')}   //   @{profile.get('name')}")
            search_state.pack_forget();confirm_state.pack(fill='both',expand=True)
        def link_worker(username):
            profile=None;err='';avatar_bytes=None
            try:
                headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":f"ZKStrap/{APP_VERSION}"};r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[username],"excludeBannedUsers":False},headers=headers,timeout=(4,10))
                if r.ok:
                    data=(r.json() or {}).get('data',[])
                    if data:
                        p=data[0];profile={"id":int(p.get('id',0)),"name":p.get('name') or username,"displayName":p.get('displayName') or p.get('name') or username}
                if profile:
                    tr=requests.get("https://thumbnails.roblox.com/v1/users/avatar-headshot",params={"userIds":profile['id'],"size":"150x150","format":"Png","isCircular":"false"},timeout=(4,8))
                    if tr.ok:
                        td=(tr.json() or {}).get('data',[])
                        if td and td[0].get('imageUrl'):
                            profile['avatar_url']=td[0]['imageUrl'];ir=requests.get(profile['avatar_url'],timeout=(4,8));avatar_bytes=ir.content if ir.ok else None
                if profile is None:err=L("Não achei esse @username. Confira a escrita.","I couldn't find that @username. Check the spelling.","No encontré ese @username. Revisa la escritura.","找不到该 @username，请检查拼写。","@username introuvable. Vérifiez l’orthographe.")
            except Exception:err=L("Roblox não respondeu agora. Tente novamente.","Roblox didn't respond. Try again.","Roblox no respondió. Intenta de nuevo.","Roblox 暂时没有响应，请重试。","Roblox ne répond pas. Réessayez.")
            self.after(0,lambda:link_result(profile,err,avatar_bytes))
        def start_link(event=None):
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Username inválido (3–20 caracteres).","Invalid username (3–20 characters).","Usuario inválido (3–20 caracteres).","用户名无效（3–20 个字符）。","Pseudo invalide (3–20 caractères)."),text_color="#FF6B7A");return
            if bool(getattr(self,'_onboarding_profile_busy',False)):return
            self._first_run_audio_event('search');self._onboarding_profile_busy=True;status.configure(text=L("Procurando perfil público...","Looking up public profile...","Buscando perfil público...","正在查询公开资料...","Recherche du profil public..."),text_color=t["accent"]);search_btn.configure(state='disabled',text=L("PROCURANDO...","SEARCHING...","BUSCANDO...","查询中...","RECHERCHE..."));fallback.configure(state='disabled');threading.Thread(target=link_worker,args=(username,),daemon=True,name='ZKFirstRunRobloxLink').start()
        def continue_nick_only():
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Digite um username válido primeiro.","Enter a valid username first.","Escribe un usuario válido primero.","请先输入有效用户名。","Entrez d’abord un pseudo valide."),text_color="#FF6B7A");return
            self._first_run_audio_event('confirm');self._mark_roblox_onboarding_done(username);begin_tutorial()
        search_btn.configure(command=start_link);fallback.configure(command=continue_nick_only);yes_btn.configure(command=confirm_profile);no_btn.configure(command=lambda:show_search(True));entry.bind('<Return>',start_link);self.after(70,lambda:entry.focus_force())
''')

# Tutorial larger and more visual.
insert_before_method('ModernConfigApp','_abrir_tutorial_ui_3205',r'''    def _ui_compact_copy(self,text,limit=155):
        raw=' '.join(str(text or '').split())
        if len(raw)<=int(limit):return raw
        for sep in ('. ','。','! ','? '):
            pos=raw.find(sep)
            if 24<pos<int(limit):return raw[:pos+len(sep.strip())].strip()
        return raw[:max(1,int(limit)-1)].rstrip()+"…"
''')

replace_method('ModernConfigApp','_abrir_tutorial_ui_3205',r'''    def _abrir_tutorial_ui_3205(self, primeiro_acesso=False):
        if primeiro_acesso:self._first_run_ensure_maximized()
        self._first_run_audio_start();self._first_run_audio_event('open')
        try:self._fechar_busca_universal()
        except Exception:pass
        try:self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception:pass
        self._tutorial_first_run=bool(primeiro_acesso);self._tutorial_replay=not bool(primeiro_acesso);self._tutorial_step_index=0;self._tutorial_max_unlocked=0;self._tutorial_step_ready=True;self._tutorial_preview_token=int(getattr(self,"_tutorial_preview_token",0) or 0)+1;self._tutorial_nav_stash={};self._tutorial_nav_capture()
        steps=self._tutorial_steps()
        if not steps:return
        self._tutorial_apply_real_unlock(0)
        try:self.show_page(str(steps[0][0]),animate=False)
        except Exception:pass
        t=TEMAS[self.tema_atual];L=self._L
        width=min(700,max(610,int(self.winfo_width()*.46)));height=405
        card=ctk.CTkFrame(self,width=width,height=height,fg_color=t.get("panel",t["card"]),corner_radius=23,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.82));card.place(relx=.985,rely=.972,anchor="se");card.pack_propagate(False);card.lift();self._tutorial_panel=card
        ctk.CTkFrame(card,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        shell=ctk.CTkFrame(card,fg_color="transparent");shell.pack(fill="both",expand=True,padx=16,pady=14)
        rail=ctk.CTkFrame(shell,width=104,fg_color=self._mix_hex(t["card"],t["accent"],.07),corner_radius=16,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));rail.pack(side="left",fill="y",padx=(0,14));rail.pack_propagate(False)
        ctk.CTkLabel(rail,text="GUIDE",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(pady=(18,4))
        self._tutorial_big_step=ctk.CTkLabel(rail,text="01",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=35,weight="bold"));self._tutorial_big_step.pack(pady=(4,1))
        self._tutorial_count=ctk.CTkLabel(rail,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));self._tutorial_count.pack()
        ctk.CTkFrame(rail,height=1,fg_color=t["card_active"]).pack(fill="x",padx=14,pady=15)
        self._tutorial_progress_text=ctk.CTkLabel(rail,text="",text_color=t["text"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"));self._tutorial_progress_text.pack()
        self._tutorial_progress=ctk.CTkProgressBar(rail,width=68,height=7,progress_color=t["accent"],fg_color=t["card_active"]);self._tutorial_progress.pack(pady=(8,14))
        self._tutorial_unlocked=ctk.CTkLabel(rail,text="",wraplength=78,justify="center",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7));self._tutorial_unlocked.pack(padx=8)
        main=ctk.CTkFrame(shell,fg_color="transparent");main.pack(side="left",fill="both",expand=True)
        top=ctk.CTkFrame(main,fg_color="transparent");top.pack(fill="x")
        ctk.CTkLabel(top,text="ZKSTRAP // GUIDED BOOT",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        self._tutorial_stage=ctk.CTkLabel(top,text="",height=25,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"));self._tutorial_stage.pack(side="right")
        self._tutorial_title=ctk.CTkLabel(main,text="",anchor="w",text_color=t["text"],font=ctk.CTkFont(size=23,weight="bold"));self._tutorial_title.pack(fill="x",pady=(17,4))
        self._tutorial_body=ctk.CTkLabel(main,text="",anchor="w",justify="left",wraplength=max(430,width-160),text_color=t["text"],font=ctk.CTkFont(size=10));self._tutorial_body.pack(fill="x",pady=(1,10))
        tipbox=ctk.CTkFrame(main,fg_color=self._mix_hex(t["card"],t["accent"],.09),corner_radius=13,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34));tipbox.pack(fill="x",pady=(2,10))
        tiptop=ctk.CTkFrame(tipbox,fg_color="transparent");tiptop.pack(fill="x",padx=12,pady=(9,2));ctk.CTkLabel(tiptop,text="✦",text_color=t["accent"],font=ctk.CTkFont(size=13,weight="bold")).pack(side="left");ctk.CTkLabel(tiptop,text=L("REPARA NISSO","NOTICE THIS","MIRA ESTO","注意这里","À NOTER"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=(7,0))
        self._tutorial_tip=ctk.CTkLabel(tipbox,text="",anchor="w",justify="left",wraplength=max(410,width-185),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9));self._tutorial_tip.pack(fill="x",padx=12,pady=(1,10))
        foot=ctk.CTkFrame(main,fg_color="transparent");foot.pack(fill="x",pady=(4,0),side="bottom")
        self._tutorial_prev=ctk.CTkButton(foot,text="←",width=48,height=38,command=lambda:self._tutorial_move(-1),fg_color=t["card_active"],hover_color=t["hover"]);self._tutorial_prev.pack(side="left")
        self._tutorial_skip=ctk.CTkButton(foot,text=L("SAIR","EXIT","SALIR","退出","QUITTER"),width=72,height=38,command=self._tutorial_skip_click,fg_color="transparent",border_width=1,border_color=t["card_active"]);self._tutorial_skip.pack(side="left",padx=7)
        self._tutorial_next=ctk.CTkButton(foot,text="",width=205,height=38,command=lambda:self._tutorial_move(1),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=9,weight="bold"));self._tutorial_next.pack(side="right")
        self._tutorial_render_step()
''')

replace_method('ModernConfigApp','_tutorial_render_step',r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps()
        if not steps:return
        idx=max(0,min(int(getattr(self,"_tutorial_step_index",0) or 0),len(steps)-1));self._tutorial_step_index=idx
        page,title,body,tip=steps[idx][:4];self._tutorial_step_ready=True;self._tutorial_apply_real_unlock(idx)
        try:self.show_page(str(page),animate=False)
        except Exception:pass
        try:
            body=self._ui_compact_copy(body,145);tip=self._ui_compact_copy(tip,105)
            self._tutorial_title.configure(text=title);self._tutorial_body.configure(text=body);self._tutorial_tip.configure(text=tip);self._tutorial_count.configure(text=f"/ {len(steps):02d}");self._tutorial_big_step.configure(text=f"{idx+1:02d}")
            pct=int(round(((idx+1)/max(1,len(steps)))*100));self._tutorial_progress.set((idx+1)/max(1,len(steps)));self._tutorial_progress_text.configure(text=f"{pct}%")
            self._tutorial_stage.configure(text=self._L("  AGORA  ","  NOW  ","  AHORA  ","  当前  ","  MAINTENANT  "))
            self._tutorial_unlocked.configure(text=self._L(f"{idx+1} ÁREAS\nLIBERADAS",f"{idx+1} AREAS\nUNLOCKED",f"{idx+1} ÁREAS\nLIBERADAS",f"已解锁\n{idx+1} 个区域",f"{idx+1} ZONES\nOUVERTES"))
            self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
            label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("LIBERAR PRÓXIMA  →","UNLOCK NEXT  →","LIBERAR SIGUIENTE  →","解锁下一项  →","OUVRIR LA SUITE  →")
            self._tutorial_next.configure(state="normal",text=label)
            panel=getattr(self,"_tutorial_panel",None)
            if panel is not None and panel.winfo_exists():panel.lift()
        except Exception:pass
''')

replace_method('ModernConfigApp','_tutorial_move',r'''    def _tutorial_move(self,delta):
        steps=self._tutorial_steps();cur=int(getattr(self,"_tutorial_step_index",0) or 0);nxt=cur+int(delta)
        self._first_run_audio_event('nav' if int(delta)>0 else 'back')
        if nxt>=len(steps):
            self._tutorial_close(mark_complete=True);return
        self._tutorial_step_index=max(0,nxt);self._tutorial_render_step()
''')

# Global visual-density pass.
replace_method('ModernConfigApp','_page_shell',r'''    def _page_shell(self, key, title, subtitle=""):
        t=TEMAS[self.tema_atual];st=self._theme_style();decor=THEME_DECOR.get(self.tema_atual,THEME_DECOR["Clean"])
        page=ctk.CTkFrame(self.content_host,fg_color="transparent");self.pages[key]=page
        if not hasattr(self,"page_art_wraps"):self.page_art_wraps={}
        hero=ctk.CTkFrame(page,height=184,fg_color=t.get("panel",t["card"]),corner_radius=0,border_width=0);hero.pack(fill="x",padx=16,pady=(14,0));hero.pack_propagate(False)
        art=Canvas(hero,bg=t.get("panel",t["card"]),highlightthickness=0,bd=0);art.place(x=0,y=0,relwidth=1,relheight=1);art._zk_page_key=key;art._zk_page_title=title;art._zk_page_subtitle=subtitle;self.page_theme_canvases[key]=art;self._bind_theme_canvas(art,self.tema_atual,zone="hero");self.page_art_wraps[key]=hero
        holder=ctk.CTkFrame(page,fg_color="transparent");holder.pack(fill="both",expand=True,padx=18,pady=(12,12));body=ZKSmoothScrollFrame(holder,width=self._desired_page_width(),fg_color="transparent",corner_radius=0,scrollbar_button_color=t["accent"],scrollbar_button_hover_color=t["hover"]);body.pack(fill="both",expand=True,padx=(8,2),pady=0);self.page_scrolls[key]=body;self._install_smooth_scroll(body,1)
        meta=SPECIAL_THEME_BANNER_META.get(self.tema_atual,{}) if self.tema_atual in SPECIAL_THEME_NAMES else {};info=ctk.CTkFrame(body,fg_color=t.get("panel",t["card"]),corner_radius=max(14,st["card_radius"]),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.48));info.pack(fill="x",padx=6,pady=(2,12));ctk.CTkFrame(info,height=2,fg_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.58),corner_radius=0).pack(fill="x",padx=12)
        inner=ctk.CTkFrame(info,fg_color="transparent");inner.pack(fill="x",padx=22,pady=(15,15));top=ctk.CTkFrame(inner,fg_color="transparent");top.pack(fill="x");left=ctk.CTkFrame(top,fg_color="transparent");left.pack(side="left",fill="x",expand=True);crumb=ctk.CTkFrame(left,fg_color="transparent");crumb.pack(anchor="w");ctk.CTkLabel(crumb,text=f"ZK  /  {key.upper().replace('_',' ')}",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left");ctk.CTkLabel(crumb,text="LOCAL  //  CONTROL DECK",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=(10,0));ctk.CTkLabel(left,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=22,weight="bold"),anchor="w").pack(anchor="w",pady=(4,0))
        if subtitle:ctk.CTkLabel(left,text=self._ui_compact_copy(subtitle,175),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=850,justify="left",anchor="w").pack(fill="x",anchor="w",pady=(4,0))
        right=ctk.CTkFrame(top,fg_color="transparent");right.pack(side="right",anchor="ne",padx=(18,0));right_title=str((meta.get("subtitle") if self.tema_atual in SPECIAL_THEME_NAMES else decor.get("tag","CORE")) or "CORE").upper();right_sub=f"{self.tema_atual.upper()}  //  SIGNATURE" if self.tema_atual in SPECIAL_THEME_NAMES else "SIGNATURE / CORE";ctk.CTkLabel(right,text=right_title,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="e");ctk.CTkLabel(right,text=right_sub,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(anchor="e",pady=(3,0));return page,body
''')

replace_method('ModernConfigApp','_section_card',r'''    def _section_card(self, parent, title, description=""):
        t=TEMAS[self.tema_atual];st=self._theme_style();radius=max(14,st["card_radius"]);border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border);card.pack(fill="x",padx=6,pady=8);ctk.CTkFrame(card,height=3,fg_color=self._mix_hex(t["card"],t["accent"],.72),corner_radius=2).pack(fill="x",padx=12)
        content=ctk.CTkFrame(card,fg_color="transparent");content.pack(fill="both",expand=True,padx=16,pady=(11,14));head=ctk.CTkFrame(content,fg_color=self._mix_hex(t["card"],t.get("icon_bg",t["card_active"]),.62),corner_radius=12,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.18));head.pack(fill="x",pady=(0,7));icon=ctk.CTkFrame(head,width=42,height=42,corner_radius=11,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.10),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.46));icon.pack(side="left",padx=(8,10),pady=7);icon.pack_propagate(False);ctk.CTkLabel(icon,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=17,weight="bold")).pack(fill="both",expand=True)
        tw=ctk.CTkFrame(head,fg_color="transparent");tw.pack(side="left",fill="x",expand=True,pady=7);ctk.CTkLabel(tw,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=14,weight="bold"),anchor="w").pack(anchor="w",fill="x");ctk.CTkLabel(tw,text="ZKSTRAP",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=6,weight="bold"),anchor="w").pack(anchor="w",pady=(1,0))
        if description:
            full=str(description);short=self._ui_compact_copy(full,165)
            ctk.CTkButton(head,text="i",width=30,height=30,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.35),text_color=t["accent"],command=lambda tt=title,dd=full:messagebox.showinfo(str(tt),str(dd),parent=self)).pack(side="right",padx=10)
            ctk.CTkLabel(content,text=short,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=980,justify="left",anchor="w").pack(fill="x",anchor="w",padx=4,pady=(0,4))
        return content
''')

_,a,b=method_span(s,'ModernConfigApp','_module_switch');chunk=s[a:b]
needle='''        ctk.CTkLabel(txt,text=description,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=760,justify="left",anchor="w").pack(anchor="w",fill="x",pady=(3,0))'''
if needle not in chunk:raise SystemExit('v3.20.11: module desc anchor')
chunk=chunk.replace(needle,'''        full_description=str(description or "");ctk.CTkLabel(txt,text=self._ui_compact_copy(full_description,120),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=8),wraplength=690,justify="left",anchor="w").pack(anchor="w",fill="x",pady=(2,0))''',1)
needle='''        controls=ctk.CTkFrame(row,fg_color="transparent"); controls.pack(side="right",padx=(12,0))'''
if needle not in chunk:raise SystemExit('v3.20.11: module controls anchor')
chunk=chunk.replace(needle,'''        controls=ctk.CTkFrame(row,fg_color="transparent"); controls.pack(side="right",padx=(12,0))
        ctk.CTkButton(controls,text="i",width=28,height=28,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"),command=lambda ll=label,dd=full_description:messagebox.showinfo(str(ll),str(dd),parent=self)).pack(side="left",padx=(0,6))''',1)
s=s[:a]+chunk+s[b:]

# Cursor page: retire in-app ANI preview and expose only Roblox overlay controls.
replace_method('ModernConfigApp','_lazy_build_page_cursor',r'''    def _lazy_build_page_cursor(self):
        if "cursor" in getattr(self,"pages",{}):return self.pages.get("cursor")
        t=TEMAS[self.tema_atual];L=self._L
        _,body=self._page_shell("cursor","CURSOR",L("Cursor PNG normal + opção de cursor animado por overlay somente dentro do Roblox.","Static PNG cursor + optional animated overlay shown only over Roblox.","Cursor PNG normal + overlay animado solo sobre Roblox.","普通 PNG 光标 + 仅在 Roblox 上显示的动画覆盖光标。","Curseur PNG classique + overlay animé uniquement sur Roblox."))
        cursor_card=self._section_card(body,L("CURSOR DO ROBLOX","ROBLOX CURSOR","CURSOR DE ROBLOX","ROBLOX 光标","CURSEUR ROBLOX"),L("O cursor estático continua usando os assets reais do Roblox. O animado roda como overlay externo e não injeta nada no jogo.","Static cursors still use Roblox assets. Animated mode is an external overlay and injects nothing into the game.","El cursor estático usa los assets de Roblox. El animado es un overlay externo sin inyección.","静态光标使用 Roblox 资源；动画模式为外部覆盖层，不向游戏注入任何内容。","Le curseur statique utilise les assets Roblox ; l’animé est un overlay externe sans injection."));self.cursor_card=cursor_card
        self.cursor_menu=ctk.CTkOptionMenu(cursor_card,values=self.listar_cursor_packs(),command=self.evento_cursor_pack,fg_color=t["card_active"],button_color=t["card_active"],button_hover_color=t["hover"],text_color=t["accent"])
        if self.cursor_pack not in self.listar_cursor_packs():self.cursor_pack="Roblox Padrão"
        self.cursor_menu.set(self.cursor_pack);self.cursor_menu.pack(fill="x",padx=16,pady=(4,8))
        preview_row=ctk.CTkFrame(cursor_card,fg_color=t["card_active"],corner_radius=13,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));preview_row.pack(fill="x",padx=16,pady=(2,10));self.cursor_preview_label=ctk.CTkLabel(preview_row,text=L("Carregando…","Loading…","Cargando…","加载中…","Chargement…"),width=138,height=138,text_color=t.get("muted","gray"));self.cursor_preview_label.pack(side="left",padx=12,pady=12);ptxt=ctk.CTkFrame(preview_row,fg_color="transparent");ptxt.pack(side="left",fill="both",expand=True,padx=(4,14),pady=12);ctk.CTkLabel(ptxt,text=L("CURSOR ESTÁTICO","STATIC CURSOR","CURSOR ESTÁTICO","静态光标","CURSEUR STATIQUE"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w");ctk.CTkLabel(ptxt,text=L("Prévia do pack usado pelo Roblox quando o overlay animado estiver desligado.","Preview of the pack Roblox uses when animated overlay is off.","Vista previa del pack usado cuando el overlay está apagado.","动画覆盖关闭时 Roblox 使用的光标包预览。","Aperçu du pack utilisé lorsque l’overlay animé est désactivé."),text_color=t.get("muted","gray"),wraplength=540,justify="left").pack(anchor="w",fill="x",pady=(5,0));self.after(40,self._refresh_cursor_preview)

        overlay=ctk.CTkFrame(cursor_card,fg_color=self._mix_hex(t["card_active"],t["accent"],.035),corner_radius=15,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.48));overlay.pack(fill="x",padx=16,pady=(2,11))
        icon=ctk.CTkFrame(overlay,width=78,height=78,corner_radius=18,fg_color=t["card_active"],border_width=1,border_color=t["accent"]);icon.pack(side="left",padx=13,pady=13);icon.pack_propagate(False);ctk.CTkLabel(icon,text="◉",text_color=t["accent"],font=ctk.CTkFont(size=28,weight="bold")).pack(fill="both",expand=True)
        ob=ctk.CTkFrame(overlay,fg_color="transparent");ob.pack(side="left",fill="both",expand=True,padx=(2,13),pady=12)
        top=ctk.CTkFrame(ob,fg_color="transparent");top.pack(fill="x");ctk.CTkLabel(top,text=L("CURSOR ANIMADO NO ROBLOX","ANIMATED CURSOR IN ROBLOX","CURSOR ANIMADO EN ROBLOX","ROBLOX 动画光标","CURSEUR ANIMÉ DANS ROBLOX"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left");self.cursor_overlay_badge=ctk.CTkLabel(top,text="",height=24,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"));self.cursor_overlay_badge.pack(side="right")
        ctk.CTkLabel(ob,text=L("Importe .ANI, .CUR ou GIF. O overlay aparece só quando Roblox está em foco e segue o mouse diretamente, sem suavização.","Import .ANI, .CUR or GIF. The overlay appears only while Roblox is focused and tracks the pointer directly with no smoothing.","Importa .ANI, .CUR o GIF. Solo aparece con Roblox en foco y sigue el puntero directamente, sin suavizado.","导入 .ANI、.CUR 或 GIF。仅在 Roblox 获得焦点时显示，并直接跟随鼠标，不做平滑处理。","Importez .ANI, .CUR ou GIF. L’overlay n’apparaît que lorsque Roblox est actif et suit directement le pointeur, sans lissage."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),wraplength=700,justify="left",anchor="w").pack(fill="x",pady=(5,5));self.cursor_overlay_file=ctk.CTkLabel(ob,text="",text_color=t["text"],font=ctk.CTkFont(size=9,weight="bold"),anchor="w");self.cursor_overlay_file.pack(fill="x",pady=(1,8));rr=ctk.CTkFrame(ob,fg_color="transparent");rr.pack(fill="x");ctk.CTkButton(rr,text=L("IMPORTAR ANIMADO","IMPORT ANIMATED","IMPORTAR ANIMADO","导入动画光标","IMPORTER ANIMÉ"),command=self._cursor_overlay_pick,height=37,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",fill="x",expand=True,padx=(0,5));self.cursor_overlay_toggle_btn=ctk.CTkButton(rr,text="",command=self._cursor_overlay_toggle,height=37,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");self.cursor_overlay_toggle_btn.pack(side="left",fill="x",expand=True,padx=(5,0));self.after(30,self._cursor_overlay_refresh_ui)

        size=self._section_card(body,L("TAMANHO E HOTSPOT","SIZE & HOTSPOT","TAMAÑO Y HOTSPOT","大小与热点","TAILLE ET HOTSPOT"),L("O overlay animado usa o mesmo tamanho visual configurado aqui para manter proporção com o cursor do Roblox.","Animated overlay uses this same visual size to match the Roblox cursor.","El overlay usa este mismo tamaño visual.","动画覆盖层使用这里设置的相同视觉大小。","L’overlay animé utilise la même taille visuelle."));row=ctk.CTkFrame(size,fg_color="transparent");row.pack(fill="x",padx=16,pady=(4,8));self.cursor_size_value=ctk.CTkLabel(row,text=f"{int(self.cursor_visual_size)} px",width=70,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"));self.cursor_size_value.pack(side="right");self.cursor_size_slider=ctk.CTkSlider(row,from_=8,to=48,number_of_steps=40,command=self.evento_cursor_tamanho,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]);self.cursor_size_slider.set(int(self.cursor_visual_size));self.cursor_size_slider.pack(side="left",fill="x",expand=True,padx=(0,10));self.cursor_anchor_menu=ctk.CTkOptionMenu(size,values=["Ponta no centro","Ponta no canto"],command=self.evento_cursor_ancora,fg_color=t["card_active"],button_color=t["card_active"],text_color=t["accent"]);self.cursor_anchor_menu.set(self.cursor_anchor_mode);self.cursor_anchor_menu.pack(fill="x",padx=16,pady=(2,10))
        r=ctk.CTkFrame(cursor_card,fg_color="transparent");r.pack(fill="x",padx=16,pady=(2,6));ctk.CTkButton(r,text="ABRIR PASTA",command=self.abrir_pasta_cursores).pack(side="left",expand=True,fill="x",padx=(0,4));ctk.CTkButton(r,text="IMPORTAR PACK",command=self.importar_cursor_pack_pasta).pack(side="left",expand=True,fill="x",padx=(4,0));self.btn_apply_cursor=ctk.CTkButton(cursor_card,text=L("APLICAR CURSOR ESTÁTICO","APPLY STATIC CURSOR","APLICAR CURSOR ESTÁTICO","应用静态光标","APPLIQUER LE CURSEUR STATIQUE"),command=self.aplicar_cursor_selecionado,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");self.btn_apply_cursor.pack(fill="x",padx=16,pady=(8,4));self.btn_restore_cursor=ctk.CTkButton(cursor_card,text=L("RESTAURAR ORIGINAL","RESTORE ORIGINAL","RESTAURAR ORIGINAL","恢复原版","RESTAURER L’ORIGINAL"),command=self.restaurar_cursor_original,fg_color="transparent",border_width=1,border_color=t["accent"],text_color=t["text"]);self.btn_restore_cursor.pack(fill="x",padx=16,pady=(4,8));self.lbl_cursor_status=ctk.CTkLabel(cursor_card,text="",text_color=t.get("muted","gray"),wraplength=820,justify="left");self.lbl_cursor_status.pack(anchor="w",padx=16,pady=(0,14));return self.pages.get("cursor")
''')

insert_before_method('ModernConfigApp','_ani_read_frames',r'''    def _cursor_overlay_dir(self):
        p=os.path.join(os.path.dirname(self.config_path),'cursor_overlay');os.makedirs(p,exist_ok=True);return p

    def _cursor_overlay_refresh_ui(self):
        try:
            path=str(getattr(self,'cursor_overlay_path','') or '');enabled=bool(getattr(self,'cursor_overlay_enabled',False));running=bool(getattr(self,'_cursor_overlay_proc',None) is not None and self._cursor_overlay_proc.poll() is None)
            badge=getattr(self,'cursor_overlay_badge',None);lab=getattr(self,'cursor_overlay_file',None);btn=getattr(self,'cursor_overlay_toggle_btn',None)
            if lab is not None and lab.winfo_exists():lab.configure(text=(os.path.basename(path) if path else self._L('Nenhum cursor animado importado','No animated cursor imported','Ningún cursor animado importado','尚未导入动画光标','Aucun curseur animé importé')))
            if badge is not None and badge.winfo_exists():badge.configure(text=(self._L('  ATIVO  ','  ACTIVE  ','  ACTIVO  ','  已启用  ','  ACTIF  ') if running else self._L('  PRONTO  ','  READY  ','  LISTO  ','  就绪  ','  PRÊT  ') if path else self._L('  VAZIO  ','  EMPTY  ','  VACÍO  ','  空  ','  VIDE  ')))
            if btn is not None and btn.winfo_exists():btn.configure(text=(self._L('DESATIVAR NO ROBLOX','DISABLE IN ROBLOX','DESACTIVAR EN ROBLOX','在 ROBLOX 中关闭','DÉSACTIVER DANS ROBLOX') if enabled else self._L('ATIVAR NO ROBLOX','ENABLE IN ROBLOX','ACTIVAR EN ROBLOX','在 ROBLOX 中启用','ACTIVER DANS ROBLOX')))
        except Exception:pass

    def _cursor_overlay_pick(self):
        try:
            src=filedialog.askopenfilename(title=self._L('Cursor animado para o Roblox','Animated cursor for Roblox','Cursor animado para Roblox','Roblox 动画光标','Curseur animé pour Roblox'),filetypes=[('Animated cursor','*.ani *.gif'),('Cursor','*.cur'),('All supported','*.ani *.cur *.gif')])
            if not src:return
            ext=os.path.splitext(src)[1].lower()
            if ext not in ('.ani','.cur','.gif'):raise ValueError('Use .ANI, .CUR ou .GIF')
            dst=os.path.join(self._cursor_overlay_dir(),'selected'+ext);shutil.copy2(src,dst);self.cursor_overlay_path=dst;self.salvar_config_app();self._play_ui_sound('select',0);self._cursor_overlay_refresh_ui()
            self.show_toast(self._L('CURSOR ANIMADO PRONTO','ANIMATED CURSOR READY','CURSOR ANIMADO LISTO','动画光标已就绪','CURSEUR ANIMÉ PRÊT'),os.path.basename(src),kind='success',duration=2600)
        except Exception as exc:self.show_toast('CURSOR',str(exc),kind='error',duration=4200)

    def _cursor_overlay_prepare_transparent_base(self):
        from PIL import Image
        base=self._cursor_overlay_dir();token=uuid.uuid4().hex;entries=[];transparent=os.path.join(base,'transparent.png');Image.new('RGBA',(64,64),(0,0,0,0)).save(transparent,'PNG')
        dirs=[]
        try:
            target=self._cursor_target_dir()
            if target:dirs.append(target)
        except Exception:pass
        try:
            bs=self._bloxstrap_cursor_dir()
            if bs:dirs.append(bs)
        except Exception:pass
        for d in dict.fromkeys(dirs):
            try:os.makedirs(d,exist_ok=True)
            except Exception:continue
            for name in ('ArrowCursor.png','ArrowFarCursor.png'):
                dst=os.path.join(d,name);existed=os.path.isfile(dst);backup=os.path.join(base,f'{token}_{len(entries)}_{name}')
                try:
                    if existed:shutil.copy2(dst,backup)
                    shutil.copy2(transparent,dst);entries.append({'dst':dst,'backup':backup,'existed':existed})
                except Exception:pass
        state=os.path.join(base,f'overlay_state_{token}.json')
        with open(state,'w',encoding='utf-8') as f:json.dump({'entries':entries},f,ensure_ascii=False,indent=2)
        self._cursor_overlay_state_path=state;return state

    def _cursor_overlay_helper_command(self,path,stop_file,state_file):
        args=['--zk-cursor-overlay','--cursor-file',path,'--cursor-stop',stop_file,'--cursor-state',state_file,'--cursor-size',str(int(getattr(self,'cursor_visual_size',24) or 24)),'--parent-pid',str(os.getpid())]
        return ([sys.executable]+args) if getattr(sys,'frozen',False) else ([sys.executable,os.path.abspath(__file__)]+args)

    def _cursor_overlay_start(self,silent=False):
        if os.name!='nt':return False
        path=str(getattr(self,'cursor_overlay_path','') or '')
        if not path or not os.path.isfile(path):
            if not silent:self.show_toast('CURSOR',self._L('Importe um .ANI/.CUR/.GIF primeiro.','Import an .ANI/.CUR/.GIF first.','Importa un .ANI/.CUR/.GIF primero.','请先导入 .ANI/.CUR/.GIF。','Importez d’abord un .ANI/.CUR/.GIF.'),kind='warning')
            self.cursor_overlay_enabled=False;self._cursor_overlay_refresh_ui();return False
        try:
            proc=getattr(self,'_cursor_overlay_proc',None)
            if proc is not None and proc.poll() is None:return True
        except Exception:pass
        try:
            state=self._cursor_overlay_prepare_transparent_base();stop=os.path.join(self._cursor_overlay_dir(),f'overlay_{uuid.uuid4().hex}.stop')
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
            self._cursor_overlay_proc=subprocess.Popen(self._cursor_overlay_helper_command(path,stop,state),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True);self._cursor_overlay_stop_file=stop;self.cursor_overlay_enabled=True;self.salvar_config_app();self._cursor_overlay_refresh_ui()
            if not silent:self.show_toast(self._L('OVERLAY ATIVO','OVERLAY ACTIVE','OVERLAY ACTIVO','覆盖层已启用','OVERLAY ACTIF'),self._L('Só aparece com Roblox em foco. Se o cursor antigo ainda aparecer junto, feche e abra o Roblox uma vez.','Visible only while Roblox is focused. If the old cursor is still visible too, restart Roblox once.','Solo aparece con Roblox en foco. Si también aparece el cursor anterior, reinicia Roblox una vez.','仅在 Roblox 获得焦点时显示。如果旧光标仍同时出现，请重启 Roblox 一次。','Visible uniquement avec Roblox actif. Si l’ancien curseur apparaît aussi, redémarrez Roblox une fois.'),kind='success',duration=5200)
            return True
        except Exception as exc:
            self.cursor_overlay_enabled=False
            try:_cursor_overlay_restore_state_file(getattr(self,'_cursor_overlay_state_path',''))
            except Exception:pass
            if not silent:self.show_toast('CURSOR OVERLAY',str(exc),kind='error',duration=4500)
            return False

    def _cursor_overlay_stop(self,persist=True):
        stop=str(getattr(self,'_cursor_overlay_stop_file','') or '');proc=getattr(self,'_cursor_overlay_proc',None);state=str(getattr(self,'_cursor_overlay_state_path','') or '')
        try:
            if stop:
                with open(stop,'w',encoding='utf-8') as f:f.write('stop')
        except Exception:pass
        try:
            if proc is not None and proc.poll() is None:proc.wait(timeout=.8)
        except Exception:
            try:proc.terminate()
            except Exception:pass
        _cursor_overlay_restore_state_file(state);self._cursor_overlay_proc=None;self._cursor_overlay_stop_file='';self._cursor_overlay_state_path=''
        if persist:
            self.cursor_overlay_enabled=False
            try:self.salvar_config_app()
            except Exception:pass
        self._cursor_overlay_refresh_ui();return True

    def _cursor_overlay_toggle(self):
        if bool(getattr(self,'cursor_overlay_enabled',False)):return self._cursor_overlay_stop(persist=True)
        return self._cursor_overlay_start(silent=False)

    def _cursor_overlay_autostart(self):
        if bool(getattr(self,'cursor_overlay_enabled',False)):
            self._cursor_overlay_start(silent=True)
''')

# Changing cursor size restarts the helper so the in-game overlay matches it.
_,a,b=method_span(s,'ModernConfigApp','evento_cursor_tamanho');chunk=s[a:b]
needle='''        try:self.salvar_config_app()
        except Exception:pass'''
if needle not in chunk:raise SystemExit('v3.20.11: cursor size save anchor')
chunk=chunk.replace(needle,needle+'''
        if bool(getattr(self,"cursor_overlay_enabled",False)):
            try:self._cursor_overlay_stop(persist=False);self.after(90,lambda:self._cursor_overlay_start(silent=True))
            except Exception:pass''',1);s=s[:a]+chunk+s[b:]

# Shutdown helper first so original cursor assets are restored.
_,a,b=method_span(s,'ModernConfigApp','_shutdown_app');chunk=s[a:b]
needle='''        self.loop_verificar_jogo=False
        self.loop_animacao=False'''
if needle not in chunk:raise SystemExit('v3.20.11: shutdown anchor')
chunk=chunk.replace(needle,needle+'''
        try:self._cursor_overlay_stop(persist=False)
        except Exception:pass''',1);s=s[:a]+chunk+s[b:]

# Start onboarding soundscape as soon as authoritative first-run router starts.
_,a,b=method_span(s,'ModernConfigApp','_first_run_route');chunk=s[a:b]
needle='''        stage=self._first_run_stage()
        if stage!="done":self._first_run_ensure_maximized()'''
if needle not in chunk:raise SystemExit('v3.20.11: first-run route audio anchor')
chunk=chunk.replace(needle,'''        stage=self._first_run_stage()
        if stage!="done":
            self._first_run_ensure_maximized();self._first_run_audio_start()''',1);s=s[:a]+chunk+s[b:]

# __main__ dispatch for separate overlay helper.
needle='''    if "--zk-audio-helper" in sys.argv:
        _run_audio_helper()
        raise SystemExit(0)'''
if needle not in s:raise SystemExit('v3.20.11: main audio helper anchor')
s=s.replace(needle,needle+'''
    if "--zk-cursor-overlay" in sys.argv:
        _run_cursor_overlay_helper()
        raise SystemExit(0)''',1)

# Validation.
for needle in (
    'APP_VERSION = "3.20.11"',
    'def _long_music_path(self, minimum_seconds=195.0):',
    'def _run_cursor_overlay_helper():',
    'def _cursor_overlay_start(self,silent=False):',
    'CURSOR ANIMADO NO ROBLOX',
    'ESSA É SUA CONTA?',
    'def _first_run_audio_start(self):',
    'def _ui_compact_copy(self,text,limit=155):',
    'self.after(2600, self._cursor_overlay_autostart)',
):
    if needle not in s:raise SystemExit('v3.20.11: missing '+needle)
_,ca,cb=method_span(s,'ModernConfigApp','_lazy_build_page_cursor');cursor_src=s[ca:cb]
for forbidden in ('ani_preview_label','_ani_preview_load(','ANI LAB'):
    if forbidden in cursor_src:raise SystemExit('v3.20.11: cursor page still exposes '+forbidden)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.11: unsafe repaint returned')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.11 overlay/audio/UX patch')
