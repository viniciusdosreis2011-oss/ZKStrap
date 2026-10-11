from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def lines_pos(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line)
        pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:
        raise SystemExit('v3.20.3: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.20.3: method missing: {name}')
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
    if n!=1:
        raise SystemExit('v3.20.3: rename failed '+name)
    s=s[:a]+chunk+s[b:]


if 'APP_VERSION = "3.20.2"' not in s:
    raise SystemExit('v3.20.3: expected v3.20.2 base')
s=s.replace('APP_VERSION = "3.20.2"','APP_VERSION = "3.20.3"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Roblox Onboarding Gate Fix"',s,count=1)
if n!=1:
    raise SystemExit('v3.20.3: timestamp missing')

# 1) The language picker from 3.19.5 still scheduled the tutorial directly.
# Route that exact first-run transition through a dedicated gate instead.
node,a,b=method_span(s,'_maybe_show_first_run_language')
chunk=s[a:b]
old='try:self.after(900,self._maybe_show_first_run_tutorial)'
new='try:self.after(700,self._first_run_after_language)'
if old not in chunk:
    raise SystemExit('v3.20.3: direct language->tutorial scheduler missing')
chunk=chunk.replace(old,new,1)
s=s[:a]+chunk+s[b:]

# 2) Persist completion of the Roblox-name step on both paths.
node,a,b=method_span(s,'_abrir_onboarding_username')
chunk=s[a:b]
old_link='''                self.onboarding_username=str(self.linked_profile.get("name") or "")
                self.salvar_config_app()'''
new_link='''                self.onboarding_username=str(self.linked_profile.get("name") or "")
                self.config_data["roblox_onboarding_completed"]=True
                self.salvar_config_app()'''
if old_link not in chunk:
    raise SystemExit('v3.20.3: linked-profile save anchor missing')
chunk=chunk.replace(old_link,new_link,1)
old_nick='''            self.onboarding_username=username
            self.salvar_config_app()'''
new_nick='''            self.onboarding_username=username
            self.config_data["roblox_onboarding_completed"]=True
            self.salvar_config_app()'''
if old_nick not in chunk:
    raise SystemExit('v3.20.3: nickname-only save anchor missing')
chunk=chunk.replace(old_nick,new_nick,1)
s=s[:a]+chunk+s[b:]

# 3) Guard every other path that may try to launch the first-run tutorial.
# This prevents startup timers from bypassing Roblox onboarding.
rename_method('_maybe_show_first_run_tutorial','_maybe_show_first_run_tutorial_base_3203')

gate=r'''    def _first_run_after_language(self):
        if not bool(getattr(self,"language_selected",False)):
            try:self.after(200,self._first_run_after_language)
            except Exception:pass
            return
        if bool(getattr(self,"tutorial_completed",False)):
            return self._maybe_show_first_run_tutorial_base_3203()
        if not bool(self.config_data.get("roblox_onboarding_completed",False)):
            panel=getattr(self,"_tutorial_panel",None)
            try:
                if panel is not None and panel.winfo_exists():
                    panel.lift();return
            except Exception:pass
            return self._abrir_onboarding_username(primeiro_acesso=True)
        return self._maybe_show_first_run_tutorial_base_3203()

    def _maybe_show_first_run_tutorial(self):
        if not bool(getattr(self,"language_selected",False)):
            try:self.after(300,self._maybe_show_first_run_tutorial)
            except Exception:pass
            return
        if bool(getattr(self,"tutorial_completed",False)):
            return self._maybe_show_first_run_tutorial_base_3203()
        if not bool(self.config_data.get("roblox_onboarding_completed",False)):
            panel=getattr(self,"_tutorial_panel",None)
            try:
                if panel is not None and panel.winfo_exists():
                    panel.lift();return
            except Exception:pass
            return self._abrir_onboarding_username(primeiro_acesso=True)
        return self._maybe_show_first_run_tutorial_base_3203()
'''
_,cls=app_class(s)
_,pos=lines_pos(s)
insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+gate.rstrip()+"\n"+s[insert_at:]

# Validation
for needle in (
    'APP_VERSION = "3.20.3"',
    'self.after(700,self._first_run_after_language)',
    'self.config_data["roblox_onboarding_completed"]=True',
    'def _first_run_after_language(self):',
    'def _maybe_show_first_run_tutorial_base_3203(',
    'def _maybe_show_first_run_tutorial(self):',
):
    if needle not in s:
        raise SystemExit('v3.20.3: missing '+needle)
if 'try:self.after(900,self._maybe_show_first_run_tutorial)' in s:
    raise SystemExit('v3.20.3: old language->tutorial bypass still present')
if s.count('def _maybe_show_first_run_tutorial(self):')!=1:
    raise SystemExit('v3.20.3: tutorial gate wrapper count invalid')
if 'RedrawWindow(' in s:
    raise SystemExit('v3.20.3: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.3 Roblox onboarding gate fix')
