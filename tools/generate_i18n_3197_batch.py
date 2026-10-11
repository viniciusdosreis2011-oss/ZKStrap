import ast
import html
import json
import os
import re
import threading
import time
from collections import defaultdict
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
    if isinstance(fn,ast.Name): return fn.id
    if isinstance(fn,ast.Attribute): return fn.attr
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
                    if isinstance(arg,ast.Constant) and isinstance(arg.value,str): literals.append(arg.value)
        self.generic_visit(node)
LiteralVisitor().visit(app)

# Include legacy dictionary strings too.
for node in ast.walk(app):
    if not isinstance(node,ast.Assign): continue
    if not any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr=='tr' for t in node.targets):
        continue
    for sub in ast.walk(node.value):
        if isinstance(sub,ast.Constant) and isinstance(sub.value,str): literals.append(sub.value)

brand_exact={'','ZK','ZKSTRAP','ROBLOX','SPOTIFY','YOUTUBE','GITHUB','DISCORD','0:00','00%','←','−1','DUP','CORE','BLOX FRUITS'}
def translatable(x):
    x=str(x or '').strip()
    if not x or x in brand_exact or len(x)<3: return False
    if re.fullmatch(r'[\W_\d]+',x): return False
    if x.startswith(('http://','https://','C:\\')): return False
    return True

rows=[]; pair_seen=set(); pair_variants=set()
for pt,en in pairs:
    if (pt,en) in pair_seen: continue
    pair_seen.add((pt,en)); pair_variants.update((pt,en))
    rows.append({'kind':'pair','pt':pt,'en':en})
for text in dict.fromkeys(literals):
    if translatable(text) and text not in pair_variants:
        rows.append({'kind':'literal','source':text})

# Build unique strings per source->target pair.
groups=defaultdict(set)
for row in rows:
    if row['kind']=='pair':
        for target in ('es','zh-CN','fr'): groups[('en',target)].add(row['en'])
    else:
        for target in ('pt','en','es','zh-CN','fr'): groups[('auto',target)].add(row['source'])

# Pack each source/target set into modest query chunks.
chunks=[]
for (source,target),texts in groups.items():
    current=[]; chars=0
    for text in sorted(texts,key=lambda x:(len(x),x)):
        cost=len(text)+35
        if current and (len(current)>=18 or chars+cost>3300):
            chunks.append((source,target,current)); current=[]; chars=0
        current.append(text); chars+=cost
    if current: chunks.append((source,target,current))

endpoint='https://translate.googleapis.com/translate_a/single'
local=threading.local()
results={}
lock=threading.Lock()


def single_translate(session,source,target,text):
    params={'client':'gtx','sl':source,'tl':target,'dt':'t','q':text}
    r=session.get(endpoint,params=params,timeout=(4,12))
    if r.status_code!=200: raise RuntimeError(f'HTTP {r.status_code}')
    data=r.json(); segs=data[0] if isinstance(data,list) and data else []
    val=''.join(str(seg[0] or '') for seg in segs if isinstance(seg,list) and seg)
    return html.unescape(val).strip() or text


def translate_chunk(item):
    source,target,texts=item
    if not hasattr(local,'session'):
        local.session=requests.Session()
        local.session.headers.update({'User-Agent':'Mozilla/5.0 ZKStrap-i18n/3.19.7'})
    session=local.session
    marker='\n<<<ZKSEP3197>>>\n'
    payload=marker.join(texts)
    for attempt in range(4):
        try:
            translated=single_translate(session,source,target,payload)
            parts=translated.split('<<<ZKSEP3197>>>')
            parts=[p.strip() for p in parts]
            if len(parts)==len(texts):
                return {(source,target,t):v for t,v in zip(texts,parts)},len(texts),0
        except Exception:
            time.sleep(.45*(attempt+1))
    # Fallback: translate only this failed chunk one by one.
    out={}; failed=0
    for text in texts:
        ok=False
        for attempt in range(3):
            try:
                out[(source,target,text)]=single_translate(session,source,target,text);ok=True;break
            except Exception:
                time.sleep(.35*(attempt+1))
        if not ok:
            out[(source,target,text)]=text;failed+=1
    return out,len(texts)-failed,failed

success=failed=0
print('Translating',sum(len(c[2]) for c in chunks),'string-targets in',len(chunks),'batched requests')
with ThreadPoolExecutor(max_workers=8) as pool:
    futures=[pool.submit(translate_chunk,c) for c in chunks]
    done=0
    for fut in as_completed(futures):
        mapping,ok,bad=fut.result()
        with lock:
            results.update(mapping);success+=ok;failed+=bad;done+=1
            if done%10==0 or done==len(futures): print('chunks',done,'/',len(futures),'failed strings',failed)

if success+failed and success/(success+failed)<.82:
    raise SystemExit(f'translation coverage too low: {success}/{success+failed}')

final=[]
for row in rows:
    if row['kind']=='pair':
        en=row['en']; rec={'pt':row['pt'],'en':en}
        for lang,target in [('es','es'),('zh','zh-CN'),('fr','fr')]: rec[lang]=results.get(('en',target,en),en)
    else:
        text=row['source'];rec={}
        for lang,target in [('pt','pt'),('en','en'),('es','es'),('zh','zh-CN'),('fr','fr')]: rec[lang]=results.get(('auto',target,text),text)
    final.append(rec)

# Manual polish for the screenshot/Home and common navigation/actions.
overrides=[
('DASHBOARD // STATUS AO VIVO','DASHBOARD // LIVE STATUS','PANEL // ESTADO EN VIVO','仪表盘 // 实时状态','TABLEAU // ÉTAT EN DIRECT'),
('Resumo rápido do Roblox, módulos, assets e estado de reinício.','Quick summary of Roblox, modules, assets and restart state.','Resumen rápido de Roblox, módulos, recursos y estado de reinicio.','Roblox、模块、资源和重启状态的快速摘要。','Résumé rapide de Roblox, des modules, des ressources et de l’état de redémarrage.'),
('CLIENTE','CLIENT','CLIENTE','客户端','CLIENT'),('OTIMIZAÇÕES','OPTIMIZATIONS','OPTIMIZACIONES','优化','OPTIMISATIONS'),
('ASSETS','ASSETS','RECURSOS','资源','RESSOURCES'),('REINÍCIO','RESTART','REINICIO','重启','REDÉMARRAGE'),
('CENTRAL RÁPIDA','QUICK CENTER','CENTRO RÁPIDO','快捷中心','CENTRE RAPIDE'),
('Aplique as opções atuais ou ative o modo FPS seguro em um clique. Nenhum app é fechado automaticamente.','Apply current options or enable safe FPS mode in one click. No apps are closed automatically.','Aplica las opciones actuales o activa el modo FPS seguro con un clic. Ninguna aplicación se cierra automáticamente.','一键应用当前选项或启用安全 FPS 模式。不会自动关闭任何应用。','Appliquez les options actuelles ou activez le mode FPS sécurisé en un clic. Aucune application n’est fermée automatiquement.'),
('⚡ OTIMIZAR ROBLOX','⚡ OPTIMIZE ROBLOX','⚡ OPTIMIZAR ROBLOX','⚡ 优化 ROBLOX','⚡ OPTIMISER ROBLOX'),
('✓  APLICAR CONFIGURAÇÕES','✓  APPLY SETTINGS','✓  APLICAR AJUSTES','✓  应用设置','✓  APPLIQUER LES RÉGLAGES'),
('≋  COMPARAR CONFIGURAÇÕES','≋  COMPARE SETTINGS','≋  COMPARAR AJUSTES','≋  比较设置','≋  COMPARER LES RÉGLAGES'),
('▣  MODO COMPACTO','▣  COMPACT MODE','▣  MODO COMPACTO','▣  紧凑模式','▣  MODE COMPACT'),
('APLICAR','APPLY','APLICAR','应用','APPLIQUER'),('Modo compacto','Compact mode','Modo compacto','紧凑模式','Mode compact'),
('Sons do ZKStrap','ZKStrap audio','Audio de ZKStrap','ZKStrap 音频','Audio ZKStrap'),
('ONLINE','ONLINE','EN LÍNEA','在线','EN LIGNE'),('NÃO LOCALIZADO','NOT LOCATED','NO LOCALIZADO','未找到','NON LOCALISÉ'),
('SIM','YES','SÍ','是','OUI'),('NÃO','NO','NO','否','NON'),('PADRÃO','DEFAULT','PREDETERMINADO','默认','PAR DÉFAUT'),
('CURSOR','CURSOR','CURSOR','光标','CURSEUR'),('FONTE','FONT','FUENTE','字体','POLICE'),
('Buscar página, opção ou ferramenta...','Search page, option or tool...','Buscar página, opción o herramienta...','搜索页面、选项或工具…','Rechercher une page, une option ou un outil…')]
for vals in overrides:
    rec=dict(zip(('pt','en','es','zh','fr'),vals));match=None
    for r in final:
        if r.get('pt')==vals[0] or r.get('en')==vals[1]:match=r;break
    if match: match.update(rec)
    else: final.append(rec)

out_rows=[];seen=set()
for r in final:
    tup=tuple(str(r.get(k,'')) for k in ('pt','en','es','zh','fr'))
    if tup in seen: continue
    seen.add(tup);out_rows.append({k:tup[i] for i,k in enumerate(('pt','en','es','zh','fr'))})

Path('i18n').mkdir(exist_ok=True)
out={'version':'3.19.7','generated_from':'3.19.6','generator':'batch-final','rows':out_rows,'translation_success':success,'translation_failed':failed}
Path('i18n/ui_3197_final.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(out_rows),'rows; translated',success,'failed',failed)
