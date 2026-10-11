import ast
import os
import re
from pathlib import Path

src_path=Path(os.environ['ZK_SOURCE_DIR'])/'ZKStrap_v3_18_0.py'
src=src_path.read_text(encoding='utf-8')
tree=ast.parse(src)

rows=[]

UI_CALL_HINTS={
    'CTkLabel','CTkButton','CTkCheckBox','CTkSwitch','CTkOptionMenu','CTkRadioButton',
    '_section_card','_hero_card','_mini_stat','_settings_row','_action_row','_info_card',
}


def call_name(fn):
    if isinstance(fn,ast.Name): return fn.id
    if isinstance(fn,ast.Attribute): return fn.attr
    return ''


def add(method,kind,text,lineno):
    text=str(text).strip()
    if not text or len(text)<2: return
    if text.startswith(('http://','https://','C:\\','{','[')): return
    if re.fullmatch(r'[\W_]+',text): return
    rows.append((method,kind,lineno,text))

class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.method='<module>'
    def visit_FunctionDef(self,node):
        old=self.method; self.method=node.name
        self.generic_visit(node); self.method=old
    visit_AsyncFunctionDef=visit_FunctionDef
    def visit_Call(self,node):
        name=call_name(node.func)
        if name in UI_CALL_HINTS or name.startswith('_section_') or name.startswith('_build_'):
            for kw in node.keywords:
                if kw.arg in {'text','placeholder_text'} and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,str):
                    add(self.method,f'{name}.{kw.arg}',kw.value.value,node.lineno)
            if name.startswith('_section_') or name in {'_section_card','_hero_card','_mini_stat','_settings_row','_action_row','_info_card'}:
                for i,arg in enumerate(node.args[:4]):
                    if isinstance(arg,ast.Constant) and isinstance(arg.value,str):
                        add(self.method,f'{name}.arg{i}',arg.value,node.lineno)
        self.generic_visit(node)

Visitor().visit(tree)

# Also catch conspicuous hard-coded UI phrases assigned to text later via configure().
for node in ast.walk(tree):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='configure':
        for kw in node.keywords:
            if kw.arg=='text' and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,str):
                add('<configure>','configure.text',kw.value.value,node.lineno)

seen=set(); unique=[]
for row in sorted(rows,key=lambda r:(r[0],r[2],r[3])):
    key=(row[0],row[1],row[3])
    if key in seen: continue
    seen.add(key); unique.append(row)

out=[]
out.append(f'ZKStrap i18n audit: {len(unique)} hard-coded UI text candidates')
out.append('Format: method | source | line | text')
out.append('')
for method,kind,line,text in unique:
    out.append(f'{method} | {kind} | {line} | {text}')

Path('tmp').mkdir(exist_ok=True)
Path('tmp/i18n_audit_3196.txt').write_text('\n'.join(out),encoding='utf-8')
print('\n'.join(out[:30]))
print(f'Wrote {len(unique)} candidates')
