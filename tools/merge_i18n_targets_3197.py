import json
from pathlib import Path

langs=('pt','en','es','zh','fr')
base=Path('tmp/i18n_targets')
packs={}
for lang in langs:
    p=base/f'{lang}.json'
    if not p.exists():raise SystemExit(f'missing target pack {p}')
    packs[lang]=json.loads(p.read_text(encoding='utf-8'))

# Index each target by deterministic row id.
indexes={lang:{r['id']:r for r in packs[lang].get('rows',[])} for lang in langs}
ids=set(indexes['en'])
for lang in langs:
    if set(indexes[lang])!=ids:
        raise SystemExit(f'row id mismatch for {lang}: {len(indexes[lang])} vs {len(ids)}')

rows=[]
for row_id in sorted(ids):
    anchor=indexes['en'][row_id]
    rec={lang:str(indexes[lang][row_id].get('value','')) for lang in langs}
    rows.append(rec)

# Manual polish for top-level navigation/Home where product wording matters.
overrides=[
('DASHBOARD // STATUS AO VIVO','DASHBOARD // LIVE STATUS','PANEL // ESTADO EN VIVO','仪表盘 // 实时状态','TABLEAU // ÉTAT EN DIRECT'),
('Resumo rápido do Roblox, módulos, assets e estado de reinício.','Quick summary of Roblox, modules, assets and restart state.','Resumen rápido de Roblox, módulos, recursos y estado de reinicio.','Roblox、模块、资源和重启状态的快速摘要。','Résumé rapide de Roblox, des modules, des ressources et de l’état de redémarrage.'),
('CLIENTE','CLIENT','CLIENTE','客户端','CLIENT'),
('OTIMIZAÇÕES','OPTIMIZATIONS','OPTIMIZACIONES','优化','OPTIMISATIONS'),
('ASSETS','ASSETS','RECURSOS','资源','RESSOURCES'),
('REINÍCIO','RESTART','REINICIO','重启','REDÉMARRAGE'),
('CENTRAL RÁPIDA','QUICK CENTER','CENTRO RÁPIDO','快捷中心','CENTRE RAPIDE'),
('Aplique as opções atuais ou ative o modo FPS seguro em um clique. Nenhum app é fechado automaticamente.','Apply current options or enable safe FPS mode in one click. No apps are closed automatically.','Aplica las opciones actuales o activa el modo FPS seguro con un clic. Ninguna aplicación se cierra automáticamente.','一键应用当前选项或启用安全 FPS 模式。不会自动关闭任何应用。','Appliquez les options actuelles ou activez le mode FPS sécurisé en un clic. Aucune application n’est fermée automatiquement.'),
('⚡ OTIMIZAR ROBLOX','⚡ OPTIMIZE ROBLOX','⚡ OPTIMIZAR ROBLOX','⚡ 优化 ROBLOX','⚡ OPTIMISER ROBLOX'),
('✓  APLICAR CONFIGURAÇÕES','✓  APPLY SETTINGS','✓  APLICAR AJUSTES','✓  应用设置','✓  APPLIQUER LES RÉGLAGES'),
('≋  COMPARAR CONFIGURAÇÕES','≋  COMPARE SETTINGS','≋  COMPARAR AJUSTES','≋  比较设置','≋  COMPARER LES RÉGLAGES'),
('▣  MODO COMPACTO','▣  COMPACT MODE','▣  MODO COMPACTO','▣  紧凑模式','▣  MODE COMPACT'),
('APLICAR','APPLY','APLICAR','应用','APPLIQUER'),
('Modo compacto','Compact mode','Modo compacto','紧凑模式','Mode compact'),
('Sons do ZKStrap','ZKStrap audio','Audio de ZKStrap','ZKStrap 音频','Audio ZKStrap'),
('ONLINE','ONLINE','EN LÍNEA','在线','EN LIGNE'),
('NÃO LOCALIZADO','NOT LOCATED','NO LOCALIZADO','未找到','NON LOCALISÉ'),
('SIM','YES','SÍ','是','OUI'),('NÃO','NO','NO','否','NON'),
('PADRÃO','DEFAULT','PREDETERMINADO','默认','PAR DÉFAUT'),
('CURSOR','CURSOR','CURSOR','光标','CURSEUR'),('FONTE','FONT','FUENTE','字体','POLICE'),
('Buscar página, opção ou ferramenta...','Search page, option or tool...','Buscar página, opción o herramienta...','搜索页面、选项或工具…','Rechercher une page, une option ou un outil…')]
for vals in overrides:
    data=dict(zip(langs,vals));found=None
    for r in rows:
        if r['pt']==vals[0] or r['en']==vals[1]:found=r;break
    if found:found.update(data)
    else:rows.append(data)

# Dedup exact five-language rows.
out=[];seen=set()
for r in rows:
    t=tuple(r[k] for k in langs)
    if t in seen:continue
    seen.add(t);out.append(dict(zip(langs,t)))

stats={lang:{'bad':packs[lang].get('bad',0),'network_count':packs[lang].get('network_count',0)} for lang in langs}
Path('i18n').mkdir(exist_ok=True)
Path('i18n/ui_3197_final.json').write_text(json.dumps({'version':'3.19.7','generated_from':'3.19.6','generator':'parallel-targets','rows':out,'stats':stats},ensure_ascii=False,indent=2),encoding='utf-8')
print('merged',len(out),'rows',stats)
if len(out)<300:raise SystemExit('merged pack too small')
