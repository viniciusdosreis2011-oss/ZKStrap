from pathlib import Path
import os, re, ast

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')

# VERSION
if 'APP_VERSION = "3.19.5"' not in s:
    raise SystemExit('v3.19.6: expected v3.19.5 base')
s=s.replace('APP_VERSION = "3.19.5"','APP_VERSION = "3.19.6"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Visible Personalization Controls"',s,count=1)
if n!=1:
    raise SystemExit('v3.19.6: timestamp missing')

# PERSONALIZAR — font/language controls were visually anonymous: two bare
# dropdowns with no labels. Replace that strip with a proper interface panel.
pattern=r'''        prefs = ctk\.CTkFrame\(theme_card, fg_color="transparent"\); prefs\.pack\(fill="x", padx=14, pady=\(2,14\)\)\n        self\.font_menu = ctk\.CTkOptionMenu\(prefs,.*?\n        self\.lang_menu = ctk\.CTkOptionMenu\(prefs,.*?\n(?=        colors = self\._section_card\(body,)'''

new_block=r'''        prefs = ctk.CTkFrame(
            theme_card,
            fg_color=self._mix_hex(t.get("panel",t["card"]),t["accent"],.045),
            corner_radius=14,
            border_width=1,
            border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30),
        )
        prefs.pack(fill="x", padx=14, pady=(8,16))

        pref_head=ctk.CTkFrame(prefs,fg_color="transparent")
        pref_head.pack(fill="x",padx=14,pady=(12,8))
        ctk.CTkLabel(
            pref_head,
            text=self._L("INTERFACE & IDIOMA","INTERFACE & LANGUAGE","INTERFAZ E IDIOMA","界面与语言","INTERFACE & LANGUE"),
            text_color=t["text"],
            font=ctk.CTkFont(size=12,weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            pref_head,
            text=self._L(
                "Ajuste a fonte do ZKStrap e o idioma da interface.",
                "Choose the ZKStrap font and interface language.",
                "Elige la fuente de ZKStrap y el idioma de la interfaz.",
                "设置 ZKStrap 字体和界面语言。",
                "Choisissez la police ZKStrap et la langue de l’interface.",
            ),
            text_color=t.get("muted","gray"),
            font=ctk.CTkFont(size=9),
            anchor="w",
        ).pack(anchor="w",pady=(2,0))

        pref_row=ctk.CTkFrame(prefs,fg_color="transparent")
        pref_row.pack(fill="x",padx=12,pady=(0,12))

        font_box=ctk.CTkFrame(
            pref_row,fg_color=t["card"],corner_radius=12,border_width=1,
            border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.20)
        )
        font_box.pack(side="left",fill="both",expand=True,padx=(0,5))
        ctk.CTkLabel(
            font_box,
            text=self._L("Aa  FONTE DA INTERFACE","Aa  INTERFACE FONT","Aa  FUENTE DE INTERFAZ","Aa  界面字体","Aa  POLICE DE L’INTERFACE"),
            text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w"
        ).pack(fill="x",padx=12,pady=(10,1))
        ctk.CTkLabel(
            font_box,
            text=self._L("Muda a família dos textos do app.","Changes the app text family.","Cambia la familia de texto del app.","更改应用文字字体。","Change la famille de texte de l’app."),
            text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w"
        ).pack(fill="x",padx=12,pady=(0,7))
        self.font_menu = ctk.CTkOptionMenu(
            font_box, values=["Segoe UI","Consolas","Arial","Tahoma","Courier New"],
            command=self.escolher_fonte, fg_color=t["card_active"], button_color=t["card_active"],
            button_hover_color=t["hover"], text_color=t["accent"], height=34
        )
        self.font_menu.set(self.fonte_ui)
        self.font_menu.pack(fill="x",padx=10,pady=(0,10))

        lang_box=ctk.CTkFrame(
            pref_row,fg_color=t["card"],corner_radius=12,border_width=1,
            border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.20)
        )
        lang_box.pack(side="left",fill="both",expand=True,padx=(5,0))
        ctk.CTkLabel(
            lang_box,
            text=self._L("LANG  IDIOMA","LANG  LANGUAGE","LANG  IDIOMA","LANG  语言","LANG  LANGUE"),
            text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w"
        ).pack(fill="x",padx=12,pady=(10,1))
        ctk.CTkLabel(
            lang_box,
            text=self._L("Troca todo o idioma do ZKStrap.","Changes the entire ZKStrap language.","Cambia todo el idioma de ZKStrap.","切换整个 ZKStrap 的语言。","Change toute la langue de ZKStrap."),
            text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w"
        ).pack(fill="x",padx=12,pady=(0,7))
        self.lang_menu = ctk.CTkOptionMenu(
            lang_box, values=["Português","English","Español","中文","Français"],
            command=self.aplicar_idioma, fg_color=t["card_active"], button_color=t["card_active"],
            button_hover_color=t["hover"], text_color=t["accent"], height=34
        )
        self.lang_menu.set({"pt":"Português","en":"English","es":"Español","zh":"中文","fr":"Français"}.get(self.idioma,"English"))
        self.lang_menu.pack(fill="x",padx=10,pady=(0,10))
'''

s,n=re.subn(pattern,lambda _m:new_block,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'v3.19.6: personalization controls block not found ({n})')

# Validate source shape.
if 'INTERFACE & IDIOMA' not in s:
    raise SystemExit('v3.19.6: visible interface header missing')
if 'Aa  FONTE DA INTERFACE' not in s:
    raise SystemExit('v3.19.6: font label missing')
if 'LANG  IDIOMA' not in s:
    raise SystemExit('v3.19.6: language label missing')
if 'values=["Português","English","Español","中文","Français"]' not in s:
    raise SystemExit('v3.19.6: five-language menu missing')
if 'child.configure(font=(self.fonte_ui,11))' in s:
    raise SystemExit('v3.19.6: old forced size-11 fallback returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.19.6 visible personalization controls patch')
