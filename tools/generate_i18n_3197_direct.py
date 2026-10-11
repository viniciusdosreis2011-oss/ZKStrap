import ast
import html
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

src_path=Path(os.environ['ZK_SOURCE_DIR'])/'ZKStrap_v3_18_0.py'
src=src_path.read_text(encoding='utf-8')
tree=ast.parse(src)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None: raise SystemExit('ModernConfigApp missing')

pairs=[]
class PairVisitor(ast.NodeVisitor):
    def visit_IfExp(self,node):
        if isinstance(node.body,ast.Constant) and isinstance(node.body.value,str) and isinstance(node.orelse,ast.Constant) and isinstance(node.orelse.value,str):
            try: cond=ast.unparse(node.test)
            except Exception: cond=''
            if 'pt' in cond or 'idioma' in cond or 'language' in cond:
                pairs.append((node.body.value,node.orelse.value))
        self.generic_visit(node)
PairVisitor().visit(app)

UI_CALLS={'CTkLabel','CTkButton','CTkCheckBox','CTkSwitch','CTkRadioButton','_section_card','_page_shell','_module_switch','_hero_card','_mini_stat','_settings_row','_action_row','_info_card'}
def call_name(fn):
    if isinstance(fn,ast.Name):return fn.id
    if isinstance(fn,ast.Attribute):return fn.attr
    return ''

literals=[]
class LiteralVisitor(ast.NodeVisitor):
    def visit_Call(self,node):
        name=call_name(node.func)
        if name in UI_CALLS or (isinstance(node.func,ast.Attribute) and node.func.attr=='configure'):
            for kw in node.keywords:
                if kw.arg in {'text','placeholder_text'} and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,str):
                    literals.append(kw.value.value)
            if name in {'_section_card','_page_shell','_module_switch','_hero_card','_mini_stat','_settings_row','_action_row','_info_card'}:
                for arg in node.args[:5]:
                    if isinstance(arg,ast.Constant) and isinstance(arg.value,str):literals.append(arg.value)
        self.generic_visit(node)
LiteralVisitor().visit(app)

for node in ast.walk(app):
    if not isinstance(node,ast.Assign):continue
    targets=node.targets
    if any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr=='tr' for t in targets):
        for sub in ast.walk(node.value):
            if isinstance(sub,ast.Constant) and isinstance(sub.value,str):literals.append(sub.value)

brand_exact={'','ZK','ZKSTRAP','ROBLOX','SPOTIFY','YOUTUBE','GITHUB','DISCORD','0:00','00%','←','−1','DUP','CORE'}
def translatable(x):
    x=str(x or '').strip()
    if not x or x in brand_exact or len(x)<3:return False
    if re.fullmatch(r'[\W_\d]+',x):return False
    if x.startswith(('http://','https://','C:\\')):return False
    return True

rows=[]; pair_seen=set(); variants=set()
for pt,en in pairs:
    if (pt,en) in pair_seen:continue
    pair_seen.add((pt,en));variants.update((pt,en));rows.append({'kind':'pair','pt':pt,'en':en})
for text in dict.fromkeys(literals):
    if translatable(text) and text not in variants:rows.append({'kind':'literal','source':text})

tasks=set()
for row in rows:
    if row['kind']=='pair':
        for target in ('es','zh-CN','fr'):tasks.add(('en',target,row['en']))
    else:
        for target in ('pt','en','es','zh-CN','fr'):tasks.add(('auto',target,row['source']))

endpoint='https://translate.googleapis.com/translate_a/single'
local=threading.local()
def translate_task(task):
    source,target,text=task
    if not hasattr(local,'session'):
        local.session=requests.Session()
        local.session.headers.update({'User-Agent':'Mozilla/5.0 ZKStrap-i18n/3.19.7'})
    params={'client':'gtx','sl':source,'tl':target,'dt':'t','q':text}
    for attempt in range(4):
        try:
            r=local.session.get(endpoint,params=params,timeout=(4,10))
            if r.status_code==200:
                data=r.json(); chunks=data[0] if isinstance(data,list) and data else []
                val=''.join(str(c[0] or '') for c in chunks if isinstance(c,list) and c)
                val=html.unescape(val).strip()
                if val:return task,val,True
            if r.status_code in (429,500,502,503,504):
                time.sleep(.7*(attempt+1));continue
        except Exception:
            time.sleep(.5*(attempt+1))
    return task,text,False

results={};success=0;done=0;lock=threading.Lock();total=len(tasks)
with ThreadPoolExecutor(max_workers=12) as pool:
    futs=[pool.submit(translate_task,t) for t in tasks]
    for fut in as_completed(futs):
        task,val,ok=fut.result();results[task]=val
        with lock:
            done+=1;success+=int(ok)
            if done%100==0 or done==total:print('translated',done,'/',total,'ok',success)

if total and success/total<0.70:
    raise SystemExit(f'translation endpoint success too low: {success}/{total}')

final=[]
for row in rows:
    if row['kind']=='pair':
        en=row['en'];rec={'pt':row['pt'],'en':en}
        for lang,target in [('es','es'),('zh','zh-CN'),('fr','fr')]:rec[lang]=results.get(('en',target,en),en)
    else:
        text=row['source'];rec={}
        for lang,target in [('pt','pt'),('en','en'),('es','es'),('zh','zh-CN'),('fr','fr')]:rec[lang]=results.get(('auto',target,text),text)
    final.append(rec)

overrides=[
('DASHBOARD // STATUS AO VIVO','DASHBOARD // LIVE STATUS','PANEL // ESTADO EN VIVO','仪表盘 // 实时状态','TABLEAU // ÉTAT EN DIRECT'),
('CLIENTE','CLIENT','CLIENTE','客户端','CLIENT'),('OTIMIZAÇÕES','OPTIMIZATIONS','OPTIMIZACIONES','优化','OPTIMISATIONS'),
('ASSETS','ASSETS','RECURSOS','资源','RESSOURCES'),('REINÍCIO','RESTART','REINICIO','重启','REDÉMARRAGE'),
('CENTRAL RÁPIDA','QUICK CENTER','CENTRO RÁPIDO','快捷中心','CENTRE RAPIDE'),
('⚡ OTIMIZAR ROBLOX','⚡ OPTIMIZE ROBLOX','⚡ OPTIMIZAR ROBLOX','⚡ 优化 ROBLOX','⚡ OPTIMISER ROBLOX'),
('✓  APLICAR CONFIGURAÇÕES','✓  APPLY SETTINGS','✓  APLICAR AJUSTES','✓  应用设置','✓  APPLIQUER LES RÉGLAGES'),
('≋  COMPARAR CONFIGURAÇÕES','≋  COMPARE SETTINGS','≋  COMPARAR AJUSTES','≋  比较设置','≋  COMPARER LES RÉGLAGES'),
('▣  MODO COMPACTO','▣  COMPACT MODE','▣  MODO COMPACTO','▣  紧凑模式','▣  MODE COMPACT'),
('APLICAR','APPLY','APLICAR','应用','APPLIQUER'),('Modo compacto','Compact mode','Modo compacto','紧凑模式','Mode compact'),
('Sons do ZKStrap','ZKStrap audio','Audio de ZKStrap','ZKStrap 音频','Audio ZKStrap'),
('ONLINE','ONLINE','EN LÍNEA','在线','EN LIGNE'),('NÃO LOCALIZADO','NOT LOCATED','NO LOCALIZADO','未找到','NON LOCALISÉ'),
('SIM','YES','SÍ','是','OUI'),('NÃO','NO','NO','否','NON'),('PADRÃO','DEFAULT','PREDETERMINADO','默认','PAR DÉFAUT'),
('CURSOR','CURSOR','CURSOR','光标','CURSEUR'),('FONTE','FONT','FUENTE','字体','POLICE')]
for vals in overrides:
    rec=dict(zip(('pt','en','es','zh','fr'),vals));match=None
    for r in final:
        if r.get('pt')==vals[0] or r.get('en')==vals[1]:match=r;break
    if match:match.update(rec)
    else:final.append(rec)

out_rows=[];seen=set()
for r in final:
    tup=tuple(r.get(k,'') for k in ('pt','en','es','zh','fr'))
    if tup in seen:continue
    seen.add(tup);out_rows.append({k:tup[i] for i,k in enumerate(('pt','en','es','zh','fr'))})

Path('i18n').mkdir(exist_ok=True)
Path('i18n/ui_3197_fast.json').write_text(json.dumps({'version':'3.19.7','generated_from':'3.19.6','rows':out_rows},ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(out_rows),'rows;',success,'/',total,'translation requests succeeded')
