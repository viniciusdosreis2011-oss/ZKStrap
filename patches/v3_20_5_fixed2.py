from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def lines_pos(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.20.5 final: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.5 final: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def rename_method(name,new_name):
    global s
    _,a,b=method_span(s,name)
    chunk=s[a:b]
    chunk,n=re.subn(r'^(\s*)def\s+'+re.escape(name)+r'\s*\(',r'\1def '+new_name+'(',chunk,count=1,flags=re.M)
    if n!=1:raise SystemExit('v3.20.5 final: rename failed '+name)
    s=s[:a]+chunk+s[b:]


if 'APP_VERSION = "3.20.4"' not in s:raise SystemExit('v3.20.5 final: expected v3.20.4 base')
s=s.replace('APP_VERSION = "3.20.4"','APP_VERSION = "3.20.5"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Single First Run Router + Tutorial Route Fix"',s,count=1)
if n!=1:raise SystemExit('v3.20.5 final: timestamp')

# REAL BLUR: remove the opaque frame that covered the blurred screenshot.
_,a,b=method_span(s,'_zk_blur_cover')
chunk=s[a:b]
old='''        shade=ctk.CTkFrame(cover,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.10),corner_radius=0);shade.place(x=0,y=0,relwidth=1,relheight=1);cover._zk_shade=shade
        cover.lift();return cover'''
new='''        cover._zk_shade=None
        cover.lift();return cover'''
if old not in chunk:raise SystemExit('v3.20.5 final: blur anchor')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

# LANGUAGE is always stage 1. Replay revision 6 once for beta verification.
_,a,b=method_span(s,'_maybe_show_first_run_language')
chunk=s[a:b]
chunk,n1=re.subn(r'picker_rev\s*>=\s*5\b','picker_rev>=6',chunk,count=1)
chunk,n2=re.subn(r'(\["language_picker_revision"\]\s*=\s*)5\b',r'\g<1>6',chunk,count=1)
if n1!=1 or n2!=1:raise SystemExit(f'v3.20.5 final: language revision {n1}/{n2}')
if 'try:self.after(120,self._first_run_after_language)' not in chunk:raise SystemExit('v3.20.5 final: language handoff')
chunk=chunk.replace('try:self.after(120,self._first_run_after_language)','try:self.after(40,self._first_run_route)',1)
s=s[:a]+chunk+s[b:]

# Preserve v3.20.4's good visual implementations behind guarded public methods.
rename_method('_abrir_onboarding_username','_abrir_onboarding_username_ui_3205')
rename_method('abrir_tutorial','_abrir_tutorial_ui_3205')

# Roblox completion must call the cinematic tutorial, never GUI INTERATIVO.
_,a,b=method_span(s,'_abrir_onboarding_username_ui_3205')
chunk=s[a:b]
old='self._tutorial_panel=None;self.after(20,lambda:self._abrir_tutorial_passos(replay=not primeiro_acesso))'
new='self._tutorial_panel=None;self.after(20,lambda:self.abrir_tutorial(primeiro_acesso=bool(primeiro_acesso)))'
if old not in chunk:raise SystemExit('v3.20.5 final: Roblox tutorial handoff')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

# Replace existing legacy startup/tutorial functions IN PLACE instead of adding
# duplicates. Old timers can keep calling these names; all converge on router.
replace_method('_first_run_after_language',r'''    def _first_run_after_language(self):
        return self._first_run_route()
''')
replace_method('_maybe_show_first_run_tutorial',r'''    def _maybe_show_first_run_tutorial(self):
        return self._first_run_route()
''')
replace_method('_abrir_tutorial_passos',r'''    def _abrir_tutorial_passos(self, replay=False):
        """Legacy GUI INTERATIVO retired; delegate to cinematic tutorial."""
        return self.abrir_tutorial(primeiro_acesso=not bool(replay))
''')

# Add only the new state engine + guarded public entrypoints.
router=r'''    def _first_run_stage(self):
        try:rev=int(self.config_data.get("language_picker_revision",0) or 0)
        except Exception:rev=0
        if not bool(getattr(self,"language_selected",False)) or rev<6:return "language"
        if not bool(self.config_data.get("roblox_onboarding_completed",False)):return "roblox"
        if not bool(getattr(self,"tutorial_completed",False)):return "tutorial"
        if not bool(self.config_data.get("first_run_setup_completed",False)):return "setup"
        return "done"

    def _first_run_route(self):
        """Authoritative first-run order: Language -> Roblox -> Tutorial -> Setup."""
        stage=self._first_run_stage()
        current=str(getattr(self,"_first_run_active_stage","") or "")
        panel=None
        if stage=="language":panel=getattr(self,"_language_panel",None)
        elif stage in ("roblox","tutorial"):panel=getattr(self,"_tutorial_panel",None)
        elif stage=="setup":panel=getattr(self,"_first_run_setup_panel",None)
        try:
            if current==stage and panel is not None and panel.winfo_exists():
                panel.lift();return
        except Exception:pass
        self._first_run_active_stage=stage
        if stage=="language":return self._maybe_show_first_run_language()
        if stage=="roblox":return self._abrir_onboarding_username_ui_3205(primeiro_acesso=True)
        if stage=="tutorial":return self._abrir_tutorial_ui_3205(primeiro_acesso=True)
        if stage=="setup":return self._show_first_run_setup_choice()
        self._first_run_active_stage="done"

    def _abrir_onboarding_username(self, primeiro_acesso=True):
        if primeiro_acesso and self._first_run_stage()!="roblox":
            return self._first_run_route()
        return self._abrir_onboarding_username_ui_3205(primeiro_acesso=primeiro_acesso)

    def abrir_tutorial(self, primeiro_acesso=False):
        if primeiro_acesso and self._first_run_stage()!="tutorial":
            return self._first_run_route()
        return self._abrir_tutorial_ui_3205(primeiro_acesso=primeiro_acesso)
'''
_,cls=app_class(s);_,pos=lines_pos(s);insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+router.rstrip()+"\n"+s[insert_at:]

# Intentional fallback if screenshot capture cannot render a page sample.
_,a,b=method_span(s,'_tutorial_capture_preview')
chunk=s[a:b]
old='lab.configure(image=None,text=self._L("Amostra desta aba","This tab preview","Vista previa de esta pestaña","此页面预览","Aperçu de cet onglet"))'
new='lab.configure(image=None,text=self._L("Prévia indisponível — avance e tente novamente.","Preview unavailable — move forward and try again.","Vista previa no disponible — avanza e inténtalo otra vez.","预览暂不可用，请继续后重试。","Aperçu indisponible — avancez puis réessayez."))'
if old in chunk:chunk=chunk.replace(old,new,1)
s=s[:a]+chunk+s[b:]

# Validate exact method uniqueness, because duplicate first-run methods caused
# the Nick -> Language -> Nick -> Language loop in v3.20.4.
tree,cls=app_class(s)
names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_first_run_after_language','_maybe_show_first_run_tutorial','_abrir_tutorial_passos','_abrir_onboarding_username','abrir_tutorial','_first_run_stage','_first_run_route'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.5 final: {unique} count={names.count(unique)}')

for needle in (
    'APP_VERSION = "3.20.5"','picker_rev>=6','["language_picker_revision"]=6',
    'def _abrir_onboarding_username_ui_3205(','def _abrir_tutorial_ui_3205(',
    'Authoritative first-run order: Language -> Roblox -> Tutorial -> Setup.',
    'Legacy GUI INTERATIVO retired','cover._zk_shade=None',
):
    if needle not in s:raise SystemExit('v3.20.5 final: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.5 final: unsafe repaint')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied final v3.20.5 single first-run router patch')
