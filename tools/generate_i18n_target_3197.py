import ast
import hashlib
import html
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

TARGET=os.environ.get('ZK_I18N_TARGET','fr')
TARGET_API={'pt':'pt','en':'en','es':'es','zh':'zh-CN','fr':'fr'}[TARGET]
src_path=Path(os.environ['ZK_SOURCE_DIR'])/'ZKStrap_v3_18_0.py'
src=src_path.read_text(encoding='utf-8')
tree=ast.parse(src)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None:raise SystemExit('ModernConfigApp missing')

pairs=[]
class PV(ast.NodeVisitor):
    def visit_IfExp(self,node):
        if isinstance(node.body,ast.Constant) and isinstance(node.body.value,str) and isinstance(node.orelse,ast.Constant) and isinstance(node.orelse.value,str):
            try:cond=ast.unparse(node.test)
            except Exception:cond=''
            if 'pt' in cond or 'idioma' in cond or 'language' in cond:pairs.append((node.body.value,node.orelse.value))
        self.generic_visit(node)
PV().visit(app)

UI_CALLS={'CTkLabel','CTkButton','CTkCheckBox','CTkSwitch','CTkRadioButton','_section_card','_page_shell','_module_switch','_hero_card','_mini_stat','_settings_row','_action_row','_info_card'}
def cname(fn):
    if isinstance(fn,ast.Name):return fn.id
    if isinstance(fn,ast.Attribute):return fn.attr
    return ''
literals=[]
class LV(ast.NodeVisitor):
    def visit_Call(self,node):
        name=cname(node.func)
        if name in UI_CALLS or (isinstance(node.func,ast.Attribute) and node.func.attr=='configure'):
            for kw in node.keywords:
                if kw.arg in {'text','placeholder_text'} and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,str):literals.append(kw.value.value)
            if name in {'_section_card','_page_shell','_module_switch','_hero_card','_mini_stat','_settings_row','_action_row','_info_card'}:
                for arg in node.args[:5]:
                    if isinstance(arg,ast.Constant) and isinstance(arg.value,str):literals.append(arg.value)
        self.generic_visit(node)
LV().visit(app)
for node in ast.walk(app):
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr=='tr' for t in node.targets):
        for sub in ast.walk(node.value):
            if isinstance(sub,ast.Constant) and isinstance(sub.value,str):literals.append(sub.value)

brand={'','ZK','ZKSTRAP','ROBLOX','SPOTIFY','YOUTUBE','GITHUB','DISCORD','BLOX FRUITS','0:00','00%','←','−1','DUP','CORE'}
def translatable(x):
    x=str(x or '').strip()
    return bool(x and x not in brand and len(x)>=3 and not re.fullmatch(r'[\W_\d]+',x) and not x.startswith(('http://','https://','C:\\')))
def rid(kind,a,b=''):
    return hashlib.sha256((kind+'\0'+a+'\0'+b).encode('utf-8')).hexdigest()[:24]

rows=[];seen_pair=set();variants=set()
for pt,en in pairs:
    if (pt,en) in seen_pair:continue
    seen_pair.add((pt,en));variants.update((pt,en))
    rows.append({'id':rid('pair',pt,en),'kind':'pair','pt':pt,'en':en})
for text in dict.fromkeys(literals):
    if translatable(text) and text not in variants:rows.append({'id':rid('literal',text),'kind':'literal','source':text})

# Known pair values require no network for PT/EN.
network=[];values={}
for row in rows:
    if row['kind']=='pair' and TARGET in ('pt','en'):
        values[row['id']]=row[TARGET]
    else:
        source_text=row['en'] if row['kind']=='pair' else row['source']
        network.append((row['id'],source_text,'en' if row['kind']=='pair' else 'auto'))

# Dedup text/source-language queries then batch.
unique={}
for _,text,sl in network:unique[(sl,text)]=None
items=list(unique)
chunks=[];cur=[];chars=0
for sl,text in sorted(items,key=lambda x:(x[0],len(x[1]),x[1])):
    cost=len(text)+35
    if cur and (len(cur)>=22 or chars+cost>3800 or cur[0][0]!=sl):chunks.append(cur);cur=[];chars=0
    cur.append((sl,text));chars+=cost
if cur:chunks.append(cur)

endpoint='https://translate.googleapis.com/translate_a/single';local=threading.local();translated={};lock=threading.Lock()
def one(session,sl,text):
    r=session.get(endpoint,params={'client':'gtx','sl':sl,'tl':TARGET_API,'dt':'t','q':text},timeout=(4,10))
    if r.status_code!=200:raise RuntimeError(r.status_code)
    data=r.json();segs=data[0] if isinstance(data,list) and data else []
    return html.unescape(''.join(str(x[0] or '') for x in segs if isinstance(x,list) and x)).strip() or text

def work(chunk):
    if not hasattr(local,'s'):
        local.s=requests.Session();local.s.headers.update({'User-Agent':'Mozilla/5.0 ZKStrap-i18n/3.19.7'})
    sess=local.s;sl=chunk[0][0];texts=[x[1] for x in chunk];marker='\n<<<ZK3197SEP>>>\n';payload=marker.join(texts)
    for attempt in range(3):
        try:
            val=one(sess,sl,payload);parts=[p.strip() for p in val.split('<<<ZK3197SEP>>>')]
            if len(parts)==len(texts):return {(sl,t):v for t,v in zip(texts,parts)},0
        except Exception:time.sleep(.35*(attempt+1))
    out={};bad=0
    for t in texts:
        ok=False
        for attempt in range(2):
            try:out[(sl,t)]=one(sess,sl,t);ok=True;break
            except Exception:time.sleep(.25*(attempt+1))
        if not ok:out[(sl,t)]=t;bad+=1
    return out,bad

bad=0
if chunks:
    print(TARGET,'translating',len(items),'unique strings in',len(chunks),'chunks')
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(work,c) for c in chunks]
        done=0
        for fut in as_completed(futs):
            data,n_bad=fut.result();translated.update(data);bad+=n_bad;done+=1
            if done%8==0 or done==len(futs):print(TARGET,'chunks',done,'/',len(futs),'bad',bad)

for row_id,text,sl in network:values[row_id]=translated.get((sl,text),text)
coverage=(len(network)-bad)/max(1,len(network))
if network and coverage<.75:raise SystemExit(f'{TARGET} coverage too low: {coverage:.3f}')

out={'target':TARGET,'rows':[],'bad':bad,'network_count':len(network)}
for row in rows:
    rec=dict(row);rec['value']=values.get(row['id'],row.get(TARGET,row.get('source','')));out['rows'].append(rec)
Path('tmp/i18n_targets').mkdir(parents=True,exist_ok=True)
Path(f'tmp/i18n_targets/{TARGET}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(TARGET,'done rows',len(rows),'bad',bad)
