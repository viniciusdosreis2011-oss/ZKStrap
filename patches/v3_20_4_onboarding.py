from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')

def line_offsets(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos

def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.20.4: ModernConfigApp missing')
    return tree,cls

def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.4: missing '+name)
    _,pos=line_offsets(text);return node,pos[node.lineno-1],pos[node.end_lineno]

def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name);s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]

if 'APP_VERSION = "3.20.3"' not in s:raise SystemExit('v3.20.4: expected v3.20.3')
s=s.replace('APP_VERSION = "3.20.3"','APP_VERSION = "3.20.4"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Cinematic First Run + Progressive Guide"',s,count=1)
if n!=1:raise SystemExit('v3.20.4: timestamp')

helpers=r'''    def _zk_blur_cover(self,host=None,radius=11,brightness=.48):
        host=host or self;t=TEMAS[self.tema_atual]
        try:self.update_idletasks()
        except Exception:pass
        cover=ctk.CTkFrame(host,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.18),corner_radius=0,border_width=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1)
        try:
            from PIL import ImageGrab,ImageFilter,ImageEnhance
            x=int(host.winfo_rootx());y=int(host.winfo_rooty());w=max(2,int(host.winfo_width()));h=max(2,int(host.winfo_height()))
            shot=ImageGrab.grab(bbox=(x,y,x+w,y+h)).convert("RGBA")
            shot=shot.filter(ImageFilter.GaussianBlur(radius=max(2,int(radius))))
            shot=ImageEnhance.Brightness(shot).enhance(max(.25,min(.90,float(brightness))))
            img=ctk.CTkImage(light_image=shot,dark_image=shot,size=(w,h))
            lab=ctk.CTkLabel(cover,text="",image=img,fg_color="transparent");lab.place(x=0,y=0,relwidth=1,relheight=1)
            cover._zk_blur_img=img;cover._zk_blur_label=lab
        except Exception:pass
        shade=ctk.CTkFrame(cover,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.10),corner_radius=0);shade.place(x=0,y=0,relwidth=1,relheight=1);cover._zk_shade=shade
        cover.lift();return cover

    def _tutorial_refresh_unlocks(self):
        box=getattr(self,"_tutorial_unlock_list",None)
        if box is None:return
        try:
            for ch in box.winfo_children():ch.destroy()
        except Exception:return
        t=TEMAS[self.tema_atual];steps=self._tutorial_steps();idx=int(getattr(self,"_tutorial_step_index",0) or 0)
        for i,step in enumerate(steps):
            if i>idx:break
            active=(i==idx)
            row=ctk.CTkFrame(box,height=35,corner_radius=9,fg_color=t["card_active"] if active else "transparent",border_width=1,border_color=t["accent"] if active else self._mix_hex(t.get("border",t["accent"]),t["accent"],.18));row.pack(fill="x",pady=3);row.pack_propagate(False)
            ctk.CTkLabel(row,text=f"{i+1:02d}",width=31,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left",padx=(7,2))
            ctk.CTkLabel(row,text=step[1],anchor="w",text_color=t["text"] if active else t.get("muted",t["text"]),font=ctk.CTkFont(size=9,weight="bold" if active else "normal")).pack(side="left",fill="x",expand=True,padx=(2,8))
        remaining=max(0,len(steps)-idx-1)
        if remaining:ctk.CTkLabel(box,text=self._L(f"+ {remaining} áreas bloqueadas",f"+ {remaining} locked areas",f"+ {remaining} áreas bloqueadas",f"+ {remaining} 个区域待解锁",f"+ {remaining} zones verrouillées"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(anchor="w",padx=7,pady=(8,4))

    def _tutorial_capture_preview(self,page,token):
        if token!=getattr(self,"_tutorial_preview_token",None):return
        cover=getattr(self,"_tutorial_panel",None)
        if cover is None:return
        try:
            cover.place_forget();self.show_page(page,animate=False);self.update_idletasks()
            from PIL import ImageGrab,ImageOps,Image
            host=self.main_container;x=int(host.winfo_rootx());y=int(host.winfo_rooty());w=max(2,int(host.winfo_width()));h=max(2,int(host.winfo_height()))
            shot=ImageGrab.grab(bbox=(x,y,x+w,y+h)).convert("RGBA")
            if token!=getattr(self,"_tutorial_preview_token",None):return
            shot=ImageOps.fit(shot,(780,410),method=Image.Resampling.LANCZOS)
            img=ctk.CTkImage(light_image=shot,dark_image=shot,size=(780,410));self._tutorial_preview_img=img
            lab=getattr(self,"_tutorial_preview_label",None)
            if lab is not None and lab.winfo_exists():lab.configure(image=img,text="")
        except Exception:
            try:
                lab=getattr(self,"_tutorial_preview_label",None)
                if lab is not None and lab.winfo_exists():lab.configure(image=None,text=self._L("Amostra desta aba","This tab preview","Vista previa de esta pestaña","此页面预览","Aperçu de cet onglet"))
            except Exception:pass
        finally:
            try:cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift()
            except Exception:pass
'''
_,cls=app_class(s);_,pos=line_offsets(s);insert_at=pos[cls.end_lineno];s=s[:insert_at]+"\n"+helpers.rstrip()+"\n"+s[insert_at:]

language=r'''    def _maybe_show_first_run_language(self):
        try:picker_rev=int(self.config_data.get("language_picker_revision",0) or 0)
        except Exception:picker_rev=0
        if bool(getattr(self,"language_selected",False)) and picker_rev>=5:return
        old=getattr(self,"_language_panel",None)
        try:
            if old is not None and old.winfo_exists():old.lift();return
        except Exception:pass
        if not getattr(self,"main_container",None):
            try:self.after(80,self._maybe_show_first_run_language)
            except Exception:pass
            return
        t=TEMAS[self.tema_atual];cover=self._zk_blur_cover(self,radius=13,brightness=.42);self._language_panel=cover
        panel=ctk.CTkFrame(cover,width=1080,height=610,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.62));panel.place(relx=.5,rely=.5,anchor="center");panel.pack_propagate(False)
        ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        body=ctk.CTkFrame(panel,fg_color="transparent");body.pack(fill="both",expand=True,padx=22,pady=22)
        hero=ctk.CTkFrame(body,width=350,fg_color=self._mix_hex(t["card"],t["accent"],.08),corner_radius=20,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));hero.pack(side="left",fill="y",padx=(0,18));hero.pack_propagate(False)
        logo=ctk.CTkFrame(hero,width=92,height=92,corner_radius=22,fg_color=t["card_active"],border_width=1,border_color=t["accent"]);logo.pack(anchor="w",padx=26,pady=(28,22));logo.pack_propagate(False)
        ctk.CTkLabel(logo,text="ZK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=29,weight="bold")).place(relx=.5,rely=.5,anchor="center")
        ctk.CTkLabel(hero,text="WELCOME // FIRST BOOT",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w").pack(fill="x",padx=26)
        ctk.CTkLabel(hero,text="ZKSTRAP",text_color=t["text"],font=ctk.CTkFont(size=31,weight="bold"),anchor="w").pack(fill="x",padx=26,pady=(7,4))
        ctk.CTkLabel(hero,text="3 passos rápidos e o app já fica com a sua cara.",wraplength=285,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=11)).pack(fill="x",padx=26,pady=(3,22))
        for num,label,active in (("01","IDIOMA",True),("02","ROBLOX",False),("03","GUIA + SETUP",False)):
            row=ctk.CTkFrame(hero,height=48,corner_radius=12,fg_color=t["card_active"] if active else "transparent",border_width=1,border_color=t["accent"] if active else self._mix_hex(t.get("border",t["accent"]),t["accent"],.16));row.pack(fill="x",padx=24,pady=4);row.pack_propagate(False)
            ctk.CTkLabel(row,text=num,width=45,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold")).pack(side="left",padx=(9,2));ctk.CTkLabel(row,text=label,text_color=t["text"] if active else t.get("muted","gray"),font=ctk.CTkFont(size=10,weight="bold")).pack(side="left")
        right=ctk.CTkFrame(body,fg_color="transparent");right.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(right,text="01 / 03   //   LANGUAGE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w").pack(fill="x",padx=6,pady=(5,7))
        ctk.CTkLabel(right,text="Escolha como o ZKStrap vai falar com você",text_color=t["text"],font=ctk.CTkFont(size=25,weight="bold"),anchor="w").pack(fill="x",padx=6)
        ctk.CTkLabel(right,text="A interface muda na hora. Você pode trocar novamente em Personalizar.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10),anchor="w").pack(fill="x",padx=6,pady=(5,16))
        grid=ctk.CTkFrame(right,fg_color="transparent");grid.pack(fill="both",expand=True,padx=2);grid.grid_columnconfigure((0,1),weight=1,uniform="lang")
        def choose(code):
            self.idioma=code;self.language_selected=True;self.config_data["language"]=code;self.config_data["language_selected"]=True;self.config_data["language_picker_revision"]=5
            try:self.salvar_config_app();cover.destroy()
            except Exception:pass
            self._language_panel=None
            try:self.reconstruir_interface()
            except Exception:pass
            try:self.after(120,self._first_run_after_language)
            except Exception:pass
        for i,item in enumerate(self._language_choices()):
            code,name,sub=item[0],item[-2],item[-1];img=self._language_flag_image(code,size=(58,36))
            card=ctk.CTkButton(grid,text=f"{name}\n{sub}",image=img,compound="left",anchor="w",height=92,corner_radius=16,fg_color=t["card"],hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.38),text_color=t["text"],font=ctk.CTkFont(size=13,weight="bold"),command=lambda c=code:choose(c))
            if i==4:card.grid(row=2,column=0,columnspan=2,sticky="ew",padx=5,pady=5)
            else:card.grid(row=i//2,column=i%2,sticky="ew",padx=5,pady=5)
        ctk.CTkLabel(right,text="ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(anchor="e",padx=7,pady=(10,3))
'''
replace_method('_maybe_show_first_run_language',language)

nick=r'''    def _abrir_onboarding_username(self, primeiro_acesso=True):
        t=TEMAS[self.tema_atual];L=self._L
        old=getattr(self,"_tutorial_panel",None)
        try:
            if old is not None:old.destroy()
        except Exception:pass
        cover=self._zk_blur_cover(self,radius=13,brightness=.43);self._tutorial_panel=cover
        panel=ctk.CTkFrame(cover,width=1040,height=585,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.62));panel.place(relx=.5,rely=.5,anchor="center");panel.pack_propagate(False)
        ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        body=ctk.CTkFrame(panel,fg_color="transparent");body.pack(fill="both",expand=True,padx=22,pady=22)
        left=ctk.CTkFrame(body,width=345,fg_color=self._mix_hex(t["card"],t["accent"],.07),corner_radius=20,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.28));left.pack(side="left",fill="y",padx=(0,18));left.pack_propagate(False)
        ctk.CTkLabel(left,text="02 / 03   //   ROBLOX LINK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=24,pady=(25,15))
        avatar_shell=ctk.CTkFrame(left,width=154,height=154,corner_radius=77,fg_color=t["card_active"],border_width=2,border_color=t["accent"]);avatar_shell.pack(pady=(8,14));avatar_shell.pack_propagate(False)
        avatar=ctk.CTkLabel(avatar_shell,text="@",text_color=t["accent"],font=ctk.CTkFont(size=49,weight="bold"));avatar.place(relx=.5,rely=.5,anchor="center")
        profile_name=ctk.CTkLabel(left,text=L("Seu perfil aparece aqui","Your profile appears here","Tu perfil aparece aquí","你的资料会显示在这里","Votre profil apparaît ici"),text_color=t["text"],font=ctk.CTkFont(size=15,weight="bold"));profile_name.pack(padx=20,pady=(3,4))
        profile_user=ctk.CTkLabel(left,text="@username",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=10));profile_user.pack()
        ctk.CTkLabel(left,text=L("Seu nick aparece no tutorial e deixa a primeira experiência mais pessoal.","Your nickname appears in the tutorial and personalizes first run.","Tu nick aparece en el tutorial y personaliza el inicio.","昵称会显示在教程中，让首次体验更个性化。","Votre pseudo apparaît dans le tutoriel et personnalise le premier lancement."),wraplength=280,justify="center",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(padx=24,pady=(18,8))
        secure=ctk.CTkFrame(left,fg_color=t["card_active"],corner_radius=11);secure.pack(fill="x",padx=22,pady=(10,0));ctk.CTkLabel(secure,text="✓  PUBLIC PROFILE ONLY",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(padx=10,pady=10)
        right=ctk.CTkFrame(body,fg_color="transparent");right.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(right,text=L("Agora coloca seu nick do Roblox","Now enter your Roblox username","Ahora pon tu usuario de Roblox","现在输入你的 Roblox 用户名","Entrez maintenant votre pseudo Roblox"),text_color=t["text"],font=ctk.CTkFont(size=26,weight="bold"),anchor="w").pack(fill="x",padx=7,pady=(12,4))
        ctk.CTkLabel(right,text=L("O ZKStrap consulta apenas o perfil público e salva o vínculo neste PC. Nunca pedimos senha, e-mail ou cookie.","ZKStrap only checks the public profile and stores the link on this PC. We never ask for passwords, email or cookies.","ZKStrap solo consulta el perfil público y guarda el vínculo en este PC. Nunca pedimos contraseña, correo ni cookie.","ZKStrap 只查询公开资料并在本机保存绑定，不会索要密码、邮箱或 Cookie。","ZKStrap consulte uniquement le profil public et enregistre le lien sur ce PC. Aucun mot de passe, e-mail ou cookie."),wraplength=610,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(fill="x",padx=7,pady=(2,20))
        entry=ctk.CTkEntry(right,placeholder_text="@username",height=55,corner_radius=14,border_width=2,border_color=t["card_active"],font=ctk.CTkFont(size=14,weight="bold"));entry.pack(fill="x",padx=7)
        status=ctk.CTkLabel(right,text=L("Digite seu username e pressione Enter ou Vincular.","Enter your username and press Enter or Link.","Escribe tu usuario y presiona Enter o Vincular.","输入用户名后按 Enter 或绑定。","Entrez votre pseudo puis appuyez sur Entrée ou Lier."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w");status.pack(fill="x",padx=8,pady=(8,11))
        info=ctk.CTkFrame(right,fg_color=t["card_active"],corner_radius=13);info.pack(fill="x",padx=7,pady=(2,13));ctk.CTkLabel(info,text=L("O QUE VAI SER VINCULADO","WHAT GETS LINKED","QUÉ SE VINCULA","绑定内容","CE QUI EST LIÉ"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x",padx=13,pady=(10,3));ctk.CTkLabel(info,text=L("Username • Display Name • ID público • avatar público","Username • Display Name • public ID • public avatar","Username • Display Name • ID público • avatar público","用户名 • 显示名 • 公开 ID • 公开头像","Pseudo • Display Name • ID public • avatar public"),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w").pack(fill="x",padx=13,pady=(1,10))
        def begin_tutorial():
            try:cover.destroy()
            except Exception:pass
            self._tutorial_panel=None;self.after(20,lambda:self._abrir_tutorial_passos(replay=not primeiro_acesso))
        def set_avatar(data):
            if not data:return
            try:
                import io
                from PIL import Image
                im=Image.open(io.BytesIO(data)).convert('RGBA');im.thumbnail((140,140),Image.Resampling.LANCZOS);self._onboarding_avatar_img=ctk.CTkImage(light_image=im,dark_image=im,size=(140,140));avatar.configure(image=self._onboarding_avatar_img,text='')
            except Exception:pass
        def link_result(profile,error="",avatar_bytes=None):
            self._onboarding_profile_busy=False
            if error:status.configure(text=error,text_color="#FF6B7A");btn.configure(state="normal",text=L("VINCULAR PERFIL","LINK PROFILE","VINCULAR PERFIL","绑定资料","LIER LE PROFIL"));fallback.configure(state="normal");return
            try:
                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":str(profile.get('avatar_url','') or '')};self.onboarding_username=self.linked_profile['name'];self.config_data['roblox_onboarding_completed']=True;self.salvar_config_app()
                profile_name.configure(text=self.linked_profile['displayName']);profile_user.configure(text='@'+self.linked_profile['name']);set_avatar(avatar_bytes);status.configure(text=L("Perfil encontrado. Preparando seu guia...","Profile found. Preparing your guide...","Perfil encontrado. Preparando tu guía...","资料已找到，正在准备教程...","Profil trouvé. Préparation du guide..."),text_color=t["accent"]);btn.configure(text=L("VINCULADO  ✓","LINKED  ✓","VINCULADO  ✓","已绑定  ✓","LIÉ  ✓"),state="disabled");fallback.configure(state="disabled");self.after(240,begin_tutorial)
            except Exception as exc:status.configure(text=str(exc),text_color="#FF6B7A");btn.configure(state="normal");fallback.configure(state="normal")
        def link_worker(username):
            profile=None;err="";avatar_bytes=None
            try:
                headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":f"ZKStrap/{APP_VERSION}"};r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[username],"excludeBannedUsers":False},headers=headers,timeout=(4,10))
                if r.ok:
                    data=(r.json() or {}).get('data',[])
                    if data:
                        p=data[0];profile={"id":int(p.get('id',0)),"name":p.get('name') or username,"displayName":p.get('displayName') or p.get('name') or username}
                if profile:
                    tr=requests.get("https://thumbnails.roblox.com/v1/users/avatar-headshot",params={"userIds":profile['id'],"size":"150x150","format":"Png","isCircular":"false"},timeout=(4,8))
                    if tr.ok:
                        td=(tr.json() or {}).get('data',[])
                        if td and td[0].get('imageUrl'):
                            profile['avatar_url']=td[0]['imageUrl'];ir=requests.get(profile['avatar_url'],timeout=(4,8));avatar_bytes=ir.content if ir.ok else None
                if profile is None:err=L("Não achei esse @username. Confira a escrita.","I couldn't find that @username. Check the spelling.","No encontré ese @username. Revisa la escritura.","找不到该 @username，请检查拼写。","@username introuvable. Vérifiez l’orthographe.")
            except Exception:err=L("Roblox não respondeu agora. Tente de novo ou continue só com o nick.","Roblox didn't respond. Try again or continue with nickname only.","Roblox no respondió. Intenta de nuevo o sigue solo con el nick.","Roblox 暂时没有响应，请重试或仅使用昵称继续。","Roblox ne répond pas. Réessayez ou continuez avec le pseudo.")
            self.after(0,lambda:link_result(profile,err,avatar_bytes))
        def start_link(event=None):
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Username inválido (3–20 caracteres).","Invalid username (3–20 characters).","Usuario inválido (3–20 caracteres).","用户名无效（3–20 个字符）。","Pseudo invalide (3–20 caractères)."),text_color="#FF6B7A");return
            if bool(getattr(self,'_onboarding_profile_busy',False)):return
            self._onboarding_profile_busy=True;status.configure(text=L("Procurando perfil público...","Looking up public profile...","Buscando perfil público...","正在查询公开资料...","Recherche du profil public..."),text_color=t["accent"]);btn.configure(state='disabled',text=L("PROCURANDO...","SEARCHING...","BUSCANDO...","查询中...","RECHERCHE..."));fallback.configure(state='disabled');threading.Thread(target=link_worker,args=(username,),daemon=True,name='ZKFirstRunRobloxLink').start()
        def continue_nick_only():
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Digite um username válido primeiro.","Enter a valid username first.","Escribe un usuario válido primero.","请先输入有效用户名。","Entrez d’abord un pseudo valide."),text_color="#FF6B7A");return
            self.onboarding_username=username;self.config_data['roblox_onboarding_completed']=True;self.salvar_config_app();begin_tutorial()
        btn=ctk.CTkButton(right,text=L("VINCULAR PERFIL","LINK PROFILE","VINCULAR PERFIL","绑定资料","LIER LE PROFIL"),command=start_link,height=48,corner_radius=13,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=11,weight="bold"));btn.pack(fill="x",padx=7,pady=(5,7));fallback=ctk.CTkButton(right,text=L("CONTINUAR SÓ COM O NICK","CONTINUE WITH NICKNAME ONLY","CONTINUAR SOLO CON EL NICK","仅使用昵称继续","CONTINUER AVEC LE PSEUDO"),command=continue_nick_only,height=38,corner_radius=11,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"));fallback.pack(fill="x",padx=7);entry.bind('<Return>',start_link);self.after(70,lambda:entry.focus_force())
'''
replace_method('_abrir_onboarding_username',nick)

tutorial_open=r'''    def abrir_tutorial(self, primeiro_acesso=False):
        try:self._fechar_busca_universal()
        except Exception:pass
        try:self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception:pass
        self._tutorial_first_run=bool(primeiro_acesso);self._tutorial_step_index=0;self._tutorial_replay=not primeiro_acesso;self._tutorial_step_ready=True;self._tutorial_preview_token=0
        t=TEMAS[self.tema_atual];L=self._L;cover=self._zk_blur_cover(self,radius=12,brightness=.38);self._tutorial_panel=cover
        shell=ctk.CTkFrame(cover,width=1260,height=690,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.58));shell.place(relx=.5,rely=.5,anchor='center');shell.pack_propagate(False)
        head=ctk.CTkFrame(shell,height=58,fg_color=t["card_active"],corner_radius=0);head.pack(fill='x');head.pack_propagate(False);ctk.CTkLabel(head,text="ZKSTRAP  //  GUIDED BOOT",text_color=t["accent"],font=ctk.CTkFont(family='Consolas',size=10,weight='bold')).pack(side='left',padx=20);self._tutorial_count=ctk.CTkLabel(head,text='',text_color=t.get('muted','gray'),font=ctk.CTkFont(family='Consolas',size=9,weight='bold'));self._tutorial_count.pack(side='right',padx=20)
        body=ctk.CTkFrame(shell,fg_color='transparent');body.pack(fill='both',expand=True,padx=16,pady=16)
        rail=ctk.CTkFrame(body,width=225,fg_color=self._mix_hex(t["card"],t["accent"],.05),corner_radius=16,border_width=1,border_color=self._mix_hex(t.get('border',t['accent']),t['accent'],.22));rail.pack(side='left',fill='y',padx=(0,12));rail.pack_propagate(False);ctk.CTkLabel(rail,text=L("DESBLOQUEADO","UNLOCKED","DESBLOQUEADO","已解锁","DÉVERROUILLÉ"),text_color=t['accent'],font=ctk.CTkFont(family='Consolas',size=8,weight='bold')).pack(anchor='w',padx=12,pady=(14,7));self._tutorial_unlock_list=ctk.CTkScrollableFrame(rail,fg_color='transparent',corner_radius=0);self._tutorial_unlock_list.pack(fill='both',expand=True,padx=8,pady=(0,8))
        center=ctk.CTkFrame(body,fg_color='transparent');center.pack(side='left',fill='both',expand=True);preview=ctk.CTkFrame(center,fg_color=t['card_active'],corner_radius=16,border_width=1,border_color=self._mix_hex(t.get('border',t['accent']),t['accent'],.26));preview.pack(fill='both',expand=True);phead=ctk.CTkFrame(preview,height=38,fg_color='transparent');phead.pack(fill='x',padx=13,pady=(10,2));phead.pack_propagate(False);ctk.CTkLabel(phead,text=L("AMOSTRA REAL DA ABA","LIVE TAB SAMPLE","MUESTRA REAL DE LA PESTAÑA","真实页面预览","APERÇU RÉEL DE L’ONGLET"),text_color=t['accent'],font=ctk.CTkFont(family='Consolas',size=8,weight='bold')).pack(side='left');self._tutorial_preview_label=ctk.CTkLabel(preview,text=L("Carregando amostra...","Loading sample...","Cargando muestra...","正在加载预览...","Chargement de l’aperçu..."),text_color=t.get('muted','gray'));self._tutorial_preview_label.pack(fill='both',expand=True,padx=12,pady=(0,12))
        guide=ctk.CTkFrame(center,height=185,fg_color=t['card'],corner_radius=15,border_width=1,border_color=t['accent']);guide.pack(fill='x',pady=(11,0));guide.pack_propagate(False);self._tutorial_title=ctk.CTkLabel(guide,text='',text_color=t['text'],font=ctk.CTkFont(size=19,weight='bold'),anchor='w');self._tutorial_title.pack(fill='x',padx=16,pady=(12,2));self._tutorial_body=ctk.CTkLabel(guide,text='',wraplength=870,justify='left',anchor='w',text_color=t['text'],font=ctk.CTkFont(size=10));self._tutorial_body.pack(fill='x',padx=16,pady=(1,3));self._tutorial_tip=ctk.CTkLabel(guide,text='',wraplength=870,justify='left',anchor='w',text_color=t.get('muted','gray'),font=ctk.CTkFont(size=9));self._tutorial_tip.pack(fill='x',padx=16)
        foot=ctk.CTkFrame(guide,fg_color='transparent');foot.pack(fill='x',padx=15,pady=(8,10),side='bottom');self._tutorial_prev=ctk.CTkButton(foot,text='←',command=lambda:self._tutorial_move(-1),width=48,height=33,fg_color=t['card_active'],hover_color=t['hover']);self._tutorial_prev.pack(side='left');self._tutorial_skip=ctk.CTkButton(foot,text=L("SAIR","EXIT","SALIR","退出","QUITTER"),command=self._tutorial_skip_click,width=70,height=33,fg_color='transparent',border_width=1,border_color=t['card_active']);self._tutorial_skip.pack(side='left',padx=6);self._tutorial_progress=ctk.CTkProgressBar(foot,height=5,progress_color=t['accent'],fg_color=t['card_active']);self._tutorial_progress.pack(side='left',fill='x',expand=True,padx=10);self._tutorial_next=ctk.CTkButton(foot,text='',command=lambda:self._tutorial_move(1),width=180,height=33,fg_color=t['accent'],hover_color=t['hover'],text_color='#050505',font=ctk.CTkFont(size=10,weight='bold'));self._tutorial_next.pack(side='right');self._tutorial_render_step()
'''
replace_method('abrir_tutorial',tutorial_open)

tutorial_render=r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps();idx=max(0,min(int(getattr(self,'_tutorial_step_index',0) or 0),len(steps)-1));self._tutorial_step_index=idx;page,title,body,tip=steps[idx][:4];self._tutorial_step_ready=True
        try:self._tutorial_title.configure(text=title);self._tutorial_body.configure(text=body);self._tutorial_tip.configure(text=tip);self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}");self._tutorial_progress.set((idx+1)/max(1,len(steps)));self._tutorial_prev.configure(state='disabled' if idx==0 else 'normal')
        except Exception:pass
        label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("PRÓXIMO  →","NEXT  →","SIGUIENTE  →","下一步  →","SUIVANT  →")
        try:self._tutorial_next.configure(state='normal',text=label);self._tutorial_refresh_unlocks()
        except Exception:pass
        self._tutorial_preview_token=int(getattr(self,'_tutorial_preview_token',0) or 0)+1;token=self._tutorial_preview_token
        try:self.after(1,lambda p=page,tok=token:self._tutorial_capture_preview(p,tok))
        except Exception:pass
'''
replace_method('_tutorial_render_step',tutorial_render)

tutorial_move=r'''    def _tutorial_move(self,delta):
        steps=self._tutorial_steps();nxt=int(getattr(self,'_tutorial_step_index',0) or 0)+int(delta)
        if nxt>=len(steps):self._tutorial_preview_token=int(getattr(self,'_tutorial_preview_token',0) or 0)+1;self._tutorial_close(mark_complete=True);return
        self._tutorial_step_index=max(0,nxt);self._tutorial_render_step()
'''
replace_method('_tutorial_move',tutorial_move)

old='''        cover=ctk.CTkFrame(self.main_container,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.78),corner_radius=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift();self._first_run_setup_panel=cover'''
new='''        cover=self._zk_blur_cover(self,radius=12,brightness=.42)
        self._first_run_setup_panel=cover'''
if old not in s:raise SystemExit('v3.20.4: setup cover anchor')
s=s.replace(old,new,1)

for needle in ('APP_VERSION = "3.20.4"','def _zk_blur_cover(','language_picker_revision"]=5','def _tutorial_capture_preview(','self.show_page(page,animate=False)','DESBLOQUEADO','cover=self._zk_blur_cover(self,radius=12,brightness=.42)'):
    if needle not in s:raise SystemExit('v3.20.4: missing '+needle)
if 'try:self.after(900,self._maybe_show_first_run_tutorial)' in s:raise SystemExit('v3.20.4: old delay remains')
if 'RedrawWindow(' in s:raise SystemExit('v3.20.4: unsafe repaint')
ast.parse(s);path.write_text(s,encoding='utf-8');print('Applied v3.20.4 onboarding/tutorial rework')
