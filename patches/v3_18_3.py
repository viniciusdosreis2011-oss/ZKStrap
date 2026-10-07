import os, re
from pathlib import Path
root = Path(os.environ.get('ZK_SOURCE_DIR','/mnt/data/zk3182work'))
p = root/'ZKStrap_v3_18_0.py'
s = p.read_text('utf-8')
orig=s

s=s.replace('APP_VERSION = "3.18.2"','APP_VERSION = "3.18.3"',1)
s=s.replace('BUILD_TIMESTAMP = "Spotify Web Detect + Secret Hover Debounce"','BUILD_TIMESTAMP = "First Run Input Hotfix"',1)
s=s.replace('        self._sound_prompt_open = False\n', '        self._sound_prompt_open = False\n        self._sound_prompt_panel = None\n',1)

# Public-user dialogs must never grab all pointer input. On some Windows/DPI setups
# a hidden/behind transient with grab_set made the whole app look unclickable.
s=s.replace('        win.transient(self)\n        win.grab_set()\n', '        win.transient(self)\n        try:\n            win.lift(); self.after(80, lambda w=win: w.focus_force() if w.winfo_exists() else None)\n        except Exception:\n            pass\n',1)
s=s.replace('        win.transient(self); win.grab_set()\n', '        win.transient(self)\n        try:\n            win.lift(); self.after(80, lambda w=win: w.focus_force() if w.winfo_exists() else None)\n        except Exception:\n            pass\n',1)

# Manual tutorial must always work, even if the user ignored the audio consent card.
old='''    def abrir_tutorial(self, primeiro_acesso=False):\n        """Tutorial v3.6: acontece dentro da janela principal, sem Toplevel/modal."""\n        self._fechar_busca_universal()\n        self._tutorial_close(mark_complete=False, voltar_home=False)\n'''
new='''    def abrir_tutorial(self, primeiro_acesso=False):\n        """Tutorial v3.6: acontece dentro da janela principal, sem Toplevel/modal."""\n        self._fechar_busca_universal()\n        # O consentimento de áudio é não-modal. Se o usuário pediu o tutorial,\n        # fecha apenas o card visual para não cobrir o onboarding. A preferência\n        # continua não definida e pode ser perguntada novamente depois.\n        sp=getattr(self,"_sound_prompt_panel",None)\n        if sp is not None:\n            try:\n                if sp.winfo_exists(): sp.destroy()\n            except Exception:\n                pass\n            self._sound_prompt_panel=None\n            self._sound_prompt_open=False\n        self._tutorial_close(mark_complete=False, voltar_home=False)\n'''
if old not in s:
    raise SystemExit('abrir_tutorial anchor not found')
s=s.replace(old,new,1)

# Remove obsolete resolution tutorial steps (the navigation page was intentionally removed).
s=s.replace('                ("resolution", "RESOLUÇÃO", "Escolha a resolução usada pelo modo de jogo/janela e configure valores personalizados quando precisar.", "Use uma resolução menor se você quer reduzir carga gráfica; teste no seu PC antes de decidir."),\n','',1)
s=s.replace('            ("resolution", "RESOLUTION", "Choose the game/window resolution or set a custom value.", "Lower resolutions can reduce graphical load; test what works best on your PC."),\n','',1)

# Replace sound consent modal Toplevel with a non-modal in-app card.
start=s.index('    def _show_sound_consent(self, first_run=False):\n')
end=s.index('    def abrir_som_config(self):\n', start)
replacement='''    def _show_sound_consent(self, first_run=False):\n        """Mostra consentimento de áudio sem usar grab_set/Toplevel.\n\n        v3.18.3: um Toplevel overrideredirect com grab_set podia ficar atrás da\n        janela em algumas combinações de DPI/Windows. O grab continuava ativo e\n        fazia TODOS os cliques da janela principal parecerem quebrados. O card\n        agora vive dentro da própria UI e nunca captura o mouse globalmente.\n        """\n        if bool(getattr(self,"_sound_prompt_open",False)):\n            panel=getattr(self,"_sound_prompt_panel",None)\n            try:\n                if panel is not None and panel.winfo_exists():\n                    panel.lift(); return\n            except Exception:\n                pass\n            self._sound_prompt_open=False\n            self._sound_prompt_panel=None\n        self._sound_prompt_open=True\n        if bool(getattr(self,"sounds_enabled",False)):\n            self._play_ui_sound("modal",.0)\n        t=TEMAS[self.tema_atual]\n        host=getattr(self,"main_container",self)\n\n        enabled_now=bool(getattr(self,"sounds_enabled",False))\n        panel=ctk.CTkFrame(host,width=500,height=365,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=2,border_color=t["accent"])\n        panel.place(relx=.5,rely=.5,anchor="center")\n        panel.pack_propagate(False)\n        self._sound_prompt_panel=panel\n        try: panel.lift()\n        except Exception: pass\n\n        topbar=ctk.CTkFrame(panel,fg_color="transparent")\n        topbar.pack(fill="x",padx=18,pady=(14,0))\n        ctk.CTkLabel(topbar,text="ZK AUDIO  //  LOCAL",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")\n        ctk.CTkButton(topbar,text="×",width=30,height=28,corner_radius=8,fg_color="transparent",hover_color=t["card_active"],text_color=t.get("muted","gray"),command=lambda:self._sound_choice(False,panel)).pack(side="right")\n\n        icon=ctk.CTkFrame(panel,width=76,height=76,corner_radius=38,fg_color=t.get("icon_bg",t["card_active"]),border_width=2,border_color=t["accent"])\n        icon.pack(pady=(8,10)); icon.pack_propagate(False)\n        ctk.CTkLabel(icon,text="♫",text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=31,weight="bold")).pack(fill="both",expand=True)\n        title=("ATIVAR SONS DO ZKSTRAP?" if first_run else "SONS DO ZKSTRAP") if self.idioma=="pt" else ("ENABLE ZKSTRAP AUDIO?" if first_run else "ZKSTRAP AUDIO")\n        ctk.CTkLabel(panel,text=title,text_color=t["text"],font=ctk.CTkFont(size=19,weight="bold")).pack(pady=(0,6))\n        msg=("Feedback de clique, sons dos temas e música ambiente. Tudo é local e opcional. Este card não bloqueia o resto do app." if self.idioma=="pt" else "Click feedback, theme sounds and ambient music. Everything is local and optional. This card never blocks the rest of the app.")\n        ctk.CTkLabel(panel,text=msg,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10),wraplength=420,justify="center").pack(padx=30,pady=(0,16))\n        row=ctk.CTkFrame(panel,fg_color="transparent"); row.pack(fill="x",padx=24,pady=(0,8))\n        off_text=("DESATIVAR" if enabled_now else "AGORA NÃO") if self.idioma=="pt" else ("DISABLE" if enabled_now else "NOT NOW")\n        on_text=("♫  MANTER ATIVOS" if enabled_now else "♫  ATIVAR SONS") if self.idioma=="pt" else ("♫  KEEP ENABLED" if enabled_now else "♫  ENABLE AUDIO")\n        ctk.CTkButton(row,text=off_text,height=44,corner_radius=12,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],command=lambda:self._sound_choice(False,panel)).pack(side="left",expand=True,fill="x",padx=(0,6))\n        ctk.CTkButton(row,text=on_text,height=44,corner_radius=12,fg_color=t["accent"],hover_color=t["hover"],text_color="#05070A",font=ctk.CTkFont(weight="bold"),command=lambda:self._sound_choice(True,panel)).pack(side="left",expand=True,fill="x",padx=(6,0))\n        try:\n            self.after(80,lambda p=panel: p.lift() if p.winfo_exists() else None)\n        except Exception:\n            pass\n\n'''
s=s[:start]+replacement+s[end:]

# Ensure _sound_choice clears the panel reference for both old and new implementations.
needle='''        self._sound_prompt_open=False\n        if popup is not None:\n'''
repl='''        self._sound_prompt_open=False\n        self._sound_prompt_panel=None\n        if popup is not None:\n'''
if needle not in s:
    raise SystemExit('_sound_choice anchor not found')
s=s.replace(needle,repl,1)

# Add a keyboard fullscreen fallback. This is independent of the title-bar maximize button.
needle='''        self.bind("<Escape>", self._handle_global_escape, add="+")\n        self.after(120, self._apply_responsive_layout)\n'''
repl='''        self.bind("<Escape>", self._handle_global_escape, add="+")\n        self.bind("<F11>", self._toggle_window_fullscreen, add="+")\n        self.bind("<Alt-Return>", self._toggle_window_fullscreen, add="+")\n        self.after(120, self._apply_responsive_layout)\n'''
if needle not in s:
    raise SystemExit('startup bind anchor not found')
s=s.replace(needle,repl,1)

# Insert fullscreen helper before static color method.
needle='''    @staticmethod\n    def _cor_hex_valida(cor):\n'''
helper='''    def _toggle_window_fullscreen(self, event=None):\n        """F11 / Alt+Enter: fallback seguro para fullscreen em qualquer perfil."""\n        try:\n            current=bool(self.attributes("-fullscreen"))\n            self.attributes("-fullscreen",not current)\n            return "break"\n        except Exception:\n            try:\n                self.state("zoomed")\n            except Exception:\n                pass\n        return "break"\n\n    @staticmethod\n    def _cor_hex_valida(cor):\n'''
if needle not in s:
    raise SystemExit('color static anchor not found')
s=s.replace(needle,helper,1)

if s==orig:
    raise SystemExit('no changes')
p.write_text(s,'utf-8')
print('patched',p,'bytes',len(s.encode()))
