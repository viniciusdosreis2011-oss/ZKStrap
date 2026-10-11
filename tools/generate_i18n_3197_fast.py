import ast
import html
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from deep_translator import GoogleTranslator

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

brand_exact={'','ZK','ZKSTRAP','ROBLOX','SPOTIFY','YOUTUBE','GITHUB','DISCORD','0:00','00%','←','−1','DUP','CORE'}
def translatable(s):
    s=str(s or '').strip()
    if not s or s in brand_exact or len(s)<3:return False
    if re.fullmatch(r'[\W_\d]+',s):return False
    if s.startswith(('http://','https://','C:\\')):return False
    return True

rows=[]; pair_seen=set(); variants=set()
for pt,en in pairs:
    if (pt,en) in pair_seen: continue
    pair_seen.add((pt,en)); variants.update((pt,en))
    rows.append({'kind':'pair','pt':pt,'en':en})
for text in dict.fromkeys(literals):
    if not translatable(text) or text in variants: continue
    rows.append({'kind':'literal','source':text})

# Build a deduplicated translation task list.
tasks={}
for row in rows:
    if row['kind']=='pair':
        for lang,target in [('es','es'),('zh','zh-CN'),('fr','fr')]:
            tasks[('en',target,row['en'])]=None
    else:
        for lang,target in [('pt','pt'),('en','en'),('es','es'),('zh','zh-CN'),('fr','fr')]:
            tasks[('auto',target,row['source'])]=None

lock=threading.Lock(); done=0; total=len(tasks)
def translate_task(item):
    source,target,text=item
    last=None
    for attempt in range(5):
        try:
            val=GoogleTranslator(source=source,target=target).translate(text)
            val=html.unescape(str(val or text)).strip() or text
            return item,val
        except Exception as exc:
            last=exc; time.sleep(.45*(attempt+1))
    return item,text

results={}
with ThreadPoolExecutor(max_workers=8) as pool:
    futs=[pool.submit(translate_task,k) for k in tasks]
    for fut in as_completed(futs):
        item,val=fut.result(); results[item]=val
        with lock:
            done+=1
            if done%50==0 or done==total: print('translated',done,'/',total)

final=[]
for row in rows:
    if row['kind']=='pair':
        en=row['en']; rec={'pt':row['pt'],'en':en}
        for lang,target in [('es','es'),('zh','zh-CN'),('fr','fr')]:rec[lang]=results.get(('en',target,en),en)
    else:
        text=row['source']; rec={}
        for lang,target in [('pt','pt'),('en','en'),('es','es'),('zh','zh-CN'),('fr','fr')]:rec[lang]=results.get(('auto',target,text),text)
    final.append(rec)

# Hand-polish the highest-visibility command bar + Home status vocabulary.
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
    rec=dict(zip(('pt','en','es','zh','fr'),vals)); found=None
    for r in final:
        if r.get('pt')==vals[0] or r.get('en')==vals[1]:found=r;break
    if found:found.update(rec)
    else:final.append(rec)

# Dedup exact rows.
out_rows=[]; seen=set()
for r in final:
    tup=tuple(r.get(k,'') for k in ('pt','en','es','zh','fr'))
    if tup in seen:continue
    seen.add(tup);out_rows.append({k:tup[i] for i,k in enumerate(('pt','en','es','zh','fr'))})

Path('i18n').mkdir(exist_ok=True)
out={'version':'3.19.7','generated_from':'3.19.6','rows':out_rows}
Path('i18n/ui_3197_fast.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(out_rows),'five-language rows with',total,'translation tasks')
