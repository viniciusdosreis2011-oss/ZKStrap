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
    if node is None: raise SystemExit('v3.20.18 missing method: '+name)
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

if 'APP_VERSION = "3.20.17"' not in s:
    raise SystemExit('v3.20.18 expected v3.20.17 base')
s=s.replace('APP_VERSION = "3.20.17"','APP_VERSION = "3.20.18"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Restore Proven v3.20.15 Scroll"',s,count=1)

# Restore the exact coalesced Canvas wheel behavior used before the
# Personalizar-specific v3.20.16/v3.20.17 experiments. Keep every other fix
# (theme cleanup, collapsible sections, secret unlock UX, etc.) intact.
s=replace_method(s,'_queue_scroll_step',r'''
def _queue_scroll_step(self, scrollable, step):
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
''')

ast.parse(s)
q=next(n for n in next(x for x in ast.parse(s).body if isinstance(x,ast.ClassDef) and x.name=='ModernConfigApp').body if isinstance(n,ast.FunctionDef) and n.name=='_queue_scroll_step')
qsrc=ast.get_source_segment(s,q) or ''
for marker in (
    'APP_VERSION = "3.20.18"',
    'Coalesced native Canvas wheel scrolling without animated ghost trails.',
    'self.after(12,apply_target)',
    'self.after(90,settle)',
):
    if marker not in s: raise SystemExit('v3.20.18 validation missing '+marker)
for forbidden in ('_zk_light_scroll_state','self.after(130,settle)','theme_body=getattr(self,"page_scrolls",{}).get("theme")'):
    if forbidden in qsrc: raise SystemExit('v3.20.18 old experimental scroll still present: '+forbidden)
if '_zk_section_open_state' not in s:
    raise SystemExit('v3.20.18 collapsible sections regressed')

p.write_text(s,encoding='utf-8')
print('Applied v3.20.18: restored proven pre-experiment scroll, kept all newer features')
