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
    raise SystemExit('v3.19.7 runtime: localization pack missing')
pack=json.loads(pack_path.read_text(encoding='utf-8'))
rows=pack.get('rows') or []
if len(rows)<450:
    raise SystemExit(f'v3.19.7 runtime: language pack too small: {len(rows)}')


def line_offsets(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line); pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.19.7 runtime: ModernConfigApp missing')
    return tree,cls

if 'APP_VERSION = "3.19.6"' not in s:
    raise SystemExit('v3.19.7 runtime: expected v3.19.6 base')
s=s.replace('APP_VERSION = "3.19.6"','APP_VERSION = "3.19.7"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Safe Full Runtime Localization"',s,count=1)
if n!=1:raise SystemExit('v3.19.7 runtime: timestamp missing')

# Embed the localization pack so the installed app remains fully offline.
embed='''\n# FULL UI I18N v3.19.7 — embedded offline localization pack.\nI18N_UI_3197_ROWS = '''+repr(rows)+'''\nI18N_UI_3197_INDEX = {}\nfor _zk_row in I18N_UI_3197_ROWS:\n    for _zk_code in ("pt","en","es","zh","fr"):\n        _zk_value=_zk_row.get(_zk_code)\n        if isinstance(_zk_value,str) and _zk_value:\n            I18N_UI_3197_INDEX.setdefault(_zk_value,_zk_row)\n\n'''
anchor='_SAFE_START_ACTIVE = False\n'
if anchor not in s:raise SystemExit('v3.19.7 runtime: global anchor missing')
s=s.replace(anchor,anchor+embed,1)

# Runtime translators are inserted before the language picker methods.
helpers=r'''    def _i18n_text(self, text, lang=None):
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

        # A few dynamic labels are built at runtime and cannot be exact pack keys.
        m=re.fullmatch(r"\s*(\d+)\s+(ATIVAS?|ACTIVE|ACTIVES)\s*",text,re.I)
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
        if root is None:return
        stack=[root]
        while stack:
            widget=stack.pop()
            for option in ("text","placeholder_text"):
                try:
                    value=widget.cget(option)
                    if isinstance(value,str) and value:
                        translated=self._i18n_text(value)
                        if translated!=value:
                            widget.configure(**{option:translated})
                except Exception:pass
            try:stack.extend(widget.winfo_children())
            except Exception:pass

    def _i18n_runtime_tick(self):
        self._i18n_job=None
        try:
            # Make sure old two-language self.tr dictionaries cannot break FR/ES/ZH.
            tr=getattr(self,"tr",None)
            if isinstance(tr,dict):
                en=tr.get("en",{}) if isinstance(tr.get("en",{}),dict) else {}
                for code in ("es","zh","fr"):
                    if code not in tr:
                        tr[code]={k:self._i18n_text(v,lang=code) if isinstance(v,str) else v for k,v in en.items()}
            host=getattr(self,"main_container",None)
            if host is not None and host.winfo_exists():
                self._translate_widget_tree(host)
        except Exception:pass
        try:self._i18n_job=self.after(850,self._i18n_runtime_tick)
        except Exception:self._i18n_job=None

'''
marker='    def _language_choices(self):\n'
if marker not in s:raise SystemExit('v3.19.7 runtime: language method anchor missing')
s=s.replace(marker,helpers+marker,1)

# Populate self.tr for all languages immediately after its dictionary assignment.
tree,cls=app_class(s); lines,pos=line_offsets(s)
tr_assign=None
for node in ast.walk(cls):
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=='self' and target.attr=='tr':
                tr_assign=node;break
    if tr_assign is not None:break
if tr_assign is not None:
    insert_at=pos[tr_assign.end_lineno]
    tr_fill='''        try:\n            _zk_en=self.tr.get("en",{}) if isinstance(self.tr.get("en",{}),dict) else {}\n            for _zk_code in ("es","zh","fr"):\n                if _zk_code not in self.tr:\n                    self.tr[_zk_code]={_k:self._i18n_text(_v,lang=_zk_code) if isinstance(_v,str) else _v for _k,_v in _zk_en.items()}\n        except Exception:pass\n'''
    s=s[:insert_at]+tr_fill+s[insert_at:]

# Translate every lazy-loaded page after it is built.
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
if needle not in s:raise SystemExit('v3.19.7 runtime: lazy page hook missing')
s=s.replace(needle,replacement,1)

# Start a lightweight translator after each full UI construction. It also catches
# status labels that change after the page is already visible.
main_anchor='''        self.main_container=ctk.CTkFrame(self,fg_color=t["bg"])
        self.main_container.place(x=0,y=0,relwidth=1,relheight=1)
'''
main_repl=main_anchor+'''        try:
            _zk_old_i18n=getattr(self,"_i18n_job",None)
            if _zk_old_i18n is not None:self.after_cancel(_zk_old_i18n)
        except Exception:pass
        self._i18n_job=None
        try:self.after(420,self._i18n_runtime_tick)
        except Exception:pass
'''
if main_anchor not in s:raise SystemExit('v3.19.7 runtime: main container hook missing')
s=s.replace(main_anchor,main_repl,1)

# Dynamic Home values: translate them at their source instead of waiting for tick.
replacements=[
    ('labels[\'client\'].configure(text="ONLINE" if client_ok else "NÃO LOCALIZADO",','labels[\'client\'].configure(text=self._i18n_text("ONLINE" if client_ok else "NÃO LOCALIZADO"),'),
    ('labels[\'modules\'].configure(text=f"{active} ATIVAS")','labels[\'modules\'].configure(text=self._i18n_text(f"{active} ATIVAS"))'),
    ('if self.cursor_pack != "Roblox Padrão": assets.append("CURSOR")','if self.cursor_pack != "Roblox Padrão": assets.append(self._i18n_text("CURSOR"))'),
    ('if self.game_font_source: assets.append("FONTE")','if self.game_font_source: assets.append(self._i18n_text("FONTE"))'),
    ('labels[\'assets\'].configure(text=" + ".join(assets) if assets else "PADRÃO")','labels[\'assets\'].configure(text=" + ".join(assets) if assets else self._i18n_text("PADRÃO"))'),
    ('labels[\'restart\'].configure(text="SIM" if self._roblox_esta_aberto() and active else "NÃO")','labels[\'restart\'].configure(text=self._i18n_text("SIM" if self._roblox_esta_aberto() and active else "NÃO"))'),
]
for old,new in replacements:
    if old in s:s=s.replace(old,new,1)

# Structural validation.
for needle in (
    'APP_VERSION = "3.19.7"',
    'I18N_UI_3197_ROWS',
    'def _i18n_text',
    'def _translate_widget_tree',
    'def _i18n_runtime_tick',
    'TABLEAU // ÉTAT EN DIRECT',
    'CENTRE RAPIDE',
    'APPLIQUER LES RÉGLAGES',
    'PANEL // ESTADO EN VIVO',
    '仪表盘 // 实时状态',
):
    if needle not in s:raise SystemExit('v3.19.7 runtime: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.19.7 runtime: unsafe repaint returned')
if 'ctk.CTkScrollableFrame(' in s:raise SystemExit('v3.19.7 runtime: legacy scroll returned')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print(f'Applied safe ZKStrap v3.19.7 runtime localization: {len(rows)} localized rows')
