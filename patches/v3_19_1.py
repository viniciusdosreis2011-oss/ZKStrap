from pathlib import Path
import os, re, ast

root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
path = root / 'ZKStrap_v3_18_0.py'
s = path.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'v3.19.1 patch: pattern not found: {label}')
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v3.19.1 patch: regex pattern not found/ambiguous: {label} ({n})')
    s = ns


rep('APP_VERSION = "3.19.0"', 'APP_VERSION = "3.19.1"', 'version')
s, n = re.subn(r'BUILD_TIMESTAMP = "[^"]*"', 'BUILD_TIMESTAMP = "Lazy Boot + Smooth Viewport Repaint"', s, count=1)
if n != 1:
    raise SystemExit('v3.19.1 patch: BUILD_TIMESTAMP missing')

# ---------------------------------------------------------------------------
# 1) Smooth scroll: keep the native Canvas feel from 3.19.0, but invalidate
#    only the scrolling viewport and its child widgets on Windows. CTk widgets
#    draw rounded shapes through child canvases; when a canvas window moves very
#    quickly Windows can leave stale pixels until the next expose/paint event.
# ---------------------------------------------------------------------------
repaint_method = r'''    def _zk_repaint_viewport(self, final=False):
        """Invalidate the scroll viewport and descendants after a canvas move."""
        try:
            if os.name != "nt":
                if final:
                    self._parent_canvas.update_idletasks()
                return
            import ctypes
            hwnd = int(self._zk_host.winfo_id())
            RDW_INVALIDATE = 0x0001
            RDW_ERASE = 0x0004
            RDW_ALLCHILDREN = 0x0080
            RDW_UPDATENOW = 0x0100
            RDW_ERASENOW = 0x0200
            flags = RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN
            if final:
                flags |= RDW_UPDATENOW | RDW_ERASENOW
            ctypes.windll.user32.RedrawWindow(hwnd, 0, 0, flags)
        except Exception:
            if final:
                try:self._parent_canvas.update_idletasks()
                except Exception:pass

'''
marker = '    def _zk_canvas_resized(self, event=None):\n'
if '    def _zk_repaint_viewport(self, final=False):\n' not in s:
    if marker not in s:
        raise SystemExit('v3.19.1 patch: ZKSmoothScrollFrame repaint anchor missing')
    s = s.replace(marker, repaint_method + marker, 1)

new_queue = r'''    def _queue_scroll_step(self, scrollable, step):
        """Continuous target-following scroll with targeted viewport repaint."""
        try:
            if scrollable is None or not step:return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():return "break"

            now=time.monotonic()
            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"target":first,"job":None,"last_input":0.0}
                setattr(scrollable,"_zk_scroll_state",state)

            if now-float(state.get("last_input",0.0) or 0.0)>.22:
                state["target"]=first

            # A little less distance per notch than 3.19.0. Multiple fast wheel
            # events still extend the same target, so speed comes from intention
            # rather than from queuing intermediate redraws.
            px_per_step=66.0
            target=float(state.get("target",first) or first)+(float(step)*px_per_step/max(1.0,total))
            state["target"]=max(0.0,min(max_first,target))
            state["last_input"]=now
            self._mark_fast_scroll()

            def tick():
                state["job"]=None
                try:
                    if not canvas.winfo_exists():return
                    cur_first,cur_visible,_=self._scroll_canvas_metrics(canvas)
                    max_cur=max(0.0,1.0-cur_visible)
                    target=max(0.0,min(max_cur,float(state.get("target",cur_first))))
                    diff=target-cur_first
                    self._mark_fast_scroll()
                    if abs(diff)<0.00028:
                        canvas.yview_moveto(target)
                        try:scrollable._zk_repaint_viewport(True)
                        except Exception:pass
                        return
                    d=abs(diff)
                    alpha=.24 if d<.035 else (.34 if d<.12 else .46)
                    nxt=cur_first+diff*alpha
                    canvas.yview_moveto(max(0.0,min(max_cur,nxt)))
                    # Important: repaint the viewport after every actual move.
                    # This clears old CTk child-canvas pixels without repainting
                    # the whole app or changing the smooth target animation.
                    try:scrollable._zk_repaint_viewport(False)
                    except Exception:pass
                    state["job"]=self.after(16,tick)
                except Exception:
                    state["job"]=None

            if state.get("job") is None:
                try:state["job"]=self.after(1,tick)
                except Exception:tick()
            return "break"
        except Exception:
            return "break"

'''
regex_rep(
    r'    def _queue_scroll_step\(self, scrollable, step\):\n.*?(?=    def _install_global_scroll_router\(self\):\n)',
    new_queue,
    'smooth repaint queue'
)

# ---------------------------------------------------------------------------
# 2) Lazy page construction. The old build_right_tabview created every page
#    before the main window could appear. On slower PCs this is the long pause
#    observed at exactly 48%, because 48% is reported immediately before
#    criar_interface(). Build Home at boot; build each other page on first use.
# ---------------------------------------------------------------------------
if '    def _ensure_page_built(self,key):\n' in s:
    raise SystemExit('v3.19.1 patch: lazy page system already present')

tree = ast.parse(s)
app_cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModernConfigApp'), None)
if app_cls is None:
    raise SystemExit('v3.19.1 patch: ModernConfigApp missing')
build_fn = next((n for n in app_cls.body if isinstance(n, ast.FunctionDef) and n.name == 'build_right_tabview'), None)
if build_fn is None:
    raise SystemExit('v3.19.1 patch: build_right_tabview missing')

lines = s.splitlines(True)

def page_key_in_stmt(stmt):
    for node in ast.walk(stmt):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == '_page_shell':
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                return node.args[0].value
    return None

page_infos = []
for idx, stmt in enumerate(build_fn.body):
    key = page_key_in_stmt(stmt)
    if key:
        page_infos.append((idx, key, stmt))
if len(page_infos) < 10:
    raise SystemExit(f'v3.19.1 patch: expected many pages, found {len(page_infos)}')

post_stmt = None
for stmt in build_fn.body:
    segment = ast.get_source_segment(s, stmt) or ''
    if 'self.tab_config' in segment:
        post_stmt = stmt
        break
if post_stmt is None:
    raise SystemExit('v3.19.1 patch: build_right_tabview compatibility postamble missing')

helpers = r'''    def _refresh_lazy_compat_refs(self):
        pages=getattr(self,"pages",{})
        self.tab_config=pages.get("home")
        self.tab_performance=pages.get("fps")
        self.tab_fastflags=pages.get("fps")
        self.tab_cursor=pages.get("cursor")
        self.tab_manutencao=pages.get("maintenance")
        self.tab_recuperacao=pages.get("recovery")
        self.right_tabview=getattr(self,"content_host",None)
        self.more_tabview=getattr(self,"content_host",None)

    def _ensure_page_built(self,key):
        pages=getattr(self,"pages",{})
        if key in pages:return pages.get(key)
        builder=getattr(self,"_lazy_page_builders",{}).get(key)
        if not callable(builder):return None
        t0=time.perf_counter()
        try:
            page=builder()
        except Exception as exc:
            try:self.log_output(f"[-] Falha ao montar página {key}: {exc}")
            except Exception:pass
            return None
        self._refresh_lazy_compat_refs()
        try:self.restaurar_estado_interface()
        except Exception:pass
        # Font traversal is page-local and deferred; never scan the whole hidden
        # application tree during the boot path.
        try:
            if page is not None:
                self.after_idle(lambda p=page:self.aplicar_fonte_widgets(p) if self._widget_alive(p) else None)
        except Exception:pass
        try:_startup_log(f"LAZY PAGE {key}: {time.perf_counter()-t0:.3f}s")
        except Exception:pass
        return page

'''

parts = [helpers]
for pos, (_, key, stmt) in enumerate(page_infos):
    start_line = stmt.lineno
    if pos + 1 < len(page_infos):
        end_line = page_infos[pos + 1][2].lineno - 1
    else:
        end_line = post_stmt.lineno - 1
    section = ''.join(lines[start_line - 1:end_line])
    safe = re.sub(r'\W+', '_', key)
    method = f'    def _lazy_build_page_{safe}(self):\n'
    method += f'        if "{key}" in getattr(self,"pages",{{}}): return self.pages.get("{key}")\n'
    method += '        t=TEMAS[self.tema_atual]\n        st=self._theme_style()\n        pt=self.idioma=="pt"\n'
    method += section
    method += f'        return self.pages.get("{key}")\n\n'
    parts.append(method)

first_page_line = page_infos[0][2].lineno
# Keep the lightweight state initialization that was originally at the top of
# build_right_tabview, but none of the page bodies.
init_src = ''.join(lines[build_fn.lineno:first_page_line - 1])
entries = []
for _, key, _ in page_infos:
    safe = re.sub(r'\W+', '_', key)
    entries.append(f'"{key}": self._lazy_build_page_{safe}')
mapping = ', '.join(entries)

new_build = '    def build_right_tabview(self):\n' + init_src
new_build += f'        self._lazy_page_builders={{{mapping}}}\n'
new_build += '        self._ensure_page_built("home")\n'
new_build += '        self.current_page_key="home"\n'
new_build += '        self._refresh_lazy_compat_refs()\n'
new_build += '        self.show_page("home",animate=False)\n'

start_off = sum(len(x) for x in lines[:build_fn.lineno - 1])
end_off = sum(len(x) for x in lines[:build_fn.end_lineno])
s = s[:start_off] + ''.join(parts) + new_build + '\n' + s[end_off:]

# show_page now materializes a page immediately before trying to display it.
tree = ast.parse(s)
app_cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModernConfigApp')
show_fn = next(n for n in app_cls.body if isinstance(n, ast.FunctionDef) and n.name == 'show_page')
show_lines = s.splitlines(True)
insert_line = show_fn.lineno + 1
if show_fn.body and isinstance(show_fn.body[0], ast.Expr) and isinstance(getattr(show_fn.body[0], 'value', None), ast.Constant) and isinstance(show_fn.body[0].value.value, str):
    insert_line = show_fn.body[0].end_lineno + 1
insert_text = '        try:self._ensure_page_built(key)\n        except Exception:pass\n'
off = sum(len(x) for x in show_lines[:insert_line - 1])
s = s[:off] + insert_text + s[off:]

# ---------------------------------------------------------------------------
# 3) Startup timing + less artificial splash delay.
# ---------------------------------------------------------------------------
rep('        super().__init__()\n', '        super().__init__()\n        self._boot_perf0=time.perf_counter()\n', 'boot timer', 1)
rep(
'''        self.pasta_roblox_salva = self.config_data.get("roblox_dir", "")
        _startup_splash_update(self,self._startup_state,.48,"Preparando interface…","Montando shell, navegação e páginas","[UI] building workspace",pump=True)
        self.inicializar_efeito_matrix()
        self.criar_interface()
        _startup_splash_update(self,self._startup_state,.78,"Interface montada","Sincronizando módulos e temas","[UI] components mounted",pump=True)
''',
'''        self.pasta_roblox_salva = self.config_data.get("roblox_dir", "")
        _ui_boot_t0=time.perf_counter()
        _startup_splash_update(self,self._startup_state,.48,"Preparando interface…","Montando shell e página inicial","[UI] building lightweight workspace",pump=True)
        self.inicializar_efeito_matrix()
        _startup_splash_update(self,self._startup_state,.57,"Shell visual pronto","Montando Home e navegação","[UI] shell ready",pump=True)
        self.criar_interface()
        try:_startup_log(f"TIMING criar_interface lazy: {time.perf_counter()-_ui_boot_t0:.3f}s")
        except Exception:pass
        _startup_splash_update(self,self._startup_state,.82,"Interface essencial montada","Sincronizando estado local","[UI] essential workspace ready",pump=True)
''',
'48 percent UI block',1)
rep('        self.restaurar_estado_interface()\n', '        _restore_t0=time.perf_counter()\n        self.restaurar_estado_interface()\n        try:_startup_log(f"TIMING restore UI state: {time.perf_counter()-_restore_t0:.3f}s")\n        except Exception:pass\n', 'restore timing', 1)
rep('        _startup_splash_finish(self,self._startup_state,min_visible=2.85)\n', '        _startup_splash_finish(self,self._startup_state,min_visible=1.35)\n        try:_startup_log(f"TIMING total app construction: {time.perf_counter()-self._boot_perf0:.3f}s")\n        except Exception:pass\n', 'startup total timing', 1)
rep('        hold_until = time.time() + 0.90\n', '        hold_until = time.time() + 0.25\n', 'main splash hold', 1)
rep('                    if time.time()-done_since>=.62:\n', '                    if time.time()-done_since>=.20:\n', 'splash child done hold', 1)

# Static safety checks.
for required in (
    'APP_VERSION = "3.19.1"',
    'class ZKSmoothScrollFrame(ctk.CTkFrame):',
    'def _zk_repaint_viewport(self, final=False)',
    'def _ensure_page_built(self,key)',
    'self._lazy_page_builders=',
    'TIMING criar_interface lazy',
):
    if required not in s:
        raise SystemExit('v3.19.1 patch: required surface missing: '+required)
if 'ctk.CTkScrollableFrame(' in s:
    raise SystemExit('v3.19.1 patch: legacy CTkScrollableFrame returned')

# Final syntax/structure validation before writing.
final_tree = ast.parse(s)
app_cls = next(n for n in final_tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModernConfigApp')
methods = {n.name for n in app_cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
if '_ensure_page_built' not in methods or 'build_right_tabview' not in methods:
    raise SystemExit('v3.19.1 patch: lazy methods missing from ModernConfigApp')
lazy_count = sum(1 for name in methods if name.startswith('_lazy_build_page_'))
if lazy_count < 10:
    raise SystemExit(f'v3.19.1 patch: only {lazy_count} lazy builders generated')

path.write_text(s, encoding='utf-8')
print(f'Applied ZKStrap v3.19.1: {lazy_count} lazy pages + viewport repaint')
