from pathlib import Path
import os, re, ast

root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
path = root / 'ZKStrap_v3_18_0.py'
s = path.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'v3.19.3 patch: pattern not found: {label}')
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, lambda _m: replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v3.19.3 patch: regex pattern not found/ambiguous: {label} ({n})')
    s = ns


# ---------------------------------------------------------------------------
# VERSION
# ---------------------------------------------------------------------------
rep('APP_VERSION = "3.19.2"', 'APP_VERSION = "3.19.3"', 'version')
s, n = re.subn(r'BUILD_TIMESTAMP = "[^"]*"', 'BUILD_TIMESTAMP = "Stable Canvas Scroll + Real Flag Picker"', s, count=1)
if n != 1:
    raise SystemExit('v3.19.3 patch: BUILD_TIMESTAMP missing')


# ---------------------------------------------------------------------------
# SCROLL STABILITY
# ---------------------------------------------------------------------------
safe_repaint = r'''    def _zk_repaint_viewport(self, final=False):
        """Let Tk own painting; only flush idle drawing after scrolling settles."""
        if not final:
            return
        try:
            self._parent_canvas.update_idletasks()
        except Exception:
            pass

'''
regex_rep(
    r'    def _zk_repaint_viewport\(self, final=False\):\n.*?(?=    def _zk_canvas_resized\(self, event=None\):\n)',
    safe_repaint,
    'safe viewport repaint'
)

safe_full_repaint = r'''    def _force_windows_repaint(self):
        """Compatibility hook: use Tk idle painting, never Win32 ERASE/ALLCHILDREN."""
        try:
            self.update_idletasks()
        except Exception:
            pass

'''
regex_rep(
    r'    def _force_windows_repaint\(self\):\n.*?(?=    def _queue_scroll_step\(self, scrollable, step\):\n)',
    safe_full_repaint,
    'remove whole-window Win32 repaint'
)

stable_queue = r'''    def _queue_scroll_step(self, scrollable, step):
        """Coalesced native Canvas wheel scrolling without animated ghost trails."""
        try:
            if scrollable is None or not step:
                return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():
                return "break"

            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            if max_first <= 0.0:
                return "break"

            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"target":first,"job":None,"last_input":0.0,"settle":None}
                setattr(scrollable,"_zk_scroll_state",state)

            now=time.monotonic()
            if now-float(state.get("last_input",0.0) or 0.0)>.16:
                state["target"]=first

            direction=1.0 if float(step)>0 else -1.0
            magnitude=max(1.0,min(3.0,abs(float(step))))
            px=62.0*magnitude*direction
            base=float(state.get("target",first) or first)
            target=max(0.0,min(max_first,base+(px/max(1.0,total))))
            state["target"]=target
            state["last_input"]=now
            self._mark_fast_scroll()

            def apply_target():
                state["job"]=None
                try:
                    if not canvas.winfo_exists():
                        return
                    cur_first,cur_visible,_=self._scroll_canvas_metrics(canvas)
                    max_cur=max(0.0,1.0-cur_visible)
                    dest=max(0.0,min(max_cur,float(state.get("target",cur_first))))
                    canvas.yview_moveto(dest)
                except Exception:
                    pass

            if state.get("job") is None:
                try:state["job"]=self.after(12,apply_target)
                except Exception:apply_target()

            old_settle=state.get("settle")
            if old_settle is not None:
                try:self.after_cancel(old_settle)
                except Exception:pass
            def settle():
                state["settle"]=None
                try:scrollable._zk_repaint_viewport(True)
                except Exception:pass
            try:state["settle"]=self.after(90,settle)
            except Exception:pass
            return "break"
        except Exception:
            return "break"

'''
regex_rep(
    r'    def _queue_scroll_step\(self, scrollable, step\):\n.*?(?=    def _install_global_scroll_router\(self\):\n)',
    stable_queue,
    'stable coalesced scroll queue'
)


# ---------------------------------------------------------------------------
# FIRST-RUN LANGUAGE PICKER
# ---------------------------------------------------------------------------
language_block = r'''    def _language_choices(self):
        return [
            ("pt","Português","Brasil"),
            ("en","English","United States"),
            ("es","Español","España"),
            ("zh","中文","简体中文"),
            ("fr","Français","France"),
        ]

    def _language_flag_image(self, code, size=(54,34)):
        try:
            from PIL import Image, ImageDraw
            import math
            scale=3
            w,h=int(size[0])*scale,int(size[1])*scale
            im=Image.new("RGB",(w,h),(20,20,24))
            d=ImageDraw.Draw(im)
            code=str(code or "").lower()

            def star(cx,cy,r,fill):
                pts=[]
                for i in range(10):
                    a=-math.pi/2+i*math.pi/5
                    rr=r if i%2==0 else r*.40
                    pts.append((cx+math.cos(a)*rr,cy+math.sin(a)*rr))
                d.polygon(pts,fill=fill)

            if code=="pt":
                d.rectangle((0,0,w,h),fill="#009B3A")
                d.polygon(((w*.50,h*.10),(w*.90,h*.50),(w*.50,h*.90),(w*.10,h*.50)),fill="#FFDF00")
                d.ellipse((w*.34,h*.25,w*.66,h*.75),fill="#002776")
                d.arc((w*.37,h*.34,w*.64,h*.68),200,330,fill="white",width=max(2,scale))
            elif code=="en":
                stripe=h/13
                for i in range(13):
                    d.rectangle((0,int(i*stripe),w,int((i+1)*stripe)+1),fill="#B22234" if i%2==0 else "white")
                d.rectangle((0,0,int(w*.43),int(stripe*7)),fill="#3C3B6E")
                for yy in range(5):
                    for xx in range(6):
                        cx=int((xx+.55)*w*.43/6); cy=int((yy+.55)*stripe*7/5)
                        d.ellipse((cx-1*scale,cy-1*scale,cx+1*scale,cy+1*scale),fill="white")
            elif code=="es":
                d.rectangle((0,0,w,h),fill="#AA151B")
                d.rectangle((0,int(h*.25),w,int(h*.75)),fill="#F1BF00")
                d.rectangle((int(w*.28),int(h*.38),int(w*.34),int(h*.65)),fill="#AA151B")
                d.rectangle((int(w*.275),int(h*.34),int(w*.345),int(h*.40)),fill="#AA151B")
            elif code=="zh":
                d.rectangle((0,0,w,h),fill="#DE2910")
                star(w*.20,h*.30,h*.15,"#FFDE00")
                star(w*.37,h*.15,h*.052,"#FFDE00")
                star(w*.44,h*.29,h*.052,"#FFDE00")
                star(w*.43,h*.45,h*.052,"#FFDE00")
                star(w*.35,h*.57,h*.052,"#FFDE00")
            elif code=="fr":
                d.rectangle((0,0,w/3,h),fill="#0055A4")
                d.rectangle((w/3,0,2*w/3,h),fill="white")
                d.rectangle((2*w/3,0,w,h),fill="#EF4135")
            else:
                d.rectangle((0,0,w,h),fill="#303038")

            d.rectangle((0,0,w-1,h-1),outline="#6D6D78",width=scale)
            self._language_flag_images=getattr(self,"_language_flag_images",{})
            img=ctk.CTkImage(light_image=im,dark_image=im,size=size)
            self._language_flag_images[code]=img
            return img
        except Exception:
            return None

    def _maybe_show_first_run_language(self):
        try:picker_rev=int(self.config_data.get("language_picker_revision",0) or 0)
        except Exception:picker_rev=0
        if bool(getattr(self,"language_selected",False)) and picker_rev>=2:
            return
        old=getattr(self,"_language_panel",None)
        try:
            if old is not None and old.winfo_exists():
                old.lift(); return
        except Exception:pass
        host=getattr(self,"main_container",None)
        if host is None:
            try:self.after(120,self._maybe_show_first_run_language)
            except Exception:pass
            return

        t=TEMAS[self.tema_atual]
        try:self.update_idletasks()
        except Exception:pass
        try:
            host_w=max(560,int(host.winfo_width()))
            host_h=max(430,int(host.winfo_height()))
        except Exception:
            host_w,host_h=660,500
        pw=max(590,min(700,host_w-26)); ph=max(405,min(445,host_h-24))
        panel=ctk.CTkFrame(host,width=pw,height=ph,fg_color=t.get("panel",t["card"]),corner_radius=22,border_width=2,border_color=t["accent"])
        panel.place(relx=.5,rely=.5,anchor="center"); panel.pack_propagate(False); panel.lift(); self._language_panel=panel

        head=ctk.CTkFrame(panel,fg_color="transparent")
        head.pack(fill="x",padx=24,pady=(20,8))
        ctk.CTkLabel(head,text="ZKSTRAP  //  FIRST SETUP",height=27,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(head,text="Escolha seu idioma",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=23,weight="bold")).pack(anchor="w",pady=(13,1))
        ctk.CTkLabel(head,text="Choose your language  •  você pode trocar depois nas configurações",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=10)).pack(anchor="w")

        cards=ctk.CTkFrame(panel,fg_color="transparent")
        cards.pack(fill="both",expand=True,padx=20,pady=(7,5))
        row1=ctk.CTkFrame(cards,fg_color="transparent"); row1.pack(fill="x",expand=True,pady=(0,8))
        row2=ctk.CTkFrame(cards,fg_color="transparent"); row2.pack(fill="x",expand=True)

        def choose(code):
            self.idioma=code; self.language_selected=True
            self.config_data["language"]=code
            self.config_data["language_selected"]=True
            self.config_data["language_picker_revision"]=2
            try:self.salvar_config_app()
            except Exception:pass
            try:panel.destroy()
            except Exception:pass
            self._language_panel=None
            try:self.after(35,self.reconstruir_interface)
            except Exception:pass
            try:self.after(420,self._maybe_show_sound_consent)
            except Exception:pass
            try:self.after(760,self._maybe_show_first_run_tutorial)
            except Exception:pass

        choices=self._language_choices()
        for idx,(code,name,sub) in enumerate(choices):
            parent=row1 if idx<3 else row2
            img=self._language_flag_image(code)
            btn=ctk.CTkButton(
                parent,text=f"{name}\n{sub}",image=img,compound="left",anchor="w",
                height=86,corner_radius=14,fg_color=t["card"],hover_color=t["card_active"],
                border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.48),
                text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=12,weight="bold"),
                command=lambda c=code:choose(c)
            )
            btn.pack(side="left",fill="x",expand=True,padx=4)

        footer=ctk.CTkFrame(panel,fg_color="transparent")
        footer.pack(fill="x",padx=24,pady=(4,16))
        ctk.CTkLabel(footer,text="SELECT TO CONTINUE  //  5 LANGUAGES",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        ctk.CTkLabel(footer,text="LOCAL PREFERENCE",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(side="right")

'''
regex_rep(
    r'    def _language_choices\(self\):\n.*?(?=    def _tutorial_username\(self\):\n)',
    language_block,
    'real flag language picker'
)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------
for marker in (
    'APP_VERSION = "3.19.3"',
    'def _language_flag_image(self, code, size=(54,34))',
    'language_picker_revision',
    'def _zk_repaint_viewport(self, final=False)',
    'Coalesced native Canvas wheel scrolling without animated ghost trails.',
):
    if marker not in s:
        raise SystemExit('v3.19.3 patch: required marker missing: '+marker)
if 'RedrawWindow(' in s:
    raise SystemExit('v3.19.3 patch: unsafe Win32 RedrawWindow repaint still present')
if '_zk_repaint_viewport(False)' in s:
    raise SystemExit('v3.19.3 patch: per-frame repaint call still present')
for emoji_flag in ('🇧🇷','🇺🇸','🇪🇸','🇨🇳','🇫🇷'):
    if emoji_flag in s:
        raise SystemExit('v3.19.3 patch: emoji language flag still present: '+emoji_flag)

tree=ast.parse(s)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None:raise SystemExit('v3.19.3 patch: ModernConfigApp missing')
methods={n.name for n in app.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
required={'_maybe_show_first_run_language','_language_flag_image','_queue_scroll_step','_ensure_page_built','_refresh_cursor_preview','_refresh_font_preview'}
missing=sorted(required-methods)
if missing:raise SystemExit('v3.19.3 patch: missing methods: '+', '.join(missing))

path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.19.3 stable-scroll + real-flag onboarding patch')
