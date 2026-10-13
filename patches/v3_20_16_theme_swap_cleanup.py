from pathlib import Path
import ast, os, textwrap

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')


def _class(src):
    t=ast.parse(src)
    return t,next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')

def _span(src,name):
    _,cls=_class(src); lines=src.splitlines(True)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit('theme cleanup missing method: '+name)
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')
def replace_method(src,name,body):
    _,a,b=_span(src,name);return src[:a]+_norm(body)+src[b:]
def insert_before(src,before_name,body):
    _,a,_=_span(src,before_name);return src[:a]+_norm(body)+'\n'+src[a:]

if 'APP_VERSION = "3.20.16"' not in s:raise SystemExit('theme cleanup expects v3.20.16')

s=replace_method(s,'_repair_theme_render_surfaces',r'''
def _repair_theme_render_surfaces(self):
    """Hard repaint of native/CTk surfaces so a previous theme cannot bleed into the next one."""
    try:
        t=TEMAS[self.tema_atual]
        sidebar=t.get("sidebar",t.get("card",t["bg"]));panel=t.get("panel",t.get("card",t["bg"]));bg=t.get("bg",panel)
        current=str(getattr(self,"_visible_page",None) or getattr(self,"current_page_key",None) or "")
        for obj,color in ((getattr(self,"main_container",None),bg),(getattr(self,"body_frame",None),bg),(getattr(self,"left_panel",None),sidebar),(getattr(self,"content_host",None),panel),(getattr(self,"header_frame",None),panel),(getattr(self,"bottom_frame",None),panel)):
            try:
                if obj is not None and obj.winfo_exists():obj.configure(fg_color=color)
            except Exception:pass
        nav=getattr(self,"nav_scroll",None)
        if nav is not None:
            for obj in (nav,getattr(nav,"_zk_host",None)):
                try:
                    if obj is not None and obj.winfo_exists():obj.configure(fg_color=sidebar)
                except Exception:pass
            try:nav.configure(scrollbar_button_color=t["card_active"],scrollbar_button_hover_color=t["hover"])
            except Exception:pass
            # nav._parent_canvas.configure(bg=sidebar) -- normalized through cv below.
            cv=getattr(nav,"_parent_canvas",None)
            try:
                if cv is not None and cv.winfo_exists():cv.configure(bg=sidebar,highlightbackground=sidebar,highlightcolor=sidebar)
            except Exception:pass
            sb=getattr(nav,"_scrollbar",None)
            try:
                if sb is not None and sb.winfo_exists():sb.configure(fg_color=sidebar,button_color=t["card_active"],button_hover_color=t["hover"])
            except Exception:pass
        for k,b in dict(getattr(self,"nav_buttons",{}) or {}).items():
            try:b.configure(fg_color=t["card_active"] if k==current else "transparent",hover_color=t["card_active"],text_color=t["accent"] if k==current else t["text"],border_width=1,border_color=t["accent"] if k==current else self._mix_hex(sidebar,t.get("border",t["accent"]),.25))
            except Exception:pass
        for lab in list(getattr(self,"nav_section_labels",[]) or []):
            try:lab.configure(text_color=t.get("muted","gray"))
            except Exception:pass
        try:self.header_accent_line.configure(fg_color=t["accent"])
        except Exception:pass
        for key,body in dict(getattr(self,"page_scrolls",{}) or {}).items():
            try:
                body.configure(fg_color=panel,scrollbar_button_color=t["card_active"],scrollbar_button_hover_color=t["hover"])
            except Exception:pass
            try:body._zk_host.configure(fg_color=panel)
            except Exception:pass
            try:body._parent_canvas.configure(bg=panel,highlightbackground=panel,highlightcolor=panel)
            except Exception:pass
        for key,cv in dict(getattr(self,"page_theme_canvases",{}) or {}).items():
            try:
                if cv is not None and cv.winfo_exists():
                    cv.configure(bg=panel,highlightbackground=panel,highlightcolor=panel)
                    self._draw_theme_art(cv,self.tema_atual,t)
            except Exception:pass
        for cv in (getattr(self,"canvas",None),getattr(self,"header_theme_canvas",None),getattr(self,"sidebar_theme_canvas",None),getattr(self,"dock_theme_canvas",None)):
            try:
                if cv is not None and cv.winfo_exists():
                    cv.configure(bg=panel if cv is not getattr(self,"sidebar_theme_canvas",None) else sidebar)
                    self._draw_theme_art(cv,self.tema_atual,t)
            except Exception:pass
        try:self.update_idletasks()
        except Exception:pass
    except Exception as exc:
        try:_startup_log('THEME HARD REPAINT: '+repr(exc))
        except Exception:pass

def _rebuild_visible_page_after_theme_swap(self):
    """Recreate only the visible page with the new palette; avoids full-app rebuild and stale mixed colors."""
    try:
        key=str(getattr(self,"_visible_page",None) or getattr(self,"current_page_key",None) or "")
        if not key:return
        pages=getattr(self,"pages",{})
        old=pages.get(key)
        if old is None:return
        pos=0.0
        try:
            body=getattr(self,"page_scrolls",{}).get(key);pos=float(body._parent_canvas.yview()[0]) if body is not None else 0.0
        except Exception:pos=0.0
        try:old.place_forget();old.destroy()
        except Exception:pass
        for attr in ("pages","page_scrolls","page_theme_canvases","page_art_wraps"):
            try:getattr(self,attr,{}).pop(key,None)
            except Exception:pass
        if key=="theme":
            try:self._theme_gallery_built=False
            except Exception:pass
        self._visible_page=None
        try:self._ensure_page_built(key)
        except Exception as exc:_startup_log('THEME PAGE REBUILD build: '+repr(exc));return
        try:self.show_page(key,animate=False)
        except Exception as exc:_startup_log('THEME PAGE REBUILD show: '+repr(exc))
        def restore():
            try:
                body=getattr(self,"page_scrolls",{}).get(key)
                if body is not None:body._parent_canvas.yview_moveto(max(0.0,min(.999,pos)))
            except Exception:pass
            self._repair_theme_render_surfaces()
        try:self.after(45,restore)
        except Exception:restore()
    except Exception as exc:
        try:_startup_log('THEME PAGE REBUILD: '+repr(exc))
        except Exception:pass
''')

node,a,b=_span(s,'_fast_apply_theme');chunk=s[a:b]
anchor='''        try:self._repair_theme_render_surfaces()\n        except Exception:pass\n        try:self.update_idletasks()'''
repl='''        try:self._repair_theme_render_surfaces()\n        except Exception:pass\n        try:self.after(35,self._rebuild_visible_page_after_theme_swap)\n        except Exception:pass\n        try:self.update_idletasks()'''
if anchor not in chunk:raise SystemExit('theme cleanup fast-apply anchor missing')
chunk=chunk.replace(anchor,repl,1);s=s[:a]+chunk+s[b:]

ast.parse(s)
for marker in ('def _rebuild_visible_page_after_theme_swap','nav._parent_canvas.configure(bg=sidebar','self.after(35,self._rebuild_visible_page_after_theme_swap)','body._parent_canvas.configure(bg=panel'):
    if marker not in s:raise SystemExit('theme cleanup validation missing '+marker)
p.write_text(s,encoding='utf-8')
print('Applied v3.20.16 hard theme swap cleanup')
