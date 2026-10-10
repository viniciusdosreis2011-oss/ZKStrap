from pathlib import Path
import os, re, ast

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'v3.19.4 fixed: missing {label}')
    s=s.replace(old,new,1)


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
    if cls is None: raise SystemExit('ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_method):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'v3.19.4 fixed: method missing: {name}')
    _,pos=offsets(s)
    start=pos[node.lineno-1]; end=pos[node.end_lineno]
    s=s[:start]+new_method.rstrip()+"\n\n"+s[end:]


def replace_nav_block(new_block):
    global s
    tree,cls=app_class(s)
    found=None
    for fn in cls.body:
        if not isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
        nav_node=None; sections=None
        for node in fn.body:
            if isinstance(node,ast.Assign):
                names=[t.id for t in node.targets if isinstance(t,ast.Name)]
                if 'nav' in names: nav_node=node
                if 'section_breaks' in names: sections=node
            if nav_node is not None and sections is not None:
                found=(nav_node,sections);break
        if found:break
    if not found: raise SystemExit('v3.19.4 fixed: nav block missing')
    nav_node,sections=found
    _,pos=offsets(s)
    start=pos[nav_node.lineno-1]; end=pos[sections.end_lineno]
    s=s[:start]+new_block.rstrip()+"\n"+s[end:]


# --- version ---------------------------------------------------------------
replace_once('APP_VERSION = "3.19.3"','APP_VERSION = "3.19.4"','version')
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Smooth Scroll + Persistent Language + Guided Tutorial"',s,count=1)
if n!=1: raise SystemExit('v3.19.4 fixed: timestamp missing')

# --- persist first-run language state -------------------------------------
lang='                "language": getattr(self, "idioma", "pt"),\n'
if lang not in s: raise SystemExit('v3.19.4 fixed: language config field missing')
if '"language_selected": bool(getattr(self, "language_selected", False))' not in s:
    s=s.replace(lang,lang+'                "language_selected": bool(getattr(self, "language_selected", False)),\n                "language_picker_revision": int(getattr(self, "config_data", {}).get("language_picker_revision", 0) or 0),\n',1)
old='            os.replace(tmp, self.config_path)\n'
if old not in s: raise SystemExit('v3.19.4 fixed: config replace missing')
if '            self.config_data = dict(dados)\n' not in s:
    s=s.replace(old,old+'            self.config_data = dict(dados)\n',1)

language_method='''    def aplicar_idioma(self, escolha):
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
        try:self.config_data["language_picker_revision"]=2
        except Exception:pass
        self.salvar_config_app()
        names={"pt":"Português","en":"English","es":"Español","zh":"中文","fr":"Français"}
        self.log_output(f"[*] Idioma alterado para: {names.get(code,code)}")
        self.after(10,self.reconstruir_interface)
'''
replace_app_method('aplicar_idioma',language_method)

old_menu='        self.lang_menu = ctk.CTkOptionMenu(prefs, values=["Português","English"], command=self.aplicar_idioma, fg_color=t["card_active"], button_color=t["card_active"], text_color=t["accent"]); self.lang_menu.set("Português" if pt else "English"); self.lang_menu.pack(side="left", expand=True, fill="x", padx=(5,0))\n'
new_menu='        self.lang_menu = ctk.CTkOptionMenu(prefs, values=["Português","English","Español","中文","Français"], command=self.aplicar_idioma, fg_color=t["card_active"], button_color=t["card_active"], text_color=t["accent"]); self.lang_menu.set({"pt":"Português","en":"English","es":"Español","zh":"中文","fr":"Français"}.get(self.idioma,"English")); self.lang_menu.pack(side="left", expand=True, fill="x", padx=(5,0))\n'
replace_once(old_menu,new_menu,'Personalizar language menu')
s=s.replace('                self.lang_menu.set("Português" if self.idioma == "pt" else "English")\n','                self.lang_menu.set({"pt":"Português","en":"English","es":"Español","zh":"中文","fr":"Français"}.get(self.idioma,"English"))\n',1)

# --- sidebar regroup / no hub ---------------------------------------------
nav='''        nav=[
            ("home",self._L("INÍCIO","HOME","INICIO","主页","ACCUEIL")),
            ("fps",self._L("FPS & GRÁFICOS","FPS & GRAPHICS","FPS & GRÁFICOS","FPS 与画质","FPS & GRAPHISMES")),
            ("ping",self._L("PING & LATÊNCIA","PING & LATENCY","PING & LATENCIA","PING 与网络","PING & LATENCE")),
            ("cursor","CURSOR"),
            ("fonts",self._L("FONTES","FONTS","FUENTES","字体","POLICES")),
            ("theme",self._L("PERSONALIZAR","CUSTOMIZE","PERSONALIZAR","个性化","PERSONNALISER")),
            ("audio",self._L("ÁUDIO","AUDIO","AUDIO","音频","AUDIO")),
            ("spotify","SPOTIFY"),
            ("combo","COMBO PLANNER"),
            ("roulette","BUILD ROULETTE"),
            ("creator",self._L("CREATOR MODE","CREATOR MODE","MODO CREADOR","创作者模式","MODE CRÉATEUR")),
            ("ai","ZK ASSIST"),
            ("setups","SETUPS"),
            ("maintenance",self._L("DESEMPENHO","PERFORMANCE","RENDIMIENTO","性能","PERFORMANCES")),
            ("recovery",self._L("RECUPERAÇÃO","RECOVERY","RECUPERACIÓN","恢复","RÉCUPÉRATION")),
            ("updates",self._L("ATUALIZAÇÕES","UPDATES","ACTUALIZACIONES","更新","MISES À JOUR")),
            ("feedback",self._L("SUGESTÕES & BUGS","FEEDBACK & BUGS","SUGERENCIAS & BUGS","建议与错误","SUGGESTIONS & BUGS")),
            ("support",self._L("APOIAR","SUPPORT","APOYAR","支持","SOUTENIR")),
            ("about",self._L("SOBRE","ABOUT","ACERCA DE","关于","À PROPOS")),
        ]
        self._nav_label_map=dict(nav)
        section_breaks={
            0:self._L("GERAL","GENERAL","GENERAL","常用","GÉNÉRAL"),
            3:self._L("VISUAL","VISUAL","VISUAL","视觉","VISUEL"),
            7:self._L("MÍDIA","MEDIA","MEDIA","媒体","MÉDIA"),
            8:"BLOX FRUITS",
            12:self._L("FERRAMENTAS","TOOLS","HERRAMIENTAS","工具","OUTILS"),
            15:self._L("SISTEMA","SYSTEM","SISTEMA","系统","SYSTÈME"),
            17:"INFO",
        }'''
replace_nav_block(nav)

# --- smooth scroll: native Canvas target following, no Win32 redraw --------
queue='''    def _queue_scroll_step(self, scrollable, step):
        """Smooth target-following Canvas scroll without Win32 repaint churn."""
        try:
            if scrollable is None or not step:return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():return "break"
            now=time.monotonic()
            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            if max_first<=0.0:return "break"
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"target":first,"job":None,"last_input":0.0}
                setattr(scrollable,"_zk_scroll_state",state)
            if now-float(state.get("last_input",0.0) or 0.0)>.20:
                state["target"]=first
            target=float(state.get("target",first) or first)+(float(step)*64.0/max(1.0,total))
            state["target"]=max(0.0,min(max_first,target)); state["last_input"]=now
            self._mark_fast_scroll()
            def tick():
                state["job"]=None
                try:
                    if not canvas.winfo_exists():return
                    cur,vis,_=self._scroll_canvas_metrics(canvas)
                    limit=max(0.0,1.0-vis); dest=max(0.0,min(limit,float(state.get("target",cur))))
                    diff=dest-cur
                    if abs(diff)<0.00030:
                        canvas.yview_moveto(dest)
                        try:scrollable._zk_repaint_viewport(True)
                        except Exception:pass
                        return
                    d=abs(diff); alpha=.27 if d<.035 else (.38 if d<.12 else .50)
                    canvas.yview_moveto(max(0.0,min(limit,cur+diff*alpha)))
                    state["job"]=self.after(14,tick)
                except Exception:state["job"]=None
            if state.get("job") is None:
                try:state["job"]=self.after(1,tick)
                except Exception:tick()
            return "break"
        except Exception:return "break"
'''
replace_app_method('_queue_scroll_step',queue)

# --- guided tutorial -------------------------------------------------------
render='''    def _tutorial_render_step(self):
        steps=self._tutorial_steps(); idx=max(0,min(self._tutorial_step_index,len(steps)-1)); self._tutorial_step_index=idx
        step=steps[idx]; page,title,body,tip=step[:4]; mission=step[4] if len(step)>4 else ""
        self._tutorial_step_ready=False
        try:self.show_page(page,animate=True)
        except Exception:pass
        self._tutorial_title.configure(text=title); self._tutorial_body.configure(text=body); self._tutorial_tip.configure(text=tip)
        try:self._tutorial_mission.configure(text=mission)
        except Exception:pass
        self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
        self._tutorial_progress.set((idx+1)/max(1,len(steps)))
        self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
        label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("PRÓXIMO  →","NEXT  →","SIGUIENTE  →","下一步  →","SUIVANT  →")
        self._tutorial_next.configure(state="disabled",text=label)
        try:self._tutorial_explore.configure(text=self._L("DESTACAR","HIGHLIGHT","DESTACAR","高亮","SURLIGNER"),fg_color=TEMAS[self.tema_atual]["card_active"],text_color=TEMAS[self.tema_atual]["accent"])
        except Exception:pass
        self.after(210,lambda:self._tutorial_place_spotlight(self._tutorial_target_widget(page)))
'''
replace_app_method('_tutorial_render_step',render)

explore='''    def _tutorial_explore_current(self):
        try:
            steps=self._tutorial_steps(); page=steps[self._tutorial_step_index][0]
            self.show_page(page,animate=True); self._tutorial_step_ready=True
            self._tutorial_explore.configure(text=self._L("✓  TESTADO","✓  TRIED","✓  PROBADO","✓  已查看","✓  TESTÉ"),fg_color=TEMAS[self.tema_atual]["accent"],text_color="#050505")
            self._tutorial_next.configure(state="normal")
            self.after(120,lambda:self._tutorial_place_spotlight(self._tutorial_target_widget(page)))
            self.after(360,lambda:self._tutorial_place_spotlight(self._tutorial_target_widget(page)))
        except Exception:pass
'''
replace_app_method('_tutorial_explore_current',explore)

skip='''    def _tutorial_skip_click(self):
        now=time.monotonic(); armed=float(getattr(self,"_tutorial_skip_armed_until",0.0) or 0.0)
        if now<armed:
            self._tutorial_close(mark_complete=False)
            try:self.show_toast(self._L("TUTORIAL ADIADO","TUTORIAL POSTPONED","TUTORIAL POSPUESTO","教程已暂缓","TUTORIEL REPORTÉ"),self._L("Ele volta no próximo início até você concluir todas as etapas.","It returns next launch until every step is completed.","Volverá al próximo inicio hasta completar todas las etapas.","下次启动时会再次出现，直到完成全部步骤。","Il reviendra au prochain lancement jusqu’à sa conclusion."),kind="info")
            except Exception:pass
            return
        self._tutorial_skip_armed_until=now+3.0
        try:self._tutorial_skip.configure(text=self._L("CLIQUE DE NOVO","CLICK AGAIN","CLIC OTRA VEZ","再次点击","CLIQUEZ ENCORE"),text_color="#FF8A8A",border_color="#FF6B6B")
        except Exception:pass
        def reset():
            if time.monotonic()>=float(getattr(self,"_tutorial_skip_armed_until",0.0) or 0.0):
                try:self._tutorial_skip.configure(text=self._L("SAIR","EXIT","SALIR","退出","QUITTER"),text_color=TEMAS[self.tema_atual].get("muted","gray"),border_color=TEMAS[self.tema_atual]["card_active"])
                except Exception:pass
        try:self.after(3100,reset)
        except Exception:pass
'''
replace_app_method('_tutorial_skip_click',skip)

move='''    def _tutorial_move(self, delta):
        if int(delta)>0 and not bool(getattr(self,"_tutorial_step_ready",False)):
            try:self._tutorial_explore.configure(text=self._L("TESTE PRIMEIRO ↑","TRY IT FIRST ↑","PRUÉBALO PRIMERO ↑","请先查看 ↑","TESTEZ D’ABORD ↑")); self._play_ui_sound("warning",0)
            except Exception:pass
            return
        steps=self._tutorial_steps(); nxt=self._tutorial_step_index+int(delta)
        if nxt>=len(steps):self._tutorial_close(mark_complete=True); return
        self._tutorial_step_index=max(0,nxt); self._tutorial_render_step()
'''
replace_app_method('_tutorial_move',move)

# --- validation ------------------------------------------------------------
for mark in ('APP_VERSION = "3.19.4"','"language_selected": bool(getattr(self, "language_selected", False))','("ai","ZK ASSIST")','Smooth target-following Canvas scroll without Win32 repaint churn.','self._tutorial_step_ready=True'):
    if mark not in s:raise SystemExit('v3.19.4 fixed: marker missing: '+mark)
if '("bloxhub","BLOX HUB")' in s:raise SystemExit('v3.19.4 fixed: Blox Hub in nav')
if 'RedrawWindow(' in s:raise SystemExit('v3.19.4 fixed: Win32 RedrawWindow present')
if 'ctk.CTkScrollableFrame(' in s:raise SystemExit('v3.19.4 fixed: legacy CTkScrollableFrame present')
if 'discord.com/api/webhooks/' in s or 'discordapp.com/api/webhooks/' in s:raise SystemExit('v3.19.4 fixed: webhook embedded')
final=ast.parse(s)
cls=next(n for n in final.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
methods={n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
need={'aplicar_idioma','_maybe_show_first_run_language','_language_flag_image','_refresh_cursor_preview','_refresh_font_preview','_tutorial_render_step','_tutorial_explore_current','_tutorial_skip_click','_tutorial_move','_queue_scroll_step','_open_support_page','_copy_support_link'}
missing=sorted(need-methods)
if missing:raise SystemExit('v3.19.4 fixed: missing methods: '+', '.join(missing))
path.write_text(s,encoding='utf-8')
print('Applied robust AST-based ZKStrap v3.19.4 patch')
