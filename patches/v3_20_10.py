from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def lines_pos(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.20.10: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.10: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


if 'APP_VERSION = "3.20.9"' not in s:raise SystemExit('v3.20.10: expected v3.20.9 base')
s=s.replace('APP_VERSION = "3.20.9"','APP_VERSION = "3.20.10"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "First Run Polish + Profile Confirmation"',s,count=1)
if n!=1:raise SystemExit('v3.20.10: timestamp')

# -----------------------------------------------------------------------------
# FIRST-RUN WINDOW + TRUE APP BLUR
# Capture the visible ZKStrap BEFORE placing the overlay. v3.20.4 created the
# overlay first, so ImageGrab could catch the desktop/black cover instead.
# Also resize the blurred image with the window so maximizing/restoring never
# leaves only a small blurred rectangle surrounded by black.
# -----------------------------------------------------------------------------
replace_method('_zk_blur_cover',r'''    def _zk_blur_cover(self,host=None,radius=11,brightness=.48):
        host=host or self;t=TEMAS[self.tema_atual]
        shot=None;w=2;h=2
        try:
            self.update_idletasks();host.update_idletasks()
            from PIL import ImageGrab,ImageFilter,ImageEnhance
            x=int(host.winfo_rootx());y=int(host.winfo_rooty());w=max(2,int(host.winfo_width()));h=max(2,int(host.winfo_height()))
            # IMPORTANT: grab the already-rendered application BEFORE creating cover.
            shot=ImageGrab.grab(bbox=(x,y,x+w,y+h)).convert("RGBA")
            shot=shot.filter(ImageFilter.GaussianBlur(radius=max(2,int(radius))))
            shot=ImageEnhance.Brightness(shot).enhance(max(.25,min(.90,float(brightness))))
        except Exception:
            shot=None

        cover=ctk.CTkFrame(host,fg_color=self._mix_hex(t.get("bg","#08070C"),"#000000",.18),corner_radius=0,border_width=0)
        cover.place(x=0,y=0,relwidth=1,relheight=1)
        cover._zk_blur_source=shot;cover._zk_blur_img=None;cover._zk_blur_resize_after=None
        if shot is not None:
            lab=ctk.CTkLabel(cover,text="",fg_color="transparent")
            lab.place(x=0,y=0,relwidth=1,relheight=1)
            cover._zk_blur_label=lab
            def paint_blur(width,height):
                try:
                    if not cover.winfo_exists():return
                    width=max(2,int(width));height=max(2,int(height))
                    img=ctk.CTkImage(light_image=shot,dark_image=shot,size=(width,height))
                    cover._zk_blur_img=img;lab.configure(image=img,text="")
                except Exception:pass
            paint_blur(w,h)
            def blur_resize(event):
                try:
                    old=getattr(cover,"_zk_blur_resize_after",None)
                    if old:self.after_cancel(old)
                except Exception:pass
                try:cover._zk_blur_resize_after=self.after(35,lambda ew=event.width,eh=event.height:paint_blur(ew,eh))
                except Exception:pass
            try:cover.bind("<Configure>",blur_resize,add="+")
            except Exception:pass
        else:
            cover._zk_blur_label=None
        cover._zk_shade=None
        cover.lift();return cover
''')

helper=r'''    def _first_run_ensure_maximized(self):
        """Keep first-run cinematic screens inside a fully sized ZKStrap window."""
        try:
            state=str(self.state() or "").lower()
            if state!="zoomed":self.state("zoomed")
        except Exception:
            try:self.attributes("-zoomed",True)
            except Exception:pass
        try:self.update_idletasks()
        except Exception:pass
'''
_,cls=app_class(s);_,pos=lines_pos(s);insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+helper.rstrip()+"\n"+s[insert_at:]

# Maximize once the first-run router knows it is actually in a first-run stage.
_,a,b=method_span(s,'_first_run_route')
chunk=s[a:b]
anchor='stage=self._first_run_stage()'
if anchor not in chunk:raise SystemExit('v3.20.10: first-run route anchor missing')
chunk=chunk.replace(anchor,anchor+'\n        if stage!="done":self._first_run_ensure_maximized()',1)
s=s[:a]+chunk+s[b:]

# -----------------------------------------------------------------------------
# ROBLOX LINK: SEARCH -> PREVIEW -> CONFIRM
# Do not commit the profile as soon as search returns. Let the user verify it,
# search again if the username was mistyped, then persist + refresh top profile.
# -----------------------------------------------------------------------------
replace_method('_abrir_onboarding_username_ui_3205',r'''    def _abrir_onboarding_username_ui_3205(self, primeiro_acesso=True):
        t=TEMAS[self.tema_atual];L=self._L
        if primeiro_acesso:self._first_run_ensure_maximized()
        old=getattr(self,"_tutorial_panel",None)
        try:
            if old is not None:old.destroy()
        except Exception:pass
        cover=self._zk_blur_cover(self,radius=13,brightness=.43);self._tutorial_panel=cover
        panel=ctk.CTkFrame(cover,width=1080,height=610,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.62));panel.place(relx=.5,rely=.5,anchor="center");panel.pack_propagate(False)
        ctk.CTkFrame(panel,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        body=ctk.CTkFrame(panel,fg_color="transparent");body.pack(fill="both",expand=True,padx=22,pady=22)

        left=ctk.CTkFrame(body,width=350,fg_color=self._mix_hex(t["card"],t["accent"],.07),corner_radius=20,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.28));left.pack(side="left",fill="y",padx=(0,18));left.pack_propagate(False)
        ctk.CTkLabel(left,text="02 / 03   //   ROBLOX LINK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=24,pady=(25,15))
        avatar_shell=ctk.CTkFrame(left,width=154,height=154,corner_radius=77,fg_color=t["card_active"],border_width=2,border_color=t["accent"]);avatar_shell.pack(pady=(8,14));avatar_shell.pack_propagate(False)
        avatar=ctk.CTkLabel(avatar_shell,text="@",text_color=t["accent"],font=ctk.CTkFont(size=49,weight="bold"));avatar.place(relx=.5,rely=.5,anchor="center")
        profile_name=ctk.CTkLabel(left,text=L("Seu perfil aparece aqui","Your profile appears here","Tu perfil aparece aquí","你的资料会显示在这里","Votre profil apparaît ici"),text_color=t["text"],font=ctk.CTkFont(size=15,weight="bold"));profile_name.pack(padx=20,pady=(3,4))
        profile_user=ctk.CTkLabel(left,text="@username",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=10));profile_user.pack()
        confirm_badge=ctk.CTkLabel(left,text=L("AGUARDANDO BUSCA","WAITING FOR SEARCH","ESPERANDO BÚSQUEDA","等待搜索","EN ATTENTE DE RECHERCHE"),height=27,corner_radius=8,fg_color=t["card_active"],text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));confirm_badge.pack(padx=22,pady=(16,8),fill="x")
        ctk.CTkLabel(left,text=L("Confira o Display Name, @username e avatar antes de confirmar. Assim um erro de digitação não vincula a conta errada.","Check the Display Name, @username and avatar before confirming so a typo never links the wrong account.","Comprueba el Display Name, @usuario y avatar antes de confirmar para no vincular una cuenta incorrecta.","确认前请核对显示名称、@用户名和头像，避免因输入错误绑定错误账号。","Vérifiez le Display Name, le @pseudo et l’avatar avant de confirmer afin d’éviter de lier le mauvais compte."),wraplength=285,justify="center",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(padx=24,pady=(8,8))
        secure=ctk.CTkFrame(left,fg_color=t["card_active"],corner_radius=11);secure.pack(fill="x",padx=22,pady=(10,0));ctk.CTkLabel(secure,text="✓  PUBLIC PROFILE ONLY",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(padx=10,pady=10)

        right=ctk.CTkFrame(body,fg_color="transparent");right.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(right,text=L("Encontre sua conta do Roblox","Find your Roblox account","Encuentra tu cuenta de Roblox","找到你的 Roblox 账号","Trouvez votre compte Roblox"),text_color=t["text"],font=ctk.CTkFont(size=26,weight="bold"),anchor="w").pack(fill="x",padx=7,pady=(12,4))
        ctk.CTkLabel(right,text=L("Digite o @username. Primeiro mostramos o perfil encontrado; só vinculamos depois que você confirmar que é a conta certa.","Enter the @username. We show the profile first and only link it after you confirm it is the correct account.","Escribe el @usuario. Primero mostramos el perfil y solo lo vinculamos después de que confirmes que es la cuenta correcta.","输入 @用户名。我们会先显示找到的资料，只有在你确认账号正确后才会绑定。","Entrez le @pseudo. Nous affichons d’abord le profil trouvé et ne le lions qu’après votre confirmation."),wraplength=625,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(fill="x",padx=7,pady=(2,17))
        entry=ctk.CTkEntry(right,placeholder_text="@username",height=55,corner_radius=14,border_width=2,border_color=t["card_active"],font=ctk.CTkFont(size=14,weight="bold"));entry.pack(fill="x",padx=7)
        status=ctk.CTkLabel(right,text=L("Digite seu username e pressione Enter ou Buscar perfil.","Enter your username and press Enter or Search profile.","Escribe tu usuario y presiona Enter o Buscar perfil.","输入用户名后按 Enter 或搜索资料。","Entrez votre pseudo puis appuyez sur Entrée ou Rechercher."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w");status.pack(fill="x",padx=8,pady=(8,10))

        info=ctk.CTkFrame(right,fg_color=t["card_active"],corner_radius=13);info.pack(fill="x",padx=7,pady=(2,12))
        ctk.CTkLabel(info,text=L("ANTES DE VINCULAR","BEFORE LINKING","ANTES DE VINCULAR","绑定之前","AVANT DE LIER"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x",padx=13,pady=(10,3))
        ctk.CTkLabel(info,text=L("1. Buscar perfil  →  2. Conferir conta  →  3. Confirmar vínculo","1. Search profile  →  2. Verify account  →  3. Confirm link","1. Buscar perfil  →  2. Comprobar cuenta  →  3. Confirmar vínculo","1. 搜索资料  →  2. 核对账号  →  3. 确认绑定","1. Rechercher  →  2. Vérifier le compte  →  3. Confirmer le lien"),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w").pack(fill="x",padx=13,pady=(1,10))

        pending={"profile":None,"avatar":None}

        def begin_tutorial():
            try:cover.destroy()
            except Exception:pass
            self._tutorial_panel=None;self._first_run_active_stage=""
            try:self.after(20,lambda:self._abrir_tutorial_ui_3205(primeiro_acesso=bool(primeiro_acesso)))
            except Exception:pass

        def set_avatar(data=None):
            if not data:
                try:avatar.configure(image=None,text="@")
                except Exception:pass
                return
            try:
                import io
                from PIL import Image
                im=Image.open(io.BytesIO(data)).convert('RGBA');im.thumbnail((140,140),Image.Resampling.LANCZOS)
                self._onboarding_avatar_img=ctk.CTkImage(light_image=im,dark_image=im,size=(140,140));avatar.configure(image=self._onboarding_avatar_img,text='')
            except Exception:pass

        def refresh_top_profile():
            try:self._render_profile_button()
            except Exception:pass
            try:self._refresh_home_profile_card()
            except Exception:pass

        def reset_search(clear=True):
            pending["profile"]=None;pending["avatar"]=None;self._onboarding_profile_busy=False
            try:
                entry.configure(state="normal")
                if clear:entry.delete(0,"end")
                profile_name.configure(text=L("Seu perfil aparece aqui","Your profile appears here","Tu perfil aparece aquí","你的资料会显示在这里","Votre profil apparaît ici"))
                profile_user.configure(text="@username");set_avatar(None)
                confirm_badge.configure(text=L("AGUARDANDO BUSCA","WAITING FOR SEARCH","ESPERANDO BÚSQUEDA","等待搜索","EN ATTENTE DE RECHERCHE"),text_color=t.get("muted","gray"))
                status.configure(text=L("Digite outro @username e pesquise novamente.","Enter another @username and search again.","Escribe otro @usuario y vuelve a buscar.","输入另一个 @用户名并重新搜索。","Entrez un autre @pseudo et relancez la recherche."),text_color=t.get("muted","gray"))
                btn.configure(state="normal",text=L("BUSCAR PERFIL","SEARCH PROFILE","BUSCAR PERFIL","搜索资料","RECHERCHER LE PROFIL"),command=start_link)
                retry.configure(state="disabled");fallback.configure(state="normal")
                entry.focus_force()
            except Exception:pass

        def confirm_profile():
            profile=pending.get("profile")
            if not profile:return
            try:
                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":str(profile.get("avatar_url","") or "")}
                self._mark_roblox_onboarding_done(self.linked_profile["name"])
                refresh_top_profile()
                try:self.after(60,refresh_top_profile)
                except Exception:pass
                confirm_badge.configure(text=L("CONTA CONFIRMADA  ✓","ACCOUNT CONFIRMED  ✓","CUENTA CONFIRMADA  ✓","账号已确认  ✓","COMPTE CONFIRMÉ  ✓"),text_color=t["accent"])
                status.configure(text=L("Conta vinculada. Abrindo seu guia...","Account linked. Opening your guide...","Cuenta vinculada. Abriendo tu guía...","账号已绑定，正在打开教程...","Compte lié. Ouverture du guide..."),text_color=t["accent"])
                btn.configure(text=L("VINCULADO  ✓","LINKED  ✓","VINCULADO  ✓","已绑定  ✓","LIÉ  ✓"),state="disabled");retry.configure(state="disabled");fallback.configure(state="disabled")
                self.after(360,begin_tutorial)
            except Exception as exc:
                status.configure(text=str(exc),text_color="#FF6B7A");btn.configure(state="normal")

        def link_result(profile,error="",avatar_bytes=None):
            self._onboarding_profile_busy=False
            if error:
                status.configure(text=error,text_color="#FF6B7A");btn.configure(state="normal",text=L("BUSCAR PERFIL","SEARCH PROFILE","BUSCAR PERFIL","搜索资料","RECHERCHER LE PROFIL"),command=start_link);retry.configure(state="normal");fallback.configure(state="normal");return
            pending["profile"]=profile;pending["avatar"]=avatar_bytes
            try:
                profile_name.configure(text=str(profile.get("displayName") or profile.get("name") or ""));profile_user.configure(text='@'+str(profile.get("name") or ""));set_avatar(avatar_bytes)
                confirm_badge.configure(text=L("ESSA É SUA CONTA?","IS THIS YOUR ACCOUNT?","¿ES ESTA TU CUENTA?","这是你的账号吗？","EST-CE VOTRE COMPTE ?"),text_color=t["accent"])
                status.configure(text=L("Confira o perfil ao lado. Se estiver certo, confirme. Se não, pesquise de novo.","Check the profile on the left. Confirm if it is correct, or search again if it is not.","Comprueba el perfil de la izquierda. Confirma si es correcto o vuelve a buscar.","请核对左侧资料。正确就确认，不正确就重新搜索。","Vérifiez le profil à gauche. Confirmez s’il est correct, sinon relancez la recherche."),text_color=t["accent"])
                entry.configure(state="disabled")
                btn.configure(state="normal",text=L("SIM, É MINHA CONTA  ✓","YES, THIS IS MY ACCOUNT  ✓","SÍ, ES MI CUENTA  ✓","是的，这是我的账号  ✓","OUI, C’EST MON COMPTE  ✓"),command=confirm_profile)
                retry.configure(state="normal");fallback.configure(state="disabled")
            except Exception:pass

        def link_worker(username):
            profile=None;err="";avatar_bytes=None
            try:
                headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":f"ZKStrap/{APP_VERSION}"}
                r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[username],"excludeBannedUsers":False},headers=headers,timeout=(4,10))
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
            except Exception:err=L("Roblox não respondeu agora. Tente novamente ou continue só com o nick.","Roblox didn't respond. Try again or continue with nickname only.","Roblox no respondió. Intenta de nuevo o sigue solo con el nick.","Roblox 暂时没有响应，请重试或仅使用昵称继续。","Roblox ne répond pas. Réessayez ou continuez avec le pseudo.")
            self.after(0,lambda:link_result(profile,err,avatar_bytes))

        def start_link(event=None):
            if pending.get("profile") is not None:return confirm_profile()
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Username inválido (3–20 caracteres).","Invalid username (3–20 characters).","Usuario inválido (3–20 caracteres).","用户名无效（3–20 个字符）。","Pseudo invalide (3–20 caractères)."),text_color="#FF6B7A");return
            if bool(getattr(self,'_onboarding_profile_busy',False)):return
            self._onboarding_profile_busy=True;status.configure(text=L("Procurando perfil público...","Looking up public profile...","Buscando perfil público...","正在查询公开资料...","Recherche du profil public..."),text_color=t["accent"]);btn.configure(state='disabled',text=L("PROCURANDO...","SEARCHING...","BUSCANDO...","查询中...","RECHERCHE..."));retry.configure(state='disabled');fallback.configure(state='disabled');threading.Thread(target=link_worker,args=(username,),daemon=True,name='ZKFirstRunRobloxLink').start()

        def continue_nick_only():
            username=entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):status.configure(text=L("Digite um username válido primeiro.","Enter a valid username first.","Escribe un usuario válido primero.","请先输入有效用户名。","Entrez d’abord un pseudo valide."),text_color="#FF6B7A");return
            self._mark_roblox_onboarding_done(username);begin_tutorial()

        btn=ctk.CTkButton(right,text=L("BUSCAR PERFIL","SEARCH PROFILE","BUSCAR PERFIL","搜索资料","RECHERCHER LE PROFIL"),command=start_link,height=48,corner_radius=13,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=11,weight="bold"));btn.pack(fill="x",padx=7,pady=(4,7))
        retry=ctk.CTkButton(right,text=L("NÃO É ESSA — PESQUISAR OUTRA","NOT THIS ONE — SEARCH AGAIN","NO ES ESTA — BUSCAR OTRA","不是这个 — 重新搜索","PAS CELUI-CI — RECHERCHER"),command=lambda:reset_search(True),state="disabled",height=38,corner_radius=11,fg_color="transparent",border_width=1,border_color=t["accent"],text_color=t["accent"]);retry.pack(fill="x",padx=7,pady=(0,7))
        fallback=ctk.CTkButton(right,text=L("CONTINUAR SÓ COM O NICK","CONTINUE WITH NICKNAME ONLY","CONTINUAR SOLO CON EL NICK","仅使用昵称继续","CONTINUER AVEC LE PSEUDO"),command=continue_nick_only,height=36,corner_radius=11,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"));fallback.pack(fill="x",padx=7)
        entry.bind('<Return>',start_link);self.after(70,lambda:entry.focus_force())
''')

# -----------------------------------------------------------------------------
# RICHER IN-APP TUTORIAL CONTROLLER
# Keep progressive unlocking directly in the real application, but give the
# controller stronger hierarchy, context and progress instead of a bare box.
# -----------------------------------------------------------------------------
replace_method('_abrir_tutorial_ui_3205',r'''    def _abrir_tutorial_ui_3205(self, primeiro_acesso=False):
        if primeiro_acesso:self._first_run_ensure_maximized()
        try:self._fechar_busca_universal()
        except Exception:pass
        try:self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception:pass
        self._tutorial_first_run=bool(primeiro_acesso);self._tutorial_replay=not bool(primeiro_acesso);self._tutorial_step_index=0;self._tutorial_max_unlocked=0;self._tutorial_step_ready=True;self._tutorial_preview_token=int(getattr(self,"_tutorial_preview_token",0) or 0)+1;self._tutorial_nav_stash={};self._tutorial_nav_capture()
        steps=self._tutorial_steps()
        if not steps:return
        self._tutorial_apply_real_unlock(0)
        try:self.show_page(str(steps[0][0]),animate=False)
        except Exception:pass
        t=TEMAS[self.tema_atual];L=self._L
        card=ctk.CTkFrame(self,width=545,height=315,fg_color=t.get("panel",t["card"]),corner_radius=21,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.78));card.place(relx=.985,rely=.975,anchor="se");card.pack_propagate(False);card.lift();self._tutorial_panel=card
        ctk.CTkFrame(card,height=4,fg_color=t["accent"],corner_radius=0).pack(fill="x")
        top=ctk.CTkFrame(card,fg_color="transparent");top.pack(fill="x",padx=16,pady=(12,4))
        ctk.CTkLabel(top,text="ZKSTRAP // GUIA INTERATIVO",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        self._tutorial_count=ctk.CTkLabel(top,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));self._tutorial_count.pack(side="right")
        meta=ctk.CTkFrame(card,height=34,fg_color=t["card_active"],corner_radius=10);meta.pack(fill="x",padx=15,pady=(4,7));meta.pack_propagate(False)
        self._tutorial_stage=ctk.CTkLabel(meta,text="",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w");self._tutorial_stage.pack(side="left",padx=11)
        self._tutorial_unlocked=ctk.CTkLabel(meta,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8),anchor="e");self._tutorial_unlocked.pack(side="right",padx=11)
        self._tutorial_title=ctk.CTkLabel(card,text="",anchor="w",text_color=t["text"],font=ctk.CTkFont(size=19,weight="bold"));self._tutorial_title.pack(fill="x",padx=16,pady=(2,1))
        self._tutorial_body=ctk.CTkLabel(card,text="",anchor="w",justify="left",wraplength=505,text_color=t["text"],font=ctk.CTkFont(size=10));self._tutorial_body.pack(fill="x",padx=16,pady=(1,4))
        tipbox=ctk.CTkFrame(card,fg_color=self._mix_hex(t["card"],t["accent"],.08),corner_radius=10,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.28));tipbox.pack(fill="x",padx=15,pady=(2,6))
        ctk.CTkLabel(tipbox,text=L("DICA // O QUE OBSERVAR","TIP // WHAT TO NOTICE","TIP // QUÉ MIRAR","提示 // 注意事项","ASTUCE // À OBSERVER"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(fill="x",padx=10,pady=(7,1))
        self._tutorial_tip=ctk.CTkLabel(tipbox,text="",anchor="w",justify="left",wraplength=485,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9));self._tutorial_tip.pack(fill="x",padx=10,pady=(1,7))
        progrow=ctk.CTkFrame(card,fg_color="transparent");progrow.pack(fill="x",padx=15,pady=(0,2))
        ctk.CTkLabel(progrow,text=L("PROGRESSO DO GUIA","GUIDE PROGRESS","PROGRESO DE LA GUÍA","教程进度","PROGRESSION DU GUIDE"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(side="left")
        self._tutorial_progress_text=ctk.CTkLabel(progrow,text="",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"));self._tutorial_progress_text.pack(side="right")
        self._tutorial_progress=ctk.CTkProgressBar(card,height=5,progress_color=t["accent"],fg_color=t["card_active"]);self._tutorial_progress.pack(fill="x",padx=15,pady=(0,8))
        foot=ctk.CTkFrame(card,fg_color="transparent");foot.pack(fill="x",padx=15,pady=(0,12),side="bottom")
        self._tutorial_prev=ctk.CTkButton(foot,text="←",width=45,height=32,command=lambda:self._tutorial_move(-1),fg_color=t["card_active"],hover_color=t["hover"]);self._tutorial_prev.pack(side="left")
        self._tutorial_skip=ctk.CTkButton(foot,text=L("SAIR","EXIT","SALIR","退出","QUITTER"),width=66,height=32,command=self._tutorial_skip_click,fg_color="transparent",border_width=1,border_color=t["card_active"]);self._tutorial_skip.pack(side="left",padx=6)
        self._tutorial_next=ctk.CTkButton(foot,text="",width=176,height=32,command=lambda:self._tutorial_move(1),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=9,weight="bold"));self._tutorial_next.pack(side="right")
        self._tutorial_render_step()
''')

replace_method('_tutorial_render_step',r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps()
        if not steps:return
        idx=max(0,min(int(getattr(self,"_tutorial_step_index",0) or 0),len(steps)-1));self._tutorial_step_index=idx
        page,title,body,tip=steps[idx][:4];self._tutorial_step_ready=True;self._tutorial_apply_real_unlock(idx)
        try:self.show_page(str(page),animate=False)
        except Exception:pass
        try:
            self._tutorial_title.configure(text=title);self._tutorial_body.configure(text=body);self._tutorial_tip.configure(text=tip);self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
            pct=int(round(((idx+1)/max(1,len(steps)))*100));self._tutorial_progress.set((idx+1)/max(1,len(steps)));self._tutorial_progress_text.configure(text=f"{pct}%")
            self._tutorial_stage.configure(text=self._L(f"AGORA // {title.upper()}",f"NOW // {title.upper()}",f"AHORA // {title.upper()}",f"当前 // {title}",f"MAINTENANT // {title.upper()}"))
            self._tutorial_unlocked.configure(text=self._L(f"{idx+1} ÁREAS LIBERADAS",f"{idx+1} AREAS UNLOCKED",f"{idx+1} ÁREAS DESBLOQUEADAS",f"已解锁 {idx+1} 个区域",f"{idx+1} ZONES DÉVERROUILLÉES"))
            self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
            label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("LIBERAR PRÓXIMA  →","UNLOCK NEXT  →","DESBLOQUEAR SIGUIENTE  →","解锁下一项  →","DÉVERROUILLER LA SUITE  →")
            self._tutorial_next.configure(state="normal",text=label)
            panel=getattr(self,"_tutorial_panel",None)
            if panel is not None and panel.winfo_exists():panel.lift()
        except Exception:pass
''')

# -----------------------------------------------------------------------------
# LOCALIZE SETUP TITLES/TAGS + TOAST NAMES
# -----------------------------------------------------------------------------
_,a,b=method_span(s,'_show_first_run_setup_choice')
chunk=s[a:b]
old1='make_card(0,"FPS MÁXIMO","COMPETITIVE // MAX FPS",'
new1='make_card(0,L("FPS MÁXIMO","MAX FPS","FPS MÁXIMOS","最高 FPS","FPS MAX"),L("COMPETITIVO // FPS MÁXIMO","COMPETITIVE // MAX FPS","COMPETITIVO // FPS MÁXIMOS","竞技 // 最高 FPS","COMPÉTITIF // FPS MAX"),'
old2='make_card(1,"PC FRACO","STABLE // LOW LOAD",'
new2='make_card(1,L("PC FRACO","LOW-END PC","PC MODESTO","低配电脑","PC PEU PUISSANT"),L("ESTÁVEL // BAIXA CARGA","STABLE // LOW LOAD","ESTABLE // BAJA CARGA","稳定 // 低负载","STABLE // FAIBLE CHARGE"),'
if old1 not in chunk or old2 not in chunk:raise SystemExit('v3.20.10: setup title anchors missing')
chunk=chunk.replace(old1,new1,1).replace(old2,new2,1)
s=s[:a]+chunk+s[b:]

_,a,b=method_span(s,'_apply_first_run_setup_choice')
chunk=s[a:b]
chunk=chunk.replace('chosen="FPS MÁXIMO"','chosen=L("FPS MÁXIMO","MAX FPS","FPS MÁXIMOS","最高 FPS","FPS MAX")',1)
chunk=chunk.replace('chosen="PC FRACO"','chosen=L("PC FRACO","LOW-END PC","PC MODESTO","低配电脑","PC PEU PUISSANT")',1)
s=s[:a]+chunk+s[b:]

# Validation
tree,cls=app_class(s);names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_zk_blur_cover','_first_run_ensure_maximized','_first_run_route','_abrir_onboarding_username_ui_3205','_abrir_tutorial_ui_3205','_tutorial_render_step','_show_first_run_setup_choice'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.10: {unique} count={names.count(unique)}')
for needle in (
    'APP_VERSION = "3.20.10"',
    'First Run Polish + Profile Confirmation',
    'grab the already-rendered application BEFORE creating cover',
    'if stage!="done":self._first_run_ensure_maximized()',
    'ESSA É SUA CONTA?',
    'SIM, É MINHA CONTA  ✓',
    'refresh_top_profile()',
    'ZKSTRAP // GUIA INTERATIVO',
    'PROGRESSO DO GUIA',
    'LOW-END PC',
    '低配电脑',
):
    if needle not in s:raise SystemExit('v3.20.10: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.10: unsafe repaint')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied v3.20.10 first-run polish/profile confirmation')
