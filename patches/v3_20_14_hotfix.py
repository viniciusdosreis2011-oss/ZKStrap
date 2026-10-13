from pathlib import Path
import ast, os, textwrap, hashlib
root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')

def replace_method(src,name,body):
    t=ast.parse(src);cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit(f'hotfix method missing: {name}')
    lines=src.splitlines(True);start=sum(len(x) for x in lines[:node.lineno-1]);end=sum(len(x) for x in lines[:node.end_lineno])
    raw=body.strip().splitlines();norm=[raw[0]]+[(line[4:] if line.startswith('    ') else line) for line in raw[1:]]
    code=textwrap.indent('\n'.join(norm)+'\n','    ')
    return src[:start]+code+src[end:]

s=replace_method(s,'_install_global_scroll_router','''def _install_global_scroll_router(self):
        """Single wheel router for main pages plus Owner/Compact auxiliary windows."""
        try:self.unbind_all("<MouseWheel>")
        except Exception:pass
        try:self.unbind_all("<Button-4>");self.unbind_all("<Button-5>")
        except Exception:pass
        def inside_aux(widget,sc):
            try:
                if self._scroll_is_descendant(widget,sc):return True
                host=getattr(sc,"_zk_host",None);canvas=getattr(sc,"_parent_canvas",None)
                return (host is not None and self._scroll_is_descendant(widget,host)) or widget is canvas
            except Exception:return False
        def route(event):
            if self._scroll_widget_chain_has(getattr(event,"widget",None),("slider","scrollbar","combobox","spinbox")):return None
            widget=getattr(event,"widget",None);target=None
            clean=[]
            for sc in list(getattr(self,"_aux_scroll_targets",[]) or []):
                try:
                    if sc is None or not sc.winfo_exists():continue
                    clean.append(sc)
                    if target is None and inside_aux(widget,sc):target=sc
                except Exception:continue
            self._aux_scroll_targets=clean
            if target is None:
                nav=getattr(self,"nav_scroll",None)
                if nav is not None and self._scroll_is_descendant(widget,nav):target=nav
                else:
                    key=str(getattr(self,"current_page_key","") or "");body=getattr(self,"page_scrolls",{}).get(key);host=getattr(self,"content_host",None)
                    if body is not None and (self._scroll_is_descendant(widget,body) or (host is not None and self._scroll_is_descendant(widget,host))):target=body
            if target is None:return None
            delta=getattr(event,"delta",0)
            if delta:
                notches=max(1,min(5,int(round(abs(float(delta))/120.0)) or 1));return self._queue_scroll_step(target,(-1 if delta>0 else 1)*notches)
            num=getattr(event,"num",0)
            if num in (4,5):return self._queue_scroll_step(target,-1 if num==4 else 1)
            return None
        try:self.bind_all("<MouseWheel>",route,add=False)
        except Exception:pass
        try:self.bind_all("<Button-4>",route,add=False);self.bind_all("<Button-5>",route,add=False)
        except Exception:pass''')
s=replace_method(s,'_install_smooth_scroll','''def _install_smooth_scroll(self, scrollable, units=1):
        """Register regular page scroll or an auxiliary Toplevel scroll target."""
        try:
            setattr(scrollable,"_zk_scroll_units",max(1,int(units)))
            try:
                top=scrollable.winfo_toplevel()
                if top is not self:
                    reg=list(getattr(self,"_aux_scroll_targets",[]) or [])
                    if scrollable not in reg:reg.append(scrollable)
                    self._aux_scroll_targets=reg
            except Exception:pass
            self.after_idle(self._install_global_scroll_router)
        except Exception:pass''')
s=replace_method(s,'_roblox_logo_ctk','''def _roblox_logo_ctk(self,size=44,theme=None):
        """Official Roblox Tilt asset from Roblox's press-kit; never redraw it by hand."""
        try:
            from PIL import Image
            black=_resource_path("zkstrap_assets","roblox_tilt_black.png")
            white=_resource_path("zkstrap_assets","roblox_tilt_white.png")
            if os.path.isfile(black) and os.path.isfile(white):
                light=Image.open(black).convert("RGBA");dark=Image.open(white).convert("RGBA")
                img=ctk.CTkImage(light_image=light,dark_image=dark,size=(int(size),int(size)))
                if not hasattr(self,"_v3214_roblox_logo_refs"):self._v3214_roblox_logo_refs=[]
                self._v3214_roblox_logo_refs.append(img);self._v3214_roblox_logo_refs=self._v3214_roblox_logo_refs[-24:]
                return img
        except Exception:pass
        return None''')
s=replace_method(s,'_v3214_bootstrap_state','''def _v3214_bootstrap_state(self):
        cfg=dict(getattr(self,"config_data",{}) or {})
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
            self.cursor_overlay_enabled=False;self.config_data["cursor_overlay_enabled"]=False
            stop=getattr(self,"_cursor_overlay_stop",None)
            if callable(stop):stop(persist=False)
        except Exception:pass
        return True''')
s=replace_method(s,'_lazy_build_page_cursor','''def _lazy_build_page_cursor(self):
        if "cursor" in getattr(self,"pages",{}):return self.pages.get("cursor")
        t=TEMAS[self.tema_atual];L=self._L
        _,body=self._page_shell("cursor","CURSOR",L("Escolha, visualize e aplique o cursor do Roblox.","Choose, preview and apply the Roblox cursor.","Elige, previsualiza y aplica el cursor de Roblox.","选择、预览并应用 Roblox 光标。","Choisissez, prévisualisez et appliquez le curseur Roblox."))
        cursor_card=self._section_card(body,L("CURSOR DO ROBLOX","ROBLOX CURSOR","CURSOR DE ROBLOX","ROBLOX 光标","CURSEUR ROBLOX"),L("Use packs estáticos com prévia real antes de aplicar.","Use static packs with a real preview before applying.","Usa packs estáticos con vista previa real antes de aplicar.","使用静态光标包，并在应用前查看真实预览。","Utilisez des packs statiques avec un aperçu réel avant application."));self.cursor_card=cursor_card
        self.cursor_menu=ctk.CTkOptionMenu(cursor_card,values=self.listar_cursor_packs(),command=self.evento_cursor_pack,fg_color=t["card_active"],button_color=t["card_active"],button_hover_color=t["hover"],text_color=t["accent"])
        if self.cursor_pack not in self.listar_cursor_packs():self.cursor_pack="Roblox Padrão"
        self.cursor_menu.set(self.cursor_pack);self.cursor_menu.pack(fill="x",padx=16,pady=(4,8))
        preview_row=ctk.CTkFrame(cursor_card,fg_color=t["card_active"],corner_radius=13,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));preview_row.pack(fill="x",padx=16,pady=(2,10));self.cursor_preview_label=ctk.CTkLabel(preview_row,text=L("Carregando…","Loading…","Cargando…","加载中…","Chargement…"),width=138,height=138,text_color=t.get("muted","gray"));self.cursor_preview_label.pack(side="left",padx=12,pady=12);ptxt=ctk.CTkFrame(preview_row,fg_color="transparent");ptxt.pack(side="left",fill="both",expand=True,padx=(4,14),pady=12);ctk.CTkLabel(ptxt,text=L("PRÉVIA DO CURSOR","CURSOR PREVIEW","VISTA PREVIA DEL CURSOR","光标预览","APERÇU DU CURSEUR"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w");ctk.CTkLabel(ptxt,text=L("Este é o pack que será aplicado ao Roblox.","This is the pack that will be applied to Roblox.","Este es el pack que se aplicará a Roblox.","这是将应用到 Roblox 的光标包。","C'est le pack qui sera appliqué à Roblox."),text_color=t.get("muted","gray"),wraplength=540,justify="left").pack(anchor="w",fill="x",pady=(5,0));self.after(40,self._refresh_cursor_preview)
        size=self._section_card(body,L("TAMANHO E HOTSPOT","SIZE & HOTSPOT","TAMAÑO Y HOTSPOT","大小与热点","TAILLE ET HOTSPOT"),L("Ajuste o tamanho visual e o ponto ativo do cursor.","Adjust cursor visual size and hotspot.","Ajusta el tamaño visual y el punto activo del cursor.","调整光标视觉大小和热点。","Réglez la taille visuelle et le point actif du curseur."));row=ctk.CTkFrame(size,fg_color="transparent");row.pack(fill="x",padx=16,pady=(4,8));self.cursor_size_value=ctk.CTkLabel(row,text=f"{int(self.cursor_visual_size)} px",width=70,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"));self.cursor_size_value.pack(side="right");self.cursor_size_slider=ctk.CTkSlider(row,from_=8,to=48,number_of_steps=40,command=self.evento_cursor_tamanho,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]);self.cursor_size_slider.set(int(self.cursor_visual_size));self.cursor_size_slider.pack(side="left",fill="x",expand=True,padx=(0,10));self.cursor_anchor_menu=ctk.CTkOptionMenu(size,values=["Ponta no centro","Ponta no canto"],command=self.evento_cursor_ancora,fg_color=t["card_active"],button_color=t["card_active"],text_color=t["accent"]);self.cursor_anchor_menu.set(self.cursor_anchor_mode);self.cursor_anchor_menu.pack(fill="x",padx=16,pady=(2,10))
        r=ctk.CTkFrame(cursor_card,fg_color="transparent");r.pack(fill="x",padx=16,pady=(2,6));ctk.CTkButton(r,text=L("ABRIR PASTA","OPEN FOLDER","ABRIR CARPETA","打开文件夹","OUVRIR LE DOSSIER"),command=self.abrir_pasta_cursores).pack(side="left",expand=True,fill="x",padx=(0,4));ctk.CTkButton(r,text=L("IMPORTAR PACK","IMPORT PACK","IMPORTAR PACK","导入光标包","IMPORTER UN PACK"),command=self.importar_cursor_pack_pasta).pack(side="left",expand=True,fill="x",padx=(4,0));self.btn_apply_cursor=ctk.CTkButton(cursor_card,text=L("APLICAR CURSOR","APPLY CURSOR","APLICAR CURSOR","应用光标","APPLIQUER LE CURSEUR"),command=self.aplicar_cursor_selecionado,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505");self.btn_apply_cursor.pack(fill="x",padx=16,pady=(8,4));self.btn_restore_cursor=ctk.CTkButton(cursor_card,text=L("RESTAURAR ORIGINAL","RESTORE ORIGINAL","RESTAURAR ORIGINAL","恢复原版","RESTAURER L’ORIGINAL"),command=self.restaurar_cursor_original,fg_color="transparent",border_width=1,border_color=t["accent"],text_color=t["text"]);self.btn_restore_cursor.pack(fill="x",padx=16,pady=(4,8));self.lbl_cursor_status=ctk.CTkLabel(cursor_card,text="",text_color=t.get("muted","gray"),wraplength=820,justify="left");self.lbl_cursor_status.pack(anchor="w",padx=16,pady=(0,14));return self.pages.get("cursor")''')
s=replace_method(s,'_owner_open_build_editor','''def _owner_open_build_editor(self,pal=None):
        pal=pal or self._owner_admin_palettes()["Owner Violet"];data=dict(self._owner_build_data());L=self._L;win=ctk.CTkToplevel(self);win.title(L("OWNER // Build Blox Fruits","OWNER // Blox Fruits Loadout","OWNER // Build Blox Fruits","OWNER // Blox Fruits 配装","OWNER // Build Blox Fruits"));self._center_child_window(win,980,720);win.minsize(860,620);win.transient(getattr(self,"_owner_panel",self));root=ctk.CTkFrame(win,fg_color=pal["panel"],corner_radius=14,border_width=1,border_color=pal["border"]);root.pack(fill="both",expand=True,padx=12,pady=12);ctk.CTkLabel(root,text=L("EDITAR OWNER LOADOUT","EDIT OWNER LOADOUT","EDITAR LOADOUT OWNER","编辑 OWNER 配装","MODIFIER LE LOADOUT OWNER"),text_color=pal["accent"],font=ctk.CTkFont(size=18,weight="bold")).pack(anchor="w",padx=16,pady=(15,3));ctk.CTkLabel(root,text=L("Escolha uma categoria e pesquise no mesmo catálogo do Combo Planner. Style, Fruit, Sword e Gun ficam separados.","Choose a category and search the same Combo Planner catalog. Style, Fruit, Sword and Gun stay separated.","Elige una categoría y busca en el mismo catálogo del Combo Planner. Style, Fruit, Sword y Gun quedan separados.","选择分类并搜索 Combo Planner 同一目录。Style、Fruit、Sword 和 Gun 分开显示。","Choisissez une catégorie et recherchez dans le même catalogue que Combo Planner. Style, Fruit, Sword et Gun restent séparés."),text_color=pal["muted"],wraplength=900,justify="left").pack(anchor="w",padx=16,pady=(0,10))
        active={"cat":"style"};cat_labels={"style":L("ESTILO","STYLE","ESTILO","战斗风格","STYLE"),"fruit":L("FRUTA","FRUIT","FRUTA","果实","FRUIT"),"sword":L("ESPADA","SWORD","ESPADA","剑","ÉPÉE"),"gun":"GUN"};buttons={}
        cats=ctk.CTkFrame(root,fg_color="transparent");cats.pack(fill="x",padx=14,pady=(2,6))
        top=ctk.CTkFrame(root,fg_color="transparent");top.pack(fill="x",padx=14,pady=(2,8));search=ctk.CTkEntry(top,placeholder_text=L("Pesquisar na categoria selecionada...","Search selected category...","Buscar en la categoría seleccionada...","搜索当前分类...","Rechercher dans la catégorie sélectionnée..."),height=42,fg_color=pal["card"],border_color=pal["border"],text_color=pal["text"]);search.pack(fill="x",expand=True)
        sc=ZKSmoothScrollFrame(root,fg_color=pal["bg"],corner_radius=10);sc.pack(fill="both",expand=True,padx=14,pady=4);self._install_smooth_scroll(sc,1);grid=ctk.CTkFrame(sc,fg_color="transparent");grid.pack(fill="x",expand=True)
        def choose(cat,name):
            data[cat]=name;self._owner_save_build(data);render();host=getattr(self,"_owner_build_host",None)
            if host is not None:
                try:self._owner_render_build_cards(host,pal)
                except Exception:pass
        def paint_tabs():
            for cat,b in buttons.items():
                on=cat==active["cat"]
                try:b.configure(fg_color=pal["accent"] if on else pal["card"],text_color="#08080B" if on else pal["text"],border_color=pal["accent"] if on else pal["border"])
                except Exception:pass
        def set_cat(cat):
            active["cat"]=cat;search.delete(0,"end");paint_tabs();render()
        for cat in ("style","fruit","sword","gun"):
            b=ctk.CTkButton(cats,text=cat_labels[cat],command=lambda c=cat:set_cat(c),height=38,fg_color=pal["card"],hover_color=pal["accent2"],text_color=pal["text"],border_width=1,border_color=pal["border"]);b.pack(side="left",expand=True,fill="x",padx=4);buttons[cat]=b
        def render(*_):
            for w in grid.winfo_children():
                try:w.destroy()
                except Exception:pass
            cat=active["cat"];q=search.get().strip().casefold();names=[n for n in self._combo_catalog().get(cat,[]) if not q or q in n.casefold()]
            cols=5 if win.winfo_width()>900 else 4
            for i in range(cols):grid.grid_columnconfigure(i,weight=1,uniform="own")
            if not names:
                ctk.CTkLabel(grid,text=L("Nenhum item encontrado.","No items found.","No se encontraron elementos.","未找到项目。","Aucun élément trouvé."),text_color=pal["muted"]).grid(row=0,column=0,columnspan=cols,pady=30)
                return
            for i,name in enumerate(names):
                sel=data.get(cat)==name;img=self._combo_get_ctk_thumb(cat,name,66,callback=render,allow_network=False);b=ctk.CTkButton(grid,text=name,image=img,compound="top",height=120,fg_color=pal["accent"] if sel else pal["card"],hover_color=pal["accent2"],text_color="#08080B" if sel else pal["text"],border_width=1,border_color=pal["border"],command=lambda c=cat,n=name:choose(c,n));b.grid(row=i//cols,column=i%cols,sticky="nsew",padx=4,pady=4)
            try:self._combo_prefetch_category(cat,names[:35],render)
            except Exception:pass
        search.bind("<KeyRelease>",render);paint_tabs();render();ctk.CTkButton(root,text=L("SALVAR E FECHAR","SAVE & CLOSE","GUARDAR Y CERRAR","保存并关闭","ENREGISTRER ET FERMER"),command=lambda:(self._owner_save_build(data),win.destroy()),fg_color=pal["accent"],hover_color=pal["accent2"],text_color="#08080B",height=42).pack(fill="x",padx=14,pady=(8,14))''')
s=replace_method(s,'abrir_modo_compacto','''def abrir_modo_compacto(self):
        self._v3214_bootstrap_state();t=TEMAS[self.tema_atual];st=self._theme_style();L=self._L
        old=getattr(self,"_compact_window",None)
        try:
            if old is not None and old.winfo_exists():old.lift();return
        except Exception:pass
        win=ctk.CTkToplevel(self);self._compact_window=win;win.title(f"ZKStrap Compact v{APP_VERSION}");self._center_child_window(win,620,790);win.minsize(560,700);win.configure(fg_color=t["bg"])
        try:win.attributes("-topmost",True);win.attributes("-toolwindow",False)
        except Exception:pass
        try:win.iconbitmap(_resource_path("zkstrap_icon.ico"))
        except Exception:pass
        win.after(120,lambda:win.lift())
        try:self.withdraw()
        except Exception:pass
        def close():
            self._compact_window=None
            try:win.destroy();self.deiconify();self.lift()
            except Exception:pass
        def open_full(page):
            close();self.after(30,lambda:self.show_page(page,animate=False))
        win.protocol("WM_DELETE_WINDOW",close)
        shell=ctk.CTkFrame(win,fg_color=t["panel"],corner_radius=st["radius"],border_width=1,border_color=t["border"]);shell.pack(fill="both",expand=True,padx=14,pady=14)
        head=ctk.CTkFrame(shell,fg_color=t["card"],corner_radius=13,border_width=1,border_color=t["card_active"]);head.pack(fill="x",padx=14,pady=(14,7));ctk.CTkLabel(head,text=self._L("ZKSTRAP // COMPACTO","ZKSTRAP // COMPACT","ZKSTRAP // COMPACTO","ZKSTRAP // 紧凑","ZKSTRAP // COMPACT"),text_color=t["text"],font=ctk.CTkFont(size=20,weight="bold")).pack(anchor="w",padx=14,pady=(12,2));ctk.CTkLabel(head,text=L("PAINEL RÁPIDO DO ROBLOX","ROBLOX QUICK DECK","PANEL RÁPIDO DE ROBLOX","ROBLOX 快速面板","PANNEAU RAPIDE ROBLOX"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w",padx=14,pady=(0,10))
        prof=ctk.CTkFrame(shell,fg_color=t["card_active"],corner_radius=12);prof.pack(fill="x",padx=14,pady=7);p=getattr(self,"linked_profile",{}) or {};img=self._load_profile_avatar_ctk(54) if p.get("name") else self._roblox_logo_ctk(50);ctk.CTkLabel(prof,text="",image=img,width=64,height=64).pack(side="left",padx=(12,8),pady=10);ptxt=ctk.CTkFrame(prof,fg_color="transparent");ptxt.pack(side="left",fill="x",expand=True);ctk.CTkLabel(ptxt,text=str(p.get("displayName") or p.get("name") or L("Perfil Roblox","Roblox profile","Perfil Roblox","Roblox 资料","Profil Roblox")),text_color=t["text"],font=ctk.CTkFont(size=13,weight="bold"),anchor="w").pack(fill="x");ctk.CTkLabel(ptxt,text=("@"+str(p.get("name")) if p.get("name") else L("Não vinculado","Not linked","No vinculado","未关联","Non lié")),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8),anchor="w").pack(fill="x",pady=(2,0));ctk.CTkLabel(prof,text=L("ONLINE","ONLINE","EN LÍNEA","在线","EN LIGNE") if self._roblox_esta_aberto() else "OFFLINE",text_color="#58E38C" if self._roblox_esta_aberto() else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="right",padx=12)
        sc=ZKSmoothScrollFrame(shell,fg_color="transparent",corner_radius=0);sc.pack(fill="both",expand=True,padx=8,pady=4);self._install_smooth_scroll(sc,1)
        def title(txt):ctk.CTkLabel(sc,text=txt,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w").pack(fill="x",padx=12,pady=(12,5))
        title(L("CONTROLES RÁPIDOS","QUICK CONTROLS","CONTROLES RÁPIDOS","快速控制","CONTRÔLES RAPIDES"))
        quick=ctk.CTkFrame(sc,fg_color=t["card"],corner_radius=11);quick.pack(fill="x",padx=10,pady=(0,4));vars={"performance_boost":ctk.BooleanVar(value=bool(self.module_states.get("performance_boost",False))),"gray_sky":ctk.BooleanVar(value=bool(self.module_states.get("gray_sky",False))),"reapply":ctk.BooleanVar(value=bool(self.config_watchdog_enabled)),"cache":ctk.BooleanVar(value=bool(self.auto_cache_cleanup_enabled))};rows=[("performance_boost",L("Modo FPS","FPS mode","Modo FPS","FPS 模式","Mode FPS")),("gray_sky",L("Céu cinza","Gray sky","Cielo gris","灰色天空","Ciel gris")),("reapply",L("Reaplicar após updates","Reapply after updates","Reaplicar tras updates","更新后重新应用","Réappliquer après mises à jour")),("cache",L("Limpeza automática de cache","Automatic cache cleanup","Limpieza automática de caché","自动清理缓存","Nettoyage auto du cache"))]
        for key,label in rows:
            row=ctk.CTkFrame(quick,fg_color="transparent");row.pack(fill="x",padx=10,pady=4);ctk.CTkLabel(row,text=label,text_color=t["text"],anchor="w").pack(side="left",fill="x",expand=True);cmd=(lambda k=key,v=vars[key]:self._compact_toggle_v3214(k,v));ctk.CTkSwitch(row,text="",variable=vars[key],command=cmd,progress_color=t["accent"],fg_color=t["card_active"]).pack(side="right")
        title(L("PERSONALIZAÇÃO","PERSONALIZATION","PERSONALIZACIÓN","个性化","PERSONNALISATION"));pers=ctk.CTkFrame(sc,fg_color=t["card"],corner_radius=11);pers.pack(fill="x",padx=10,pady=(0,4));cur=str(getattr(self,"cursor_pack","Roblox Padrão") or "Roblox Padrão");cur="Roblox Padrão" if ("animad" in cur.casefold() or "animated" in cur.casefold()) else cur
        for label,value,page in [(L("Cursor atual","Current cursor","Cursor actual","当前光标","Curseur actuel"),cur,"cursor"),(L("Fonte do Roblox","Roblox font","Fuente de Roblox","Roblox 字体","Police Roblox"),os.path.basename(str(getattr(self,"game_font_source","") or "")) or L("Padrão","Default","Predeterminada","默认","Par défaut"),"fonts")]:
            row=ctk.CTkFrame(pers,fg_color="transparent");row.pack(fill="x",padx=10,pady=5);txt=ctk.CTkFrame(row,fg_color="transparent");txt.pack(side="left",fill="x",expand=True);ctk.CTkLabel(txt,text=label,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x");ctk.CTkLabel(txt,text=value,text_color=t["accent"],font=ctk.CTkFont(size=10,weight="bold"),anchor="w").pack(fill="x");ctk.CTkButton(row,text=L("TROCAR","CHANGE","CAMBIAR","更换","CHANGER"),command=lambda p=page:open_full(p),width=90,fg_color=t["card_active"],text_color=t["text"]).pack(side="right")
        title("ROBLOX");rb=ctk.CTkFrame(sc,fg_color=t["card"],corner_radius=11);rb.pack(fill="x",padx=10,pady=(0,6));changes=self._roblox_change_count();ctk.CTkLabel(rb,text=L(f"{changes} alteração(ões) detectada(s)",f"{changes} detected change(s)",f"{changes} cambio(s) detectado(s)",f"检测到 {changes} 项更改",f"{changes} modification(s) détectée(s)"),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(anchor="w",padx=10,pady=(9,5));b1=ctk.CTkFrame(rb,fg_color="transparent");b1.pack(fill="x",padx=8,pady=3);ctk.CTkButton(b1,text=L("✓ APLICAR","✓ APPLY","✓ APLICAR","✓ 应用","✓ APPLIQUER"),command=self.aplicar_configuracoes,fg_color=t["accent"],text_color="#050505").pack(side="left",expand=True,fill="x",padx=(0,3));ctk.CTkButton(b1,text=L("↶ RESTAURAR","↶ RESTORE","↶ RESTAURAR","↶ 恢复","↶ RESTAURER"),command=self._open_restore_roblox_panel,fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",expand=True,fill="x",padx=(3,0));b2=ctk.CTkFrame(rb,fg_color="transparent");b2.pack(fill="x",padx=8,pady=(3,8));ctk.CTkButton(b2,text="CLIENTSETTINGS",command=self.abrir_pasta_clientsettings,fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(0,3));ctk.CTkButton(b2,text=L("PASTA ROBLOX","ROBLOX FOLDER","CARPETA ROBLOX","ROBLOX 文件夹","DOSSIER ROBLOX"),command=self._open_roblox_folder_safe,fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(3,0));ctk.CTkButton(shell,text=L("VOLTAR AO ZKSTRAP","BACK TO ZKSTRAP","VOLVER A ZKSTRAP","返回 ZKSTRAP","RETOUR AU ZKSTRAP"),command=close,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"],height=38).pack(fill="x",padx=14,pady=(6,14))''')
p.write_text(s,encoding='utf-8',newline='\n')
print('v3.20.14 hotfix applied',hashlib.sha256(p.read_bytes()).hexdigest())
