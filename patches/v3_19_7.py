from pathlib import Path
import ast
import json
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')
repo_root=Path(__file__).resolve().parent.parent
pack_path=repo_root/'i18n'/'ui_3197_final.json'
if not pack_path.exists():
    raise SystemExit('v3.19.7: i18n/ui_3197_final.json missing')
pack=json.loads(pack_path.read_text(encoding='utf-8'))
rows=pack.get('rows') or []
if len(rows)<300:
    raise SystemExit(f'v3.19.7: language pack too small: {len(rows)} rows')


def line_offsets(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line); pos.append(total)
    return lines,pos


def char_abs(text,node,end=False):
    lines,pos=line_offsets(text)
    ln=node.end_lineno if end else node.lineno
    col=node.end_col_offset if end else node.col_offset
    raw=lines[ln-1]
    prefix=raw.encode('utf-8')[:col].decode('utf-8','ignore')
    return pos[ln-1]+len(prefix)


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None: raise SystemExit('v3.19.7: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_method):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'v3.19.7: method missing: {name}')
    start=char_abs(s,node,False); end=char_abs(s,node,True)
    s=s[:start]+new_method.rstrip()+"\n\n"+s[end:]


if 'APP_VERSION = "3.19.6"' not in s:
    raise SystemExit('v3.19.7: expected v3.19.6 base')
s=s.replace('APP_VERSION = "3.19.6"','APP_VERSION = "3.19.7"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Full Five-Language UI + Runtime i18n"',s,count=1)
if n!=1: raise SystemExit('v3.19.7: timestamp missing')

embed='''\n# FULL UI I18N v3.19.7 — generated at build time and embedded for offline use.\nI18N_UI_3197_ROWS = '''+repr(rows)+'''\nI18N_UI_3197_INDEX = {}\nfor _zk_i18n_row in I18N_UI_3197_ROWS:\n    for _zk_i18n_code in ("pt","en","es","zh","fr"):\n        _zk_i18n_value=_zk_i18n_row.get(_zk_i18n_code)\n        if isinstance(_zk_i18n_value,str) and _zk_i18n_value:\n            I18N_UI_3197_INDEX.setdefault(_zk_i18n_value,_zk_i18n_row)\n\n'''
anchor='_SAFE_START_ACTIVE = False\n'
if anchor not in s: raise SystemExit('v3.19.7: global embed anchor missing')
s=s.replace(anchor,anchor+embed,1)

tree,cls=app_class(s)
repls=[]
class LegacyPairVisitor(ast.NodeVisitor):
    def visit_IfExp(self,node):
        if isinstance(node.body,ast.Constant) and isinstance(node.body.value,str) and isinstance(node.orelse,ast.Constant) and isinstance(node.orelse.value,str):
            try: cond=ast.unparse(node.test)
            except Exception: cond=''
            if 'pt' in cond or 'idioma' in cond or 'language' in cond:
                a=char_abs(s,node,False); b=char_abs(s,node,True)
                repls.append((a,b,f'self._L({node.body.value!r}, {node.orelse.value!r})'))
        self.generic_visit(node)
LegacyPairVisitor().visit(cls)
for a,b,new in sorted(repls,reverse=True):
    s=s[:a]+new+s[b:]
if len(repls)<300:
    raise SystemExit(f'v3.19.7: expected >=300 legacy language pairs, converted {len(repls)}')

L_method=r'''    def _L(self, pt, en, es=None, zh=None, fr=None):
        """Resolve all five interface languages without English fallback leaks."""
        code=str(getattr(self,"idioma","pt") or "pt").lower()
        if code=="pt": return pt
        if code=="en": return en
        explicit={"es":es,"zh":zh,"fr":fr}.get(code)
        if explicit is not None:
            return explicit
        row=I18N_UI_3197_INDEX.get(str(en)) or I18N_UI_3197_INDEX.get(str(pt))
        if isinstance(row,dict):
            value=row.get(code)
            if isinstance(value,str) and value:
                return value
        return en
'''
replace_app_method('_L',L_method)

helper_methods=r'''    def _i18n_text(self, text, lang=None):
        if not isinstance(text,str) or not text:
            return text
        code=str(lang or getattr(self,"idioma","pt") or "pt").lower()
        if code not in ("pt","en","es","zh","fr"):
            code="en"
        row=I18N_UI_3197_INDEX.get(text)
        if isinstance(row,dict):
            value=row.get(code)
            if isinstance(value,str) and value:
                return value

        m=re.fullmatch(r"\s*(\d+)\s+ATIVAS?\s*",text,re.I)
        if m:
            n=m.group(1)
            return {
                "pt":f"{n} ATIVAS","en":f"{n} ACTIVE","es":f"{n} ACTIVAS",
                "zh":f"{n} 项启用","fr":f"{n} ACTIVES",
            }.get(code,text)

        if " + " in text:
            parts=text.split(" + ")
            translated=[self._i18n_text(p,lang=code) for p in parts]
            if translated!=parts:
                return " + ".join(translated)
        return text

    def _translate_widget_tree(self, root):
        """Translate currently rendered widgets, including old hard-coded labels."""
        if root is None:
            return
        stack=[root]
        while stack:
            widget=stack.pop()
            try:
                if widget is not root and hasattr(widget,"winfo_ismapped") and not widget.winfo_ismapped():
                    continue
            except Exception:
                pass
            for option in ("text","placeholder_text"):
                try:
                    value=widget.cget(option)
                    if isinstance(value,str) and value:
                        translated=self._i18n_text(value)
                        if translated!=value:
                            widget.configure(**{option:translated})
                except Exception:
                    pass
            try:
                stack.extend(widget.winfo_children())
            except Exception:
                pass

    def _i18n_runtime_tick(self):
        """Keep dynamic status labels in the selected language without network calls."""
        self._i18n_job=None
        try:
            host=getattr(self,"main_container",None)
            if host is not None and host.winfo_exists():
                self._translate_widget_tree(host)
        except Exception:
            pass
        try:
            self._i18n_job=self.after(1100,self._i18n_runtime_tick)
        except Exception:
            self._i18n_job=None

'''
marker='    def _language_choices(self):\n'
if marker not in s: raise SystemExit('v3.19.7: language choices anchor missing')
s=s.replace(marker,helper_methods+marker,1)

tree,cls=app_class(s)
tr_assign=None
for node in ast.walk(cls):
    if not isinstance(node,ast.Assign): continue
    for target in node.targets:
        if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=='self' and target.attr=='tr':
            tr_assign=node; break
    if tr_assign is not None: break
if tr_assign is None: raise SystemExit('v3.19.7: self.tr assignment missing')
insert_at=char_abs(s,tr_assign,True)
tr_fill='''\n        for _zk_lang in ("es","zh","fr"):\n            if _zk_lang not in self.tr:\n                self.tr[_zk_lang]={_k:self._i18n_text(_v,lang=_zk_lang) if isinstance(_v,str) else _v for _k,_v in self.tr.get("en",{}).items()}\n'''
s=s[:insert_at]+tr_fill+s[insert_at:]

needle='''        try:_startup_log(f"LAZY PAGE {key}: {time.perf_counter()-t0:.3f}s")
        except Exception:pass
        return page
'''
replacement='''        try:
            if page is not None:
                self.after_idle(lambda p=page:self._translate_widget_tree(p) if self._widget_alive(p) else None)
                self.after(140,lambda p=page:self._translate_widget_tree(p) if self._widget_alive(p) else None)
        except Exception:pass
        try:_startup_log(f"LAZY PAGE {key}: {time.perf_counter()-t0:.3f}s")
        except Exception:pass
        return page
'''
if needle not in s: raise SystemExit('v3.19.7: lazy page return hook missing')
s=s.replace(needle,replacement,1)

main_anchor='''        self.main_container=ctk.CTkFrame(self,fg_color=t["bg"])
        self.main_container.place(x=0,y=0,relwidth=1,relheight=1)
'''
main_repl=main_anchor+'''        try:
            old_i18n_job=getattr(self,"_i18n_job",None)
            if old_i18n_job is not None:self.after_cancel(old_i18n_job)
        except Exception:pass
        self._i18n_job=None
        try:self.after(650,self._i18n_runtime_tick)
        except Exception:pass
'''
if main_anchor not in s: raise SystemExit('v3.19.7: main UI i18n hook missing')
s=s.replace(main_anchor,main_repl,1)

s=s.replace('labels[\'client\'].configure(text="ONLINE" if client_ok else "NÃO LOCALIZADO",',
            'labels[\'client\'].configure(text=self._i18n_text("ONLINE" if client_ok else "NÃO LOCALIZADO"),',1)
s=s.replace('labels[\'modules\'].configure(text=f"{active} ATIVAS")',
            'labels[\'modules\'].configure(text=self._i18n_text(f"{active} ATIVAS"))',1)
s=s.replace('if self.cursor_pack != "Roblox Padrão": assets.append("CURSOR")',
            'if self.cursor_pack != "Roblox Padrão": assets.append(self._i18n_text("CURSOR"))',1)
s=s.replace('if self.game_font_source: assets.append("FONTE")',
            'if self.game_font_source: assets.append(self._i18n_text("FONTE"))',1)
s=s.replace('labels[\'assets\'].configure(text=" + ".join(assets) if assets else "PADRÃO")',
            'labels[\'assets\'].configure(text=" + ".join(assets) if assets else self._i18n_text("PADRÃO"))',1)
s=s.replace('labels[\'restart\'].configure(text="SIM" if self._roblox_esta_aberto() and active else "NÃO")',
            'labels[\'restart\'].configure(text=self._i18n_text("SIM" if self._roblox_esta_aberto() and active else "NÃO"))',1)

if 'TABLEAU // ÉTAT EN DIRECT' not in s: raise SystemExit('v3.19.7: polished French Home missing')
if 'APPLIQUER LES RÉGLAGES' not in s: raise SystemExit('v3.19.7: French apply label missing')
if 'I18N_UI_3197_ROWS' not in s: raise SystemExit('v3.19.7: embedded pack missing')
if 'def _i18n_text' not in s or 'def _translate_widget_tree' not in s or 'def _i18n_runtime_tick' not in s:
    raise SystemExit('v3.19.7: runtime i18n helpers missing')
if 'RedrawWindow(' in s: raise SystemExit('v3.19.7: unsafe Win32 repaint returned')

tree,cls=app_class(s)
remaining=0
for node in ast.walk(cls):
    if isinstance(node,ast.IfExp) and isinstance(node.body,ast.Constant) and isinstance(node.body.value,str) and isinstance(node.orelse,ast.Constant) and isinstance(node.orelse.value,str):
        try:cond=ast.unparse(node.test)
        except Exception:cond=''
        if 'pt' in cond or 'idioma' in cond or 'language' in cond:
            remaining+=1
if remaining>3:
    raise SystemExit(f'v3.19.7: too many legacy bilingual fallbacks remain: {remaining}')

path.write_text(s,encoding='utf-8')
print(f'Applied ZKStrap v3.19.7 full five-language UI patch: {len(rows)} rows, {len(repls)} legacy pairs converted, {remaining} remain')
