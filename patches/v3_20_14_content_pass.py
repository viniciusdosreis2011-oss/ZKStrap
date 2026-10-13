from pathlib import Path
import ast, os, textwrap, hashlib

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')

def _class_and_lines(src):
    t=ast.parse(src)
    cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
    return t,cls,src.splitlines(True)

def _normalize_method(body):
    raw=body.strip('\n').splitlines()
    if not raw:return ''
    if raw[0].lstrip().startswith(('def ','async def ')) and raw[0]==raw[0].lstrip():
        raw=[raw[0]]+[(line[4:] if line.startswith('    ') else line) for line in raw[1:]]
    else:
        raw=textwrap.dedent(body).strip('\n').splitlines()
    return '\n'.join(raw)+'\n'

def replace_method(src,name,body):
    t,cls,lines=_class_and_lines(src)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit(f'content-pass method missing: {name}')
    start=sum(len(x) for x in lines[:node.lineno-1]);end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:start]+textwrap.indent(_normalize_method(body),'    ')+src[end:]

def insert_method_after(src,after_name,name,body):
    t,cls,lines=_class_and_lines(src)
    if any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name for n in cls.body):
        raise SystemExit(f'content-pass method already exists: {name}')
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==after_name),None)
    if node is None:raise SystemExit(f'insert anchor missing: {after_name}')
    end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:end]+'\n'+textwrap.indent(_normalize_method(body),'    ')+src[end:]

def replace_assign(src,name,body):
    t=ast.parse(src);lines=src.splitlines(True)
    node=next((n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets)),None)
    if node is None:raise SystemExit(f'global assignment missing: {name}')
    start=sum(len(x) for x in lines[:node.lineno-1]);end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:start]+textwrap.dedent(body).strip('\n')+'\n'+src[end:]

s=replace_assign(s,'AUDIO_PACKS','''AUDIO_PACKS = {
    "NEON HEART": {"folder":"neon_heart", "genre":"Trap Melódico", "bpm":138, "desc":"Plucks emotivos, pads e 808 limpo."},
    "OVERCLOCK": {"folder":"overclock", "genre":"Drum & Bass", "bpm":174, "desc":"Break rápido, reese bass e energia contínua."},
    "MIDNIGHT.exe": {"folder":"midnight_exe", "genre":"Synthwave", "bpm":105, "desc":"Synths analógicos, arpejo e bateria retrô."},
    "AFTER HOURS": {"folder":"after_hours", "genre":"Lo-fi", "bpm":82, "desc":"Rhodes, bateria macia e textura noturna."},
    "REDLINE": {"folder":"redline", "genre":"Electro Rock", "bpm":150, "desc":"Riffs sintéticos, bateria pesada e bass agressivo."},
    "ABYSS": {"folder":"abyss", "genre":"Dark Ambient", "bpm":68, "desc":"Drones, sinos distantes e espaço profundo."},
    "FINAL PHASE": {"folder":"final_phase", "genre":"Boss Battle OST", "bpm":156, "desc":"Ostinatos, impactos e clímax cinematográfico."},
    "LOW GRAVITY": {"folder":"low_gravity", "genre":"Future Garage", "bpm":134, "desc":"Drums espaçados, subs e pads aéreos."},
    "SUNSET MODE": {"folder":"sunset_mode", "genre":"Chillwave", "bpm":95, "desc":"Pads quentes, chorus synth e groove de pôr do sol."},
}''')
s=replace_assign(s,'DEFAULT_AUDIO_PACK','DEFAULT_AUDIO_PACK = "SUNSET MODE"')
s=replace_assign(s,'AUDIO_PACK_ALIASES','''AUDIO_PACK_ALIASES = {
    "ZK Signature":"SUNSET MODE",
    "Neon Tech":"MIDNIGHT.exe",
    "Glass UI":"NEON HEART",
    "Soft Clicks":"AFTER HOURS",
    "Deep Space":"ABYSS",
    "Void Calm":"ABYSS",
    "Tactical":"REDLINE",
    "Cyber Pulse":"OVERCLOCK",
    "Arcade":"NEON HEART",
    "Retro Digital":"MIDNIGHT.exe",
    "VOID DRIVE":"REDLINE",
    "NIGHT RUNNER":"OVERCLOCK",
    "NO SIGNAL":"ABYSS",
    "SYSTEM BREACH":"MIDNIGHT.exe",
    "GLITCHED":"NEON HEART",
    "PIXEL RUSH":"NEON HEART",
    "ICE COLD":"SUNSET MODE",
    "BLACKOUT":"ABYSS",
    "LAST ROUND":"FINAL PHASE",
}''')

s=insert_method_after(s,'_module_icon_for_key','_ui_pictogram_ctk','''def _ui_pictogram_ctk(self, key, size=34):
        """Small generated pictogram used to break up text-heavy cards without external assets."""
        try:
            from PIL import Image, ImageDraw
            t=TEMAS[self.tema_atual]
            key=str(key or "generic").lower()
            cache=getattr(self,"_zk_pictogram_cache",None)
            if not isinstance(cache,dict):
                cache={};self._zk_pictogram_cache=cache
            ck=(key,int(size),str(t.get("accent","#a855f7")),str(t.get("text","#ffffff")))
            if ck in cache:return cache[ck]
            n=64
            im=Image.new("RGBA",(n,n),(0,0,0,0));d=ImageDraw.Draw(im)
            def col(v,alpha=255):
                v=str(v or "#ffffff")
                if v.startswith("#") and len(v)>=7:
                    return (int(v[1:3],16),int(v[3:5],16),int(v[5:7],16),alpha)
                return (255,255,255,alpha)
            ac=col(t.get("accent","#a855f7")); tx=col(t.get("text","#ffffff"),220); mu=col(t.get("muted","#999999"),170)
            def line(points,fill=ac,width=5):d.line(points,fill=fill,width=width,joint="curve")
            if key.startswith("audio:") or key in ("audio","music","sound"):
                seed=sum(ord(c) for c in key)
                bars=[14+((seed>>(i*2))%28) for i in range(5)]
                for i,h in enumerate(bars):
                    x=9+i*11; d.rounded_rectangle((x,32-h//2,x+7,32+h//2),radius=3,fill=ac if i%2==0 else tx)
            elif key in ("textures","texture"):
                for y in range(3):
                    for x in range(3):
                        fill=ac if (x+y)%2==0 else tx
                        d.rounded_rectangle((10+x*15,10+y*15,22+x*15,22+y*15),radius=2,fill=fill)
            elif key in ("grass","vegetation"):
                line((9,50,18,24),tx,4);line((18,50,28,16),ac,5);line((31,50,36,21),tx,4);line((41,50,52,19),ac,5);line((7,50,56,50),mu,4)
            elif key in ("msaa","antialias"):
                line((10,48,50,14),ac,6);line((15,50,55,16),tx,2)
                for p in ((12,18),(22,14),(44,46),(52,38)):d.ellipse((p[0]-3,p[1]-3,p[0]+3,p[1]+3),fill=mu)
            elif key in ("frm_low","quality","lod"):
                line((15,20,32,10,49,20,32,30,15,20),ac,4);line((15,20,15,43,32,53,49,43,49,20),tx,4);line((32,30,32,53),mu,3)
            elif key in ("voxelizer","lighting","light"):
                d.ellipse((23,23,41,41),outline=ac,width=5)
                for a,b in [((32,7),(32,17)),((32,47),(32,57)),((7,32),(17,32)),((47,32),(57,32)),((14,14),(21,21)),((43,43),(50,50)),((14,50),(21,43)),((43,21),(50,14))]:line((a,b),tx,3)
            elif key in ("d3d11","gpu"):
                d.rounded_rectangle((13,16,51,48),radius=7,outline=ac,width=4)
                line((20,28,44,28),tx,3);line((20,36,40,36),tx,3)
                for x in (18,27,36,45):line((x,10,x,16),mu,2);line((x,48,x,54),mu,2)
            elif key in ("dpi","resolution","display"):
                d.rounded_rectangle((10,14,54,44),radius=5,outline=ac,width=4);line((26,50,38,50),tx,4);line((32,44,32,50),tx,4);line((18,35,29,24,40,35),mu,3)
            elif key in ("performance_boost","fps_unlock","fps","performance"):
                d.arc((10,10,54,54),190,350,fill=ac,width=5);line((32,36,47,22),tx,5);d.ellipse((27,31,37,41),fill=ac)
            elif key in ("gray_sky","sky"):
                d.ellipse((12,29,34,49),fill=mu);d.ellipse((24,19,46,49),fill=ac);d.ellipse((36,29,54,49),fill=tx);d.rectangle((16,36,50,49),fill=ac)
            elif key in ("ping_boost","ping","network"):
                for i,h in enumerate((10,18,27,36)):d.rounded_rectangle((10+i*11,50-h,17+i*11,50),radius=2,fill=ac if i>1 else tx)
                d.ellipse((49,45,57,53),fill=ac)
            elif key in ("telemetry_off","privacy"):
                d.ellipse((14,14,50,50),outline=ac,width=4);line((16,48,48,16),tx,5);d.ellipse((27,27,37,37),fill=mu)
            elif key in ("micro_opt","cpu"):
                d.rounded_rectangle((17,17,47,47),radius=5,outline=ac,width=4);d.rectangle((25,25,39,39),fill=tx)
                for x in (22,32,42):line((x,9,x,17),mu,2);line((x,47,x,55),mu,2)
            elif key in ("draco_aura","blox","combo","build"):
                d.polygon([(32,7),(51,29),(38,29),(48,56),(17,35),(29,35)],fill=ac);line((19,16,44,48),tx,2)
            elif key in ("cursor","mouse"):
                d.polygon([(13,8),(13,49),(24,39),(31,55),(39,51),(32,36),(48,35)],fill=ac);line((15,12,43,33),tx,2)
            elif key in ("font","fonte"):
                d.ellipse((11,13,37,39),outline=ac,width=4);line((16,50,28,20),ac,5);line((28,20,40,50),ac,5);line((19,38,37,38),tx,4)
            elif key in ("cache","storage"):
                d.ellipse((13,13,51,25),outline=ac,width=4);line((13,19,13,45),ac,4);line((51,19,51,45),ac,4);d.arc((13,34,51,50),0,180,fill=tx,width=4)
            elif key in ("update","updates"):
                d.arc((12,12,52,52),25,250,fill=ac,width=5);d.polygon([(13,16),(27,14),(18,27)],fill=tx)
            else:
                d.rounded_rectangle((11,11,53,53),radius=12,outline=ac,width=3)
                for x,y in ((22,22),(42,22),(22,42),(42,42)):d.ellipse((x-4,y-4,x+4,y+4),fill=ac if (x+y)%4 else tx)
            img=ctk.CTkImage(light_image=im,dark_image=im,size=(int(size),int(size)))
            cache[ck]=img
            if len(cache)>180:
                for old in list(cache)[:-120]:cache.pop(old,None)
            return img
        except Exception:
            return None''')

s=replace_method(s,'_section_card','''def _section_card(self,parent,title,description=""):
        t=TEMAS[self.tema_atual];st=self._theme_style();radius=max(14,st["card_radius"]);border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border);card.pack(fill="x",padx=6,pady=8)
        ctk.CTkFrame(card,height=3,fg_color=self._mix_hex(t["card"],t["accent"],.72),corner_radius=2).pack(fill="x",padx=12)
        content=ctk.CTkFrame(card,fg_color="transparent");content.pack(fill="both",expand=True,padx=16,pady=(10,12))
        head=ctk.CTkFrame(content,fg_color=self._mix_hex(t["card"],t.get("icon_bg",t["card_active"]),.62),corner_radius=12,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.18));head.pack(fill="x",pady=(0,6))
        icon=ctk.CTkFrame(head,width=48,height=48,corner_radius=12,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.10),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.46));icon.pack(side="left",padx=(8,10),pady=7);icon.pack_propagate(False)
        text=str(title or "").upper()
        if "ROBLOX" in text:im=self._roblox_logo_ctk(31)
        else:
            key="generic"
            for words,k in ((("FPS","DESEMPENHO","PERFORMANCE"),"performance"),(("CURSOR",),"cursor"),(("FONTE","FONT"),"font"),(("PING","LATÊNCIA","LATENCY","REDE","NETWORK"),"network"),(("UPDATE","ATUALIZA"),"update"),(("CACHE",),"cache"),(("ÁUDIO","AUDIO","MÚSICA","MUSIC","SOUND"),"audio"),(("RESOLU","DISPLAY"),"resolution"),(("BLOX","COMBO","BUILD"),"build")):
                if any(w in text for w in words):key=k;break
            im=self._ui_pictogram_ctk(key,31)
        if im is not None:ctk.CTkLabel(icon,text="",image=im).pack(fill="both",expand=True)
        else:ctk.CTkLabel(icon,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=17,weight="bold")).pack(fill="both",expand=True)
        tw=ctk.CTkFrame(head,fg_color="transparent");tw.pack(side="left",fill="x",expand=True,pady=7);ctk.CTkLabel(tw,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=14,weight="bold"),anchor="w").pack(anchor="w",fill="x")
        if description:
            full=str(description);short=self._ui_compact_copy(full,92);ctk.CTkButton(head,text="i",width=30,height=30,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.35),text_color=t["accent"],command=lambda tt=title,dd=full:messagebox.showinfo(str(tt),str(dd),parent=self)).pack(side="right",padx=10);ctk.CTkLabel(content,text=short,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=8),wraplength=980,justify="left",anchor="w").pack(fill="x",anchor="w",padx=4,pady=(0,3))
        return content''')

s=replace_method(s,'_module_switch','''def _module_switch(self, parent, key, label=None, description=None):
        t=TEMAS[self.tema_atual];st=self._theme_style();data=FLAG_MODULES[key];label=label or (data["pt"] if self.idioma=="pt" else data["en"])
        if description is None:description=data["tooltip_pt"] if self.idioma=="pt" else data["tooltip_en"]
        active=bool(self.module_states.get(key,False));border=t["accent"] if active else self._mix_hex(t["card_active"],t["border"],.34)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=max(13,st["card_radius"]),border_width=1,border_color=border);card.pack(fill="x",padx=8,pady=6)
        row=ctk.CTkFrame(card,fg_color="transparent");row.pack(fill="x",padx=12,pady=9)
        icon_box=ctk.CTkFrame(row,width=56,height=56,corner_radius=14,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.14 if active else .05),border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.50 if active else .20));icon_box.pack(side="left",padx=(0,11));icon_box.pack_propagate(False)
        im=self._ui_pictogram_ctk(key,38)
        if im is not None:ctk.CTkLabel(icon_box,text="",image=im).pack(fill="both",expand=True)
        else:ctk.CTkLabel(icon_box,text=self._module_icon_for_key(key),text_color=t["accent"],font=ctk.CTkFont(size=19,weight="bold")).pack(fill="both",expand=True)
        txt=ctk.CTkFrame(row,fg_color="transparent");txt.pack(side="left",fill="both",expand=True);ctk.CTkLabel(txt,text=label,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"),anchor="w").pack(anchor="w",fill="x")
        full_description=str(description or "");short=self._ui_compact_copy(full_description,72)
        if short:ctk.CTkLabel(txt,text=short,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=8),wraplength=610,justify="left",anchor="w").pack(anchor="w",fill="x",pady=(2,0))
        controls=ctk.CTkFrame(row,fg_color="transparent");controls.pack(side="right",padx=(12,0));ctk.CTkButton(controls,text="i",width=28,height=28,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray"),command=lambda ll=label,dd=full_description:messagebox.showinfo(str(ll),str(dd),parent=self)).pack(side="left",padx=(0,7));state=ctk.CTkLabel(controls,text=("● ON" if active else "○ OFF"),height=27,corner_radius=9,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.12 if active else .0),text_color=t["accent"] if active else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold"));state.pack(side="left",padx=(0,8));sw=ctk.CTkSwitch(controls,text="",width=48,command=lambda k=key:self.evento_switch_modulo(k),progress_color=t["accent"],button_color=t["text"],button_hover_color=t["hover"],fg_color=t["card_active"]);sw.pack(side="left")
        if active:sw.select()
        self.module_switches[key]=sw;self.module_cards[key]=card;return card,sw''')

s=replace_method(s,'_lazy_build_page_cursor','''def _lazy_build_page_cursor(self):
        if "cursor" in getattr(self,"pages",{}):return self.pages.get("cursor")
        t=TEMAS[self.tema_atual];L=self._L;_,body=self._page_shell("cursor","CURSOR",L("Escolha e aplique um cursor para o Roblox.","Choose and apply a cursor for Roblox.","Elige y aplica un cursor para Roblox.","选择并应用 Roblox 光标。","Choisissez et appliquez un curseur pour Roblox."))
        card=self._section_card(body,L("CURSOR DO ROBLOX","ROBLOX CURSOR","CURSOR DE ROBLOX","ROBLOX 光标","CURSEUR ROBLOX"),L("Prévia real, tamanho e ponto ativo no mesmo painel.","Real preview, size and hotspot in one panel.","Vista previa real, tamaño y hotspot en un solo panel.","真实预览、大小和热点集中在同一面板。","Aperçu réel, taille et point actif dans un seul panneau."));self.cursor_card=card
        self.cursor_menu=ctk.CTkOptionMenu(card,values=self.listar_cursor_packs(),command=self.evento_cursor_pack,fg_color=t["card_active"],button_color=t["card_active"],button_hover_color=t["hover"],text_color=t["accent"])
        if self.cursor_pack not in self.listar_cursor_packs():self.cursor_pack="Roblox Padrão"
        self.cursor_menu.set(self.cursor_pack);self.cursor_menu.pack(fill="x",padx=12,pady=(3,8))
        preview=ctk.CTkFrame(card,fg_color=t["card_active"],corner_radius=13,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));preview.pack(fill="x",padx=12,pady=(0,9));self.cursor_preview_label=ctk.CTkLabel(preview,text=L("Carregando…","Loading…","Cargando…","加载中…","Chargement…"),width=112,height=112,text_color=t.get("muted","gray"));self.cursor_preview_label.pack(side="left",padx=10,pady=10);center=ctk.CTkFrame(preview,fg_color="transparent");center.pack(side="left",fill="both",expand=True,padx=(4,12),pady=10);ctk.CTkLabel(center,text=L("PRÉVIA","PREVIEW","VISTA PREVIA","预览","APERÇU"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w")
        size_row=ctk.CTkFrame(center,fg_color="transparent");size_row.pack(fill="x",pady=(10,6));self.cursor_size_slider=ctk.CTkSlider(size_row,from_=8,to=48,number_of_steps=40,command=self.evento_cursor_tamanho,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]);self.cursor_size_slider.set(int(self.cursor_visual_size));self.cursor_size_slider.pack(side="left",fill="x",expand=True,padx=(0,8));self.cursor_size_value=ctk.CTkLabel(size_row,text=f"{int(self.cursor_visual_size)} px",width=58,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"));self.cursor_size_value.pack(side="right");self.cursor_anchor_menu=ctk.CTkOptionMenu(center,values=["Ponta no centro","Ponta no canto"],command=self.evento_cursor_ancora,fg_color=t["card"],button_color=t["card"],text_color=t["accent"],height=30);self.cursor_anchor_menu.set(self.cursor_anchor_mode);self.cursor_anchor_menu.pack(fill="x",pady=(2,0));self.after(40,self._refresh_cursor_preview)
        actions=ctk.CTkFrame(card,fg_color="transparent");actions.pack(fill="x",padx=12,pady=(1,5));ctk.CTkButton(actions,text=L("ABRIR PASTA","OPEN FOLDER","ABRIR CARPETA","打开文件夹","OUVRIR LE DOSSIER"),command=self.abrir_pasta_cursores).pack(side="left",expand=True,fill="x",padx=(0,4));ctk.CTkButton(actions,text=L("IMPORTAR PACK","IMPORT PACK","IMPORTAR PACK","导入光标包","IMPORTER UN PACK"),command=self.importar_cursor_pack_pasta).pack(side="left",expand=True,fill="x",padx=4);self.btn_apply_cursor=ctk.CTkButton(actions,text=L("APLICAR","APPLY","APLICAR","应用","APPLIQUER"),command=self.aplicar_cursor_selecionado,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");self.btn_apply_cursor.pack(side="left",expand=True,fill="x",padx=(4,0));self.btn_restore_cursor=ctk.CTkButton(card,text=L("RESTAURAR CURSOR ORIGINAL","RESTORE ORIGINAL CURSOR","RESTAURAR CURSOR ORIGINAL","恢复原始光标","RESTAURER LE CURSEUR ORIGINAL"),command=self.restaurar_cursor_original,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]);self.btn_restore_cursor.pack(fill="x",padx=12,pady=(2,5));self.lbl_cursor_status=ctk.CTkLabel(card,text="",text_color=t.get("muted","gray"),wraplength=820,justify="left");self.lbl_cursor_status.pack(anchor="w",padx=12,pady=(0,7));return self.pages.get("cursor")''')

s=replace_method(s,'_first_run_audio_start','''def _first_run_audio_start(self):
        try:
            test_mode=bool(_owner_test_profile_enabled()) and self._first_run_stage()!="done"
            if bool(getattr(self,"sound_prompted",False)) and not test_mode:
                if bool(getattr(self,"sounds_enabled",False)):self._start_ambient_if_enabled()
                return
            if not bool(getattr(self,"first_run_intro_audio",True)):return
            mgr=getattr(self,"_sound_manager",None)
            if mgr is None:return
            mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK);mgr.enabled=True;mgr.music_enabled=True;mgr.sfx_enabled=True;mgr.music_volume=min(.18,max(.08,float(getattr(self,"music_volume",.22) or .22)))
            if not bool(getattr(self,"_first_run_intro_active",False)):mgr.start_music(force_restart=True);self._first_run_intro_active=True
        except Exception as exc:_startup_log("FIRST RUN AUDIO start: "+repr(exc))''')

s=replace_method(s,'_first_run_audio_event','''def _first_run_audio_event(self,name="select"):
        try:
            test_mode=bool(_owner_test_profile_enabled()) and self._first_run_stage()!="done"
            if bool(getattr(self,"sound_prompted",False)) and not test_mode:return self._play_ui_sound(name,0)
            if not bool(getattr(self,"first_run_intro_audio",True)):return
            self._first_run_audio_start();mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:mgr.enabled=True;mgr.sfx_enabled=True;mgr.play(name,throttle=0)
        except Exception:pass''')

s=replace_method(s,'_global_click_sound','''def _global_click_sound(self,event=None):
        try:test_intro=bool(getattr(self,"first_run_intro_audio",True)) and self._first_run_stage()!="done"
        except Exception:test_intro=False
        if not bool(getattr(self,"sounds_enabled",False)) and not test_intro:return
        try:
            w=getattr(event,"widget",None);cur=w;kind="";label=""
            for _ in range(6):
                if cur is None:break
                name=cur.__class__.__name__
                if name in ("CTkButton","CTkSwitch","CTkCheckBox","CTkRadioButton","CTkSegmentedButton","CTkOptionMenu","CTkComboBox"):
                    kind=name
                    try:label=str(cur.cget("text") or "").upper()
                    except Exception:label=""
                    break
                cur=getattr(cur,"master",None)
            if not kind:return
            if kind in ("CTkSwitch","CTkCheckBox","CTkRadioButton"):snd="toggle_on"
            elif any(k in label for k in ("VOLTAR","BACK","CANCEL","FECHAR","CLOSE","NÃO","NO")):snd="back"
            elif any(k in label for k in ("APLICAR","APPLY","ATIVAR","ENABLE","SALVAR","SAVE","CONFIRM","SIM","YES")):snd="confirm"
            elif any(k in label for k in ("TEMA","THEME","ATMOSFERA","PERSONALIZAR","CUSTOMIZE")):snd="theme"
            elif any(k in label for k in ("INÍCIO","HOME","FPS","PING","REDE","NETWORK","RESOLUÇÃO","RESOLUTION","CURSOR","FONTES","FONTS","COMBO","ZK AI","ÁUDIO","AUDIO","DESEMPENHO","PERFORMANCE","RECUPERAÇÃO","RECOVERY","ATUALIZAÇÕES","UPDATES","SUGESTÕES","BUGS","APOIAR","SUPPORT")):snd="nav"
            else:snd="click"
            if test_intro and not bool(getattr(self,"sounds_enabled",False)):self._first_run_audio_event(snd)
            else:self._play_ui_sound(snd,.025)
        except Exception:pass''')

s=replace_method(s,'_owner_prepare_test_profile','''def _owner_prepare_test_profile(self,stage="language"):
        if not self._owner_key_valid():return
        if not messagebox.askyesno("FIRST RUN LAB",self._L("Abrir um PERFIL DE TESTE isolado neste cenário? Seu perfil principal não será alterado.","Open an isolated TEST PROFILE in this scenario? Your main profile will not be changed.","¿Abrir un PERFIL DE PRUEBA aislado en este escenario? Tu perfil principal no se modificará.","要在此场景打开隔离的测试资料吗？主资料不会被修改。","Ouvrir un PROFIL DE TEST isolé dans ce scénario ? Votre profil principal ne sera pas modifié."),parent=self):return
        try:
            test=self._owner_test_profile_dir();shutil.rmtree(test,ignore_errors=True);os.makedirs(test,exist_ok=True);cfg={"version":APP_VERSION,"language":"pt","language_selected":False,"language_picker_revision":0,"tutorial_completed":False,"sound_prompted":False,"sounds_enabled":False,"first_run_intro_audio":True,"music_enabled":True,"sfx_enabled":True,"sound_pack":DEFAULT_AUDIO_PACK,"modules":{},"advanced_values":{},"combo_entries":[]}
            if stage in ("roblox","tutorial","setup","no_profile","skipped","no_roblox"):cfg.update({"language_selected":True,"language_picker_revision":6})
            if stage in ("tutorial","setup","no_profile","skipped","no_roblox"):cfg.update({"roblox_onboarding_completed":True,"onboarding_username":"OwnerTest"})
            if stage in ("setup","no_profile","no_roblox"):cfg["tutorial_completed"]=True
            if stage in ("no_profile","no_roblox"):cfg["first_run_setup_completed"]=True;cfg["first_run_setup_choice"]="standard";cfg["linked_profile"]={}
            if stage=="skipped":cfg["tutorial_completed"]=True;cfg["first_run_setup_completed"]=False
            with open(os.path.join(test,"config.json"),"w",encoding="utf-8") as f:json.dump(cfg,f,indent=2,ensure_ascii=False)
            st=self._owner_state_load();st["test_profile"]=True;st["simulate_no_roblox"]=(stage=="no_roblox");st["first_run_stage"]=stage;self._owner_state=st;self._owner_state_save();self._owner_restart()
        except Exception as exc:messagebox.showerror("FIRST RUN LAB",str(exc),parent=self)''')

s=replace_method(s,'_start_ambient_if_enabled','''def _start_ambient_if_enabled(self):
        try:
            if bool(getattr(self,"_spotify_internal_music_suppressed",False)):return
            if bool(getattr(self,"sounds_enabled",False)) and bool(getattr(self,"sound_prompted",False)) and bool(getattr(self,"music_enabled",True)):
                mgr=getattr(self,"_sound_manager",None)
                if mgr is not None:mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK);mgr.enabled=True;mgr.music_enabled=True;mgr.music_volume=float(getattr(self,"music_volume",0.22));mgr.start_music()
        except Exception as exc:_startup_log("AUDIO: ambient start exception "+repr(exc))''')

s=insert_method_after(s,'_start_ambient_if_enabled','_spotify_sync_internal_music','''def _spotify_sync_internal_music(self, spotify_playing=None):
        """Pause only ZKStrap background music while Spotify is actively playing; keep user preference unchanged."""
        try:
            if spotify_playing is None:
                snap=dict(getattr(self,"_spotify_current",{}) or {});spotify_playing=bool(snap.get("ok")) and "PLAYING" in str(snap.get("status") or "").upper()
            playing=bool(spotify_playing);mgr=getattr(self,"_sound_manager",None);was=bool(getattr(self,"_spotify_internal_music_suppressed",False));self._spotify_internal_music_suppressed=playing
            if playing:
                if mgr is not None:mgr.stop_music()
                return True
            if was and bool(getattr(self,"music_enabled",True)) and bool(getattr(self,"sounds_enabled",False)) and bool(getattr(self,"sound_prompted",False)):
                try:self.after(120,self._start_ambient_if_enabled)
                except Exception:self._start_ambient_if_enabled()
            return False
        except Exception:return False''')

s=replace_method(s,'_spotify_apply_snapshot','''def _spotify_apply_snapshot(self,snap):
        self._spotify_current=dict(snap or {});ok=bool(snap.get("ok"))
        if ok:
            title=str(snap.get("title") or "Spotify");artist=str(snap.get("artist") or "Artista não informado");album=str(snap.get("album") or "");source=self._spotify_source_name(snap.get("source"));playing="PLAYING" in str(snap.get("status") or "").upper();self._spotify_sync_internal_music(playing);pos=float(snap.get("position") or 0);dur=float(snap.get("duration") or 0);self._spotify_set_status(("tocando" if playing else "pausado")+f" • {source}","ok")
            try:self.spotify_source_label.configure(text=("● TOCANDO  •  " if playing else "Ⅱ PAUSADO  •  ")+source.upper())
            except Exception:pass
            try:self.spotify_title_label.configure(text=title)
            except Exception:pass
            try:self.spotify_artist_label.configure(text=artist)
            except Exception:pass
            try:self.spotify_album_label.configure(text=("ÁLBUM  •  "+album) if album else "")
            except Exception:pass
            try:self.spotify_progress.set(max(0.0,min(1.0,pos/dur if dur>0 else 0.0)))
            except Exception:pass
            try:self.spotify_time_label.configure(text=self._spotify_format_time(pos));self.spotify_duration_label.configure(text=self._spotify_format_time(dur))
            except Exception:pass
            try:
                art=self._spotify_make_art(snap.get("art") or b"",132);self._spotify_art_ctk=art;self.spotify_art_label.configure(image=art,text="" if art else "♫")
            except Exception:pass
            try:
                if getattr(self,"spotify_now_label",None):self.spotify_now_label.configure(text=f"Alvo: {source}  •  {title} — {artist}  •  backend {snap.get('backend','WinRT')}")
            except Exception:pass
            try:
                if self._spotify_mini_frame and self._spotify_mini_frame.winfo_exists():
                    self._spotify_mini_title.configure(text=title);self._spotify_mini_artist.configure(text=artist);mart=self._spotify_make_art(snap.get("art") or b"",86);self._spotify_mini_art_ctk=mart
                    if getattr(self,"_spotify_mini_art_label",None):self._spotify_mini_art_label.configure(image=mart,text="" if mart else "♫")
            except Exception:pass
            try:
                now=time.monotonic()
                if now-float(getattr(self,"_spotify_last_volume_probe",0.0))>4.5:self._spotify_last_volume_probe=now;self._spotify_volume_async("read",None,True)
            except Exception:pass
        else:
            self._spotify_sync_internal_music(False);reason=str(snap.get("reason") or "");error=str(snap.get("error") or "").strip()
            if reason=="browser_ambiguous":self._spotify_set_status("mídia do navegador detectada, mas não é possível provar que é Spotify Web; controles bloqueados para não pausar YouTube","warning")
            elif reason=="no_spotify_session":self._spotify_set_status("Spotify não encontrado nas sessões do Windows; YouTube e outros players serão ignorados","warning");detail="Dê play uma vez no Spotify Desktop/Web. Depois ele pode ficar pausado que o ZKStrap continua mirando a sessão dele."
            elif reason=="not_windows":self._spotify_set_status("Now Playing disponível somente no Windows","warning");detail=""
            else:self._spotify_set_status("falha no leitor do Spotify/Windows; veja o diagnóstico abaixo","error");detail=error or "Sessão não disponível."
            try:self.spotify_source_label.configure(text="SPOTIFY // SESSÃO ALVO")
            except Exception:pass
            try:self.spotify_title_label.configure(text="Spotify não detectado")
            except Exception:pass
            try:self.spotify_artist_label.configure(text="Use Spotify Desktop para controle 100% exclusivo. No navegador, sessões ambíguas são bloqueadas.")
            except Exception:pass
            try:self.spotify_album_label.configure(text="")
            except Exception:pass
            try:self.spotify_progress.set(0);self.spotify_time_label.configure(text="0:00");self.spotify_duration_label.configure(text="0:00")
            except Exception:pass
            try:self.spotify_art_label.configure(image=None,text="♫");self._spotify_art_ctk=None
            except Exception:pass
            try:
                if getattr(self,"spotify_now_label",None):self.spotify_now_label.configure(text=("Diagnóstico: "+detail) if detail else "")
            except Exception:pass''')

s=replace_method(s,'spotify_disconnect','''def spotify_disconnect(self):
        self.spotify_auth={};self.spotify_client_id="";self._spotify_current={};self._spotify_sync_internal_music(False);self._spotify_set_status("nenhuma conta fica conectada nesta versão","ok")''')

s=replace_method(s,'_audio_select_pack','''def _audio_select_pack(self, pack):
        if pack not in AUDIO_PACKS:return
        self.sound_pack=pack;self.sounds_enabled=True;self.sound_prompted=True;mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:mgr.enabled=True;mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True));mgr.music_enabled=bool(getattr(self,"music_enabled",True));mgr.music_volume=float(getattr(self,"music_volume",0.22));mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0));mgr.set_pack(pack);mgr.play("theme",0)
        self._spotify_sync_internal_music(None);self.salvar_config_app();self._refresh_sound_button()
        try:self.audio_current_label.configure(text=self._L(f"IDENTIDADE ATIVA  //  {pack}",f"ACTIVE IDENTITY  //  {pack}",f"IDENTIDAD ACTIVA  //  {pack}",f"当前身份  //  {pack}",f"IDENTITÉ ACTIVE  //  {pack}"))
        except Exception:pass
        try:
            for name,btn in getattr(self,"audio_pack_buttons",{}).items():
                tt=TEMAS[self.tema_atual];active=(name==pack);btn.configure(text=(self._L("ATIVO ✓","ACTIVE ✓","ACTIVO ✓","已启用 ✓","ACTIF ✓") if active else self._L("USAR","USE","USAR","使用","UTILISER")),fg_color=tt["accent"] if active else tt["card_active"],text_color="#050505" if active else tt["text"])
        except Exception:pass''')

s=replace_method(s,'_audio_toggle_music','''def _audio_toggle_music(self):
        try:self.music_enabled=bool(self.audio_music_switch.get())
        except Exception:self.music_enabled=not bool(getattr(self,"music_enabled",True))
        self.sounds_enabled=True;self.sound_prompted=True;mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:mgr.enabled=True;mgr.set_music_enabled(self.music_enabled)
        self._spotify_sync_internal_music(None);self.salvar_config_app();self._refresh_sound_button()''')

s=replace_method(s,'_audio_master_toggle','''def _audio_master_toggle(self):
        self.sounds_enabled=not bool(getattr(self,"sounds_enabled",False));self.sound_prompted=True;mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK);mgr.music_enabled=bool(getattr(self,"music_enabled",True));mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True));mgr.music_volume=float(getattr(self,"music_volume",0.22));mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0));mgr.set_enabled(self.sounds_enabled)
        self._spotify_sync_internal_music(None);self.salvar_config_app();self._refresh_sound_button()
        try:self.audio_master_button.configure(text=self._L("DESATIVAR ÁUDIO","DISABLE AUDIO","DESACTIVAR AUDIO","关闭音频","DÉSACTIVER L'AUDIO") if self.sounds_enabled else self._L("ATIVAR ÁUDIO","ENABLE AUDIO","ACTIVAR AUDIO","启用音频","ACTIVER L'AUDIO"))
        except Exception:pass''')

s=replace_method(s,'_lazy_build_page_audio','''def _lazy_build_page_audio(self):
        if "audio" in getattr(self,"pages",{}):return self.pages.get("audio")
        t=TEMAS[self.tema_atual];L=self._L;_,abody=self._page_shell("audio",L("ÁUDIO // SOUND STUDIO","AUDIO // SOUND STUDIO","AUDIO // SOUND STUDIO","音频 // SOUND STUDIO","AUDIO // SOUND STUDIO"),L("Nove identidades sonoras escolhidas para o ZKStrap.","Nine selected sound identities for ZKStrap.","Nueve identidades sonoras elegidas para ZKStrap.","ZKStrap 精选的九种声音身份。","Neuf identités sonores sélectionnées pour ZKStrap."))
        hero=self._section_card(abody,"ZK AUDIO ENGINE",L("Música e SFX no mesmo estilo. Ao tocar Spotify, a música do ZKStrap pausa sozinha.","Music and SFX share one identity. While Spotify plays, ZKStrap music pauses automatically.","Música y SFX comparten una identidad. Si Spotify reproduce, la música de ZKStrap se pausa sola.","音乐与 SFX 使用同一身份；Spotify 播放时 ZKStrap 音乐会自动暂停。","Musique et SFX partagent une identité. Quand Spotify joue, la musique ZKStrap se met en pause."));self.audio_current_label=ctk.CTkLabel(hero,text=L(f"IDENTIDADE ATIVA  //  {self.sound_pack}",f"ACTIVE IDENTITY  //  {self.sound_pack}",f"IDENTIDAD ACTIVA  //  {self.sound_pack}",f"当前身份  //  {self.sound_pack}",f"IDENTITÉ ACTIVE  //  {self.sound_pack}"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"),anchor="w");self.audio_current_label.pack(fill="x",padx=14,pady=(3,8))
        togg=ctk.CTkFrame(hero,fg_color="transparent");togg.pack(fill="x",padx=14,pady=(0,7));self.audio_master_button=ctk.CTkButton(togg,text=L("ÁUDIO ATIVO","AUDIO ON","AUDIO ACTIVO","音频开启","AUDIO ACTIF") if self.sounds_enabled else L("ATIVAR ÁUDIO","ENABLE AUDIO","ACTIVAR AUDIO","启用音频","ACTIVER L'AUDIO"),command=self._audio_master_toggle,fg_color=t["accent"] if self.sounds_enabled else t["card_active"],hover_color=t["hover"],text_color="#050505" if self.sounds_enabled else t["text"]);self.audio_master_button.pack(side="left",expand=True,fill="x",padx=(0,4));ctk.CTkButton(togg,text=L("OUVIR IDENTIDADE","HEAR IDENTITY","ESCUCHAR IDENTIDAD","试听身份","ÉCOUTER L'IDENTITÉ"),command=self._audio_demo_theme,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",expand=True,fill="x",padx=(4,0))
        switches=ctk.CTkFrame(hero,fg_color="transparent");switches.pack(fill="x",padx=14,pady=(1,7));self.audio_music_switch=ctk.CTkSwitch(switches,text=L("MÚSICA","MUSIC","MÚSICA","音乐","MUSIQUE"),command=self._audio_toggle_music,progress_color=t["accent"],fg_color=t["card_active"],text_color=t["text"]);self.audio_music_switch.pack(side="left",padx=(0,22));self.audio_sfx_switch=ctk.CTkSwitch(switches,text="SFX",command=self._audio_toggle_sfx,progress_color=t["accent"],fg_color=t["card_active"],text_color=t["text"]);self.audio_sfx_switch.pack(side="left")
        if self.music_enabled:self.audio_music_switch.select()
        if self.sfx_enabled:self.audio_sfx_switch.select()
        mrow=ctk.CTkFrame(hero,fg_color="transparent");mrow.pack(fill="x",padx=14,pady=(2,6));ctk.CTkLabel(mrow,text=L("MÚSICA","MUSIC","MÚSICA","音乐","MUSIQUE"),text_color=t.get("muted","gray"),width=80,anchor="w").pack(side="left");self.audio_music_volume_slider=ctk.CTkSlider(mrow,from_=0,to=.65,number_of_steps=65,command=self._audio_music_volume_preview,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]);self.audio_music_volume_slider.pack(side="left",fill="x",expand=True,padx=(6,8));self.audio_music_volume_slider.set(float(self.music_volume));self.audio_music_volume_label=ctk.CTkLabel(mrow,text=f"{int(self.music_volume*100)}%",text_color=t["accent"],width=42);self.audio_music_volume_label.pack(side="right");self.audio_music_volume_slider.bind("<ButtonRelease-1>",self._audio_music_volume_apply)
        srow=ctk.CTkFrame(hero,fg_color="transparent");srow.pack(fill="x",padx=14,pady=(2,10));ctk.CTkLabel(srow,text="SFX",text_color=t.get("muted","gray"),width=80,anchor="w").pack(side="left");self.audio_sfx_volume_slider=ctk.CTkSlider(srow,from_=0,to=1.5,number_of_steps=75,command=self._audio_sfx_volume_preview,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]);self.audio_sfx_volume_slider.pack(side="left",fill="x",expand=True,padx=(6,8));self.audio_sfx_volume_slider.set(float(self.sfx_volume));self.audio_sfx_volume_label=ctk.CTkLabel(srow,text=f"{int(self.sfx_volume*100)}%",text_color=t["accent"],width=42);self.audio_sfx_volume_label.pack(side="right");self.audio_sfx_volume_slider.bind("<ButtonRelease-1>",self._audio_sfx_volume_apply)
        packs=self._section_card(abody,L("9 IDENTIDADES","9 IDENTITIES","9 IDENTIDADES","9 种身份","9 IDENTITÉS"),L("Escolha pela vibe; os detalhes ficam no botão de informação.","Choose by vibe; details stay behind the info button.","Elige por la vibra; los detalles quedan en el botón de información.","按氛围选择；详细信息放在信息按钮中。","Choisissez selon l'ambiance ; les détails restent dans le bouton d'information."));grid=ctk.CTkFrame(packs,fg_color="transparent");grid.pack(fill="x",padx=6,pady=(2,10));self.audio_pack_buttons={}
        for col in range(3):grid.grid_columnconfigure(col,weight=1,uniform="aud")
        for i,(name,meta) in enumerate(AUDIO_PACKS.items()):
            sel=name==self.sound_pack;card=ctk.CTkFrame(grid,fg_color=t["card"],corner_radius=13,border_width=2 if sel else 1,border_color=t["accent"] if sel else t["card_active"]);card.grid(row=i//3,column=i%3,sticky="nsew",padx=5,pady=5);top=ctk.CTkFrame(card,fg_color="transparent");top.pack(fill="x",padx=10,pady=(10,5));art=self._ui_pictogram_ctk("audio:"+name,42);ctk.CTkLabel(top,text="",image=art,width=48,height=48).pack(side="left",padx=(0,8));tt=ctk.CTkFrame(top,fg_color="transparent");tt.pack(side="left",fill="x",expand=True);ctk.CTkLabel(tt,text=name,text_color=t["text"],font=ctk.CTkFont(size=10,weight="bold"),anchor="w").pack(fill="x");ctk.CTkLabel(tt,text=f"{meta.get('genre','')}  •  {meta.get('bpm','?')} BPM",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7),anchor="w").pack(fill="x",pady=(2,0));ctk.CTkButton(top,text="i",width=26,height=26,corner_radius=8,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=t["card_active"],text_color=t["accent"],command=lambda n=name,m=meta:messagebox.showinfo(n,str(m.get("desc","")),parent=self)).pack(side="right",padx=(5,0));b=ctk.CTkButton(card,text=L("ATIVO ✓","ACTIVE ✓","ACTIVO ✓","已启用 ✓","ACTIF ✓") if sel else L("USAR","USE","USAR","使用","UTILISER"),height=32,command=lambda n=name:self._audio_select_pack(n),fg_color=t["accent"] if sel else t["card_active"],hover_color=t["hover"],text_color="#050505" if sel else t["text"]);b.pack(fill="x",padx=9,pady=(0,9));self.audio_pack_buttons[name]=b
        return self.pages.get("audio")''')

s=replace_method(s,'_v3214_bootstrap_state','''def _v3214_bootstrap_state(self):
        cfg=dict(getattr(self,"config_data",{}) or {})
        try:
            current=_normalize_audio_pack(getattr(self,"sound_pack",cfg.get("sound_pack",DEFAULT_AUDIO_PACK)));self.sound_pack=current;self.config_data["sound_pack"]=current;mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:mgr.pack=current
        except Exception:pass
        if not hasattr(self,"auto_cache_cleanup_enabled"):self.auto_cache_cleanup_enabled=bool(cfg.get("auto_cache_cleanup_enabled",False))
        if not hasattr(self,"auto_cache_cleanup_threshold_mb"):
            try:self.auto_cache_cleanup_threshold_mb=max(100,min(4096,int(cfg.get("auto_cache_cleanup_threshold_mb",512) or 512)))
            except Exception:self.auto_cache_cleanup_threshold_mb=512
        if not hasattr(self,"last_cache_cleanup_version"):self.last_cache_cleanup_version=str(cfg.get("last_cache_cleanup_version","") or "")
        if not hasattr(self,"last_roblox_update_detected"):self.last_roblox_update_detected=str(cfg.get("last_roblox_update_detected","") or "")
        if not hasattr(self,"notification_history"):self.notification_history=list(cfg.get("notification_history",[]) if isinstance(cfg.get("notification_history",[]),list) else [])[-60:]
        try:
            old=str(getattr(self,"cursor_pack","") or "")
            if "animad" in old.casefold() or "animated" in old.casefold():self.cursor_pack="Roblox Padrão"
            self.cursor_overlay_enabled=False;self.config_data["cursor_overlay_enabled"]=False;stop=getattr(self,"_cursor_overlay_stop",None)
            if callable(stop):stop(persist=False)
        except Exception:pass
        return True''')

ast.parse(s)
p.write_text(s,encoding='utf-8',newline='\n')
print('content-pass',p,'sha256',hashlib.sha256(p.read_bytes()).hexdigest())
