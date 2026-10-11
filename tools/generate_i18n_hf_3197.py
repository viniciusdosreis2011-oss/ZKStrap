import gc
import json
import re
from pathlib import Path

from langdetect import detect, DetectorFactory
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

DetectorFactory.seed = 3197
LANGS=('pt','en','es','zh','fr')

pairs_path=Path('tmp/i18n_pairs_3196.txt')
uncovered_path=Path('tmp/i18n_uncovered_3196.txt')
if not pairs_path.exists() or not uncovered_path.exists():
    raise SystemExit('v3.19.7: required audit reports are missing')

# ------------------------------------------------------------------
# Parse canonical PT/EN pairs already present in the application.
# ------------------------------------------------------------------
pairs=[]
for raw in pairs_path.read_text(encoding='utf-8').splitlines()[3:]:
    parts=raw.split(' | ',4)
    if len(parts)!=5: continue
    pt=parts[3].replace('\\n','\n')
    en=parts[4].replace('\\n','\n')
    pairs.append((pt,en))

# Static strings that were not part of those old bilingual expressions.
uncovered=[]
for raw in uncovered_path.read_text(encoding='utf-8').splitlines()[3:]:
    parts=raw.split(' | ',3)
    if len(parts)!=4: continue
    text=parts[3].replace('\\n','\n')
    if text not in uncovered: uncovered.append(text)

print('input pairs',len(pairs),'uncovered',len(uncovered))
if len(pairs)<340 or len(uncovered)<120:
    raise SystemExit('v3.19.7: audit input unexpectedly small')

# ------------------------------------------------------------------
# Source-language classifier for previously hard-coded strings.
# It is deliberately biased toward Portuguese because the original app
# was written mostly in PT with scattered English product labels.
# ------------------------------------------------------------------
PT_WORDS={
    'não','nenhum','nenhuma','seu','sua','você','para','aqui','como','usar','abrir','fechar',
    'salvar','alterações','pronto','testando','dica','desafio','recompensas','carregado','carregada',
    'ainda','clique','escolha','passe','mouse','pode','podem','tudo','quando','cada','isso','temas',
    'fonte','rede','perfil','aplicar','contadores','zerar','histórico','criar','restaurar','último',
    'dados','segurança','chave','senha','texto','apenas','local','rápido','atualizar','modo','assistente',
    'estado','atalhos','conversa','livre','editar','mídia','sessão','volume','indisponível','seleção',
    'raridade','próxima','decisão','busca','universal','voltar','descoberta','oculta','condição','concluído',
    'perdi','morri','marcar','adicionar','vitória','configuração','núcleo','ambiente','inicializando',
    'preparando','galeria','será','serão','página','aberta','sob','demanda','junto','som','efeitos',
    'barulhos','interface','sorteie','completa','interessantes','resultado','funcionando','detectado',
    'detectada','controle','navegador','aba','abas','procurando','ferramenta','ferramentas','principal',
}
EN_WORDS={
    'the','and','to','of','is','are','now','playing','live','found','session','complete','continue',
    'ready','mode','open','close','search','secret','discovered','hover','locked','cards','themes','game',
    'packs','engine','client','configurator','performance','visual','assets','language','preference','first',
    'setup','signature','media','volume','dashboard','status','quick','center','apply','settings','compare',
    'compact','profile','audio','local','core','next','decision','special','hidden','identities','sources',
    'credits','selection','mass','rarity','challenge','history','random','build','target','current','windows',
}
KEEP_EXACT={
    'ZK','ZKSTRAP','ROBLOX','SPOTIFY','YOUTUBE','GITHUB','DISCORD','BLOX FRUITS','RBX','CORE',
    '0:00','00%','−1','DUP','LOCAL CORE','● READY','FPS','SFX','CLIENTSETTINGS','SECRET','OWNER',
}

def words(text):
    return re.findall(r"[A-Za-zÀ-ÿ]+",text.lower())

def source_lang(text):
    t=text.strip()
    if t in KEEP_EXACT: return 'keep'
    ws=words(t)
    pt_score=sum(w in PT_WORDS for w in ws)
    en_score=sum(w in EN_WORDS for w in ws)
    if re.search(r'[ãõáéíóúçâêôàü]',t.lower()): pt_score+=2
    if pt_score>en_score: return 'pt'
    if en_score>pt_score: return 'en'
    if len(t)>=18:
        try:
            code=detect(re.sub(r'[/•→←⚡✓▣≋?]+',' ',t))
            if code=='pt': return 'pt'
            if code=='en': return 'en'
        except Exception:
            pass
    # Short technical labels are more often English/brand terms in this codebase.
    return 'en'

# ------------------------------------------------------------------
# Marian helpers. Models are loaded one at a time to keep runner RAM low.
# ------------------------------------------------------------------
def translate_model(model_name,texts,batch_size=20):
    texts=list(texts)
    if not texts:return {}
    print('loading',model_name,'for',len(texts),'strings')
    tok=AutoTokenizer.from_pretrained(model_name)
    model=AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model.eval()
    out={}
    for start in range(0,len(texts),batch_size):
        batch=texts[start:start+batch_size]
        enc=tok(batch,return_tensors='pt',padding=True,truncation=True,max_length=480)
        gen=model.generate(**enc,max_new_tokens=420,num_beams=4,early_stopping=True)
        vals=tok.batch_decode(gen,skip_special_tokens=True)
        for src,val in zip(batch,vals):
            val=str(val or '').strip()
            out[src]=val if val else src
        if start and start%(batch_size*5)==0:
            print(model_name,start,'/',len(texts))
    del model,tok
    gc.collect()
    return out

# Create rows for known PT/EN pairs first.
rows=[]
seen_pairs=set()
for pt,en in pairs:
    if (pt,en) in seen_pairs:continue
    seen_pairs.add((pt,en))
    rows.append({'pt':pt,'en':en,'_origin':'pair'})

# Classify uncovered strings and canonicalize PT/EN using offline models.
classified={t:source_lang(t) for t in uncovered}
pt_uncovered=sorted({t for t,c in classified.items() if c=='pt'})
en_uncovered=sorted({t for t,c in classified.items() if c=='en'})
keep_uncovered=sorted({t for t,c in classified.items() if c=='keep'})
print('uncovered source split pt/en/keep',len(pt_uncovered),len(en_uncovered),len(keep_uncovered))

pt_to_en=translate_model('geralt/Opus-mt-pt-en',pt_uncovered,batch_size=18)
en_to_pt=translate_model('tonythethompson/Opus-MT-En-PT',en_uncovered,batch_size=14)

for text in uncovered:
    kind=classified[text]
    if kind=='pt':
        pt=text; en=pt_to_en.get(text,text)
    elif kind=='en':
        en=text; pt=en_to_pt.get(text,text)
    else:
        pt=en=text
    rows.append({'pt':pt,'en':en,'_origin':'literal','_source':text})

# Deduplicate canonical EN strings before the three target models.
canonical_en=sorted({r['en'] for r in rows if r['en'] and r['en'] not in KEEP_EXACT})
en_fr=translate_model('Helsinki-NLP/opus-mt-en-fr',canonical_en,batch_size=20)
en_es=translate_model('Helsinki-NLP/opus-mt-en-es',canonical_en,batch_size=20)
en_zh=translate_model('Helsinki-NLP/opus-mt-en-zh',canonical_en,batch_size=18)

for r in rows:
    en=r['en']
    if en in KEEP_EXACT:
        r['fr']=r['es']=r['zh']=en
    else:
        r['fr']=en_fr.get(en,en)
        r['es']=en_es.get(en,en)
        r['zh']=en_zh.get(en,en)

# ------------------------------------------------------------------
# Product-language polish for the most visible controls/statuses.
# Machine output remains coverage fallback; these are authoritative UI terms.
# ------------------------------------------------------------------
overrides=[
('DASHBOARD // STATUS AO VIVO','DASHBOARD // LIVE STATUS','PANEL // ESTADO EN VIVO','仪表盘 // 实时状态','TABLEAU // ÉTAT EN DIRECT'),
('Resumo rápido do Roblox, módulos, assets e necessidade de reinício.','Quick summary of Roblox, modules, assets and restart state.','Resumen rápido de Roblox, módulos, recursos y estado de reinicio.','Roblox、模块、资源和重启状态的快速摘要。','Résumé rapide de Roblox, des modules, des ressources et de l’état de redémarrage.'),
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
('⌕   Buscar página, opção ou ferramenta…                                  CTRL+K','⌕   Search page, option or tool…                                  CTRL+K','⌕   Buscar página, opción o herramienta…                                  CTRL+K','⌕   搜索页面、选项或工具…                                  CTRL+K','⌕   Rechercher une page, une option ou un outil…                                  CTRL+K'),
('BENCHMARK DO SISTEMA','SYSTEM BENCHMARK','BENCHMARK DEL SISTEMA','系统基准测试','BENCHMARK SYSTÈME'),
('Nenhuma medição ainda.','No measurement yet.','Aún no hay medición.','暂无测量结果。','Aucune mesure pour le moment.'),
('MEDIR AGORA','MEASURE NOW','MEDIR AHORA','立即测量','MESURER MAINTENANT'),
('ABRIR RECUPERAÇÃO','OPEN RECOVERY','ABRIR RECUPERACIÓN','打开恢复','OUVRIR LA RÉCUPÉRATION'),
('CLIENTE ROBLOX','ROBLOX CLIENT','CLIENTE ROBLOX','ROBLOX 客户端','CLIENT ROBLOX'),
('PERFIL ROBLOX','ROBLOX PROFILE','PERFIL ROBLOX','ROBLOX 资料','PROFIL ROBLOX'),
('VINCULAR / TROCAR','LINK / CHANGE','VINCULAR / CAMBIAR','关联 / 更换','LIER / MODIFIER'),
('DESVINCULAR','UNLINK','DESVINCULAR','取消关联','DÉLIER'),
('PERFIL','PROFILE','PERFIL','资料','PROFIL'),
('?   TUTORIAL','?   TUTORIAL','?   TUTORIAL','?   教程','?   TUTORIEL'),
('FECHAR LOG','CLOSE LOG','CERRAR LOG','关闭日志','FERMER LE JOURNAL'),
('ABRIR LOG','OPEN LOG','ABRIR LOG','打开日志','OUVRIR LE JOURNAL'),
('Rede: --','Network: --','Red: --','网络：--','Réseau : --'),
('Testando rota…','Testing route…','Probando ruta…','正在测试路由…','Test de la route…'),
('Testando DNS por RTT real…','Testing DNS by real RTT…','Probando DNS por RTT real…','正在按真实 RTT 测试 DNS…','Test DNS par RTT réel…'),
('DIAGNÓSTICO RÁPIDO','QUICK DIAGNOSTIC','DIAGNÓSTICO RÁPIDO','快速诊断','DIAGNOSTIC RAPIDE'),
('ANALISAR AGORA','ANALYZE NOW','ANALIZAR AHORA','立即分析','ANALYSER MAINTENANT'),
('IMPORTAR PNG','IMPORT PNG','IMPORTAR PNG','导入 PNG','IMPORTER PNG'),
('IMPORTAR PACK','IMPORT PACK','IMPORTAR PACK','导入包','IMPORTER UN PACK'),
('ATUALIZAR','REFRESH','ACTUALIZAR','刷新','ACTUALISER'),
('SESSÃO DE MÍDIA','MEDIA SESSION','SESIÓN MULTIMEDIA','媒体会话','SESSION MÉDIA'),
('Nenhum setup salvo ainda.','No setup saved yet.','Aún no hay setups guardados.','尚未保存任何配置。','Aucun setup enregistré pour le moment.'),
]

def apply_override(vals):
    data=dict(zip(LANGS,vals))
    found=None
    for r in rows:
        if r.get('pt')==vals[0] or r.get('en')==vals[1]:
            found=r;break
    if found: found.update(data)
    else: rows.append({**data,'_origin':'manual'})
for vals in overrides: apply_override(vals)

# Remove internal metadata and exact duplicate rows.
out=[];seen=set()
for r in rows:
    clean={k:str(r.get(k,'')) for k in LANGS}
    key=tuple(clean[k] for k in LANGS)
    if key in seen:continue
    seen.add(key);out.append(clean)

# Ensure every original uncovered string is an alias in at least one row.
all_aliases={v for r in out for v in r.values() if isinstance(v,str)}
missing=[t for t in uncovered if t not in all_aliases]
if missing:
    raise SystemExit(f'v3.19.7: {len(missing)} uncovered source aliases missing, first={missing[:3]!r}')

payload={
    'version':'3.19.7','generated_from':'3.19.6','generator':'offline-marian',
    'rows':out,
    'stats':{'legacy_pairs':len(pairs),'uncovered':len(uncovered),'rows':len(out),'source_pt':len(pt_uncovered),'source_en':len(en_uncovered),'source_keep':len(keep_uncovered)},
}
Path('i18n').mkdir(exist_ok=True)
Path('i18n/ui_3197_final.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print('generated final i18n pack',payload['stats'])
