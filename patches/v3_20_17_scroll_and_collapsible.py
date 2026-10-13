from pathlib import Path
import ast, os, re, textwrap

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')


def _class(src):
    tree=ast.parse(src)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
    return tree,cls

def _span(src,name):
    _,cls=_class(src); lines=src.splitlines(True)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit('v3.20.17 missing method: '+name)
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

if 'APP_VERSION = "3.20.16"' not in s:
    raise SystemExit('v3.20.17 expected v3.20.16 base')
s=s.replace('APP_VERSION = "3.20.16"','APP_VERSION = "3.20.17"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Light Theme Scroll + Collapsible Heavy Sections"',s,count=1)

s=replace_method(s,'_queue_scroll_step',r'''
def _queue_scroll_step(self, scrollable, step):
    """Fast scroll for canvas-heavy Personalizar; smooth scrolling elsewhere."""
    try:
        if scrollable is None or not step:return "break"
        canvas=getattr(scrollable,"_parent_canvas",None)
        if canvas is None or not canvas.winfo_exists():return "break"

        theme_body=getattr(self,"page_scrolls",{}).get("theme")
        if scrollable is theme_body:
            # Personalizar contains many live preview canvases. Repainting those
            # during every wheel event is extremely expensive on Windows. Move
            # the native canvas immediately and do ONE cleanup after scrolling
            # settles instead of invalidating every descendant per frame.
            self._mark_fast_scroll()
            state=getattr(scrollable,"_zk_light_scroll_state",None)
            if not isinstance(state,dict):
                state={"settle":None}; setattr(scrollable,"_zk_light_scroll_state",state)
            direction=1 if float(step)>0 else -1
            units=max(2,min(12,int(abs(float(step))*3)))
            canvas.yview_scroll(direction*units,"units")
            try:
                old=state.get("settle")
                if old is not None:self.after_cancel(old)
            except Exception:pass
            def settle():
                state["settle"]=None
                try:self._repair_theme_render_surfaces()
                except Exception:pass
            try:state["settle"]=self.after(130,settle)
            except Exception:state["settle"]=None
            return "break"

        now=time.monotonic()
        first,visible,total=self._scroll_canvas_metrics(canvas)
        max_first=max(0.0,1.0-visible)
        if max_first<=0.0:return "break"
        state=getattr(scrollable,"_zk_scroll_state",None)
        if not isinstance(state,dict):
            state={"target":first,"job":None,"last_input":0.0}
            setattr(scrollable,"_zk_scroll_state",state)
        if now-float(state.get("last_input",0.0) or 0.0)>.20:state["target"]=first
        target=float(state.get("target",first) or first)+(float(step)*64.0/max(1.0,total))
        state["target"]=max(0.0,min(max_first,target));state["last_input"]=now
        self._mark_fast_scroll()
        def tick():
            state["job"]=None
            try:
                if not canvas.winfo_exists():return
                cur,vis,_=self._scroll_canvas_metrics(canvas);limit=max(0.0,1.0-vis);dest=max(0.0,min(limit,float(state.get("target",cur))));diff=dest-cur
                if abs(diff)<0.00030:
                    canvas.yview_moveto(dest)
                    try:scrollable._zk_repaint_viewport(True)
                    except Exception:pass
                    return
                d=abs(diff);alpha=.27 if d<.035 else (.38 if d<.12 else .50)
                canvas.yview_moveto(max(0.0,min(limit,cur+diff*alpha)))
                state["job"]=self.after(14,tick)
            except Exception:state["job"]=None
        if state.get("job") is None:
            try:state["job"]=self.after(1,tick)
            except Exception:tick()
        return "break"
    except Exception:return "break"
''')

s=replace_method(s,'_section_card',r'''
def _section_card(self,parent,title,description=""):
    """Section card that automatically collapses option-dense groups."""
    t=TEMAS[self.tema_atual]; st=self._theme_style(); radius=max(14,st["card_radius"]); border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34)
    card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border); card.pack(fill="x",padx=6,pady=8)
    ctk.CTkFrame(card,height=3,fg_color=self._mix_hex(t["card"],t["accent"],.72),corner_radius=2).pack(fill="x",padx=12)
    content=ctk.CTkFrame(card,fg_color="transparent"); content.pack(fill="both",expand=True,padx=16,pady=(10,12))
    head=ctk.CTkFrame(content,fg_color=self._mix_hex(t["card"],t.get("icon_bg",t["card_active"]),.62),corner_radius=12,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.18)); head.pack(fill="x",pady=(0,6))
    icon=ctk.CTkFrame(head,width=48,height=48,corner_radius=12,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.08),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.36)); icon.pack(side="left",padx=(8,10),pady=7); icon.pack_propagate(False)
    text=str(title or "").upper()
    if "ROBLOX" in text: im=self._roblox_logo_ctk(31)
    else:
        key="generic"
        for words,k in ((("FPS","DESEMPENHO","PERFORMANCE"),"performance"),(("CURSOR",),"cursor"),(("FONTE","FONT"),"font"),(("PING","LATÊNCIA","LATENCY","REDE","NETWORK"),"network"),(("UPDATE","ATUALIZA"),"update"),(("CACHE",),"cache"),(("ÁUDIO","AUDIO","MÚSICA","MUSIC","SOUND"),"audio"),(("SPOTIFY",),"spotify"),(("COMBO","BUILD"),"combo"),(("ROULETTE","ROLETA"),"roulette"),(("CREATOR","CRIADOR"),"creator"),(("SETUP",),"setups"),(("MANUT","MAINT"),"maintenance"),(("RECUP","RECOVER","RESTORE"),"recovery"),(("BUG","SUGEST","FEEDBACK"),"feedback"),(("TEMA","THEME","PERSONAL"),"theme"),(("SOBRE","ABOUT","INFO"),"about"),(("INÍCIO","HOME","STATUS"),"home"),(("FIRST RUN","PRIMEIRO","TUTORIAL"),"first_run")):
            if any(w in text for w in words):key=k;break
        im=self._ui_pictogram_ctk(key,31)
    if im is not None: ctk.CTkLabel(icon,text="",image=im).pack(fill="both",expand=True)
    else: ctk.CTkLabel(icon,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=17,weight="bold")).pack(fill="both",expand=True)
    tw=ctk.CTkFrame(head,fg_color="transparent"); tw.pack(side="left",fill="x",expand=True,pady=7)
    ctk.CTkLabel(tw,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=14,weight="bold"),anchor="w").pack(anchor="w",fill="x")

    # Keep the header visible while the option body can be collapsed.
    body=ctk.CTkFrame(content,fg_color="transparent")
    body.pack(fill="both",expand=True,pady=(2,0))
    state_map=getattr(self,"_zk_section_open_state",None)
    if not isinstance(state_map,dict):state_map={};self._zk_section_open_state=state_map
    state_key=str(title or "")
    arrow=ctk.CTkButton(head,text="⌄",width=32,height=30,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.35),text_color=t["accent"])

    def set_open(opened):
        state_map[state_key]=bool(opened)
        try:
            if opened:
                if not body.winfo_ismapped():body.pack(fill="both",expand=True,pady=(2,0))
                arrow.configure(text="⌄")
            else:
                body.pack_forget();arrow.configure(text="›")
            try:
                sync=getattr(parent,"_zk_sync_region",None)
                if callable(sync):self.after_idle(sync)
            except Exception:pass
        except Exception:pass
    arrow.configure(command=lambda:set_open(not bool(state_map.get(state_key,False))))

    if description:
        full=str(description); short=self._ui_compact_copy(full,92)
        ctk.CTkButton(head,text="i",width=30,height=30,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.35),text_color=t["accent"],command=lambda tt=title,dd=full:messagebox.showinfo(str(tt),str(dd),parent=self)).pack(side="right",padx=(4,10))
        ctk.CTkLabel(content,text=short,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=8),wraplength=980,justify="left",anchor="w").pack(fill="x",anchor="w",padx=4,pady=(0,3),before=body)

    def count_interactive(widget):
        total=0
        try:
            for child in widget.winfo_children():
                cname=child.__class__.__name__.lower()
                if any(k in cname for k in ("button","switch","slider","combobox","optionmenu","entry","checkbox","textbox")):total+=1
                total+=count_interactive(child)
        except Exception:pass
        return total
    def finish_density_check():
        try:
            dense=count_interactive(body)>=4
            if dense:
                arrow.pack(side="right",padx=(4,8),pady=7)
                set_open(bool(state_map.get(state_key,False)))
            else:
                state_map[state_key]=True
                set_open(True)
                try:arrow.pack_forget()
                except Exception:pass
        except Exception:pass
    try:self.after_idle(finish_density_check)
    except Exception:finish_density_check()
    return body
''')

ast.parse(s)
for marker in (
    'APP_VERSION = "3.20.17"',
    'def _queue_scroll_step(self, scrollable, step):',
    '_zk_light_scroll_state',
    'self.after(130,settle)',
    'def _section_card(self,parent,title,description=""):',
    '_zk_section_open_state',
    'count_interactive(body)>=4',
    'text="›"',
):
    if marker not in s:raise SystemExit('v3.20.17 validation missing '+marker)
p.write_text(s,encoding='utf-8')
print('Applied v3.20.17 lightweight Personalizar scroll + collapsible heavy sections')
