from pathlib import Path
import os, re

root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
path = root / 'ZKStrap_v3_18_0.py'
s = path.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'v3.18.7 patch: pattern not found: {label}')
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v3.18.7 patch: regex pattern not found/ambiguous: {label} ({n})')
    s = ns


rep('APP_VERSION = "3.18.6"', 'APP_VERSION = "3.18.7"', 'version')
rep('BUILD_TIMESTAMP = "Input Polish + Spotify Volume + Visual Icons"', 'BUILD_TIMESTAMP = "Scroll Router + Visual Depth"', 'timestamp')

# ------------------------------------------------------------------
# SCROLL FIX v2
# CustomTkinter CTkScrollableFrame installs bind_all(<MouseWheel>) for every
# instance and scrolls directly on each wheel event. Binding only the canvas
# therefore did not stop the original global handlers. v3.18.7 removes those
# global CTk wheel handlers after page construction and installs ONE router.
# The router drops intermediate frames and renders only the newest target
# position at ~33 FPS, preventing a huge Tk redraw backlog during fast wheel.
# ------------------------------------------------------------------
scroll_block = r'''    def _mark_fast_scroll(self):
        self._scroll_active_until=time.monotonic()+0.24

    def _scroll_widget_chain_has(self, widget, names):
        try:
            cur=widget
            for _ in range(36):
                if cur is None:break
                cls=type(cur).__name__.lower()
                if any(n in cls for n in names):return True
                cur=getattr(cur,"master",None)
        except Exception:pass
        return False

    def _scroll_is_descendant(self, widget, ancestor):
        try:
            cur=widget
            for _ in range(48):
                if cur is ancestor:return True
                cur=getattr(cur,"master",None)
                if cur is None:break
        except Exception:pass
        return False

    def _scroll_canvas_metrics(self, canvas):
        try:
            first,last=canvas.yview()
        except Exception:
            first,last=0.0,1.0
        visible=max(0.0,min(1.0,float(last)-float(first)))
        total=1.0
        try:
            raw=canvas.cget("scrollregion")
            vals=[float(v) for v in canvas.tk.splitlist(raw)]
            if len(vals)>=4: total=max(1.0,vals[3]-vals[1])
        except Exception:
            try:
                box=canvas.bbox("all")
                if box:total=max(1.0,float(box[3]-box[1]))
            except Exception:pass
        return float(first),visible,total

    def _queue_scroll_step(self, scrollable, step):
        """Latest-position scrolling: wheel bursts update one target, not a queue of redraws."""
        try:
            if scrollable is None or not step:return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():return "break"
            now=time.monotonic()
            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"target":first,"job":None,"last_input":0.0,"settle":None}
                setattr(scrollable,"_zk_scroll_state",state)
            if now-float(state.get("last_input",0.0) or 0.0)>.22:
                state["target"]=first
            pixel_delta=float(step)*72.0
            target=float(state.get("target",first) or first)+(pixel_delta/max(1.0,total))
            state["target"]=max(0.0,min(max_first,target))
            state["last_input"]=now
            self._mark_fast_scroll()

            def render_latest():
                state["job"]=None
                try:
                    if not canvas.winfo_exists():return
                    _,vis,_=self._scroll_canvas_metrics(canvas)
                    pos=max(0.0,min(max(0.0,1.0-vis),float(state.get("target",0.0))))
                    canvas.yview_moveto(pos)
                except Exception:return
                try:canvas.update_idletasks()
                except Exception:pass
                if time.monotonic()-float(state.get("last_input",0.0) or 0.0)<.045:
                    try:state["job"]=self.after(30,render_latest)
                    except Exception:state["job"]=None

            if state.get("job") is None:
                try:state["job"]=self.after(1,render_latest)
                except Exception:render_latest()
            return "break"
        except Exception:
            return "break"

    def _install_global_scroll_router(self):
        """Replace CTkScrollableFrame's per-instance bind_all handlers with one app router."""
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:pass
        try:
            self.unbind_all("<Button-4>"); self.unbind_all("<Button-5>")
        except Exception:pass

        def route(event):
            if self._scroll_widget_chain_has(getattr(event,"widget",None),("slider","scrollbar","combobox","spinbox")):
                return None
            widget=getattr(event,"widget",None)
            target=None
            nav=getattr(self,"nav_scroll",None)
            if nav is not None and self._scroll_is_descendant(widget,nav):
                target=nav
            else:
                key=str(getattr(self,"current_page_key","") or "")
                body=getattr(self,"page_scrolls",{}).get(key)
                host=getattr(self,"content_host",None)
                if body is not None and (self._scroll_is_descendant(widget,body) or (host is not None and self._scroll_is_descendant(widget,host))):
                    target=body
            if target is None:return None
            delta=getattr(event,"delta",0)
            if delta:
                notches=max(1,min(5,int(round(abs(float(delta))/120.0)) or 1))
                return self._queue_scroll_step(target,(-1 if delta>0 else 1)*notches)
            num=getattr(event,"num",0)
            if num in (4,5):return self._queue_scroll_step(target,-1 if num==4 else 1)
            return None

        try:self.bind_all("<MouseWheel>",route,add=False)
        except Exception:pass
        try:
            self.bind_all("<Button-4>",route,add=False)
            self.bind_all("<Button-5>",route,add=False)
        except Exception:pass

    def _install_smooth_scroll(self, scrollable, units=1):
        """Register a page for the global wheel router after all CTk frames are built."""
        try:
            setattr(scrollable,"_zk_scroll_units",max(1,int(units)))
            self.after_idle(self._install_global_scroll_router)
        except Exception:pass

    def _bind_outer_scroll(self, widget, page_key):
        """No local wheel scrolling: the app-wide router owns every page wheel event."""
        try:
            target=getattr(widget,"_textbox",widget)
            def on_wheel(event):
                body=getattr(self,"page_scrolls",{}).get(page_key)
                if body is None:return "break"
                delta=getattr(event,"delta",0)
                if delta:
                    notches=max(1,min(5,int(round(abs(float(delta))/120.0)) or 1))
                    return self._queue_scroll_step(body,(-1 if delta>0 else 1)*notches)
                return "break"
            target.bind("<MouseWheel>",on_wheel,add=False)
            target.bind("<Button-4>",lambda e:self._queue_scroll_step(getattr(self,"page_scrolls",{}).get(page_key),-1),add=False)
            target.bind("<Button-5>",lambda e:self._queue_scroll_step(getattr(self,"page_scrolls",{}).get(page_key),1),add=False)
        except Exception:pass

'''
regex_rep(
    r'    def _mark_fast_scroll\(self\):\n.*?(?=    def _page_shell\(self, key, title, subtitle=""\):\n)',
    scroll_block,
    'replace scroll system'
)

new_section_card = r'''    def _section_card(self, parent, title, description=""):
        t=TEMAS[self.tema_atual]; st=self._theme_style()
        radius=max(14,st["card_radius"])
        border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border)
        card.pack(fill="x",padx=6,pady=10)
        ctk.CTkFrame(card,height=3,fg_color=self._mix_hex(t["card"],t["accent"],.72),corner_radius=2).pack(fill="x",padx=12,pady=(0,0))
        content=ctk.CTkFrame(card,fg_color="transparent"); content.pack(fill="both",expand=True,padx=16,pady=(13,17))
        head_band=ctk.CTkFrame(content,fg_color=self._mix_hex(t["card"],t.get("icon_bg",t["card_active"]),.62),corner_radius=12,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.18))
        head_band.pack(fill="x",pady=(0,8))
        icon_chip=ctk.CTkFrame(head_band,width=46,height=46,corner_radius=12,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.10),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.46))
        icon_chip.pack(side="left",padx=(8,11),pady=8); icon_chip.pack_propagate(False)
        ctk.CTkLabel(icon_chip,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=18,weight="bold")).pack(fill="both",expand=True)
        title_wrap=ctk.CTkFrame(head_band,fg_color="transparent"); title_wrap.pack(side="left",fill="x",expand=True,pady=8)
        ctk.CTkLabel(title_wrap,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(anchor="w",fill="x")
        ctk.CTkLabel(title_wrap,text="ZKSTRAP",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=6,weight="bold"),anchor="w").pack(anchor="w",pady=(2,0))
        ctk.CTkLabel(head_band,text="•••",text_color=self._mix_hex(t.get("muted","gray"),t["accent"],.35),font=ctk.CTkFont(size=11,weight="bold")).pack(side="right",padx=13)
        if description:
            ctk.CTkLabel(content,text=description,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=10),wraplength=1020,justify="left",anchor="w").pack(fill="x",anchor="w",padx=4,pady=(1,5))
        return content

'''
regex_rep(
    r'    def _section_card\(self, parent, title, description=""\):\n.*?(?=    def _module_switch\(self, parent, key, label=None, description=None\):\n)',
    new_section_card,
    'section card visual redesign'
)

module_helper = r'''    def _module_icon_for_key(self, key):
        return {
            "performance_boost":"⚡",
            "gray_sky":"☁",
            "fps_unlock":"∞",
            "ping_boost":"⌁",
            "telemetry_off":"◉",
            "micro_opt":"⌘",
            "draco_aura":"✦",
        }.get(str(key),"◆")

'''
anchor='    def _module_switch(self, parent, key, label=None, description=None):\n'
if anchor not in s:raise SystemExit('v3.18.7 patch: module switch anchor missing')
s=s.replace(anchor,module_helper+anchor,1)

new_module_switch = r'''    def _module_switch(self, parent, key, label=None, description=None):
        t=TEMAS[self.tema_atual]; st=self._theme_style(); data=FLAG_MODULES[key]
        label=label or (data["pt"] if self.idioma=="pt" else data["en"])
        if description is None:description=data["tooltip_pt"] if self.idioma=="pt" else data["tooltip_en"]
        active=bool(self.module_states.get(key,False))
        border=t["accent"] if active else self._mix_hex(t["card_active"],t["border"],.34)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=max(13,st["card_radius"]),border_width=1,border_color=border)
        card.pack(fill="x",padx=8,pady=7)
        ctk.CTkFrame(card,height=3,fg_color=t["accent"] if active else self._mix_hex(t["card_active"],t["accent"],.20),corner_radius=2).pack(fill="x",padx=12)
        row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=13,pady=11)
        icon_box=ctk.CTkFrame(row,width=48,height=48,corner_radius=13,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.13 if active else .04),border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.46 if active else .18))
        icon_box.pack(side="left",padx=(0,11)); icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box,text=self._module_icon_for_key(key),text_color=t["accent"] if active else self._mix_hex(t.get("muted","gray"),t["accent"],.30),font=ctk.CTkFont(family="Segoe UI Symbol",size=19,weight="bold")).pack(fill="both",expand=True)
        txt=ctk.CTkFrame(row,fg_color="transparent"); txt.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(txt,text=label,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"),anchor="w").pack(anchor="w",fill="x")
        ctk.CTkLabel(txt,text=description,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=760,justify="left",anchor="w").pack(anchor="w",fill="x",pady=(3,0))
        controls=ctk.CTkFrame(row,fg_color="transparent"); controls.pack(side="right",padx=(12,0))
        state=ctk.CTkLabel(controls,text=("●  ON" if active else "○  OFF"),height=27,corner_radius=9,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.12 if active else .0),text_color=t["accent"] if active else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold"))
        state.pack(side="left",padx=(0,9))
        sw=ctk.CTkSwitch(controls,text="",width=48,command=lambda k=key:self.evento_switch_modulo(k),progress_color=t["accent"],button_color=t["text"],button_hover_color=t["hover"],fg_color=t["card_active"])
        sw.pack(side="left")
        if active:sw.select()
        self.module_switches[key]=sw; self.module_cards[key]=card
        return card,sw

'''
regex_rep(
    r'    def _module_switch\(self, parent, key, label=None, description=None\):\n.*?(?=    def build_right_tabview\(self\):\n)',
    new_module_switch,
    'module card visual redesign'
)

path.write_text(s,encoding='utf-8')
print('patched v3.18.7',path,len(s.encode('utf-8')))
