"""v3.20.22: compact cursor UI, explicit apply, safe pending selection."""
from pathlib import Path
import ast
import os

path=Path(os.environ.get("ZK_SOURCE_DIR", "."))/"ZKStrap_v3_18_0.py"
s=path.read_text(encoding="utf-8")

def replace_method(text,name,replacement):
    tree=ast.parse(text)
    cls=next((x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="ModernConfigApp"),None)
    if cls is None:raise SystemExit("ModernConfigApp missing")
    method=next((x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==name),None)
    if method is None:raise SystemExit("method missing: "+name)
    lines=text.splitlines(True)
    start=sum(map(len,lines[:method.lineno-1]))
    end=sum(map(len,lines[:method.end_lineno]))
    return text[:start]+replacement.rstrip()+"\n"+text[end:]

s=replace_method(s,"_lazy_build_page_cursor", '''
    def _lazy_build_page_cursor(self):
        """Compact cursor deck. All actions remain visible above the fold."""
        if "cursor" in getattr(self, "pages", {}):
            return self.pages.get("cursor")
        t=TEMAS[self.tema_atual]
        L=self._L
        _,body=self._page_shell(
            "cursor","CURSOR",
            L("Escolha, visualize e aplique um cursor ao Roblox.",
              "Choose, preview and apply a Roblox cursor.",
              "Elige, previsualiza y aplica un cursor de Roblox.",
              "选择、预览并应用 Roblox 光标。",
              "Choisissez, prévisualisez et appliquez un curseur Roblox.")
        )
        # Only a single content-sized card. No expanding bottom placeholder.
        card=ctk.CTkFrame(
            body,fg_color=t["card"],corner_radius=14,border_width=1,
            border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.42)
        )
        card.pack(fill="x",expand=False,padx=6,pady=(0,8))
        self.cursor_card=card
        ctk.CTkLabel(
            card,text=L("CURSOR DO ROBLOX","ROBLOX CURSOR","CURSOR DE ROBLOX",
                        "ROBLOX 光标","CURSEUR ROBLOX"),
            text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold")
        ).pack(anchor="w",padx=18,pady=(13,5))
        choices=self.listar_cursor_packs()
        if getattr(self,"cursor_pack","Roblox Padrão") not in choices:
            self.cursor_pack="Roblox Padrão"
        selected=getattr(self,"_cursor_pending_pack",None)
        if selected not in choices:
            selected=self.cursor_pack
        self.cursor_menu=ctk.CTkOptionMenu(
            card,values=choices,command=self.evento_cursor_pack,height=35,
            fg_color=t["card_active"],button_color=t["card_active"],
            button_hover_color=t["hover"],text_color=t["accent"]
        )
        self.cursor_menu.set(selected)
        self.cursor_menu.pack(fill="x",padx=18,pady=(2,9))

        # The primary actions appear immediately below the pack selector,
        # instead of after a large preview/scrollable blank section.
        main_actions=ctk.CTkFrame(card,fg_color="transparent")
        main_actions.pack(fill="x",padx=18,pady=(0,9))
        self.btn_apply_cursor=ctk.CTkButton(
            main_actions,text=L("APLICAR CURSOR","APPLY CURSOR","APLICAR CURSOR",
                                "应用光标","APPLIQUER LE CURSEUR"),
            command=self.aplicar_cursor_selecionado,height=38,
            fg_color=t["accent"],hover_color=t["hover"],text_color="#050505"
        )
        self.btn_apply_cursor.pack(side="left",fill="x",expand=True,padx=(0,5))
        self.btn_restore_cursor=ctk.CTkButton(
            main_actions,text=L("RESTAURAR ORIGINAL","RESTORE ORIGINAL",
                                "RESTAURAR ORIGINAL","恢复原版","RESTAURER L’ORIGINAL"),
            command=self.restaurar_cursor_original,height=38,
            fg_color="transparent",border_width=1,border_color=t["accent"],
            text_color=t["text"]
        )
        self.btn_restore_cursor.pack(side="left",fill="x",expand=True,padx=(5,0))

        preview=ctk.CTkFrame(
            card,fg_color=t["card_active"],corner_radius=12,border_width=1,
            border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.35)
        )
        preview.pack(fill="x",padx=18,pady=(0,8))
        self.cursor_preview_label=ctk.CTkLabel(
            preview,text=L("Carregando prévia...","Loading preview...",
                           "Cargando vista previa...","加载预览...","Chargement..."),
            width=118,height=118,text_color=t.get("muted","gray")
        )
        self.cursor_preview_label.pack(side="left",padx=9,pady=9)
        detail=ctk.CTkFrame(preview,fg_color="transparent")
        detail.pack(side="left",fill="both",expand=True,padx=(5,12),pady=9)
        ctk.CTkLabel(detail,text=L("PRÉVIA","PREVIEW","VISTA PREVIA","预览","APERÇU"),
                     text_color=t["accent"],
                     font=ctk.CTkFont(family="Consolas",size=9,weight="bold")
        ).pack(anchor="w")
        size_line=ctk.CTkFrame(detail,fg_color="transparent")
        size_line.pack(fill="x",pady=(8,5))
        self.cursor_size_slider=ctk.CTkSlider(
            size_line,from_=8,to=48,number_of_steps=40,
            command=self.evento_cursor_tamanho,progress_color=t["accent"],
            button_color=t["accent"],button_hover_color=t["hover"]
        )
        self.cursor_size_slider.pack(side="left",fill="x",expand=True,padx=(0,9))
        self.cursor_size_value=ctk.CTkLabel(
            size_line,text=f"{int(self.cursor_visual_size)} px",width=60,
            text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")
        )
        self.cursor_size_value.pack(side="right")
        self.cursor_size_slider.set(int(self.cursor_visual_size))
        valid_modes=["Ponta no centro","Centro"]
        if self.cursor_anchor_mode not in valid_modes:
            self.cursor_anchor_mode="Ponta no centro"
        self.cursor_anchor_menu=ctk.CTkOptionMenu(
            detail,values=valid_modes,command=self.evento_cursor_ancora,
            height=30,fg_color=t["card"],button_color=t["card"],
            button_hover_color=t["hover"],text_color=t["accent"]
        )
        self.cursor_anchor_menu.set(self.cursor_anchor_mode)
        self.cursor_anchor_menu.pack(fill="x",pady=(1,0))

        import_actions=ctk.CTkFrame(card,fg_color="transparent")
        import_actions.pack(fill="x",padx=18,pady=(0,6))
        ctk.CTkButton(
            import_actions,text=L("IMPORTAR PNG","IMPORT PNG","IMPORTAR PNG",
                                  "导入 PNG","IMPORTER PNG"),
            command=self.importar_cursor_png,height=33,
            fg_color=t["card_active"],hover_color=t["hover"],
            text_color=t["text"]
        ).pack(side="left",fill="x",expand=True,padx=(0,5))
        ctk.CTkButton(
            import_actions,text=L("IMPORTAR PACK","IMPORT PACK","IMPORTAR PACK",
                                  "导入光标包","IMPORTER UN PACK"),
            command=self.importar_cursor_pack_pasta,height=33,
            fg_color=t["card_active"],hover_color=t["hover"],
            text_color=t["text"]
        ).pack(side="left",fill="x",expand=True,padx=(5,0))
        self.lbl_cursor_status=ctk.CTkLabel(
            card,text=L("Selecione um cursor e clique em Aplicar.",
                        "Select a cursor and click Apply.",
                        "Elige un cursor y pulsa Aplicar.",
                        "选择光标后点击应用。",
                        "Choisissez un curseur et cliquez sur Appliquer."),
            text_color=t.get("muted","gray"),wraplength=900,
            anchor="w",justify="left"
        )
        self.lbl_cursor_status.pack(fill="x",padx=18,pady=(1,11))
        self.after(35,self._refresh_cursor_preview)
        return self.pages.get("cursor")
''')

s=replace_method(s,"evento_cursor_pack", '''
    def evento_cursor_pack(self, valor):
        """Preview selection without modifying the Roblox files."""
        pack=str(valor or "Roblox Padrão")
        choices=self.listar_cursor_packs()
        if pack not in choices:
            return
        self._cursor_pending_pack=pack
        try:
            self.cursor_menu.set(pack)
            self.lbl_cursor_status.configure(
                text=self._L("Prévia selecionada. Clique em APLICAR CURSOR para salvar no Roblox.",
                             "Preview selected. Click APPLY CURSOR to change Roblox files.",
                             "Vista previa seleccionada. Haz clic en APLICAR CURSOR.",
                             "已选择预览。点击应用光标。",
                             "Aperçu sélectionné. Cliquez sur APPLIQUER LE CURSEUR.")
            )
        except Exception:
            pass
        self._refresh_cursor_preview()
''')

s=replace_method(s,"_cursor_preview_source", '''
    def _cursor_preview_source(self):
        pack=str(getattr(self,"_cursor_pending_pack",None) or
                 getattr(self,"cursor_pack","Roblox Padrão") or "Roblox Padrão")
        if pack!="Roblox Padrão":
            base=os.path.join(self.get_cursor_packs_dir(),pack)
            p=self._cursor_source_file(base,far=False)
            if p and os.path.isfile(p):
                return p
            p=os.path.join(base,"ArrowCursor.png")
            if os.path.isfile(p):
                return p
        root=str(getattr(self,"pasta_roblox_salva","") or "")
        if root:
            p=os.path.join(root,"content","textures","Cursors","KeyboardMouse","ArrowCursor.png")
            if os.path.isfile(p):
                return p
        return ""
''')

s=replace_method(s,"aplicar_cursor_selecionado", '''
    def aplicar_cursor_selecionado(self):
        """Apply explicitly and let the existing verified backup flow run."""
        menu=getattr(self,"cursor_menu",None)
        pack=str(menu.get() if menu is not None else
                 getattr(self,"_cursor_pending_pack",None) or self.cursor_pack)
        if pack not in self.listar_cursor_packs():
            try:
                self.lbl_cursor_status.configure(text="Cursor não encontrado. Importe ou selecione outro pack.")
            except Exception:
                pass
            return False
        ok=bool(self.aplicar_cursor_pack(pack))
        if ok:
            self._cursor_pending_pack=None
            try:
                self.cursor_menu.set(self.cursor_pack)
                self._refresh_cursor_preview()
            except Exception:
                pass
        return ok
''')

# Old importer code applies a pack immediately; importing must now only
# prepare it and refresh the selection + preview.
for method in ("importar_cursor_png","importar_cursor_pack_pasta"):
    tree=ast.parse(s)
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="ModernConfigApp")
    node=next((x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==method),None)
    if node is None:
        raise SystemExit("cursor importer missing: "+method)
    lines=s.splitlines(True)
    a=sum(map(len,lines[:node.lineno-1]))
    b=sum(map(len,lines[:node.end_lineno]))
    chunk=s[a:b]
    if chunk.count("self.cursor_pack = nome")!=1 or chunk.count("self.aplicar_cursor_pack(nome)")!=1:
        raise SystemExit("cursor importer unexpected source: "+method)
    chunk=chunk.replace("self.cursor_pack = nome","self._cursor_pending_pack = nome")
    chunk=chunk.replace("self.aplicar_cursor_pack(nome)","self._refresh_cursor_preview()")
    s=s[:a]+chunk+s[b:]

old='APP_VERSION = "3.20.21"'
if s.count(old)!=1:
    raise SystemExit("v3.20.21 version anchor missing")
s=s.replace(old,'APP_VERSION = "3.20.22"',1)
ast.parse(s)
compile(s,str(path),"exec")
path.write_text(s,encoding="utf-8")
print("v3.20.22 cursor update: syntax OK")
