from pathlib import Path
import os, re, ast

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def offsets(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line); pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None: raise SystemExit('v3.19.5: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_method):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'v3.19.5: method missing: {name}')
    _,pos=offsets(s)
    start=pos[node.lineno-1]; end=pos[node.end_lineno]
    s=s[:start]+new_method.rstrip()+"\n\n"+s[end:]


# VERSION
if 'APP_VERSION = "3.19.4"' not in s:
    raise SystemExit('v3.19.5: expected v3.19.4 base')
s=s.replace('APP_VERSION = "3.19.4"','APP_VERSION = "3.19.5"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Readable Type + Premium Onboarding + Clean Tutorial"',s,count=1)
if n!=1: raise SystemExit('v3.19.5: timestamp missing')


# TYPOGRAPHY — never collapse native/tuple fonts to size 11 after a rebuild.
font_method=r'''    def aplicar_fonte_widgets(self, widget):
        """Apply the selected UI family without changing any widget's size."""
        try:
            children=widget.winfo_children()
        except Exception:
            return
        for child in children:
            try:
                fonte=child.cget("font")
                if isinstance(fonte,ctk.CTkFont):
                    tamanho=fonte.cget("size")
                    try:familia=str(fonte.cget("family") or "")
                    except Exception:familia=""
                    if familia in ("Consolas","Courier New") and abs(int(tamanho or 0))<=8 and self.fonte_ui!="Consolas":
                        pass
                    else:
                        kwargs={"family":self.fonte_ui,"size":tamanho}
                        for key in ("weight","slant","underline","overstrike"):
                            try:kwargs[key]=fonte.cget(key)
                            except Exception:pass
                        child.configure(font=ctk.CTkFont(**kwargs))
                # Tk widgets can return tuple/named-font strings. Leave those untouched
                # instead of forcing every one of them to (family, 11).
            except Exception:
                pass
            try:self.aplicar_fonte_widgets(child)
            except Exception:pass
'''
replace_app_method('aplicar_fonte_widgets',font_method)


# LANGUAGE APPLY — persist the new picker revision before rebuilding.
language_apply=r'''    def aplicar_idioma(self, escolha):
        raw=str(escolha or "").strip().lower()
        mapping={
            "português":"pt","portugues":"pt","pt":"pt",
            "english":"en","en":"en",
            "español":"es","espanol":"es","es":"es",
            "中文":"zh","chinese":"zh","zh":"zh",
            "français":"fr","francais":"fr","fr":"fr",
        }
        code=next((v for k,v in mapping.items() if k in raw),"en")
        self.idioma=code
        self.language_selected=True
        try:self.config_data["language_picker_revision"]=3
        except Exception:pass
        self.salvar_config_app()
        names={"pt":"Português","en":"English","es":"Español","zh":"中文","fr":"Français"}
        self.log_output(f"[*] Idioma alterado para: {names.get(code,code)}")
        self.after(25,self.reconstruir_interface)
'''
replace_app_method('aplicar_idioma',language_apply)


# SPLASH — keep it visible long enough to actually read it.
s,n=re.subn(r'_startup_splash_finish\(self,self\._startup_state,min_visible=[0-9.]+\)',
            '_startup_splash_finish(self,self._startup_state,min_visible=3.05)',s,count=1)
if n!=1: raise SystemExit('v3.19.5: splash min-visible call missing')
s,n=re.subn(r'hold_until = time\.time\(\) \+ [0-9.]+','hold_until = time.time() + 0.50',s,count=1)
if n!=1: raise SystemExit('v3.19.5: splash 100% hold missing')
s,n=re.subn(r'if time\.time\(\)-done_since>=[0-9.]+:','if time.time()-done_since>=.45:',s,count=1)
if n!=1: raise SystemExit('v3.19.5: detached splash finish hold missing')


# LANGUAGE ONBOARDING — full-screen, deliberate first-run screen.
language_picker=r'''    def _maybe_show_first_run_language(self):
        try:picker_rev=int(self.config_data.get("language_picker_revision",0) or 0)
        except Exception:picker_rev=0
        if bool(getattr(self,"language_selected",False)) and picker_rev>=3:
            return
        old=getattr(self,"_language_panel",None)
        try:
            if old is not None and old.winfo_exists():
                old.lift(); return
        except Exception:pass
        host=getattr(self,"main_container",None)
        if host is None:
            try:self.after(120,self._maybe_show_first_run_language)
            except Exception:pass
            return

        t=TEMAS[self.tema_atual]
        try:self.update_idletasks()
        except Exception:pass
        cover=ctk.CTkFrame(host,fg_color=t["bg"],corner_radius=0,border_width=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1)
        cover.lift(); self._language_panel=cover

        try:
            hw=max(720,int(host.winfo_width())); hh=max(560,int(host.winfo_height()))
        except Exception:
            hw,hh=1000,700
        pw=max(720,min(880,hw-54)); ph=max(470,min(535,hh-48))
        panel=ctk.CTkFrame(cover,width=pw,height=ph,fg_color=t.get("panel",t["card"]),corner_radius=22,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.55))
        panel.place(relx=.5,rely=.5,anchor="center"); panel.pack_propagate(False)

        cap=ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0)
        cap.pack(fill="x",side="top")
        body=ctk.CTkFrame(panel,fg_color="transparent")
        body.pack(fill="both",expand=True,padx=18,pady=18)

        hero=ctk.CTkFrame(body,width=270,fg_color=self._mix_hex(t.get("panel",t["card"]),t["accent"],.08),corner_radius=18,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.26))
        hero.pack(side="left",fill="y",padx=(0,16)); hero.pack_propagate(False)
        logo=ctk.CTkFrame(hero,width=70,height=70,corner_radius=18,fg_color=t["card_active"],border_width=1,border_color=t["accent"])
        logo.pack(anchor="w",padx=22,pady=(25,18)); logo.pack_propagate(False)
        ctk.CTkLabel(logo,text="ZK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=22,weight="bold")).place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(hero,text="FIRST SETUP",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w").pack(fill="x",padx=22)
        ctk.CTkLabel(hero,text="ZKSTRAP",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=26,weight="bold"),anchor="w").pack(fill="x",padx=22,pady=(6,3))
        ctk.CTkLabel(hero,text="Configure a linguagem da interface antes de entrar no app.",wraplength=220,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=11)).pack(fill="x",padx=22,pady=(4,18))

        meter=ctk.CTkFrame(hero,fg_color="transparent")
        meter.pack(fill="x",padx=22,pady=(8,0))
        ctk.CTkLabel(meter,text="LOCAL PREFERENCE",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(anchor="w")
        line=ctk.CTkFrame(meter,height=3,fg_color=t["card_active"],corner_radius=2); line.pack(fill="x",pady=(7,7))
        ctk.CTkFrame(line,width=82,height=3,fg_color=t["accent"],corner_radius=2).place(x=0,y=0)
        ctk.CTkLabel(meter,text="01 / 01   •   LANGUAGE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w")

        right=ctk.CTkFrame(body,fg_color="transparent")
        right.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(right,text="Escolha seu idioma",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=24,weight="bold"),anchor="w").pack(fill="x",padx=6,pady=(4,2))
        ctk.CTkLabel(right,text="Choose your interface language",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=11),anchor="w").pack(fill="x",padx=6,pady=(0,13))

        def choose(code):
            self.idioma=code; self.language_selected=True
            self.config_data["language"]=code
            self.config_data["language_selected"]=True
            self.config_data["language_picker_revision"]=3
            try:self.salvar_config_app()
            except Exception:pass
            try:cover.destroy()
            except Exception:pass
            self._language_panel=None
            try:self.after(40,self.reconstruir_interface)
            except Exception:pass
            try:self.after(520,self._maybe_show_sound_consent)
            except Exception:pass
            try:self.after(900,self._maybe_show_first_run_tutorial)
            except Exception:pass

        for code,name,sub in self._language_choices():
            img=self._language_flag_image(code,size=(48,30))
            btn=ctk.CTkButton(right,text=f"{name}\n{sub}",image=img,compound="left",anchor="w",height=62,corner_radius=13,fg_color=t["card"],hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.38),text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=12,weight="bold"),command=lambda c=code:choose(c))
            btn.pack(fill="x",padx=6,pady=4)

        foot=ctk.CTkFrame(right,fg_color="transparent")
        foot.pack(fill="x",padx=6,pady=(10,0))
        ctk.CTkLabel(foot,text="Você pode alterar depois em Personalizar.",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),anchor="w").pack(side="left")
        ctk.CTkLabel(foot,text="5 LANGUAGES  //  READY",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="right")
'''
replace_app_method('_maybe_show_first_run_language',language_picker)


# TUTORIAL CONTENT — explain every sidebar destination, no missions.
tutorial_steps=r'''    def _tutorial_steps(self):
        nick=self._tutorial_username()
        L=self._L
        return [
            ("home",L("INÍCIO","HOME","INICIO","主页","ACCUEIL"),L(f"Bem-vindo, @{nick}. Aqui fica o resumo do ZKStrap, estado do Roblox e atalhos principais.",f"Welcome, @{nick}. This is the ZKStrap overview, Roblox status and main shortcuts.",f"Bienvenido, @{nick}. Aquí ves el resumen de ZKStrap, Roblox y accesos rápidos.",f"欢迎，@{nick}。这里是 ZKStrap 概览、Roblox 状态和主要快捷入口。",f"Bienvenue, @{nick}. Ici se trouvent le résumé ZKStrap, l’état Roblox et les raccourcis."),L("Use esta página como ponto de partida.","Use this page as your starting point.","Usa esta página como punto de partida.","把这里当作起点。","Utilisez cette page comme point de départ.")),
            ("fps",L("FPS & GRÁFICOS","FPS & GRAPHICS","FPS & GRÁFICOS","FPS 与画质","FPS & GRAPHISMES"),L("Reúne os ajustes de desempenho e gráficos do cliente Roblox, incluindo os controles mais usados.","Contains Roblox client performance and graphics controls, including the most-used options.","Reúne los controles de rendimiento y gráficos del cliente Roblox.","包含 Roblox 客户端的性能与画质设置。","Regroupe les réglages de performances et graphismes du client Roblox."),L("O Modo Avançado concentra as opções mais técnicas.","Advanced Mode contains the more technical controls.","El Modo Avanzado contiene los controles técnicos.","高级模式包含更技术性的选项。","Le Mode avancé contient les réglages techniques.")),
            ("ping",L("PING & LATÊNCIA","PING & LATENCY","PING & LATENCIA","PING 与网络","PING & LATENCE"),L("Ferramentas para diagnosticar conexão, latência e estabilidade de rede durante o Roblox.","Tools for diagnosing connection, latency and network stability while using Roblox.","Herramientas para diagnosticar conexión, latencia y estabilidad de red.","用于诊断连接、延迟和网络稳定性。","Outils pour diagnostiquer connexion, latence et stabilité réseau."),L("Use os testes daqui para separar problema de rede de problema de FPS.","Use these tests to separate network issues from FPS issues.","Usa estas pruebas para separar red de FPS.","用这些测试区分网络与 FPS 问题。","Utilisez ces tests pour distinguer réseau et FPS.")),
            ("cursor",L("CURSOR","CURSOR","CURSOR","光标","CURSEUR"),L("Troque o cursor do Roblox por packs personalizados e veja a prévia antes de aplicar.","Apply custom Roblox cursor packs and preview them before changing files.","Cambia el cursor de Roblox con packs y vista previa.","更换 Roblox 光标包并在应用前预览。","Changez le curseur Roblox avec aperçu avant application."),L("O backup permite voltar ao original.","A backup lets you restore the original.","El backup permite volver al original.","备份可恢复原版。","La sauvegarde permet de revenir à l’original.")),
            ("fonts",L("FONTES","FONTS","FUENTES","字体","POLICES"),L("Importe TTF/OTF, veja a prévia real e aplique fontes ao Roblox sem mexer nos arquivos de emoji.","Import TTF/OTF files, preview them and apply fonts to Roblox without replacing emoji files.","Importa TTF/OTF, mira la vista previa y aplica fuentes sin tocar emojis.","导入 TTF/OTF、预览并应用到 Roblox，同时保留表情字体。","Importez TTF/OTF, prévisualisez puis appliquez sans toucher aux emojis."),L("A prévia mostra a fonte selecionada antes da alteração.","The preview shows the selected font before applying it.","La vista previa muestra la fuente antes de aplicarla.","预览会在应用前显示字体效果。","L’aperçu montre la police avant application.")),
            ("theme",L("PERSONALIZAR","CUSTOMIZE","PERSONALIZAR","个性化","PERSONNALISER"),L("Mude tema, cor de destaque, fonte da interface e idioma do ZKStrap.","Change the ZKStrap theme, accent, interface font and language.","Cambia tema, color, fuente de interfaz e idioma.","更改主题、强调色、界面字体和语言。","Changez thème, couleur, police d’interface et langue."),L("As mudanças visuais ficam salvas localmente.","Visual preferences are stored locally.","Las preferencias visuales se guardan localmente.","视觉偏好会保存在本地。","Les préférences visuelles restent locales.")),
            ("audio",L("ÁUDIO","AUDIO","AUDIO","音频","AUDIO"),L("Controle sons da interface, música ambiente, volume e packs sonoros do ZKStrap.","Control interface sounds, ambient music, volume and ZKStrap sound packs.","Controla sonidos, música, volumen y packs de audio.","控制界面音效、背景音乐、音量和音效包。","Contrôlez sons, musique, volume et packs audio."),L("Você pode deixar tudo desligado se preferir.","Everything can stay disabled if you prefer.","Puedes dejar todo desactivado si prefieres.","也可以全部关闭。","Vous pouvez tout désactiver si vous préférez.")),
            ("spotify",L("SPOTIFY","SPOTIFY","SPOTIFY","SPOTIFY","SPOTIFY"),L("Mostra e controla a mídia compatível do sistema dentro do app quando disponível.","Shows and controls compatible system media inside the app when available.","Muestra y controla multimedia compatible del sistema.","在可用时显示并控制系统媒体。","Affiche et contrôle les médias système compatibles."),L("A integração depende do player e das permissões do Windows.","Integration depends on the player and Windows permissions.","La integración depende del reproductor y Windows.","集成取决于播放器和 Windows 权限。","L’intégration dépend du lecteur et de Windows.")),
            ("combo",L("COMBO PLANNER","COMBO PLANNER","COMBO PLANNER","连招规划","COMBO PLANNER"),L("Monte e salve builds, sequências e ideias de combo para consultar depois.","Create and save builds, sequences and combo ideas for later.","Crea y guarda builds, secuencias y combos.","创建并保存配装、技能顺序和连招。","Créez et sauvegardez builds, séquences et combos."),L("Os dados ficam no seu ZKStrap.","Your data stays in ZKStrap.","Los datos quedan en ZKStrap.","数据保存在 ZKStrap 中。","Les données restent dans ZKStrap.")),
            ("roulette",L("BUILD ROULETTE","BUILD ROULETTE","BUILD ROULETTE","随机配装","BUILD ROULETTE"),L("Gere combinações aleatórias para desafios, vídeos ou simplesmente testar builds diferentes.","Generate random combinations for challenges, videos or trying different builds.","Genera combinaciones aleatorias para retos, videos o pruebas.","生成随机配装用于挑战、视频或测试。","Générez des combinaisons aléatoires pour défis ou vidéos."),L("Boa para sair da build de sempre.","Useful when you want something different from your usual build.","Útil para salir de la build de siempre.","适合尝试不同玩法。","Pratique pour changer de votre build habituelle.")),
            ("creator",L("CREATOR MODE","CREATOR MODE","MODO CREADOR","创作者模式","MODE CRÉATEUR"),L("Ferramentas pensadas para gravação, organização e fluxo de criação de conteúdo.","Tools designed around recording, organization and content-creation workflows.","Herramientas para grabación, organización y creación de contenido.","面向录制、整理和内容创作流程的工具。","Outils pour enregistrement, organisation et création de contenu."),L("Ative só o que fizer sentido para sua gravação.","Enable only what helps your recording workflow.","Activa solo lo que ayude a tu grabación.","只启用对录制有帮助的功能。","Activez seulement ce qui aide votre workflow.")),
            ("ai",L("ZK ASSIST","ZK ASSIST","ZK ASSIST","ZK ASSIST","ZK ASSIST"),L("Central de ajuda do ZKStrap para dúvidas sobre configurações, aplicação e recursos do app.","ZKStrap help center for settings, applying changes and app features.","Centro de ayuda de ZKStrap para ajustes y funciones.","ZKStrap 帮助中心，用于设置、应用和功能说明。","Centre d’aide ZKStrap pour réglages et fonctions."),L("A assistência geral continua separada dos guias do app.","General assistance stays separate from the app guides.","La asistencia general sigue separada de las guías.","通用助手与应用指南分开。","L’assistance générale reste séparée des guides.")),
            ("setups",L("SETUPS","SETUPS","SETUPS","预设","SETUPS"),L("Organize e reaplique conjuntos de configurações sem precisar refazer tudo manualmente.","Organize and reapply groups of settings without rebuilding them manually.","Organiza y reaplica grupos de configuraciones.","整理并重新应用成套设置。","Organisez et réappliquez des ensembles de réglages."),L("Use nomes claros para saber rapidamente o objetivo de cada setup.","Use clear names so each setup is easy to recognize.","Usa nombres claros para reconocer cada setup.","用清晰名称区分每个预设。","Utilisez des noms clairs pour chaque setup.")),
            ("maintenance",L("DESEMPENHO","PERFORMANCE","RENDIMIENTO","性能","PERFORMANCES"),L("Benchmark e diagnóstico do sistema para comparar CPU, RAM, processos e uso do Roblox.","System benchmark and diagnostics for CPU, RAM, processes and Roblox usage.","Benchmark y diagnóstico de CPU, RAM, procesos y Roblox.","用于 CPU、内存、进程和 Roblox 使用情况的基准与诊断。","Benchmark et diagnostic CPU, RAM, processus et Roblox."),L("Serve para medir o sistema antes e depois de ajustes.","Use it to compare the system before and after changes.","Sirve para comparar antes y después de cambios.","用于比较调整前后的系统状态。","Comparez le système avant et après les réglages.")),
            ("recovery",L("RECUPERAÇÃO","RECOVERY","RECUPERACIÓN","恢复","RÉCUPÉRATION"),L("Ferramentas para restaurar configurações, corrigir alterações e voltar a um estado seguro.","Tools to restore settings, repair changes and return to a safe state.","Herramientas para restaurar y reparar configuraciones.","用于恢复设置、修复更改并回到安全状态。","Outils pour restaurer et réparer les réglages."),L("É a primeira parada se alguma personalização não sair como esperado.","Use this first if a customization does not behave as expected.","Úsalo primero si una personalización sale mal.","自定义出现问题时先来这里。","À utiliser en premier si une personnalisation pose problème.")),
            ("updates",L("ATUALIZAÇÕES","UPDATES","ACTUALIZACIONES","更新","MISES À JOUR"),L("Veja sua versão, canal Stable/Beta e o histórico das mudanças do ZKStrap.","See your version, Stable/Beta channel and ZKStrap change history.","Mira tu versión, canal Stable/Beta e historial.","查看版本、Stable/Beta 渠道和更新历史。","Consultez version, canal Stable/Beta et historique."),L("Beta recebe testes antes de uma versão virar Stable.","Beta receives testing before a build becomes Stable.","Beta recibe pruebas antes de pasar a Stable.","Beta 会先测试，再进入 Stable。","La Beta est testée avant de devenir Stable.")),
            ("feedback",L("SUGESTÕES & BUGS","FEEDBACK & BUGS","SUGERENCIAS & BUGS","建议与错误","SUGGESTIONS & BUGS"),L("Envie relatos de erro e sugestões com contexto para facilitar as próximas correções.","Send bug reports and suggestions with context to make fixes easier.","Envía errores y sugerencias con contexto.","提交带上下文的错误报告和建议。","Envoyez bugs et suggestions avec du contexte."),L("Quanto mais específico o relato, melhor.","The more specific the report, the better.","Cuanto más específico, mejor.","描述越具体越好。","Plus le rapport est précis, mieux c’est.")),
            ("support",L("APOIAR","SUPPORT","APOYAR","支持","SOUTENIR"),L("Área com formas de apoiar o projeto e acessar os canais públicos relacionados ao ZKStrap.","Area for supporting the project and accessing related public ZKStrap channels.","Área para apoyar el proyecto y acceder a canales públicos.","用于支持项目并访问 ZKStrap 公共渠道。","Zone pour soutenir le projet et accéder aux canaux publics."),L("Apoiar é opcional; o app continua funcionando normalmente.","Support is optional; the app keeps working normally.","Apoyar es opcional; el app funciona igual.","支持完全可选，不影响应用使用。","Le soutien est facultatif; l’app fonctionne normalement.")),
            ("about",L("SOBRE","ABOUT","ACERCA DE","关于","À PROPOS"),L("Informações do ZKStrap, versão atual e detalhes gerais do projeto.","ZKStrap information, current version and general project details.","Información de ZKStrap, versión y detalles del proyecto.","ZKStrap 信息、当前版本和项目详情。","Informations ZKStrap, version actuelle et détails du projet."),L("É aqui que você confere exatamente qual build está usando.","This is where you can confirm the exact build you are using.","Aquí puedes confirmar la build exacta.","这里可以确认正在使用的具体版本。","C’est ici que vous vérifiez la build exacte.")),
        ]
'''
replace_app_method('_tutorial_steps',tutorial_steps)


# TUTORIAL UI — clean guide card, no mission, no highlight rectangle, no gate.
tutorial_open=r'''    def abrir_tutorial(self, primeiro_acesso=False):
        """Clean in-app guide that explains each navigation destination."""
        try:self._fechar_busca_universal()
        except Exception:pass
        try:self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception:pass
        self._tutorial_first_run=bool(primeiro_acesso)
        self._tutorial_step_index=0
        self._tutorial_replay=not primeiro_acesso
        self._tutorial_step_ready=True
        self._tutorial_spotlight=None
        self._tutorial_mission=None
        self._tutorial_explore=None

        t=TEMAS[self.tema_atual]
        panel=ctk.CTkFrame(self.main_container,width=470,height=405,fg_color=t.get("panel",t["card"]),corner_radius=18,border_width=2,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.72))
        panel.place(relx=.985,rely=.52,anchor="e"); panel.pack_propagate(False); panel.lift()
        self._tutorial_panel=panel

        accent=ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0)
        accent.pack(fill="x")
        top=ctk.CTkFrame(panel,fg_color="transparent")
        top.pack(fill="x",padx=18,pady=(15,5))
        self._tutorial_badge=ctk.CTkLabel(top,text=self._L("ZK // GUIA RÁPIDO","ZK // QUICK GUIDE","ZK // GUÍA RÁPIDA","ZK // 快速指南","ZK // GUIDE RAPIDE"),height=26,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"))
        self._tutorial_badge.pack(side="left")
        self._tutorial_count=ctk.CTkLabel(top,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=9,weight="bold"))
        self._tutorial_count.pack(side="right")
        self._tutorial_title=ctk.CTkLabel(panel,text="",font=ctk.CTkFont(family="Segoe UI",size=22,weight="bold"),text_color=t["text"],anchor="w")
        self._tutorial_title.pack(fill="x",padx=18,pady=(8,3))
        self._tutorial_body=ctk.CTkLabel(panel,text="",wraplength=420,justify="left",anchor="w",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=11))
        self._tutorial_body.pack(fill="x",padx=18,pady=(4,10))

        info=ctk.CTkFrame(panel,fg_color=t["card_active"],corner_radius=12,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.22))
        info.pack(fill="x",padx=18,pady=(1,12))
        ctk.CTkLabel(info,text=self._L("NESTA ABA","IN THIS TAB","EN ESTA PESTAÑA","此页面","DANS CET ONGLET"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x",padx=12,pady=(10,2))
        self._tutorial_tip=ctk.CTkLabel(info,text="",wraplength=390,justify="left",anchor="w",text_color=t.get("muted",t["text"]),font=ctk.CTkFont(family="Segoe UI",size=10))
        self._tutorial_tip.pack(fill="x",padx=12,pady=(2,11))

        progress_head=ctk.CTkFrame(panel,fg_color="transparent")
        progress_head.pack(fill="x",padx=18,pady=(0,4))
        ctk.CTkLabel(progress_head,text=self._L("PROGRESSO","PROGRESS","PROGRESO","进度","PROGRESSION"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left")
        self._tutorial_progress=ctk.CTkProgressBar(panel,height=5,progress_color=t["accent"],fg_color=t["card_active"])
        self._tutorial_progress.pack(fill="x",padx=18,pady=(0,13))

        row=ctk.CTkFrame(panel,fg_color="transparent")
        row.pack(fill="x",padx=18,pady=(0,15),side="bottom")
        self._tutorial_prev=ctk.CTkButton(row,text="←",command=lambda:self._tutorial_move(-1),width=50,height=34,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"])
        self._tutorial_prev.pack(side="left")
        self._tutorial_skip=ctk.CTkButton(row,text=self._L("SAIR","EXIT","SALIR","退出","QUITTER"),command=self._tutorial_skip_click,width=74,height=34,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"))
        self._tutorial_skip.pack(side="left",padx=7)
        self._tutorial_next=ctk.CTkButton(row,text="",command=lambda:self._tutorial_move(1),height=34,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=11,weight="bold"))
        self._tutorial_next.pack(side="left",fill="x",expand=True)
        self._tutorial_render_step()
'''
replace_app_method('abrir_tutorial',tutorial_open)


tutorial_render=r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps()
        idx=max(0,min(self._tutorial_step_index,len(steps)-1)); self._tutorial_step_index=idx
        page,title,body,tip=steps[idx][:4]
        self._tutorial_step_ready=True
        try:self.show_page(page,animate=True)
        except Exception:pass
        try:self._tutorial_place_spotlight(None)
        except Exception:pass
        self._tutorial_title.configure(text=title)
        self._tutorial_body.configure(text=body)
        self._tutorial_tip.configure(text=tip)
        self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
        self._tutorial_progress.set((idx+1)/max(1,len(steps)))
        self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
        label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("PRÓXIMO  →","NEXT  →","SIGUIENTE  →","下一步  →","SUIVANT  →")
        self._tutorial_next.configure(state="normal",text=label)
'''
replace_app_method('_tutorial_render_step',tutorial_render)


tutorial_move=r'''    def _tutorial_move(self, delta):
        steps=self._tutorial_steps()
        nxt=self._tutorial_step_index+int(delta)
        if nxt>=len(steps):
            self._tutorial_close(mark_complete=True)
            try:self.show_toast(self._L("TUTORIAL CONCLUÍDO","TUTORIAL COMPLETE","TUTORIAL COMPLETADO","教程完成","TUTORIEL TERMINÉ"),self._L("Você pode abrir o guia novamente pelo botão Tutorial.","You can reopen the guide from the Tutorial button.","Puedes abrir la guía otra vez desde Tutorial.","可通过 Tutorial 按钮再次打开指南。","Vous pouvez rouvrir le guide avec le bouton Tutorial."),kind="success")
            except Exception:pass
            return
        self._tutorial_step_index=max(0,nxt)
        self._tutorial_render_step()
'''
replace_app_method('_tutorial_move',tutorial_move)


tutorial_skip=r'''    def _tutorial_skip_click(self):
        self._tutorial_close(mark_complete=False)
        try:self.show_toast(self._L("GUIA FECHADO","GUIDE CLOSED","GUÍA CERRADA","指南已关闭","GUIDE FERMÉ"),self._L("Você pode continuar depois pelo botão Tutorial.","You can continue later from the Tutorial button.","Puedes continuar después desde Tutorial.","之后可通过 Tutorial 按钮继续查看。","Vous pourrez continuer plus tard via Tutorial."),kind="info")
        except Exception:pass
'''
replace_app_method('_tutorial_skip_click',tutorial_skip)


tutorial_explore=r'''    def _tutorial_explore_current(self):
        return
'''
replace_app_method('_tutorial_explore_current',tutorial_explore)


tutorial_spotlight=r'''    def _tutorial_place_spotlight(self, widget):
        """v3.19.5: tutorial no longer draws highlight rectangles over the app."""
        try:
            old=getattr(self,"_tutorial_spotlight",None)
            if isinstance(old,(list,tuple)):
                for part in old:
                    try:part.destroy()
                    except Exception:pass
            elif old is not None:
                try:old.destroy()
                except Exception:pass
        except Exception:pass
        self._tutorial_spotlight=None
        return
'''
replace_app_method('_tutorial_place_spotlight',tutorial_spotlight)


# VALIDATION
for needle in (
    'APP_VERSION = "3.19.5"',
    'min_visible=3.05',
    'language_picker_revision"]=3',
    'def aplicar_fonte_widgets(self, widget)',
    'instead of forcing every one of them to (family, 11).',
    'def _tutorial_place_spotlight(self, widget)',
    'tutorial no longer draws highlight rectangles',
    'ZK // GUIA RÁPIDO',
    '("ping",L("PING & LATÊNCIA"',
    '("about",L("SOBRE"',
):
    if needle not in s:
        raise SystemExit('v3.19.5: required surface missing: '+needle)

for forbidden in (
    'self._tutorial_mission.configure(text=mission)',
    'self._tutorial_next.configure(state="disabled"',
    'TESTE PRIMEIRO ↑',
):
    if forbidden in s:
        raise SystemExit('v3.19.5: old tutorial gate remained: '+forbidden)

tree=ast.parse(s)
app=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
if app is None: raise SystemExit('v3.19.5: ModernConfigApp missing after patch')
methods={n.name for n in app.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
required={'aplicar_idioma','aplicar_fonte_widgets','_maybe_show_first_run_language','_tutorial_steps','abrir_tutorial','_tutorial_render_step','_tutorial_move','_tutorial_skip_click','_tutorial_place_spotlight'}
missing=sorted(required-methods)
if missing: raise SystemExit('v3.19.5: missing methods: '+', '.join(missing))

path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.19.5 readable-type + premium-onboarding + clean-tutorial patch')
