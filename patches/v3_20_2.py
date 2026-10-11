from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def line_offsets(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line)
        pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:
        raise SystemExit('v3.20.2: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_block):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.20.2: method missing: {name}')
    _,pos=line_offsets(s)
    start=pos[node.lineno-1]
    end=pos[node.end_lineno]
    s=s[:start]+new_block.rstrip()+"\n\n"+s[end:]


def rename_method(name,new_name):
    global s
    tree,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.20.2: method missing for rename: {name}')
    _,pos=line_offsets(s)
    start=pos[node.lineno-1]
    end=pos[node.end_lineno]
    chunk=s[start:end]
    chunk,n=re.subn(r'^(\s*)def\s+'+re.escape(name)+r'\s*\(',r'\1def '+new_name+'(',chunk,count=1,flags=re.M)
    if n!=1:
        raise SystemExit(f'v3.20.2: could not rename {name}')
    s=s[:start]+chunk+s[end:]


if 'APP_VERSION = "3.20.1"' not in s:
    raise SystemExit('v3.20.2: expected v3.20.1 base')
s=s.replace('APP_VERSION = "3.20.1"','APP_VERSION = "3.20.2"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Roblox Link + Guided Setup Choice"',s,count=1)
if n!=1:
    raise SystemExit('v3.20.2: timestamp missing')

# -----------------------------------------------------------------------------
# FIRST-RUN ROBLOX LINKING
# Language -> Roblox username/profile -> tutorial.
# -----------------------------------------------------------------------------
onboarding=r'''    def _abrir_onboarding_username(self, primeiro_acesso=True):
        t=TEMAS[self.tema_atual]
        L=self._L

        old=getattr(self,"_tutorial_panel",None)
        try:
            if old is not None:
                old.destroy()
        except Exception:pass

        cover=ctk.CTkFrame(self.main_container,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.42),corner_radius=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1); cover.lift()
        panel=ctk.CTkFrame(cover,width=620,height=470,fg_color=t.get("panel",t["card"]),corner_radius=20,border_width=1,border_color=t["accent"])
        panel.place(relx=.5,rely=.5,anchor="center"); panel.pack_propagate(False)
        self._tutorial_panel=cover

        ctk.CTkLabel(panel,text="ZK  //  ROBLOX LINK",height=28,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=24,pady=(24,10))
        ctk.CTkLabel(panel,text=L("Vincule seu Roblox","Link your Roblox","Vincula tu Roblox","绑定你的 Roblox","Liez votre Roblox"),font=ctk.CTkFont(size=25,weight="bold"),text_color=t["text"],anchor="w").pack(fill="x",padx=24)
        desc=L(
            "Digite seu username do Roblox. O ZKStrap consulta apenas o perfil público, salva o nick neste PC e usa ele no tutorial. Nunca pedimos senha, e-mail ou cookie.",
            "Enter your Roblox username. ZKStrap only checks the public profile, saves the nickname on this PC and uses it in the tutorial. We never ask for a password, email or cookie.",
            "Escribe tu usuario de Roblox. ZKStrap solo consulta el perfil público, guarda el nick en este PC y lo usa en el tutorial. Nunca pedimos contraseña, correo ni cookie.",
            "输入你的 Roblox 用户名。ZKStrap 只查询公开资料，将昵称保存在本机并用于教程。我们不会索要密码、邮箱或 Cookie。",
            "Entrez votre nom d’utilisateur Roblox. ZKStrap consulte uniquement le profil public, enregistre le pseudo sur ce PC et l’utilise dans le tutoriel. Aucun mot de passe, e-mail ou cookie n’est demandé."
        )
        ctk.CTkLabel(panel,text=desc,wraplength=565,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(fill="x",padx=24,pady=(8,16))

        entry=ctk.CTkEntry(panel,placeholder_text=L("ex: Builderman","e.g. Builderman","ej: Builderman","例如: Builderman","ex : Builderman"),height=48,border_width=2,border_color=t["card_active"],font=ctk.CTkFont(size=13,weight="bold"))
        entry.pack(fill="x",padx=24)
        old_nick=str((getattr(self,"linked_profile",{}) or {}).get("name") or getattr(self,"onboarding_username","") or "").strip().lstrip("@")
        if old_nick:entry.insert(0,old_nick)
        status=ctk.CTkLabel(panel,text=L("Digite seu username para continuar.","Enter your username to continue.","Escribe tu usuario para continuar.","输入用户名以继续。","Entrez votre pseudo pour continuer."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w")
        status.pack(fill="x",padx=24,pady=(7,8))

        def begin_tutorial():
            try:cover.destroy()
            except Exception:pass
            self._tutorial_panel=None
            self._abrir_tutorial_passos(replay=not primeiro_acesso)

        def link_result(profile,error=""):
            self._onboarding_profile_busy=False
            try:
                if error:
                    status.configure(text=error,text_color="#FF6B7A")
                    btn.configure(state="normal",text=L("VINCULAR E CONTINUAR","LINK & CONTINUE","VINCULAR Y CONTINUAR","绑定并继续","LIER ET CONTINUER"))
                    fallback.configure(state="normal")
                    return
                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":""}
                self.onboarding_username=str(self.linked_profile.get("name") or "")
                self.salvar_config_app()
                try:self._render_profile_button()
                except Exception:pass
                try:self._refresh_home_profile_card()
                except Exception:pass
                status.configure(text=L(
                    f"Perfil encontrado: {self.linked_profile.get('displayName')}  •  @{self.linked_profile.get('name')}",
                    f"Profile found: {self.linked_profile.get('displayName')}  •  @{self.linked_profile.get('name')}",
                    f"Perfil encontrado: {self.linked_profile.get('displayName')}  •  @{self.linked_profile.get('name')}",
                    f"已找到资料：{self.linked_profile.get('displayName')}  •  @{self.linked_profile.get('name')}",
                    f"Profil trouvé : {self.linked_profile.get('displayName')}  •  @{self.linked_profile.get('name')}"
                ),text_color=t["accent"])
                btn.configure(text=L("VINCULADO ✓","LINKED ✓","VINCULADO ✓","已绑定 ✓","LIÉ ✓"),state="disabled")
                fallback.configure(state="disabled")
                self.after(650,begin_tutorial)
            except Exception as exc:
                status.configure(text=str(exc),text_color="#FF6B7A")
                btn.configure(state="normal")
                fallback.configure(state="normal")

        def link_worker(username):
            profile=None
            err=""
            try:
                headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":f"ZKStrap/{APP_VERSION} (first-run profile linker)"}
                r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[username],"excludeBannedUsers":False},headers=headers,timeout=(4,10))
                if r.ok:
                    data=(r.json() or {}).get("data",[])
                    if data:
                        p=data[0]
                        profile={"id":int(p.get("id",0)),"name":p.get("name") or username,"displayName":p.get("displayName") or p.get("name") or username}
                if profile is None:
                    sr=requests.get("https://users.roblox.com/v1/users/search",params={"keyword":username,"limit":10},headers=headers,timeout=(4,10))
                    if sr.ok:
                        candidates=(sr.json() or {}).get("data",[])
                        p=next((x for x in candidates if str(x.get("name","")).lower()==username.lower()),None)
                        if p:
                            profile={"id":int(p.get("id",0)),"name":p.get("name") or username,"displayName":p.get("displayName") or p.get("name") or username}
                if profile is None:
                    err=L("Não achei esse username no Roblox. Confira se digitou exatamente o @username.","I couldn't find that Roblox username. Check the exact @username.","No encontré ese usuario de Roblox. Revisa el @username exacto.","没有找到该 Roblox 用户名，请检查准确的 @username。","Nom d’utilisateur Roblox introuvable. Vérifiez le @username exact.")
            except Exception:
                err=L("Não consegui consultar o Roblox agora. Você pode tentar novamente ou continuar só com o nick.","Roblox lookup is unavailable right now. Try again or continue with the nickname only.","No pude consultar Roblox ahora. Intenta otra vez o continúa solo con el nick.","暂时无法查询 Roblox。你可以重试或仅使用昵称继续。","Impossible de consulter Roblox pour le moment. Réessayez ou continuez uniquement avec le pseudo.")
            self.after(0,lambda p=profile,e=err:link_result(p,e))

        def start_link(event=None):
            username=entry.get().strip().lstrip("@")
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):
                status.configure(text=L("Use um username válido do Roblox (3–20 caracteres).","Use a valid Roblox username (3–20 characters).","Usa un usuario válido de Roblox (3–20 caracteres).","请输入有效的 Roblox 用户名（3–20 个字符）。","Utilisez un pseudo Roblox valide (3–20 caractères)."),text_color="#FF6B7A")
                return
            if bool(getattr(self,"_onboarding_profile_busy",False)):return
            self._onboarding_profile_busy=True
            status.configure(text=L("Buscando perfil público...","Looking up public profile...","Buscando perfil público...","正在查询公开资料...","Recherche du profil public..."),text_color=t["accent"])
            btn.configure(state="disabled",text=L("BUSCANDO...","SEARCHING...","BUSCANDO...","查询中...","RECHERCHE..."))
            fallback.configure(state="disabled")
            threading.Thread(target=link_worker,args=(username,),daemon=True,name="ZKFirstRunRobloxLink").start()

        def continue_nick_only():
            username=entry.get().strip().lstrip("@")
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):
                status.configure(text=L("Digite um username válido primeiro.","Enter a valid username first.","Escribe primero un usuario válido.","请先输入有效用户名。","Entrez d’abord un pseudo valide."),text_color="#FF6B7A")
                return
            self.onboarding_username=username
            self.salvar_config_app()
            begin_tutorial()

        btn=ctk.CTkButton(panel,text=L("VINCULAR E CONTINUAR","LINK & CONTINUE","VINCULAR Y CONTINUAR","绑定并继续","LIER ET CONTINUER"),command=start_link,height=46,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=11,weight="bold"))
        btn.pack(fill="x",padx=24,pady=(8,7))
        fallback=ctk.CTkButton(panel,text=L("CONTINUAR SÓ COM O NICK","CONTINUE WITH NICKNAME ONLY","CONTINUAR SOLO CON EL NICK","仅使用昵称继续","CONTINUER AVEC LE PSEUDO"),command=continue_nick_only,height=34,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"))
        fallback.pack(fill="x",padx=24,pady=(0,18))
        entry.bind("<Return>",start_link)
        self.after(90,lambda:entry.focus_force())
'''
replace_app_method('_abrir_onboarding_username',onboarding)

# -----------------------------------------------------------------------------
# POST-TUTORIAL SETUP CHOICE
# Preserve the current tutorial close implementation and wrap it.
# -----------------------------------------------------------------------------
rename_method('_tutorial_close','_tutorial_close_base_3202')

setup_methods=r'''    def _tutorial_close(self, mark_complete=False, voltar_home=True):
        first_run_finish=bool(mark_complete and not bool(getattr(self,"_tutorial_replay",False)) and not bool(self.config_data.get("first_run_setup_completed",False)))
        if first_run_finish:
            self._first_run_setup_pending=True
        self._tutorial_close_base_3202(mark_complete=mark_complete,voltar_home=voltar_home)
        if first_run_finish:
            self.after(280,self._show_first_run_setup_choice)

    def _show_first_run_setup_choice(self):
        if bool(self.config_data.get("first_run_setup_completed",False)):
            self._first_run_setup_pending=False
            return
        old=getattr(self,"_first_run_setup_panel",None)
        try:
            if old is not None and old.winfo_exists():old.lift();return
        except Exception:pass
        t=TEMAS[self.tema_atual]; L=self._L; nick=self._tutorial_username()
        cover=ctk.CTkFrame(self.main_container,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.78),corner_radius=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift();self._first_run_setup_panel=cover

        panel=ctk.CTkFrame(cover,width=900,height=550,fg_color=t.get("panel",t["card"]),corner_radius=22,border_width=1,border_color=t["accent"])
        panel.place(relx=.5,rely=.5,anchor="center");panel.pack_propagate(False)
        ctk.CTkLabel(panel,text="ZK // READY SETUP",height=28,corner_radius=8,fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=26,pady=(24,8))
        ctk.CTkLabel(panel,text=L(f"Qual setup você quer, @{nick}?",f"Which setup do you want, @{nick}?",f"¿Qué setup quieres, @{nick}?",f"@{nick}，你想使用哪个预设？",f"Quel setup voulez-vous, @{nick} ?"),text_color=t["text"],font=ctk.CTkFont(size=25,weight="bold"),anchor="w").pack(fill="x",padx=26)
        ctk.CTkLabel(panel,text=L("Você pode trocar tudo depois. Isso só deixa o ZKStrap pronto para começar com uma base coerente.","You can change everything later. This only gives ZKStrap a sensible starting configuration.","Puedes cambiar todo después. Esto solo deja ZKStrap listo con una base coherente.","之后随时可以更改。这里仅用于给 ZKStrap 一个合理的初始配置。","Vous pourrez tout modifier ensuite. Cela donne simplement à ZKStrap une base cohérente."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10),anchor="w").pack(fill="x",padx=26,pady=(5,18))

        cards=ctk.CTkFrame(panel,fg_color="transparent");cards.pack(fill="both",expand=True,padx=22,pady=(0,14));cards.grid_columnconfigure((0,1),weight=1,uniform="setup")

        def make_card(col,title,tag,description,details,kind,accent=False):
            card=ctk.CTkFrame(cards,fg_color=t["card"],corner_radius=17,border_width=2 if accent else 1,border_color=t["accent"] if accent else t.get("border",t["card_active"]))
            card.grid(row=0,column=col,sticky="nsew",padx=6,pady=4)
            ctk.CTkLabel(card,text=tag,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x",padx=18,pady=(18,5))
            ctk.CTkLabel(card,text=title,text_color=t["text"],font=ctk.CTkFont(size=21,weight="bold"),anchor="w").pack(fill="x",padx=18)
            ctk.CTkLabel(card,text=description,wraplength=360,justify="left",anchor="nw",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(fill="x",padx=18,pady=(9,10))
            ctk.CTkLabel(card,text=details,wraplength=360,justify="left",anchor="nw",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8)).pack(fill="x",padx=18,pady=(2,14))
            ctk.CTkButton(card,text=L("USAR ESTE SETUP","USE THIS SETUP","USAR ESTE SETUP","使用此预设","UTILISER CE SETUP"),command=lambda:self._apply_first_run_setup_choice(kind),height=44,fg_color=t["accent"] if accent else t["card_active"],hover_color=t["hover"],text_color="#050505" if accent else t["text"],font=ctk.CTkFont(weight="bold")).pack(fill="x",padx=18,pady=(4,18),side="bottom")

        make_card(0,"FPS MÁXIMO","COMPETITIVE // MAX FPS",L("Prioriza desempenho acima do visual. Usa textura mínima, MSAA 0, qualidade 3D mínima, grama/LOD reduzidos e alvo de 240 FPS. Bom para PvP e PCs que conseguem aproveitar FPS alto.","Prioritizes performance over visuals. Uses minimum textures, MSAA 0, minimum 3D quality, reduced grass/LOD and a 240 FPS target. Best for competitive play and systems that can benefit from high FPS.","Prioriza rendimiento sobre calidad visual. Texturas mínimas, MSAA 0, calidad 3D mínima, césped/LOD reducidos y objetivo de 240 FPS.","优先性能而非画质：最低纹理、MSAA 0、最低 3D 质量、降低草地/LOD，并以 240 FPS 为目标。","Privilégie les performances au visuel : textures minimales, MSAA 0, qualité 3D minimale, herbe/LOD réduits et cible 240 FPS."),L("Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 240 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 240 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 240 FPS","性能增强 • 灰色天空 • FPS 解锁 • Micro Opt • 240 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 240 FPS"),"fps_max",True)
        make_card(1,"PC FRACO","STABLE // LOW LOAD",L("Reduz efeitos e consumo buscando estabilidade. Mantém textura e 3D um pouco acima do mínimo absoluto, usa MSAA 0, grama baixa e alvo de 60 FPS. Melhor para hardware fraco ou quando você quer consistência.","Reduces effects and load for stability. Keeps texture and 3D quality slightly above the absolute minimum, uses MSAA 0, low grass and a 60 FPS target. Better for weaker hardware or consistent frame pacing.","Reduce efectos y consumo buscando estabilidad. Mantiene textura/3D un poco por encima del mínimo, MSAA 0, césped bajo y objetivo de 60 FPS.","降低特效和负载以追求稳定。纹理和 3D 质量略高于绝对最低值，MSAA 0、低草地，并以 60 FPS 为目标。","Réduit les effets et la charge pour favoriser la stabilité. Texture/3D légèrement au-dessus du minimum, MSAA 0, herbe basse et cible 60 FPS."),L("Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 60 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 60 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 60 FPS","性能增强 • 灰色天空 • FPS 解锁 • Micro Opt • 60 FPS","Performance Boost • Gray Sky • FPS Unlock • Micro Opt • 60 FPS"),"weak_pc",False)
        ctk.CTkLabel(panel,text=L("Depois você pode trocar, editar ou criar outros setups pela aba SETUPS.","You can later switch, edit or create other setups from the SETUPS page.","Después puedes cambiar, editar o crear otros setups en la página SETUPS.","之后可以在 SETUPS 页面切换、编辑或创建其他预设。","Vous pourrez ensuite changer, modifier ou créer d’autres setups dans la page SETUPS."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(pady=(0,18))

    def _apply_first_run_setup_choice(self,kind):
        t=TEMAS[self.tema_atual];L=self._L
        try:
            current=self._capture_setup();self.last_setup_snapshot=current
            data=dict(current);data["modules"]=dict(current.get("modules",{}));data["advanced_values"]=dict(current.get("advanced_values",{}))
            if kind=="fps_max":
                data["modules"].update({"performance_boost":True,"gray_sky":True,"fps_unlock":True,"micro_opt":True})
                data["advanced_values"].update({"texture":"0","msaa":"0","frm":"1","grass":"0","lod":"0"});data["micro_fps_target"]="240"
                chosen="FPS MÁXIMO"
            else:
                data["modules"].update({"performance_boost":True,"gray_sky":True,"fps_unlock":True,"micro_opt":True})
                data["advanced_values"].update({"texture":"1","msaa":"0","frm":"2","grass":"0","lod":"1"});data["micro_fps_target"]="60"
                chosen="PC FRACO"
            self._apply_setup_data(data)
            self.aplicar_configuracoes()
            self.config_data["first_run_setup_completed"]=True
            self.config_data["first_run_setup_choice"]=kind
            self.salvar_config_app()
            panel=getattr(self,"_first_run_setup_panel",None)
            try:
                if panel is not None:panel.destroy()
            except Exception:pass
            self._first_run_setup_panel=None;self._first_run_setup_pending=False
            self.show_toast(L("SETUP INICIAL PRONTO","STARTER SETUP READY","SETUP INICIAL LISTO","初始预设已就绪","SETUP INITIAL PRÊT"),chosen,kind="success",duration=3600)
            if not bool(getattr(self,"sound_prompted",False)):
                self.after(520,self._maybe_show_sound_consent)
        except Exception as exc:
            try:self.show_toast("SETUP",L("Não consegui aplicar esse setup. Tente novamente.","Couldn't apply that setup. Try again.","No pude aplicar ese setup. Inténtalo otra vez.","无法应用该预设，请重试。","Impossible d’appliquer ce setup. Réessayez."),kind="error",duration=4200)
            except Exception:pass
            try:self.log_output(f"[-] First-run setup apply failed: {exc}")
            except Exception:pass
'''
# Insert wrapper/new methods at end of class, just before next top-level declaration.
tree,cls=app_class(s)
_,pos=line_offsets(s)
insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+setup_methods.rstrip()+"\n"+s[insert_at:]

# -----------------------------------------------------------------------------
# SOUND CONSENT: do not interrupt language -> Roblox -> tutorial -> setup.
# -----------------------------------------------------------------------------
rename_method('_maybe_show_sound_consent','_maybe_show_sound_consent_base_3202')
sound_wrapper=r'''    def _maybe_show_sound_consent(self):
        if not bool(getattr(self,"language_selected",False)):
            try:self.after(400,self._maybe_show_sound_consent)
            except Exception:pass
            return
        if not bool(getattr(self,"tutorial_completed",False)) or bool(getattr(self,"_first_run_setup_pending",False)):
            try:self.after(500,self._maybe_show_sound_consent)
            except Exception:pass
            return
        panel=getattr(self,"_first_run_setup_panel",None)
        try:
            if panel is not None and panel.winfo_exists():
                self.after(500,self._maybe_show_sound_consent);return
        except Exception:pass
        return self._maybe_show_sound_consent_base_3202()
'''
tree,cls=app_class(s);_,pos=line_offsets(s);insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+sound_wrapper.rstrip()+"\n"+s[insert_at:]

# Structural validation.
for needle in (
    'APP_VERSION = "3.20.2"',
    'def _abrir_onboarding_username(self, primeiro_acesso=True):',
    'ZKFirstRunRobloxLink',
    'def _show_first_run_setup_choice(self):',
    'FPS MÁXIMO',
    'PC FRACO',
    'first_run_setup_completed',
    'def _tutorial_close_base_3202(',
    'def _maybe_show_sound_consent_base_3202(',
    'def _maybe_show_sound_consent(self):',
):
    if needle not in s:
        raise SystemExit('v3.20.2: missing '+needle)
if s.count('def _tutorial_close(self,')!=1:
    raise SystemExit('v3.20.2: tutorial close wrapper count invalid')
if s.count('def _maybe_show_sound_consent(self):')!=1:
    raise SystemExit('v3.20.2: sound consent wrapper count invalid')
if 'RedrawWindow(' in s:
    raise SystemExit('v3.20.2: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.2 Roblox-link onboarding + setup chooser patch')
