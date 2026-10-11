import ast
import os
from pathlib import Path

src_path=Path(os.environ['ZK_SOURCE_DIR'])/'ZKStrap_v3_18_0.py'
src=src_path.read_text(encoding='utf-8')
tree=ast.parse(src)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None: raise SystemExit('ModernConfigApp missing')

rows=[]
class V(ast.NodeVisitor):
    def __init__(self): self.method='<class>'
    def visit_FunctionDef(self,node):
        old=self.method; self.method=node.name
        self.generic_visit(node); self.method=old
    visit_AsyncFunctionDef=visit_FunctionDef
    def visit_IfExp(self,node):
        if isinstance(node.body,ast.Constant) and isinstance(node.body.value,str) and isinstance(node.orelse,ast.Constant) and isinstance(node.orelse.value,str):
            try: cond=ast.unparse(node.test)
            except Exception: cond=''
            if 'pt' in cond or 'idioma' in cond or 'language' in cond:
                rows.append((self.method,node.lineno,cond,node.body.value,node.orelse.value))
        self.generic_visit(node)
V().visit(app)

# unique by pair, preserve first method/line
seen=set(); out_rows=[]
for row in sorted(rows,key=lambda x:x[1]):
    key=(row[3],row[4])
    if key in seen: continue
    seen.add(key); out_rows.append(row)

out=[f'ZKStrap legacy bilingual pairs: {len(out_rows)}','Format: method | line | condition | PT | EN','']
for method,line,cond,pt,en in out_rows:
    pt=pt.replace('\n','\\n'); en=en.replace('\n','\\n')
    out.append(f'{method} | {line} | {cond} | {pt} | {en}')
Path('tmp').mkdir(exist_ok=True)
Path('tmp/i18n_pairs_3196.txt').write_text('\n'.join(out),encoding='utf-8')
print('\n'.join(out[:40]))
print('Wrote',len(out_rows),'pairs')
