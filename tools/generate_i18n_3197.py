import ast
import html
import json
import os
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

src_path=Path(os.environ['ZK_SOURCE_DIR'])/'ZKStrap_v3_18_0.py'
src=src_path.read_text(encoding='utf-8')
tree=ast.parse(src)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None: raise SystemExit('ModernConfigApp missing')

# Legacy PT/EN pairs.
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

# UI literals not represented by PT/EN ternaries.
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
    if not s or s in brand_exact: return False
    if len(s)<3: return False
    if re.fullmatch(r'[\W_\d]+',s): return False
    if s.startswith(('http://','https://','C:\\')): return False
    return True

# Build canonical records. English is the stable key for legacy pairs.
records={}
for pt,en in pairs:
    if not translatable(en) and not translatable(pt): continue
    key='pair:'+en
    records[key]={'pt':pt,'en':en}

paired_variants=set()
for row in records.values():
    paired_variants.add(row['pt']); paired_variants.add(row['en'])
for text in literals:
    if not translatable(text) or text in paired_variants: continue
    records.setdefault('literal:'+text,{'source':text})

cache_path=Path('tmp/i18n_3197_cache.json')
try: cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
except Exception: cache={}


def translate_one(text,target,source='auto'):
    ck=f'{source}|{target}|{text}'
    if ck in cache: return cache[ck]
    if target==source: return text
    last=None
    for attempt in range(4):
        try:
            val=GoogleTranslator(source=source,target=target).translate(text)
            val=html.unescape(str(val or text)).strip() or text
            cache[ck]=val
            cache_path.parent.mkdir(exist_ok=True)
            cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
            time.sleep(.06)
            return val
        except Exception as exc:
            last=exc; time.sleep(.65*(attempt+1))
    print('WARN translation failed',target,repr(text[:80]),repr(last))
    return text

pair_rows=[r for k,r in records.items() if k.startswith('pair:')]
for i,row in enumerate(pair_rows,1):
    en=row['en']
    for lang in ('es','zh-CN','fr'):
        out_key='zh' if lang=='zh-CN' else lang
        row[out_key]=translate_one(en,lang,source='en')
    if i%25==0: print('pairs',i,'/',len(pair_rows))

literal_rows=[r for k,r in records.items() if k.startswith('literal:')]
for i,row in enumerate(literal_rows,1):
    text=row['source']
    for lang,target in [('pt','pt'),('en','en'),('es','es'),('zh','zh-CN'),('fr','fr')]:
        row[lang]=translate_one(text,target,source='auto')
    if i%25==0: print('literals',i,'/',len(literal_rows))

rows=[]
seen=set()
for key,row in records.items():
    vals=tuple(str(row.get(k,row.get('source',''))) for k in ('pt','en','es','zh','fr'))
    if vals in seen: continue
    seen.add(vals); rows.append({'pt':vals[0],'en':vals[1],'es':vals[2],'zh':vals[3],'fr':vals[4]})

# Manual polish/overrides for the most visible Home/command-bar strings.
overrides=[
    ('DASHBOARD // STATUS AO VIVO','DASHBOARD // LIVE STATUS','PANEL // ESTADO EN VIVO','仪表盘 // 实时状态','TABLEAU // ÉTAT EN DIRECT'),
    ('CLIENTE','CLIENT','CLIENTE','客户端','CLIENT'),
    ('OTIMIZAÇÕES','OPTIMIZATIONS','OPTIMIZACIONES','优化','OPTIMISATIONS'),
    ('ASSETS','ASSETS','RECURSOS','资源','RESSOURCES'),
    ('REINÍCIO','RESTART','REINICIO','重启','REDÉMARRAGE'),
    ('CENTRAL RÁPIDA','QUICK CENTER','CENTRO RÁPIDO','快捷中心','CENTRE RAPIDE'),
    ('⚡ OTIMIZAR ROBLOX','⚡ OPTIMIZE ROBLOX','⚡ OPTIMIZAR ROBLOX','⚡ 优化 ROBLOX','⚡ OPTIMISER ROBLOX'),
    ('✓  APLICAR CONFIGURAÇÕES','✓  APPLY SETTINGS','✓  APLICAR AJUSTES','✓  应用设置','✓  APPLIQUER LES RÉGLAGES'),
    ('≋  COMPARAR CONFIGURAÇÕES','≋  COMPARE SETTINGS','≋  COMPARAR AJUSTES','≋  比较设置','≋  COMPARER LES RÉGLAGES'),
    ('▣  MODO COMPACTO','▣  COMPACT MODE','▣  MODO COMPACTO','▣  紧凑模式','▣  MODE COMPACT'),
    ('APLICAR','APPLY','APLICAR','应用','APPLIQUER'),
    ('Modo compacto','Compact mode','Modo compacto','紧凑模式','Mode compact'),
    ('Sons do ZKStrap','ZKStrap audio','Audio de ZKStrap','ZKStrap 音频','Audio ZKStrap'),
    ('ONLINE','ONLINE','EN LÍNEA','在线','EN LIGNE'),
    ('NÃO LOCALIZADO','NOT LOCATED','NO LOCALIZADO','未找到','NON LOCALISÉ'),
    ('SIM','YES','SÍ','是','OUI'),
    ('NÃO','NO','NO','否','NON'),
    ('PADRÃO','DEFAULT','PREDETERMINADO','默认','PAR DÉFAUT'),
    ('CURSOR','CURSOR','CURSOR','光标','CURSEUR'),
    ('FONTE','FONT','FUENTE','字体','POLICE'),
]
# Replace any row that contains PT or EN variant, else append.
for vals in overrides:
    found=None
    for r in rows:
        if r['pt']==vals[0] or r['en']==vals[1]: found=r; break
    data=dict(zip(('pt','en','es','zh','fr'),vals))
    if found is not None: found.update(data)
    else: rows.append(data)

out={'version':'3.19.7','generated_from':'3.19.6','rows':rows}
Path('i18n').mkdir(exist_ok=True)
Path('i18n/ui_3197.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(rows),'five-language UI rows')
