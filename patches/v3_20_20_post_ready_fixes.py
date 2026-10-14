from pathlib import Path
import ast, os, re, textwrap

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')


def _class(src):
    tree=ast.parse(src)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
    return tree,cls

def _span(src,name):
    _,cls=_class(src); lines=src.splitlines(True)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit('v3.20.20 missing method: '+name)
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

if 'APP_VERSION = "3.20.19"' not in s:
    raise SystemExit('v3.20.20 expected v3.20.19 base')
s=s.replace('APP_VERSION = "3.20.19"','APP_VERSION = "3.20.20"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Post Ready Mini Fixes"',s,count=1)

# -----------------------------------------------------------------------------
# CREATOR CHALLENGES: show USED rerolls (0/2 -> 1/2 -> 2/2), not remaining.
# Also make the replacement pool resilient to roulette_bump difficulty promotion.
# -----------------------------------------------------------------------------
s=replace_method(s,'creator_swap_challenge',r'''
def creator_swap_challenge(self,cid):
    items=[x for x in getattr(self,"creator_challenges",[]) if isinstance(x,dict)]
    old=next((x for x in items if x.get("id")==cid),None)
    if not old:
        try:self.show_toast("CREATOR MODE","Esse desafio não está mais ativo.",kind="info",duration=2200)
        except Exception:pass
        return
    if old.get("done"):
        try:self.show_toast("CREATOR MODE","Desafio já concluído.",kind="info",duration=2200)
        except Exception:pass
        return

    used_swaps=max(0,min(2,int(getattr(self,"_creator_session_swaps_used",0) or 0)))
    if used_swaps>=2:
        self.show_toast("LIMITE DE TROCAS","Você já usou 2/2 trocas nesta rodada. Gere outros desafios ou conclua todos para resetar.",kind="warning",duration=3400)
        return

    diff=str(old.get("difficulty","Médio") or "Médio")
    used_titles={str(x.get("title","") or "") for x in items}
    if diff=="SECRET":
        source=list(self._creator_secret_templates())
        pool=[x for x in source if str(x.get("title","") or "") not in used_titles]
    else:
        source=list(self._creator_templates())
        # A build Roulette can promote a template through roulette_bump. Treat the
        # promoted difficulty as part of the same pool so TROCAR never appears dead.
        pool=[x for x in source if (x.get("difficulty")==diff or x.get("roulette_bump")==diff) and str(x.get("title","") or "") not in used_titles]

    if not pool:
        self.show_toast("CREATOR MODE","Não encontrei outro desafio diferente para esta rodada. Gere outros desafios para renovar o pool.",kind="info",duration=3200)
        return

    chosen=random.choice(pool)
    repl=self._creator_new_runtime(chosen,context_build=old.get("context_build"))
    self._creator_session_swaps_used=used_swaps+1
    repl["swaps_used"]=self._creator_session_swaps_used
    self.creator_challenges=[repl if x.get("id")==cid else x for x in items]
    self.creator_refresh_challenges()
    self._play_ui_sound("select",0)
    try:self.show_toast("DESAFIO TROCADO",f"Trocas usadas: {self._creator_session_swaps_used}/2",kind="success",duration=1800)
    except Exception:pass
    if repl.get("difficulty")=="SECRET":
        self.after(120,lambda:self._creator_secret_reveal([repl.get("title")]))
''')

node,a,b=_span(s,'creator_refresh_challenges'); chunk=s[a:b]
old='''                remain=max(0,2-int(getattr(self,"_creator_session_swaps_used",0) or 0))
                ctk.CTkButton(head,text=f"TROCAR  {remain}/2",width=88,height=25,command=lambda cid=x.get("id"):self.creator_swap_challenge(cid),state="normal" if remain>0 else "disabled",fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="right")'''
new='''                used_swaps=max(0,min(2,int(getattr(self,"_creator_session_swaps_used",0) or 0)))
                ctk.CTkButton(head,text=f"TROCAR  {used_swaps}/2",width=88,height=25,command=lambda cid=x.get("id"):self.creator_swap_challenge(cid),state="normal" if used_swaps<2 else "disabled",fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="right")'''
if old not in chunk: raise SystemExit('v3.20.20 creator counter anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

# -----------------------------------------------------------------------------
# AUDIO: display-name-only rename. Folder and WAV assets stay exactly the same.
# -----------------------------------------------------------------------------
old='''    "ABYSS": {"folder":"abyss", "genre":"Dark Ambient", "bpm":68, "desc":"Drones, sinos distantes e espaço profundo."},'''
new='''    "RAIN SIGNAL": {"folder":"abyss", "genre":"Rain Ambient", "bpm":68, "desc":"Chuva distante, ruído suave e atmosfera noturna."},'''
if old not in s: raise SystemExit('v3.20.20 ABYSS pack anchor missing')
s=s.replace(old,new,1)
# Preserve existing configs and every legacy alias while changing only the label.
s=s.replace('''    "Deep Space":"ABYSS",''','''    "Deep Space":"RAIN SIGNAL",''',1)
s=s.replace('''    "Void Calm":"ABYSS",''','''    "Void Calm":"RAIN SIGNAL",''',1)
s=s.replace('''    "NO SIGNAL":"ABYSS",''','''    "NO SIGNAL":"RAIN SIGNAL",''',1)
s=s.replace('''    "BLACKOUT":"ABYSS",''','''    "BLACKOUT":"RAIN SIGNAL",''',1)
# Direct migration for people who already have ABYSS selected in config.
alias_anchor='AUDIO_PACK_ALIASES = {\n'
if alias_anchor not in s: raise SystemExit('v3.20.20 audio alias anchor missing')
s=s.replace(alias_anchor,alias_anchor+'    "ABYSS":"RAIN SIGNAL",\n',1)

# -----------------------------------------------------------------------------
# ROBLOX TOOLS: detection must always give visible feedback on the page.
# -----------------------------------------------------------------------------
helper=r'''
def _detect_roblox_with_feedback(self):
    L=self._L
    try:
        label=getattr(self,"tools_roblox_status_label",None)
        if label is not None and label.winfo_exists():
            label.configure(text=L("Procurando instalação do Roblox...","Looking for Roblox installation...","Buscando instalación de Roblox...","正在查找 Roblox 安装...","Recherche de l’installation Roblox..."),text_color=TEMAS[self.tema_atual].get("muted","gray"))
            self.update_idletasks()
    except Exception:pass

    found=""
    try:found=str(self.atualizar_pasta_roblox_atual() or "")
    except Exception:found=""
    if not (found and os.path.isfile(os.path.join(found,"RobloxPlayerBeta.exe"))):
        try:self.tentar_achar_roblox_automatico()
        except Exception:pass
        found=str(getattr(self,"pasta_roblox_salva","") or "")

    ok=bool(found and os.path.isfile(os.path.join(found,"RobloxPlayerBeta.exe")))
    label=getattr(self,"tools_roblox_status_label",None)
    if ok:
        version=os.path.basename(found)
        try:
            if label is not None and label.winfo_exists():
                label.configure(text=L(f"Encontrado: {version}",f"Found: {version}",f"Encontrado: {version}",f"已找到：{version}",f"Trouvé : {version}"),text_color=TEMAS[self.tema_atual]["accent"])
        except Exception:pass
        try:self.show_toast(L("ROBLOX ENCONTRADO","ROBLOX FOUND","ROBLOX ENCONTRADO","已找到 ROBLOX","ROBLOX TROUVÉ"),L("Cliente localizado com sucesso.","Client located successfully.","Cliente localizado correctamente.","已成功定位客户端。","Client localisé avec succès."),kind="success",duration=2200)
        except Exception:pass
    else:
        try:
            if label is not None and label.winfo_exists():
                label.configure(text=L("Roblox não encontrado automaticamente.","Roblox was not found automatically.","Roblox no fue encontrado automáticamente.","未自动找到 Roblox。","Roblox n’a pas été trouvé automatiquement."),text_color="#FF6B6B")
        except Exception:pass
        try:self.show_toast(L("ROBLOX NÃO ENCONTRADO","ROBLOX NOT FOUND","ROBLOX NO ENCONTRADO","未找到 ROBLOX","ROBLOX INTROUVABLE"),L("Use ABRIR PASTA ROBLOX ou localize a instalação manualmente.","Use OPEN ROBLOX FOLDER or locate the installation manually.","Usa ABRIR CARPETA ROBLOX o localiza la instalación manualmente.","请打开 Roblox 文件夹或手动定位安装目录。","Ouvrez le dossier Roblox ou localisez l’installation manuellement."),kind="warning",duration=3200)
        except Exception:pass
    try:self.refresh_dashboard()
    except Exception:pass
    return found if ok else ""
'''
_,cls=_class(s); lines=s.splitlines(True); insert_at=sum(len(x) for x in lines[:cls.end_lineno])
s=s[:insert_at]+'\n'+_norm(helper)+s[insert_at:]

node,a,b=_span(s,'_lazy_build_page_recovery'); chunk=s[a:b]
old='''ctk.CTkButton(r,text=L("DETECTAR ROBLOX","DETECT ROBLOX","DETECTAR ROBLOX","检测 ROBLOX","DÉTECTER ROBLOX"),command=self.tentar_achar_roblox_automatico,fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",expand=True,fill="x",padx=(0,4))'''
new='''ctk.CTkButton(r,text=L("DETECTAR ROBLOX","DETECT ROBLOX","DETECTAR ROBLOX","检测 ROBLOX","DÉTECTER ROBLOX"),command=self._detect_roblox_with_feedback,fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",expand=True,fill="x",padx=(0,4))'''
if old not in chunk: raise SystemExit('v3.20.20 recovery detect button anchor missing')
chunk=chunk.replace(old,new,1)
status_anchor='''        ctk.CTkButton(client,text=L("VERIFICAR CONFIGURAÇÕES APLICADAS","CHECK APPLIED SETTINGS","VERIFICAR AJUSTES APLICADOS","检查已应用设置","VÉRIFIER LES RÉGLAGES APPLIQUÉS"),command=self._show_applied_settings_summary,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["accent"]).pack(fill="x",padx=12,pady=(0,12))'''
status_new='''        self.tools_roblox_status_label=ctk.CTkLabel(client,text=(L("Detectado: ","Detected: ","Detectado: ","已检测：","Détecté : ")+os.path.basename(str(getattr(self,"pasta_roblox_salva","") or "")) if str(getattr(self,"pasta_roblox_salva","") or "") else L("Clique em DETECTAR ROBLOX para conferir a instalação.","Click DETECT ROBLOX to check the installation.","Haz clic en DETECTAR ROBLOX para comprobar la instalación.","点击“检测 ROBLOX”检查安装。","Cliquez sur DÉTECTER ROBLOX pour vérifier l’installation.")),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8),anchor="w")
        self.tools_roblox_status_label.pack(fill="x",padx=14,pady=(0,7))
        ctk.CTkButton(client,text=L("VERIFICAR CONFIGURAÇÕES APLICADAS","CHECK APPLIED SETTINGS","VERIFICAR AJUSTES APLICADOS","检查已应用设置","VÉRIFIER LES RÉGLAGES APPLIQUÉS"),command=self._show_applied_settings_summary,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["accent"]).pack(fill="x",padx=12,pady=(0,12))'''
if status_anchor not in chunk: raise SystemExit('v3.20.20 recovery status anchor missing')
chunk=chunk.replace(status_anchor,status_new,1); s=s[:a]+chunk+s[b:]

# -----------------------------------------------------------------------------
# PACÍFICO: keep calm identity, but make motion clearly visible in the preview.
# Only lightweight Canvas primitives are added.
# -----------------------------------------------------------------------------
node,a,b=_span(s,'_draw_theme_art'); chunk=s[a:b]
old='''            elif theme_name=="Pacífico":
                # Movimento quase imperceptível: brilho lento correndo pela superfície.
                for j in range(6):
                    px=int((j*151+ph*(2.0+(j%2)*.55))%max(1,w))
                    py=int(h*(.56+(j%3)*.10)+math.sin(ph*.055+j)*2)
                    half=5+(j%3)*4
                    canvas.create_line(px-half,py,px+half,py,fill=accent2 if j%3==0 else self._mix_hex(base,accent,.48),width=1)
                pts=[]; yy=int(h*.79)
                for x in range(-10,w+20,28):
                    pts += [x,yy+int(math.sin(x/82.0+ph*.045)*4)]
                if len(pts)>=4: canvas.create_line(*pts,fill=self._mix_hex(base,accent,.58),width=1,smooth=True)
'''
new='''            elif theme_name=="Pacífico":
                # Movimento calmo, mas perceptível: duas marés em parallax,
                # reflexos viajando na superfície e bolhas subindo devagar.
                for row,(yyf,speed,amp) in enumerate(((.59,.095,4.0),(.74,.070,5.2))):
                    pts=[]; yy=int(h*yyf)
                    for x in range(-24,w+32,24):
                        pts += [x,yy+int(math.sin(x/68.0+ph*speed+row*.85)*amp)]
                    if len(pts)>=4:
                        canvas.create_line(*pts,fill=accent if row==0 else self._mix_hex(base,accent2,.68),width=2 if row==0 else 1,smooth=True)
                for j in range(7):
                    px=int((j*143+ph*(3.0+(j%3)*.7))%max(1,w))
                    py=int(h*(.53+(j%4)*.085)+math.sin(ph*.08+j*.9)*3)
                    half=7+(j%3)*5
                    canvas.create_line(px-half,py,px+half,py,fill=accent2 if j%3==0 else self._mix_hex(base,accent,.56),width=1)
                for j in range(5):
                    bx=int(w*(.18+j*.16)+math.sin(ph*.055+j)*8)
                    by=int(h*.90-((ph*(1.1+j*.16)+j*37)%max(24,int(h*.40))))
                    r=2+(j%2)
                    canvas.create_oval(bx-r,by-r,bx+r,by+r,outline=self._mix_hex(base,accent2,.72),width=1)
                shimmer_x=int(w*(.79+math.sin(ph*.035)*.015))
                canvas.create_line(shimmer_x,int(h*.34),shimmer_x,int(h*.49),fill=self._mix_hex(base,accent2,.52),width=1)
'''
if old not in chunk: raise SystemExit('v3.20.20 Pacific motion anchor missing')
chunk=chunk.replace(old,new,1); s=s[:a]+chunk+s[b:]

# Structural/static validation.
ast.parse(s)
required=(
    'APP_VERSION = "3.20.20"',
    'TROCAR  {used_swaps}/2',
    'Trocas usadas: {self._creator_session_swaps_used}/2',
    '"RAIN SIGNAL": {"folder":"abyss"',
    '"ABYSS":"RAIN SIGNAL"',
    'def _detect_roblox_with_feedback(self):',
    'command=self._detect_roblox_with_feedback',
    'Movimento calmo, mas perceptível',
)
for marker in required:
    if marker not in s: raise SystemExit('v3.20.20 validation missing '+marker)
if '"ABYSS": {"folder":"abyss"' in s: raise SystemExit('v3.20.20 old ABYSS display name still active')
# Never touch the actual protected sound directory name.
if '"folder":"abyss"' not in s: raise SystemExit('v3.20.20 abyss audio folder changed')

p.write_text(s,encoding='utf-8')
print('Applied v3.20.20: challenge swap UX, Rain Signal label, Roblox detect feedback, Pacific motion')
