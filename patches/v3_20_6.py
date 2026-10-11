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
    if cls is None:raise SystemExit('v3.20.6: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.6: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


if 'APP_VERSION = "3.20.5"' not in s:raise SystemExit('v3.20.6: expected v3.20.5 base')
s=s.replace('APP_VERSION = "3.20.5"','APP_VERSION = "3.20.6"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Roblox Onboarding Completion Hardening"',s,count=1)
if n!=1:raise SystemExit('v3.20.6: timestamp')

# Add one authoritative helper that survives config rewrites during the same run
# and also recognizes an already-linked profile / saved onboarding username.
helper=r'''    def _roblox_onboarding_done(self):
        if bool(getattr(self,"_roblox_onboarding_completed_runtime",False)):
            return True
        try:
            if bool(self.config_data.get("roblox_onboarding_completed",False)):
                return True
        except Exception:pass
        try:
            profile=getattr(self,"linked_profile",{}) or {}
            if str(profile.get("name","") or "").strip():
                return True
        except Exception:pass
        try:
            if str(getattr(self,"onboarding_username","") or "").strip():
                return True
        except Exception:pass
        return False

    def _mark_roblox_onboarding_done(self,username=""):
        username=str(username or "").strip().lstrip("@")
        if username:
            self.onboarding_username=username
        self._roblox_onboarding_completed_runtime=True
        try:self.roblox_onboarding_completed=True
        except Exception:pass
        try:
            self.config_data["roblox_onboarding_completed"]=True
            if username:self.config_data["onboarding_username"]=username
            self.salvar_config_app()
        except Exception:pass
        # Some legacy save/rebuild paths rewrite config_data. Re-assert after save.
        try:
            self.config_data["roblox_onboarding_completed"]=True
            if username:self.config_data["onboarding_username"]=username
        except Exception:pass
        self._roblox_onboarding_completed_runtime=True
        self._first_run_active_stage=""
        return True
'''
_,cls=app_class(s);_,pos=lines_pos(s);insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+helper.rstrip()+"\n"+s[insert_at:]

# Make the router use the hardened completion helper instead of one fragile dict flag.
_,a,b=method_span(s,'_first_run_stage')
chunk=s[a:b]
old='if not bool(self.config_data.get("roblox_onboarding_completed",False)):return "roblox"'
new='if not self._roblox_onboarding_done():return "roblox"'
if old not in chunk:raise SystemExit('v3.20.6: router Roblox flag anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

# Patch the cinematic Roblox UI completion paths.
_,a,b=method_span(s,'_abrir_onboarding_username_ui_3205')
chunk=s[a:b]

# Linked-profile path: replace the old inline flag/save with the hardened marker.
pattern=(r'self\.linked_profile=\{"id":int\(profile\.get\("id",0\)\),"name":str\(profile\.get\("name",""\) or ""\),'
         r'"displayName":str\(profile\.get\("displayName",""\) or profile\.get\("name",""\) or ""\),'
         r'"avatar_url":str\(profile\.get\(\'avatar_url\',\'\'\) or \'\'\)\};'
         r'self\.onboarding_username=self\.linked_profile\[\'name\'\];'
         r'self\.config_data\[\'roblox_onboarding_completed\'\]=True;self\.salvar_config_app\(\)')
repl=('self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),'
      '"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),'
      '"avatar_url":str(profile.get(\'avatar_url\',\'\') or \'\')};'
      'self._mark_roblox_onboarding_done(self.linked_profile[\'name\'])')
chunk,nlink=re.subn(pattern,repl,chunk,count=1)
if nlink!=1:
    # Fallback for formatting variants.
    old="self.onboarding_username=self.linked_profile['name'];self.config_data['roblox_onboarding_completed']=True;self.salvar_config_app()"
    if old not in chunk:raise SystemExit('v3.20.6: linked completion anchor missing')
    chunk=chunk.replace(old,"self._mark_roblox_onboarding_done(self.linked_profile['name'])",1)

# Nick-only path.
old="self.onboarding_username=username;self.config_data['roblox_onboarding_completed']=True;self.salvar_config_app();begin_tutorial()"
if old not in chunk:
    old="self.onboarding_username=username;self.config_data['roblox_onboarding_completed']=True;self.salvar_config_app();begin_tutorial()"
if old not in chunk:raise SystemExit('v3.20.6: nick-only completion anchor missing')
chunk=chunk.replace(old,"self._mark_roblox_onboarding_done(username);begin_tutorial()",1)

# After the Roblox panel closes, bypass the guard one time and open the known-good
# cinematic tutorial implementation directly. State is already marked above.
old='self._tutorial_panel=None;self.after(20,lambda:self.abrir_tutorial(primeiro_acesso=bool(primeiro_acesso)))'
new='self._tutorial_panel=None;self._first_run_active_stage="";self.after(20,lambda:self._abrir_tutorial_ui_3205(primeiro_acesso=bool(primeiro_acesso)))'
if old not in chunk:raise SystemExit('v3.20.6: tutorial handoff anchor missing')
chunk=chunk.replace(old,new,1)
s=s[:a]+chunk+s[b:]

# When loading an already-linked profile in a fresh app instance, prime runtime state
# so stale startup timers cannot bounce back to Roblox linking.
replace_method('_first_run_route',r'''    def _first_run_route(self):
        """Authoritative first-run order with hardened Roblox completion state."""
        if self._roblox_onboarding_done():
            self._roblox_onboarding_completed_runtime=True
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
''')

# Validation: no fragile direct router check and all completion paths use marker.
tree,cls=app_class(s);names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_roblox_onboarding_done','_mark_roblox_onboarding_done','_first_run_stage','_first_run_route','_abrir_onboarding_username_ui_3205'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.6: {unique} count={names.count(unique)}')
for needle in (
    'APP_VERSION = "3.20.6"',
    'if not self._roblox_onboarding_done():return "roblox"',
    'self._roblox_onboarding_completed_runtime=True',
    'self._mark_roblox_onboarding_done(self.linked_profile',
    'self._mark_roblox_onboarding_done(username);begin_tutorial()',
    'self._abrir_tutorial_ui_3205(primeiro_acesso=bool(primeiro_acesso))',
):
    if needle not in s:raise SystemExit('v3.20.6: missing '+needle)
if 'if not bool(self.config_data.get("roblox_onboarding_completed",False)):return "roblox"' in s:
    raise SystemExit('v3.20.6: fragile router check remains')
if 'RedrawWindow(' in s:raise SystemExit('v3.20.6: unsafe repaint')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied v3.20.6 Roblox onboarding completion hardening')
