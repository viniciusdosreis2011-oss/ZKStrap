from pathlib import Path
import ast, os, re, textwrap

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')


def _class(src):
    t=ast.parse(src)
    return t,next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')

def _span(src,name):
    _,cls=_class(src); lines=src.splitlines(True)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'v3.20.16 method missing: {name}')
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    return textwrap.indent(textwrap.dedent(body).strip('\n')+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

def insert_before(src,before_name,body):
    _,a,_=_span(src,before_name)
    return src[:a]+_norm(body)+'\n'+src[a:]

if 'APP_VERSION = "3.20.15"' not in s:
    raise SystemExit('v3.20.16 expected v3.20.15 base')
s=s.replace('APP_VERSION = "3.20.15"','APP_VERSION = "3.20.16"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Release Polish: Unlock UX + Theme Render + Spotify Secret + Split Feedback"',s,count=1)

s=insert_before(s,'_unlock_secret_theme',r'''
def _announce_secret_theme_reward(self,name,reason=""):
    try:
        title=self._L("TEMA SECRETO DESBLOQUEADO","SECRET THEME UNLOCKED","TEMA SECRETO DESBLOQUEADO","秘密主题已解锁","THÈME SECRET DÉBLOQUÉ")
        where=self._L("Personalizar > Temas Secretos","Customize > Secret Themes","Personalizar > Temas Secretos","个性化 > 秘密主题","Personnaliser > Thèmes secrets")
        detail=f"{name}" + (f" • {reason}" if reason else "") + f"  •  {where}"
        if not self._play_secret_theme_sound(name,"unlock",0): self._play_ui_sound("secret_unlock",0)
        self.show_toast(title,detail,kind="success",duration=6500)
    except Exception:pass

def _flush_secret_unlock_announcements(self):
    pending=list(getattr(self,"_pending_secret_unlock_announcements",[]) or [])
    self._pending_secret_unlock_announcements=[]
    if not pending:return
    for i,(name,reason) in enumerate(pending):
        try:self.after(i*900,lambda n=name,r=reason:self._announce_secret_theme_reward(n,r))
        except Exception:pass
''')

s=replace_method(s,'_unlock_secret_theme',r'''
def _unlock_secret_theme(self, name, reason="", announce=True):
    if name not in UNLOCKABLE_THEME_NAMES:
        return False
    unlocked=set(getattr(self,"unlocked_secret_themes",set()))
    if name in unlocked:
        return False
    unlocked.add(name); self.unlocked_secret_themes=unlocked
    self.salvar_config_app()
    try:
        refresh=getattr(self,"_refresh_secret_theme_gallery",None)
        if callable(refresh): self.after(0,refresh)
    except Exception: pass
    if announce:
        if bool(getattr(self,"_defer_secret_unlock_toast",False)):
            q=list(getattr(self,"_pending_secret_unlock_announcements",[]) or [])
            q.append((name,reason)); self._pending_secret_unlock_announcements=q
        else:
            self._announce_secret_theme_reward(name,reason)
    return True
''')

s=replace_method(s,'_secret_music_tick',r'''
def _secret_music_tick(self):
    try:
        snap=dict(getattr(self,"_spotify_current",{}) or {})
        spotify_music=bool(snap.get("ok") and snap.get("title") and "PLAYING" in str(snap.get("status") or "").upper())
        if spotify_music and "Frequency" not in set(getattr(self,"unlocked_secret_themes",set())):
            self.secret_music_seconds=int(getattr(self,"secret_music_seconds",0) or 0)+1
            if self.secret_music_seconds>=60:
                self.secret_music_seconds=60
                self._unlock_secret_theme("Frequency",self._L("1 minuto ouvindo música no Spotify","1 minute listening on Spotify","1 minuto escuchando música en Spotify","在 Spotify 收听音乐 1 分钟","1 minute d’écoute sur Spotify"))
            elif self.secret_music_seconds%10==0:
                self.salvar_config_app()
    except Exception:
        pass
    try:self._secret_music_job=self.after(1000,self._secret_music_tick)
    except Exception:self._secret_music_job=None
''')

node,a,b=_span(s,'_apply_first_run_setup_choice'); chunk=s[a:b]
old='''            self._apply_setup_data(data)\n            self.aplicar_configuracoes()'''
new='''            self._apply_setup_data(data)\n            self._defer_secret_unlock_toast=True\n            try:\n                self.aplicar_configuracoes()\n            finally:\n                self._defer_secret_unlock_toast=False'''
if old not in chunk: raise SystemExit('v3.20.16 starter unlock defer anchor missing')
chunk=chunk.replace(old,new,1)
old2='''            self.show_toast(L("SETUP INICIAL PRONTO","STARTER SETUP READY","SETUP INICIAL LISTO","初始预设已就绪","SETUP INITIAL PRÊT"),chosen,kind="success",duration=3600)\n            if not bool(getattr(self,"sound_prompted",False)):'''
new2='''            self.show_toast(L("SETUP INICIAL PRONTO","STARTER SETUP READY","SETUP INICIAL LISTO","初始预设已就绪","SETUP INITIAL PRÊT"),chosen,kind="success",duration=1100)\n            if getattr(self,"_pending_secret_unlock_announcements",None):\n                self.after(1250,self._flush_secret_unlock_announcements)\n            if not bool(getattr(self,"sound_prompted",False)):'''
if old2 not in chunk: raise SystemExit('v3.20.16 starter unlock flush anchor missing')
chunk=chunk.replace(old2,new2,1); s=s[:a]+chunk+s[b:]

s=replace_method(s,'_queue_scroll_step',r'''
def _queue_scroll_step(self, scrollable, step):
    """Smooth scrolling generally; direct stable scrolling for canvas-heavy themes."""
    try:
        if scrollable is None or not step:return "break"
        canvas=getattr(scrollable,"_parent_canvas",None)
        if canvas is None or not canvas.winfo_exists():return "break"
        theme_body=getattr(self,"page_scrolls",{}).get("theme")
        if scrollable is theme_body:
            self._mark_fast_scroll()
            direction=1 if float(step)>0 else -1
            units=max(2,min(16,int(abs(float(step))*4)))
            canvas.yview_scroll(direction*units,"units")
            try:scrollable._zk_repaint_viewport(True)
            except Exception:pass
            try:self.after(28,self._repair_theme_render_surfaces)
            except Exception:pass
            return "break"
        now=time.monotonic()
        first,visible,total=self._scroll_canvas_metrics(canvas)
        max_first=max(0.0,1.0-visible)
        if max_first<=0.0:return "break"
        state=getattr(scrollable,"_zk_scroll_state",None)
        if not isinstance(state,dict):
            state={"target":first,"job":None,"last_input":0.0}
            setattr(scrollable,"_zk_scroll_state",state)
        if now-float(state.get("last_input",0.0) or 0.0)>.20:state["target"]=first
        target=float(state.get("target",first) or first)+(float(step)*64.0/max(1.0,total))
        state["target"]=max(0.0,min(max_first,target));state["last_input"]=now
        self._mark_fast_scroll()
        def tick():
            state["job"]=None
            try:
                if not canvas.winfo_exists():return
                cur,vis,_=self._scroll_canvas_metrics(canvas);limit=max(0.0,1.0-vis);dest=max(0.0,min(limit,float(state.get("target",cur))));diff=dest-cur
                if abs(diff)<0.00030:
                    canvas.yview_moveto(dest)
                    try:scrollable._zk_repaint_viewport(True)
                    except Exception:pass
                    return
                d=abs(diff);alpha=.27 if d<.035 else (.38 if d<.12 else .50)
                canvas.yview_moveto(max(0.0,min(limit,cur+diff*alpha)))
                state["job"]=self.after(14,tick)
            except Exception:state["job"]=None
        if state.get("job") is None:
            try:state["job"]=self.after(1,tick)
            except Exception:tick()
        return "break"
    except Exception:return "break"
''')

s=insert_before(s,'_fast_apply_theme',r'''
def _repair_theme_render_surfaces(self):
    """Normalize native Tk canvas backgrounds after theme swaps / heavy scrolling."""
    try:
        t=TEMAS[self.tema_atual]
        sidebar=t.get("sidebar",t.get("card",t["bg"])); panel=t.get("panel",t.get("card",t["bg"]))
        try:self.left_panel.configure(fg_color=sidebar)
        except Exception:pass
        nav=getattr(self,"nav_scroll",None)
        if nav is not None:
            try:nav._zk_host.configure(fg_color=sidebar)
            except Exception:pass
            try:nav.configure(fg_color=sidebar)
            except Exception:pass
            try:nav._parent_canvas.configure(bg=sidebar)
            except Exception:pass
        try:self.content_host.configure(fg_color=panel)
        except Exception:pass
        for key,body in dict(getattr(self,"page_scrolls",{}) or {}).items():
            bg=panel
            try:body._zk_host.configure(fg_color=bg)
            except Exception:pass
            try:body._parent_canvas.configure(bg=bg)
            except Exception:pass
            if key=="theme":
                try:body.configure(fg_color=bg)
                except Exception:pass
        try:self.update_idletasks()
        except Exception:pass
    except Exception:pass
''')

node,a,b=_span(s,'_fast_apply_theme'); chunk=s[a:b]
anchor='''        try:self._refresh_sound_button()\n        except Exception:pass\n        try:self.update_idletasks()'''
repl='''        try:self._refresh_sound_button()\n        except Exception:pass\n        try:self._repair_theme_render_surfaces()\n        except Exception:pass\n        try:self.update_idletasks()'''
if anchor not in chunk: raise SystemExit('v3.20.16 theme repair anchor missing')
chunk=chunk.replace(anchor,repl,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_lazy_build_page_theme'); chunk=s[a:b]
anchor='''        _, body = self._page_shell("theme", "PERSONALIZAR ZKSTRAP" if pt else "CUSTOMIZE ZKSTRAP", "Temas especiais usam banner próprio no topo; o restante do app permanece limpo, alinhado e consistente." if pt else "Special themes use their own top banner while the rest of the app stays clean, aligned and consistent.")'''
repl=anchor+'''\n        try:\n            stable_bg=t.get("panel",t["card"]);body.configure(fg_color=stable_bg);body._zk_host.configure(fg_color=stable_bg);body._parent_canvas.configure(bg=stable_bg)\n        except Exception:pass'''
if anchor not in chunk: raise SystemExit('v3.20.16 theme page surface anchor missing')
chunk=chunk.replace(anchor,repl,1);s=s[:a]+chunk+s[b:]

s=insert_before(s,'_lazy_build_page_feedback',r'''
def _feedback_form_counter(self,textbox,label):
    try:
        n=len(textbox.get("0.0","end").rstrip("\n"));label.configure(text=self._L(f"{n} caracteres",f"{n} characters",f"{n} caracteres",f"{n} 个字符",f"{n} caractères"))
    except Exception:pass

def _feedback_submit_form(self,kind,title_entry,textbox,counter_label,send_button):
    try:msg=textbox.get("0.0","end").strip()
    except Exception:msg=""
    try:title=title_entry.get().strip()
    except Exception:title=""
    if len(msg)<5:
        try:messagebox.showwarning(self.tr[self.idioma]['msg_warning'],self.tr[self.idioma]['short_message_warning'])
        except Exception:pass
        return
    is_bug=(kind=="bug")
    diag,logs=({},[])
    if is_bug:
        try:diag,logs=self._collect_bug_diagnostics()
        except Exception:diag,logs=({},[])
    tipo=self._L("Reportar Bug","Report Bug","Reportar Bug","报告错误","Signaler un bug") if is_bug else self._L("Sugestão","Suggestion","Sugerencia","建议","Suggestion")
    payload={"source":"zkstrap-client","type":tipo,"title":self._sanitize_diag_text(title)[:140],"message":str(msg)[:3500],"app_version":APP_VERSION,"diagnostics":diag,"recent_logs":logs}
    try:send_button.configure(state="disabled",text=self._L("ENVIANDO…","SENDING…","ENVIANDO…","发送中…","ENVOI…"))
    except Exception:pass
    def worker():
        sent=False;copied=False;reason="";endpoint=self._feedback_endpoint()
        if endpoint:
            try:
                r=requests.post(endpoint,json=payload,timeout=8,headers={"User-Agent":f"ZKStrap/{APP_VERSION}"});sent=r.status_code in (200,201,202,204)
                if not sent:reason=f"HTTP {r.status_code}"
            except Exception as exc:reason=self._sanitize_diag_text(exc)
        else:reason="endpoint unavailable"
        if not sent:copied=self._copy_feedback_fallback(payload)
        def finish():
            try:send_button.configure(state="normal",text=self._L("ENVIAR BUG","SEND BUG","ENVIAR BUG","发送错误报告","ENVOYER LE BUG") if is_bug else self._L("ENVIAR SUGESTÃO","SEND SUGGESTION","ENVIAR SUGERENCIA","发送建议","ENVOYER LA SUGGESTION"))
            except Exception:pass
            if sent:
                try:self.show_toast(self._L("BUG ENVIADO","BUG SENT","BUG ENVIADO","错误报告已发送","BUG ENVOYÉ") if is_bug else self._L("SUGESTÃO ENVIADA","SUGGESTION SENT","SUGERENCIA ENVIADA","建议已发送","SUGGESTION ENVOYÉE"),self._L("Valeu. O relatório chegou na central do ZKStrap.","Thanks. Your report reached ZKStrap support.","Gracias. El reporte llegó al soporte de ZKStrap.","谢谢，内容已发送到 ZKStrap 支持中心。","Merci. Le rapport a été reçu par le support ZKStrap."),kind="success",duration=3200)
                except Exception:pass
                try:textbox.delete("0.0","end");title_entry.delete(0,"end");self._feedback_form_counter(textbox,counter_label)
                except Exception:pass
            else:
                msg2=self._L("Sem conexão/endpoint. O conteúdo foi copiado para a área de transferência." if copied else "Sem conexão/endpoint. Não consegui enviar o conteúdo.","No connection/endpoint. The content was copied to clipboard." if copied else "No connection/endpoint. The content could not be sent.","Sin conexión/endpoint. El contenido fue copiado al portapapeles." if copied else "Sin conexión/endpoint. No se pudo enviar.","无连接/服务端点。内容已复制到剪贴板。" if copied else "无连接/服务端点，无法发送。","Pas de connexion/endpoint. Le contenu a été copié dans le presse-papiers." if copied else "Pas de connexion/endpoint. Envoi impossible.")
                try:self.show_toast(self._L("MODO OFFLINE","OFFLINE MODE","MODO OFFLINE","离线模式","MODE HORS LIGNE"),msg2,kind="warning",duration=4200)
                except Exception:pass
                try:self.log_output(f"[!] Feedback not sent: {reason}")
                except Exception:pass
        try:self.after(0,finish)
        except Exception:pass
    threading.Thread(target=worker,daemon=True).start()

def _lazy_build_page_bugs(self):
    if "bugs" in getattr(self,"pages",{}):return self.pages.get("bugs")
    t=TEMAS[self.tema_atual];L=self._L
    _,body=self._page_shell("bugs",L("REPORTAR BUG","REPORT BUG","REPORTAR BUG","报告错误","SIGNALER UN BUG"),L("Uma área só para erros reais do ZKStrap. O diagnóstico técnico é anexado automaticamente.","A dedicated area for real ZKStrap problems. Technical diagnostics are attached automatically.","Un área solo para errores reales de ZKStrap. El diagnóstico técnico se adjunta automáticamente.","仅用于报告 ZKStrap 的实际问题，并自动附加技术诊断。","Une zone dédiée aux vrais problèmes de ZKStrap. Le diagnostic technique est joint automatiquement."))
    hero=self._section_card(body,L("O QUE QUEBROU?","WHAT BROKE?","¿QUÉ FALLÓ?","哪里出错了？","QU’EST-CE QUI A CASSÉ ?"),L("Diga a função usada, o que aconteceu e o que você esperava. Se conseguir repetir o bug, explique os passos.","Tell us which feature you used, what happened and what you expected. If reproducible, include the steps.","Di qué función usaste, qué pasó y qué esperabas. Si se puede repetir, incluye los pasos.","说明使用了哪个功能、发生了什么以及预期结果；如果能复现，请写出步骤。","Indiquez la fonction utilisée, ce qui s’est passé et le résultat attendu. Si le bug est reproductible, donnez les étapes."))
    title=ctk.CTkEntry(hero,placeholder_text=L("Título curto — ex.: Personalizar fica preto ao rolar","Short title — e.g. Customize turns black while scrolling","Título corto — ej.: Personalizar se pone negro al desplazar","简短标题 — 例如：滚动个性化页面时变黑","Titre court — ex. Personnaliser devient noir en défilant"),height=40);title.pack(fill="x",padx=16,pady=(4,7))
    box=ctk.CTkTextbox(hero,height=200,fg_color=t.get("panel",t["card"]),text_color=t["text"],border_width=1,border_color=t["card_active"],font=ctk.CTkFont(size=10));box.pack(fill="x",padx=16,pady=5);self._bind_outer_scroll(box,"bugs")
    counter=ctk.CTkLabel(hero,text=L("0 caracteres","0 characters","0 caracteres","0 个字符","0 caractères"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8));counter.pack(anchor="e",padx=16,pady=(0,4));box.bind("<KeyRelease>",lambda e:self._feedback_form_counter(box,counter))
    ctk.CTkLabel(hero,text=L("O relatório inclui versão do app, Windows, tema atual, estado do Roblox e logs recentes sanitizados — nunca senha ou token.","The report includes app version, Windows, current theme, Roblox state and sanitized recent logs — never passwords or tokens.","El reporte incluye versión, Windows, tema, estado de Roblox y logs recientes sanitizados — nunca contraseñas ni tokens.","报告包含应用版本、Windows、当前主题、Roblox 状态和已清理的近期日志——绝不包含密码或令牌。","Le rapport inclut version, Windows, thème actuel, état Roblox et logs récents nettoyés — jamais de mot de passe ni de jeton."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),wraplength=920,justify="left",anchor="w").pack(fill="x",padx=16,pady=(2,8))
    send=ctk.CTkButton(hero,text=L("ENVIAR BUG","SEND BUG","ENVIAR BUG","发送错误报告","ENVOYER LE BUG"),height=42,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");send.configure(command=lambda:self._feedback_submit_form("bug",title,box,counter,send));send.pack(fill="x",padx=16,pady=(2,14))
    self._section_card(body,L("ANTES DE ENVIAR","BEFORE SENDING","ANTES DE ENVIAR","发送前","AVANT D’ENVOYER"),L("Reinicie a função/aba uma vez, confira se o erro continua e descreva o mais específico possível.","Retry the feature/tab once, confirm the issue persists and describe it as specifically as possible.","Reintenta la función/pestaña una vez, confirma que el error continúa y descríbelo con detalle.","先重试一次相关功能/页面，确认问题仍存在，并尽量具体描述。","Réessayez une fois la fonction/l’onglet, vérifiez que le problème persiste et décrivez-le précisément."))
    return self.pages.get("bugs")

def _lazy_build_page_suggestions(self):
    if "suggestions" in getattr(self,"pages",{}):return self.pages.get("suggestions")
    t=TEMAS[self.tema_atual];L=self._L
    _,body=self._page_shell("suggestions",L("SUGERIR","SUGGEST","SUGERIR","提出建议","SUGGÉRER"),L("Mande ideias para deixar o ZKStrap melhor sem misturar com relatórios de bug.","Send ideas to improve ZKStrap without mixing them with bug reports.","Envía ideas para mejorar ZKStrap sin mezclarlas con reportes de bugs.","提交改进 ZKStrap 的想法，不与错误报告混在一起。","Envoyez des idées pour améliorer ZKStrap sans les mélanger aux rapports de bugs."))
    allowed=self._section_card(body,L("O QUE VOCÊ PODE SUGERIR","WHAT YOU CAN SUGGEST","QUÉ PUEDES SUGERIR","可以建议什么","CE QUE VOUS POUVEZ SUGGÉRER"),L("Temas • FastFlags seguras • recursos do app • melhorias visuais • áudio • qualidade de vida • novas ferramentas úteis.","Themes • safe FastFlags • app features • visual improvements • audio • quality-of-life • useful new tools.","Temas • FastFlags seguras • funciones • mejoras visuales • audio • calidad de vida • herramientas útiles.","主题 • 安全 FastFlags • 应用功能 • 视觉改进 • 音频 • 体验优化 • 实用新工具。","Thèmes • FastFlags sûres • fonctions • améliorations visuelles • audio • qualité de vie • nouveaux outils utiles."))
    chips=ctk.CTkFrame(allowed,fg_color="transparent");chips.pack(fill="x",padx=14,pady=(2,12))
    for label in (L("TEMAS","THEMES","TEMAS","主题","THÈMES"),"FASTFLAGS",L("RECURSOS","FEATURES","FUNCIONES","功能","FONCTIONS"),L("VISUAL","VISUAL","VISUAL","视觉","VISUEL"),L("ÁUDIO","AUDIO","AUDIO","音频","AUDIO")):
        ctk.CTkLabel(chips,text=label,height=27,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=(0,6))
    self._section_card(body,L("LIMITE DE SEGURANÇA","SAFETY LIMIT","LÍMITE DE SEGURIDAD","安全限制","LIMITE DE SÉCURITÉ"),L("Não envie pedidos de exploit, cheat, bypass, roubo de conta, coisas ilegais ou recursos que tenham objetivo de causar ban. A ideia do ZKStrap é melhorar configuração e experiência sem transformar o app em ferramenta de trapaça.","Do not request exploits, cheats, bypasses, account theft, illegal features or tools intended to cause bans. ZKStrap is for improving configuration and experience, not becoming a cheating tool.","No pidas exploits, cheats, bypasses, robo de cuentas, funciones ilegales ni herramientas pensadas para causar bans. ZKStrap busca mejorar configuración y experiencia, no ser una herramienta de trampas.","请勿提出漏洞利用、作弊、绕过、账号盗取、违法功能或以导致封禁为目的的工具。ZKStrap 的目标是改善配置和体验，而不是成为作弊工具。","Ne demandez pas d’exploits, cheats, contournements, vol de compte, fonctions illégales ou outils destinés à provoquer un bannissement. ZKStrap améliore la configuration et l’expérience, ce n’est pas un outil de triche."))
    form=self._section_card(body,L("SUA IDEIA","YOUR IDEA","TU IDEA","你的想法","VOTRE IDÉE"),L("Explique o que seria, onde entraria no app e por que seria útil.","Explain what it is, where it would fit in the app and why it would be useful.","Explica qué sería, dónde iría en la app y por qué sería útil.","说明它是什么、应该放在应用哪里，以及为什么有用。","Expliquez ce que c’est, où cela s’intégrerait dans l’app et pourquoi ce serait utile."))
    title=ctk.CTkEntry(form,placeholder_text=L("Título — ex.: tema inspirado em...","Title — e.g. theme inspired by...","Título — ej.: tema inspirado en...","标题 — 例如：受…启发的主题","Titre — ex. thème inspiré de..."),height=40);title.pack(fill="x",padx=16,pady=(4,7))
    box=ctk.CTkTextbox(form,height=190,fg_color=t.get("panel",t["card"]),text_color=t["text"],border_width=1,border_color=t["card_active"],font=ctk.CTkFont(size=10));box.pack(fill="x",padx=16,pady=5);self._bind_outer_scroll(box,"suggestions")
    counter=ctk.CTkLabel(form,text=L("0 caracteres","0 characters","0 caracteres","0 个字符","0 caractères"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8));counter.pack(anchor="e",padx=16,pady=(0,4));box.bind("<KeyRelease>",lambda e:self._feedback_form_counter(box,counter))
    send=ctk.CTkButton(form,text=L("ENVIAR SUGESTÃO","SEND SUGGESTION","ENVIAR SUGERENCIA","发送建议","ENVOYER LA SUGGESTION"),height=42,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");send.configure(command=lambda:self._feedback_submit_form("suggestion",title,box,counter,send));send.pack(fill="x",padx=16,pady=(2,14))
    return self.pages.get("suggestions")
''')

s=replace_method(s,'_lazy_build_page_feedback',r'''
def _lazy_build_page_feedback(self):
    return self._lazy_build_page_bugs()
''')

node,a,b=_span(s,'criar_interface');chunk=s[a:b]
old='''            ("feedback",self._L("SUGESTÕES & BUGS","FEEDBACK & BUGS","SUGERENCIAS & BUGS","建议与错误","SUGGESTIONS & BUGS")),'''
new='''            ("bugs",self._L("REPORTAR BUG","REPORT BUG","REPORTAR BUG","报告错误","SIGNALER UN BUG")),\n            ("suggestions",self._L("SUGERIR","SUGGEST","SUGERIR","提出建议","SUGGÉRER")),'''
if old not in chunk:raise SystemExit('v3.20.16 nav feedback anchor missing')
chunk=chunk.replace(old,new,1)
old='''            15:self._L("SISTEMA","SYSTEM","SISTEMA","系统","SYSTÈME"),\n            17:"INFO",'''
new='''            15:self._L("FEEDBACK","FEEDBACK","FEEDBACK","反馈","FEEDBACK"),\n            17:"INFO",'''
if old not in chunk:raise SystemExit('v3.20.16 nav sections anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'build_right_tabview');chunk=s[a:b]
old='''"feedback": self._lazy_build_page_feedback, "support": self._lazy_build_page_support'''
new='''"bugs": self._lazy_build_page_bugs, "suggestions": self._lazy_build_page_suggestions, "feedback": self._lazy_build_page_feedback, "support": self._lazy_build_page_support'''
if old not in chunk:raise SystemExit('v3.20.16 lazy builder anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'show_page');chunk=s[a:b]
old='''        if key=="ai": key="feedback"'''
new='''        if key in ("ai","feedback"): key="bugs"'''
if old not in chunk:raise SystemExit('v3.20.16 show_page compatibility anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_search_catalog');chunk=s[a:b]
old='''            {"title":"Sugestões & Bugs","sub":"Feedback","keys":"bug erro sugestao feedback discord","page":"feedback","scroll":0.0},'''
new='''            {"title":self._L("Reportar Bug","Report Bug","Reportar Bug","报告错误","Signaler un bug"),"sub":"Feedback","keys":"bug erro error problema report reportar","page":"bugs","scroll":0.0},\n            {"title":self._L("Sugerir","Suggest","Sugerir","提出建议","Suggérer"),"sub":"Feedback","keys":"sugestao suggestion ideia tema flag recurso feature feedback","page":"suggestions","scroll":0.0},'''
if old not in chunk:raise SystemExit('v3.20.16 search feedback anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_tutorial_steps');chunk=s[a:b]
chunk=chunk.replace('(\"feedback\",L(\"SUGESTÕES & BUGS\"','(\"bugs\",L(\"REPORTAR BUG\"',1)
chunk=chunk.replace('L(\"Envie relatos de erro e sugestões com contexto para facilitar as próximas correções.\"','L(\"Reporte problemas reais com contexto para facilitar as próximas correções.\"',1)
chunk=chunk.replace('L(\"Quanto mais específico o relato, melhor.\"','L(\"Quanto mais específico o bug, melhor.\"',1)
s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_make_nav_icon');chunk=s[a:b]
old='''            elif key == "feedback":\n                d.rounded_rectangle((6*scale,7*scale,22*scale,18*scale), radius=3*scale, outline=accent, width=w)\n                d.polygon([(10*scale,18*scale),(10*scale,22*scale),(15*scale,18*scale)], fill=accent)\n                d.line((10*scale,11*scale,18*scale,11*scale), fill=accent2, width=scale)\n                d.line((10*scale,14*scale,16*scale,14*scale), fill=accent2, width=scale)'''
new='''            elif key in ("feedback","bugs"):\n                d.rounded_rectangle((6*scale,7*scale,22*scale,18*scale), radius=3*scale, outline=accent, width=w)\n                d.polygon([(10*scale,18*scale),(10*scale,22*scale),(15*scale,18*scale)], fill=accent)\n                d.line((14*scale,10*scale,14*scale,14*scale), fill=accent2, width=2*scale)\n                d.ellipse((13*scale,16*scale,15*scale,18*scale), fill=accent2)\n            elif key == "suggestions":\n                d.ellipse((8*scale,6*scale,20*scale,18*scale), outline=accent, width=w)\n                d.line((11*scale,20*scale,17*scale,20*scale),fill=accent2,width=2*scale)\n                d.line((12*scale,23*scale,16*scale,23*scale),fill=accent,width=scale)\n                for ax,ay,bx,by in ((14,3,14,5),(5,10,7,11),(21,10,23,11)):\n                    d.line((ax*scale,ay*scale,bx*scale,by*scale),fill=accent2,width=scale)'''
if old not in chunk:raise SystemExit('v3.20.16 nav icon anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

ast.parse(s)
for marker in ('APP_VERSION = "3.20.16"','spotify_music=bool(snap.get("ok")','def _flush_secret_unlock_announcements','def _repair_theme_render_surfaces','if scrollable is theme_body','def _lazy_build_page_bugs','def _lazy_build_page_suggestions','("bugs",self._L("REPORTAR BUG"','("suggestions",self._L("SUGERIR"'):
    if marker not in s:raise SystemExit('v3.20.16 validation missing '+marker)
p.write_text(s,encoding='utf-8')
print('Applied v3.20.16 release polish: unlock UX, stable theme rendering, Spotify-only secret, split feedback')
