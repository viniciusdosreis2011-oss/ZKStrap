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
    if node is None: raise SystemExit('v3.20.19 missing method: '+name)
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

if 'APP_VERSION = "3.20.18"' not in s:
    raise SystemExit('v3.20.19 expected v3.20.18 base')
s=s.replace('APP_VERSION = "3.20.18"','APP_VERSION = "3.20.19"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Creator Swap Reset + Theme Scroll Live + Pacific Calm"',s,count=1)

# Creator page copy must describe the new round-level rule, not the old per-card rule.
# Target the actual page method: the same phrases also exist in the legacy i18n row table.
node,a,b=_span(s,'_lazy_build_page_creator'); chunk=s[a:b]
old_pt="Trocas são limitadas a 2 por desafio. Winstreak/killstreak só contam contra players de 5M+; 2.5M não conta."
new_pt="A rodada inteira tem 2 trocas; o contador reseta ao gerar outros desafios ou concluir todos. Winstreak/killstreak só contam contra players de 5M+; 2.5M não conta."
old_en="Choose difficulty and quantity. Each challenge can be rerolled only twice."
new_en="Choose difficulty and quantity. Each round has two rerolls total; the counter resets when you generate a new set or complete them all."
if old_pt not in chunk or old_en not in chunk: raise SystemExit('v3.20.19 creator page copy anchor missing')
chunk=chunk.replace(old_pt,new_pt,1).replace(old_en,new_en,1); s=s[:a]+chunk+s[b:]

# PACIFICO — calm normal Core theme. No external/generated assets required.
anchor='TEMAS.update(_SECRET_THEME_PALETTES)\n\nfor _nome_tema, _tema in TEMAS.items():'
insert='''TEMAS.update(_SECRET_THEME_PALETTES)\n\n# Calm ocean identity requested for the regular Core gallery.\nTEMAS["Pacífico"] = {\n    "bg":"#061214",\n    "card":"#0C2021",\n    "card_active":"#163536",\n    "panel":"#091A1C",\n    "sidebar":"#081719",\n    "icon_bg":"#122D2F",\n    "accent":"#7EDBC4",\n    "hover":"#A9EAD9",\n    "text":"#EDF9F6",\n    "muted":"#7FA39F",\n    "border":"#579BA5",\n}\n\nfor _nome_tema, _tema in TEMAS.items():'''
if anchor not in s: raise SystemExit('v3.20.19 Pacífico palette anchor missing')
s=s.replace(anchor,insert,1)

anchor='THEME_STYLE = {'
pos=s.find(anchor)
if pos<0: raise SystemExit('v3.20.19 THEME_STYLE anchor missing')
s=s[:pos]+'THEME_DECOR["Pacífico"] = {"tag":"PACIFIC TIDE", "icon":"≈", "symbols":"≈·○~"}\n\n'+s[pos:]

anchor='# Unlockable themes live in a dedicated locked gallery.'
pos=s.find(anchor)
if pos<0: raise SystemExit('v3.20.19 unlockable anchor missing')
s=s[:pos]+'THEME_STYLE["Pacífico"] = {"radius":24,"nav_radius":17,"card_radius":22,"border_width":1,"accent2":"#8DB7D1","motif":"TIDE"}\n\n'+s[pos:]

static_anchor='''            elif theme_name=="ZKStrap Core":\n                # assinatura do próprio app: monograma gigante, slashes e módulos assimétricos'''
static_branch='''            elif theme_name=="Pacífico":\n                # Horizonte calmo, mar em camadas e reflexos discretos.\n                horizon=int(h*.38)\n                sky=self._mix_hex(base,accent2,.08)\n                sea=self._mix_hex(base,accent,.10)\n                rect(0,0,w,horizon,fill=sky)\n                rect(0,horizon,w,h,fill=sea)\n                sx=int(w*.80); sy=int(h*.24); rr=max(10,min(24,int(h*.10)))\n                canvas.create_oval(sx-rr,sy-rr,sx+rr,sy+rr,fill=self._mix_hex(base,accent2,.42),outline=self._mix_hex(base,accent2,.64),width=1)\n                for row in range(5):\n                    yy=horizon+10+row*max(12,int((h-horizon-18)/5))\n                    pts=[]\n                    for x in range(-16,w+24,24):\n                        wave=math.sin(x/74.0+phase*.055+row*.72)* (3.2+row*.45)\n                        pts += [x,int(yy+wave)]\n                    if len(pts)>=4:\n                        canvas.create_line(*pts,fill=accent if row==1 else (accent2 if row==3 else line),width=2 if row==1 else 1,smooth=True)\n                for j in range(7):\n                    gx=int(w*(.10+j*.12)); gy=int(h*(.58+(j%3)*.09))\n                    gl=10+(j%3)*7\n                    canvas.create_line(gx-gl,gy,gx+gl,gy,fill=self._mix_hex(base,accent,.26+(j%2)*.08),width=1)\n                corner_frame(self._mix_hex(border,accent2,.55),18); micro_tag("PACÍFICO // CALM TIDE")\n\n            elif theme_name=="ZKStrap Core":\n                # assinatura do próprio app: monograma gigante, slashes e módulos assimétricos'''
if static_anchor not in s: raise SystemExit('v3.20.19 static Pacífico anchor missing')
s=s.replace(static_anchor,static_branch,1)

motion_anchor='''            elif theme_name=="ZKStrap Core":\n                # Movimento assinatura: slash principal + trilhas paralelas + módulos pulsantes'''
motion_branch='''            elif theme_name=="Pacífico":\n                # Movimento quase imperceptível: brilho lento correndo pela superfície.\n                for j in range(6):\n                    px=int((j*151+ph*(2.0+(j%2)*.55))%max(1,w))\n                    py=int(h*(.56+(j%3)*.10)+math.sin(ph*.055+j)*2)\n                    half=5+(j%3)*4\n                    canvas.create_line(px-half,py,px+half,py,fill=accent2 if j%3==0 else self._mix_hex(base,accent,.48),width=1)\n                pts=[]; yy=int(h*.79)\n                for x in range(-10,w+20,28):\n                    pts += [x,yy+int(math.sin(x/82.0+ph*.045)*4)]\n                if len(pts)>=4: canvas.create_line(*pts,fill=self._mix_hex(base,accent,.58),width=1,smooth=True)\n\n            elif theme_name=="ZKStrap Core":\n                # Movimento assinatura: slash principal + trilhas paralelas + módulos pulsantes'''
if motion_anchor not in s: raise SystemExit('v3.20.19 motion Pacífico anchor missing')
s=s.replace(motion_anchor,motion_branch,1)
s=s.replace('elif theme_name in ("Blox Fruits","Deep Ocean"):', 'elif theme_name in ("Blox Fruits","Deep Ocean","Pacífico"):',1)

# Theme gallery scroll: keep animations live and remove forced settle repaint.
s=replace_method(s,'_queue_scroll_step',r'''
def _queue_scroll_step(self, scrollable, step):
    """Coalesced Canvas wheel scroll; Personalizar stays live while moving."""
    try:
        if scrollable is None or not step:return "break"
        canvas=getattr(scrollable,"_parent_canvas",None)
        if canvas is None or not canvas.winfo_exists():return "break"
        first,visible,total=self._scroll_canvas_metrics(canvas)
        max_first=max(0.0,1.0-visible)
        if max_first<=0.0:return "break"
        is_theme=(scrollable is getattr(self,"page_scrolls",{}).get("theme"))
        state=getattr(scrollable,"_zk_scroll_state",None)
        if not isinstance(state,dict):
            state={"target":first,"job":None,"last_input":0.0,"settle":None}; setattr(scrollable,"_zk_scroll_state",state)
        now=time.monotonic()
        if now-float(state.get("last_input",0.0) or 0.0)>.16:state["target"]=first
        direction=1.0 if float(step)>0 else -1.0
        magnitude=max(1.0,min(3.0,abs(float(step))))
        px=(50.0 if is_theme else 62.0)*magnitude*direction
        base=float(state.get("target",first) or first)
        state["target"]=max(0.0,min(max_first,base+(px/max(1.0,total)))); state["last_input"]=now
        if not is_theme:self._mark_fast_scroll()
        def apply_target():
            state["job"]=None
            try:
                if not canvas.winfo_exists():return
                cur_first,cur_visible,_=self._scroll_canvas_metrics(canvas); max_cur=max(0.0,1.0-cur_visible)
                dest=max(0.0,min(max_cur,float(state.get("target",cur_first))))
                canvas.yview_moveto(dest)
            except Exception:pass
        if state.get("job") is None:
            try:state["job"]=self.after(10 if is_theme else 12,apply_target)
            except Exception:apply_target()
        old_settle=state.get("settle")
        if old_settle is not None:
            try:self.after_cancel(old_settle)
            except Exception:pass
        def settle():
            state["settle"]=None
            if is_theme:return
            try:scrollable._zk_repaint_viewport(True)
            except Exception:pass
        try:state["settle"]=self.after(90,settle)
        except Exception:pass
        return "break"
    except Exception:return "break"
''')

node,a,b=_span(s,'animar_chuva_matrix_frame'); chunk=s[a:b]
old='''        try:\n            if time.monotonic() < float(getattr(self,"_scroll_active_until",0.0)):\n                if getattr(self,"loop_animacao",True): self.after(90,self.animar_chuva_matrix_frame)\n                return\n            self._ambient_phase=(getattr(self,"_ambient_phase",0.0)+0.055)%1000'''
new='''        try:\n            self._ambient_phase=(getattr(self,"_ambient_phase",0.0)+0.055)%1000'''
if old not in chunk: raise SystemExit('v3.20.19 animation pause anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

# Creator challenges: two swaps belong to the CURRENT ROUND, not each card.
init_anchor='''        self._creator_session_started_at = 0.0\n        self._creator_session_initial_count = 0\n        self._creator_secret_reveal_open = False'''
init_repl='''        self._creator_session_started_at = 0.0\n        self._creator_session_initial_count = 0\n        self._creator_session_swaps_used = 0\n        self._creator_secret_reveal_open = False'''
if init_anchor not in s: raise SystemExit('v3.20.19 creator init anchor missing')
s=s.replace(init_anchor,init_repl,1)

node,a,b=_span(s,'creator_generate_challenges'); chunk=s[a:b]
old='''        self.creator_challenges=out\n        self._creator_session_started_at=time.time(); self._creator_session_initial_count=len(out); self._creator_celebration_open=False'''
new='''        self.creator_challenges=out\n        self._creator_session_swaps_used=0\n        self._creator_session_started_at=time.time(); self._creator_session_initial_count=len(out); self._creator_celebration_open=False'''
if old not in chunk: raise SystemExit('v3.20.19 creator generate reset anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

s=replace_method(s,'creator_swap_challenge',r'''
def creator_swap_challenge(self,cid):
    old=self._creator_find(cid)
    if not old or old.get("done"):return
    used_swaps=int(getattr(self,"_creator_session_swaps_used",0) or 0)
    if used_swaps>=2:
        self.show_toast("LIMITE DE TROCAS","Essa rodada já usou as 2 trocas disponíveis. Gere outros desafios ou conclua a rodada para resetar.",kind="warning",duration=3300); return
    diff=old.get("difficulty","Médio"); used={x.get("title") for x in self.creator_challenges if isinstance(x,dict)}
    source=self._creator_secret_templates() if diff=="SECRET" else self._creator_templates()
    pool=[x for x in source if x.get("difficulty")==diff and x.get("title") not in used]
    if not pool:
        self.show_toast("CREATOR MODE","Não há outro desafio diferente nessa categoria agora.",kind="info"); return
    repl=self._creator_new_runtime(random.choice(pool),context_build=old.get("context_build"))
    self._creator_session_swaps_used=used_swaps+1
    repl["swaps_used"]=self._creator_session_swaps_used
    self.creator_challenges=[repl if x.get("id")==cid else x for x in self.creator_challenges]
    self.creator_refresh_challenges(); self._play_ui_sound("select",0)
    if repl.get("difficulty")=="SECRET":self.after(120,lambda:self._creator_secret_reveal([repl.get("title")]))
''')

node,a,b=_span(s,'creator_refresh_challenges'); chunk=s[a:b]
old='''                remain=max(0,2-int(x.get("swaps_used",0) or 0))'''
new='''                remain=max(0,2-int(getattr(self,"_creator_session_swaps_used",0) or 0))'''
if old not in chunk: raise SystemExit('v3.20.19 creator UI counter anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_creator_session_complete_if_ready'); chunk=s[a:b]
old='''        if not all(bool(x.get("done")) for x in items):return\n        self._creator_celebration_open=True; self._creator_show_session_complete(items)'''
new='''        if not all(bool(x.get("done")) for x in items):return\n        self._creator_session_swaps_used=0\n        self._creator_celebration_open=True; self._creator_show_session_complete(items)'''
if old not in chunk: raise SystemExit('v3.20.19 creator completion reset anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_creator_show_session_complete'); chunk=s[a:b]
old='''            self.creator_challenges=[]; self._creator_celebration_open=False; self._creator_session_started_at=0.0; self._creator_session_initial_count=0'''
new='''            self.creator_challenges=[]; self._creator_celebration_open=False; self._creator_session_started_at=0.0; self._creator_session_initial_count=0; self._creator_session_swaps_used=0'''
if old not in chunk: raise SystemExit('v3.20.19 creator finish reset anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

ast.parse(s)
required=(
    'APP_VERSION = "3.20.19"','TEMAS["Pacífico"]','THEME_DECOR["Pacífico"]','THEME_STYLE["Pacífico"]',
    'PACÍFICO // CALM TIDE','if not is_theme:','px=(50.0 if is_theme else 62.0)',
    'self._creator_session_swaps_used=0','Essa rodada já usou as 2 trocas disponíveis',
    'A rodada inteira tem 2 trocas','Each round has two rerolls total',
)
for marker in required:
    if marker not in s: raise SystemExit('v3.20.19 validation missing '+marker)
node,_,_=_span(s,'animar_chuva_matrix_frame'); anim=ast.get_source_segment(s,node) or ''
if '_scroll_active_until' in anim: raise SystemExit('v3.20.19 animation still pauses during scroll')
m=re.search(r'UNLOCKABLE_THEME_NAMES\s*=\s*\[[^\]]*\]',s,re.S)
if not m or 'Pacífico' in m.group(0): raise SystemExit('v3.20.19 Pacífico accidentally secret')

p.write_text(s,encoding='utf-8')
print('Applied v3.20.19: round swap reset, live theme scroll, Pacífico calm theme')
