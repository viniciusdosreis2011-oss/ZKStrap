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
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls_name),None)
    if cls is None:raise SystemExit('v3.20.12: class missing '+cls_name)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.12: method missing '+cls_name+'.'+name)
    _,pos=lines_pos(text);return node,pos[node.lineno-1],pos[node.end_lineno]


def global_span(text,name):
    tree=ast.parse(text)
    node=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.12: global missing '+name)
    _,pos=lines_pos(text);return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(cls_name,name,new_src):
    global s
    _,a,b=method_span(s,cls_name,name);s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def replace_global(name,new_src):
    global s
    _,a,b=global_span(s,name);s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def insert_before_method(cls_name,name,src):
    global s
    _,a,_=method_span(s,cls_name,name);s=s[:a]+src.rstrip()+"\n\n"+s[a:]


def rename_method(cls_name,name,new_name):
    global s
    _,a,b=method_span(s,cls_name,name);chunk=s[a:b]
    chunk,n=re.subn(r'^(\s*)def\s+'+re.escape(name)+r'\s*\(',r'\1def '+new_name+'(',chunk,count=1,flags=re.M)
    if n!=1:raise SystemExit('v3.20.12: rename failed '+name)
    s=s[:a]+chunk+s[b:]


if 'APP_VERSION = "3.20.11"' not in s:raise SystemExit('v3.20.12: expected v3.20.11 base')
s=s.replace('APP_VERSION = "3.20.11"','APP_VERSION = "3.20.12"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Whole App Guided Mode + Original Music + Runtime Fixes"',s,count=1)
if n!=1:raise SystemExit('v3.20.12: timestamp')

# -----------------------------------------------------------------------------
# MUSIC: v3.20.12 ships genuine 2+ minute tracks generated at build time.
# Do NOT concatenate/rearrange the old 26 second stems anymore.
# -----------------------------------------------------------------------------
replace_method('ZKSoundManager','_long_music_path',r'''    def _long_music_path(self, minimum_seconds=120.0):
        """Return the real long-form track bundled for the active pack.

        v3.20.12 replaces the old short ambient stems during CI with a new
        original composition. Runtime no longer constructs a fake long loop.
        """
        try:
            paths=[p for p in self.paths("ambient") if os.path.isfile(p)]
            preferred=[p for p in paths if "v3212_original" in os.path.basename(p).lower()]
            return (preferred or paths)[0] if (preferred or paths) else ""
        except Exception:return ""
''')

# -----------------------------------------------------------------------------
# COMBO PLANNER: its editor is a CTkToplevel, outside the app page scroll router.
# Bind the wheel directly to the modal scroll canvas and every recreated card.
# -----------------------------------------------------------------------------
insert_before_method('ModernConfigApp','_combo_open_editor',r'''    def _combo_bind_modal_scroll(self,scrollable,root_widget):
        """Route mouse wheel from Combo Planner descendants to its own canvas."""
        if scrollable is None or root_widget is None:return
        def wheel(event):
            try:
                widget=getattr(event,"widget",None)
                if self._scroll_widget_chain_has(widget,("slider","scrollbar","combobox","spinbox")):
                    return None
                delta=int(getattr(event,"delta",0) or 0)
                if delta:
                    notches=max(1,min(5,int(round(abs(delta)/120.0)) or 1))
                    return self._queue_scroll_step(scrollable,(-1 if delta>0 else 1)*notches)
                num=int(getattr(event,"num",0) or 0)
                if num in (4,5):return self._queue_scroll_step(scrollable,-1 if num==4 else 1)
            except Exception:pass
            return None
        def bind_tree(w):
            try:
                w.bind("<MouseWheel>",wheel,add="+")
                w.bind("<Button-4>",wheel,add="+")
                w.bind("<Button-5>",wheel,add="+")
            except Exception:pass
            try:
                for child in w.winfo_children():bind_tree(child)
            except Exception:pass
        bind_tree(root_widget)
        try:bind_tree(getattr(scrollable,"_zk_host",scrollable))
        except Exception:pass
        try:bind_tree(getattr(scrollable,"_parent_canvas",scrollable))
        except Exception:pass
''')

_,a,b=method_span(s,'ModernConfigApp','_combo_open_editor');chunk=s[a:b]
needle='''            sc=ZKSmoothScrollFrame(area,fg_color=t["card"],corner_radius=10); sc.pack(fill="both",expand=True,padx=4,pady=2); self._install_smooth_scroll(sc,1)
            grid=ctk.CTkFrame(sc,fg_color="transparent"); grid.pack(fill="x",expand=True)'''
repl='''            sc=ZKSmoothScrollFrame(area,fg_color=t["card"],corner_radius=10); sc.pack(fill="both",expand=True,padx=4,pady=2); self._install_smooth_scroll(sc,1)
            grid=ctk.CTkFrame(sc,fg_color="transparent"); grid.pack(fill="x",expand=True)
            self._combo_bind_modal_scroll(sc,grid);self._combo_bind_modal_scroll(sc,search)'''
if needle not in chunk:raise SystemExit('v3.20.12: combo scroll creation anchor')
chunk=chunk.replace(needle,repl,1)
needle='''                    card.grid(row=i//5,column=i%5,padx=5,pady=5,sticky="nsew")
                if prefetch and shown: self._combo_prefetch_category(category,shown,lambda:render(prefetch=False))'''
repl='''                    card.grid(row=i//5,column=i%5,padx=5,pady=5,sticky="nsew")
                self._combo_bind_modal_scroll(sc,grid)
                if prefetch and shown: self._combo_prefetch_category(category,shown,lambda:render(prefetch=False))'''
if needle not in chunk:raise SystemExit('v3.20.12: combo rendered cards anchor')
chunk=chunk.replace(needle,repl,1);s=s[:a]+chunk+s[b:]

# -----------------------------------------------------------------------------
# CURSOR OVERLAY: handshake + preflight. v3.20.11 marked the overlay active as
# soon as Popen() succeeded, even if the helper immediately crashed. The helper
# now reports STARTING/READY/ERROR through a tiny status JSON file.
# -----------------------------------------------------------------------------
insert_before_method('ModernConfigApp','_cursor_overlay_helper_command',r'''    def _cursor_overlay_verify_start(self,status_file,state_file,stop_file,silent=False,attempt=0):
        try:
            proc=getattr(self,"_cursor_overlay_proc",None)
            payload={}
            if status_file and os.path.isfile(status_file):
                try:
                    with open(status_file,"r",encoding="utf-8") as f:payload=json.load(f) or {}
                except Exception:payload={}
            state=str(payload.get("state","") or "").lower()
            if state=="ready":
                self.cursor_overlay_enabled=True;self._cursor_overlay_status_file=status_file
                try:self.salvar_config_app()
                except Exception:pass
                self._cursor_overlay_refresh_ui()
                if not silent:self.show_toast(self._L("CURSOR PRONTO NO ROBLOX","ROBLOX CURSOR READY","CURSOR LISTO EN ROBLOX","ROBLOX 光标已就绪","CURSEUR ROBLOX PRÊT"),self._L("Overlay validado. Ele aparece somente quando o Roblox estiver em foco.","Overlay validated. It only appears while Roblox is focused.","Overlay validado. Solo aparece cuando Roblox está en foco.","覆盖层已验证，仅在 Roblox 获得焦点时显示。","Overlay validé. Il apparaît uniquement lorsque Roblox est actif."),kind="success",duration=4200)
                return True
            dead=(proc is None)
            try:dead=dead or proc.poll() is not None
            except Exception:dead=True
            if state=="error" or dead or int(attempt)>=12:
                error=str(payload.get("error","") or "")
                if not error:error=self._L("O processo do cursor fechou antes de ficar pronto.","The cursor process closed before becoming ready.","El proceso del cursor se cerró antes de estar listo.","光标进程在准备完成前已关闭。","Le processus du curseur s’est fermé avant d’être prêt.")
                self.cursor_overlay_enabled=False
                try:_cursor_overlay_restore_state_file(state_file)
                except Exception:pass
                try:
                    if stop_file and os.path.isfile(stop_file):os.remove(stop_file)
                except Exception:pass
                self._cursor_overlay_proc=None;self._cursor_overlay_stop_file="";self._cursor_overlay_state_path=""
                try:
                    if status_file and os.path.isfile(status_file):os.remove(status_file)
                except Exception:pass
                self._cursor_overlay_status_file="";self._cursor_overlay_refresh_ui()
                if not silent:self.show_toast("CURSOR OVERLAY",error,kind="error",duration=6000)
                return False
            self.after(110,lambda:self._cursor_overlay_verify_start(status_file,state_file,stop_file,silent,int(attempt)+1))
            return None
        except Exception as exc:
            try:_cursor_overlay_restore_state_file(state_file)
            except Exception:pass
            self.cursor_overlay_enabled=False;self._cursor_overlay_refresh_ui()
            if not silent:self.show_toast("CURSOR OVERLAY",str(exc),kind="error",duration=5200)
            return False
''')

replace_method('ModernConfigApp','_cursor_overlay_helper_command',r'''    def _cursor_overlay_helper_command(self,path,stop_file,state_file,status_file):
        args=['--zk-cursor-overlay','--cursor-file',path,'--cursor-stop',stop_file,'--cursor-state',state_file,'--cursor-status',status_file,'--cursor-size',str(int(getattr(self,'cursor_visual_size',24) or 24)),'--parent-pid',str(os.getpid())]
        return ([sys.executable]+args) if getattr(sys,'frozen',False) else ([sys.executable,os.path.abspath(__file__)]+args)
''')

replace_method('ModernConfigApp','_cursor_overlay_start',r'''    def _cursor_overlay_start(self,silent=False):
        if os.name!='nt':return False
        path=str(getattr(self,'cursor_overlay_path','') or '')
        if not path or not os.path.isfile(path):
            if not silent:self.show_toast('CURSOR',self._L('Importe um .ANI/.CUR/.GIF primeiro.','Import an .ANI/.CUR/.GIF first.','Importa un .ANI/.CUR/.GIF primero.','请先导入 .ANI/.CUR/.GIF。','Importez d’abord un .ANI/.CUR/.GIF.'),kind='warning')
            self.cursor_overlay_enabled=False;self._cursor_overlay_refresh_ui();return False
        try:
            proc=getattr(self,'_cursor_overlay_proc',None)
            if proc is not None and proc.poll() is None:return True
        except Exception:pass
        # Preflight BEFORE hiding the normal Roblox cursor.
        try:
            frames,delays,hotspots=_cursor_overlay_decode_file(path,int(getattr(self,'cursor_visual_size',24) or 24))
            if not frames:raise ValueError('nenhum frame encontrado')
        except Exception as exc:
            self.cursor_overlay_enabled=False;self._cursor_overlay_refresh_ui()
            if not silent:self.show_toast('CURSOR',self._L('Esse arquivo de cursor não pôde ser lido: ','This cursor file could not be read: ','No se pudo leer este cursor: ','无法读取此光标文件：','Ce fichier de curseur est illisible : ')+str(exc),kind='error',duration=6200)
            return False
        try:
            state=self._cursor_overlay_prepare_transparent_base();base=self._cursor_overlay_dir();token=uuid.uuid4().hex
            stop=os.path.join(base,f'overlay_{token}.stop');status=os.path.join(base,f'overlay_{token}.status.json')
            try:
                if os.path.isfile(status):os.remove(status)
            except Exception:pass
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
            cmd=self._cursor_overlay_helper_command(path,stop,state,status)
            self._cursor_overlay_proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)
            self._cursor_overlay_stop_file=stop;self._cursor_overlay_state_path=state;self._cursor_overlay_status_file=status
            self.cursor_overlay_enabled=False;self._cursor_overlay_refresh_ui()
            self.after(90,lambda:self._cursor_overlay_verify_start(status,state,stop,silent,0))
            return True
        except Exception as exc:
            self.cursor_overlay_enabled=False
            try:_cursor_overlay_restore_state_file(getattr(self,'_cursor_overlay_state_path',''))
            except Exception:pass
            self._cursor_overlay_proc=None;self._cursor_overlay_stop_file='';self._cursor_overlay_state_path='';self._cursor_overlay_status_file=''
            self._cursor_overlay_refresh_ui()
            if not silent:self.show_toast('CURSOR OVERLAY',str(exc),kind='error',duration=5500)
            return False
''')

replace_global('_run_cursor_overlay_helper',r'''def _run_cursor_overlay_helper():
    """Click-through animated cursor visible only while Roblox is foreground."""
    path=_audio_cli_arg('--cursor-file','');stop_file=_audio_cli_arg('--cursor-stop','');state_path=_audio_cli_arg('--cursor-state','');status_path=_audio_cli_arg('--cursor-status','');parent=_audio_cli_arg('--parent-pid','0');size=_audio_cli_arg('--cursor-size','24')
    def status(state,error=''):
        if not status_path:return
        try:
            os.makedirs(os.path.dirname(status_path),exist_ok=True)
            tmp=status_path+'.tmp'
            with open(tmp,'w',encoding='utf-8') as f:json.dump({'state':state,'error':str(error or ''),'pid':os.getpid()},f,ensure_ascii=False)
            os.replace(tmp,status_path)
        except Exception:pass
    status('starting')
    try:parent=int(parent or 0)
    except Exception:parent=0
    try:size=int(size or 24)
    except Exception:size=24
    if os.name!='nt' or not path or not os.path.isfile(path):
        status('error','cursor file missing');_cursor_overlay_restore_state_file(state_path);raise SystemExit(0)
    win=None
    try:
        from PIL import ImageTk
        frames,delays,hotspots=_cursor_overlay_decode_file(path,size)
        if not frames:raise ValueError('no cursor frames')
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
        status('ready')

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
                        if user32.GetWindowRect(fg,ctypes.byref(rect)):inside=(rect.left<=point.x<rect.right and rect.top<=point.y<rect.bottom)
                        if inside:
                            hx,hy=shared['hotspot'];user32.SetWindowPos(hwnd,HWND_TOPMOST,int(point.x-hx),int(point.y-hy),0,0,SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW);shared['shown']=True
                        elif shared['shown']:user32.ShowWindow(hwnd,SW_HIDE);shared['shown']=False
                    elif shared['shown']:user32.ShowWindow(hwnd,SW_HIDE);shared['shown']=False
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
        status('error',repr(exc));_startup_log('CURSOR OVERLAY helper: '+repr(exc))
    finally:
        try:ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:pass
        _cursor_overlay_restore_state_file(state_path)
        try:
            if stop_file and os.path.isfile(stop_file):os.remove(stop_file)
        except Exception:pass
    raise SystemExit(0)
''')

# Ensure stop also clears handshake file; keep v3.20.11 restoration behavior.
_,a,b=method_span(s,'ModernConfigApp','_cursor_overlay_stop');chunk=s[a:b]
needle="""        _cursor_overlay_restore_state_file(state);self._cursor_overlay_proc=None;self._cursor_overlay_stop_file='';self._cursor_overlay_state_path=''"""
repl="""        _cursor_overlay_restore_state_file(state);self._cursor_overlay_proc=None;self._cursor_overlay_stop_file='';self._cursor_overlay_state_path=''
        status_file=str(getattr(self,'_cursor_overlay_status_file','') or '')
        try:
            if status_file and os.path.isfile(status_file):os.remove(status_file)
        except Exception:pass
        self._cursor_overlay_status_file=''"""
if needle not in chunk:raise SystemExit('v3.20.12: cursor stop anchor')
chunk=chunk.replace(needle,repl,1);s=s[:a]+chunk+s[b:]

# -----------------------------------------------------------------------------
# WHOLE-APP GUIDED MODE. The existing controller remains, but the entire real
# application now gets persistent tutorial chrome so it no longer feels like a
# normal page with a random popup in the corner.
# -----------------------------------------------------------------------------
rename_method('ModernConfigApp','_abrir_tutorial_ui_3205','_abrir_tutorial_ui_3211')
rename_method('ModernConfigApp','_tutorial_render_step','_tutorial_render_step_3211')
rename_method('ModernConfigApp','_tutorial_close','_tutorial_close_3211')

insert_before_method('ModernConfigApp','_abrir_tutorial_ui_3211',r'''    def _guided_mode_stop(self):
        for name in ('_guided_topbar','_guided_topline','_guided_bottom','_guided_edge_l','_guided_edge_r'):
            obj=getattr(self,name,None)
            try:
                if obj is not None and obj.winfo_exists():obj.destroy()
            except Exception:pass
            try:setattr(self,name,None)
            except Exception:pass
        stash=dict(getattr(self,'_guided_nav_style',{}) or {})
        for key,vals in stash.items():
            btn=(getattr(self,'nav_buttons',{}) or {}).get(key)
            if btn is None:continue
            try:
                kwargs={k:v for k,v in vals.items() if v is not None};btn.configure(**kwargs)
            except Exception:pass
        self._guided_nav_style={}

    def _guided_mode_start(self):
        self._guided_mode_stop();host=getattr(self,'content_host',None)
        if host is None:return
        t=TEMAS[self.tema_atual];L=self._L
        try:
            edge=self._mix_hex(t.get('border',t['accent']),t['accent'],.88)
            self._guided_edge_l=ctk.CTkFrame(host,width=3,fg_color=edge,corner_radius=0);self._guided_edge_l.place(x=0,y=0,relheight=1)
            self._guided_edge_r=ctk.CTkFrame(host,width=3,fg_color=edge,corner_radius=0);self._guided_edge_r.place(relx=1,x=-3,y=0,relheight=1)
            self._guided_topline=ctk.CTkFrame(host,height=3,fg_color=t['accent'],corner_radius=0);self._guided_topline.place(x=0,y=0,relwidth=1)
            bar=ctk.CTkFrame(host,height=46,fg_color=self._mix_hex(t.get('panel',t['card']),t['accent'],.13),corner_radius=12,border_width=1,border_color=edge);bar.place(x=16,y=12,relwidth=1,width=-32);bar.pack_propagate(False);self._guided_topbar=bar
            left=ctk.CTkFrame(bar,fg_color='transparent');left.pack(side='left',fill='y',padx=(14,8))
            self._guided_badge=ctk.CTkLabel(left,text=L('●  MODO GUIADO','●  GUIDED MODE','●  MODO GUIADO','●  引导模式','●  MODE GUIDÉ'),text_color=t['accent'],font=ctk.CTkFont(family='Consolas',size=8,weight='bold'));self._guided_badge.pack(anchor='w',pady=(7,0))
            self._guided_step_text=ctk.CTkLabel(left,text='',text_color=t.get('muted','gray'),font=ctk.CTkFont(family='Consolas',size=7));self._guided_step_text.pack(anchor='w')
            self._guided_now=ctk.CTkLabel(bar,text='',text_color=t['text'],font=ctk.CTkFont(size=13,weight='bold'));self._guided_now.pack(side='left',expand=True)
            self._guided_next=ctk.CTkLabel(bar,text='',text_color=t.get('muted','gray'),font=ctk.CTkFont(family='Consolas',size=8,weight='bold'));self._guided_next.pack(side='right',padx=(8,15))
            bottom=ctk.CTkFrame(host,height=28,fg_color=self._mix_hex(t.get('panel',t['card']),t['accent'],.10),corner_radius=0);bottom.place(x=0,rely=1,y=-28,relwidth=1);bottom.pack_propagate(False);self._guided_bottom=bottom
            self._guided_progress=ctk.CTkProgressBar(bottom,height=4,progress_color=t['accent'],fg_color=t['card_active']);self._guided_progress.pack(fill='x',side='top',padx=0,pady=0)
            self._guided_bottom_text=ctk.CTkLabel(bottom,text=L('VOCÊ ESTÁ NO TUTORIAL  •  USE A PÁGINA REAL ENQUANTO AS ÁREAS SÃO LIBERADAS','YOU ARE IN THE TUTORIAL  •  USE THE REAL PAGE WHILE AREAS UNLOCK','ESTÁS EN EL TUTORIAL  •  USA LA PÁGINA REAL MIENTRAS SE DESBLOQUEAN ÁREAS','你正在教程中  •  使用真实页面并逐步解锁区域','VOUS ÊTES DANS LE TUTORIEL  •  UTILISEZ LA VRAIE PAGE PENDANT LE DÉVERROUILLAGE'),text_color=t.get('muted','gray'),font=ctk.CTkFont(family='Consolas',size=7,weight='bold'));self._guided_bottom_text.pack(expand=True)
            self._guided_nav_style={}
            for key,btn in dict(getattr(self,'nav_buttons',{}) or {}).items():
                vals={}
                for prop in ('border_width','border_color'):
                    try:vals[prop]=btn.cget(prop)
                    except Exception:vals[prop]=None
                self._guided_nav_style[key]=vals
            for w in (self._guided_edge_l,self._guided_edge_r,self._guided_topline,self._guided_topbar,self._guided_bottom):
                try:w.lift()
                except Exception:pass
        except Exception as exc:_startup_log('GUIDED MODE start: '+repr(exc))
        self._guided_mode_refresh()

    def _guided_mode_refresh(self):
        try:
            steps=self._tutorial_steps();idx=max(0,min(int(getattr(self,'_tutorial_step_index',0) or 0),len(steps)-1))
            page,title=steps[idx][0],steps[idx][1];nxt=steps[idx+1][1] if idx+1<len(steps) else self._L('FINALIZAR','FINISH','FINALIZAR','完成','TERMINER')
            self._guided_step_text.configure(text=self._L(f'ETAPA {idx+1:02d} DE {len(steps):02d}',f'STEP {idx+1:02d} OF {len(steps):02d}',f'PASO {idx+1:02d} DE {len(steps):02d}',f'第 {idx+1:02d}/{len(steps):02d} 步',f'ÉTAPE {idx+1:02d} SUR {len(steps):02d}'))
            self._guided_now.configure(text='→  '+str(title).upper())
            self._guided_next.configure(text=self._L('PRÓXIMA: ','NEXT: ','SIGUIENTE: ','下一项：','SUIVANTE : ')+str(nxt).upper())
            self._guided_progress.set((idx+1)/max(1,len(steps)))
            stash=dict(getattr(self,'_guided_nav_style',{}) or {})
            for key,vals in stash.items():
                btn=(getattr(self,'nav_buttons',{}) or {}).get(key)
                if btn is None:continue
                try:btn.configure(**{k:v for k,v in vals.items() if v is not None})
                except Exception:pass
            btn=(getattr(self,'nav_buttons',{}) or {}).get(str(page))
            if btn is not None:
                try:btn.configure(border_width=2,border_color=TEMAS[self.tema_atual]['accent'])
                except Exception:pass
            for w in (getattr(self,'_guided_topbar',None),getattr(self,'_guided_bottom',None),getattr(self,'_tutorial_panel',None)):
                try:
                    if w is not None and w.winfo_exists():w.lift()
                except Exception:pass
        except Exception:pass

    def _abrir_tutorial_ui_3205(self,primeiro_acesso=False):
        result=self._abrir_tutorial_ui_3211(primeiro_acesso=primeiro_acesso)
        try:self._guided_mode_start()
        except Exception:pass
        return result

    def _tutorial_render_step(self):
        result=self._tutorial_render_step_3211()
        try:self.after_idle(self._guided_mode_refresh)
        except Exception:pass
        return result

    def _tutorial_close(self,mark_complete=True,voltar_home=True):
        try:self._guided_mode_stop()
        except Exception:pass
        return self._tutorial_close_3211(mark_complete=mark_complete,voltar_home=voltar_home)
''')

# Structural validation.
for needle in (
    'APP_VERSION = "3.20.12"',
    'Whole App Guided Mode + Original Music + Runtime Fixes',
    'def _combo_bind_modal_scroll(self,scrollable,root_widget):',
    'def _cursor_overlay_verify_start(self,status_file,state_file,stop_file,silent=False,attempt=0):',
    "--cursor-status",
    "status('ready')",
    'def _guided_mode_start(self):',
    '●  MODO GUIADO',
    'def _long_music_path(self, minimum_seconds=120.0):',
    'v3212_original',
):
    if needle not in s:raise SystemExit('v3.20.12: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.12: unsafe repaint returned')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.12 guided mode + cursor handshake + combo scroll + original music runtime')
