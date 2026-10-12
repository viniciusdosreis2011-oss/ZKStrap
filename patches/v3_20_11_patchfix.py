from pathlib import Path

p=Path('patches/v3_20_11.py')
s=p.read_text(encoding='utf-8')
old='''# Language screen: start intro music, add a visible intro mute button, SFX on selection.
_,a,b=method_span(s,'ModernConfigApp','_maybe_show_first_run_language');chunk=s[a:b]
needle=''' + "'''        t=TEMAS[self.tema_atual]\n        rev=6'''" + '''
if needle not in chunk:raise SystemExit('v3.20.11: language start anchor')
chunk=chunk.replace(needle,''' + "'''        t=TEMAS[self.tema_atual]\n        self._first_run_audio_start()\n        rev=6'''" + ''',1)
needle=''' + "'''        def choose(code):\n            self.idioma=code'''" + '''
if needle not in chunk:raise SystemExit('v3.20.11: language choose anchor')
chunk=chunk.replace(needle,''' + "'''        def choose(code):\n            self._first_run_audio_event(\"select\")\n            self.idioma=code'''" + ''',1)
needle=''' + "'''        ctk.CTkLabel(right,text=\"ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS\",text_color=t.get(\"muted\",\"gray\"),font=ctk.CTkFont(family=\"Consolas\",size=7)).pack(anchor=\"e\",padx=8,pady=(8,2))'''" + '''
if needle not in chunk:raise SystemExit('v3.20.11: language footer anchor')
chunk=chunk.replace(needle,''' + "'''        footer=ctk.CTkFrame(right,fg_color=\"transparent\");footer.pack(fill=\"x\",padx=8,pady=(8,2))\n        ctk.CTkLabel(footer,text=\"ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS\",text_color=t.get(\"muted\",\"gray\"),font=ctk.CTkFont(family=\"Consolas\",size=7)).pack(side=\"right\")\n        self._first_run_audio_btn=ctk.CTkButton(footer,text=(\"♫  INTRO ON\" if self.first_run_intro_audio else \"♫  INTRO OFF\"),width=112,height=28,corner_radius=9,fg_color=t[\"card_active\"],hover_color=t[\"hover\"],text_color=t[\"accent\"],command=self._first_run_audio_toggle,font=ctk.CTkFont(family=\"Consolas\",size=7,weight=\"bold\"));self._first_run_audio_btn.pack(side=\"left\")'''" + ''',1)
s=s[:a]+chunk+s[b:]
'''
new='''# Language screen: use the actual v3.20.10 layout. Keep the patch tolerant of
# small typography/padding changes so onboarding polish does not block a build.
_,a,b=method_span(s,'ModernConfigApp','_maybe_show_first_run_language');chunk=s[a:b]
cover_anchor='        t=TEMAS[self.tema_atual];cover=self._zk_blur_cover(self,radius=13,brightness=.42);self._language_panel=cover'
if cover_anchor in chunk and 'self._first_run_audio_start()' not in chunk:
    chunk=chunk.replace(cover_anchor,'        self._first_run_audio_start()\\n'+cover_anchor,1)
elif 'self._first_run_audio_start()' not in chunk:
    nl=chunk.find('\\n')
    if nl<0:raise SystemExit('v3.20.11: language method malformed')
    chunk=chunk[:nl+1]+'        self._first_run_audio_start()\\n'+chunk[nl+1:]

if 'self._first_run_audio_event("select")' not in chunk:
    marker='        def choose(code):\\n'
    if marker not in chunk:raise SystemExit('v3.20.11: language choose anchor')
    chunk=chunk.replace(marker,marker+'            self._first_run_audio_event("select")\\n',1)

footer_line='        ctk.CTkLabel(right,text="ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(anchor="e",padx=7,pady=(10,3))'
if footer_line in chunk:
    chunk=chunk.replace(footer_line,'        footer=ctk.CTkFrame(right,fg_color="transparent");footer.pack(fill="x",padx=7,pady=(10,3))\\n        self._first_run_audio_btn=ctk.CTkButton(footer,text=("♫  INTRO ON" if self.first_run_intro_audio else "♫  INTRO OFF"),command=self._first_run_audio_toggle,width=112,height=28,corner_radius=9,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));self._first_run_audio_btn.pack(side="left")\\n        ctk.CTkLabel(footer,text="ESCOLHA LIVRE  •  SEM REINICIAR  •  5 IDIOMAS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(side="right")',1)
s=s[:a]+chunk+s[b:]
'''
if old not in s:
    raise SystemExit('v3.20.11 patchfix: old language block not found')
s=s.replace(old,new,1)

# The final v3.20.10 cursor-size handler changed shape, so do not anchor on a
# specific save_config try/except block. Append the overlay restart to the real
# method body instead. This survives small implementation/layout changes.
old_cursor='''# Changing cursor size restarts the helper so the in-game overlay matches it.
_,a,b=method_span(s,'ModernConfigApp','evento_cursor_tamanho');chunk=s[a:b]
needle=''' + "'''        try:self.salvar_config_app()\n        except Exception:pass'''" + '''
if needle not in chunk:raise SystemExit('v3.20.11: cursor size save anchor')
chunk=chunk.replace(needle,needle+''' + "'''\n        if bool(getattr(self,\"cursor_overlay_enabled\",False)):\n            try:self._cursor_overlay_stop(persist=False);self.after(90,lambda:self._cursor_overlay_start(silent=True))\n            except Exception:pass'''" + ''',1);s=s[:a]+chunk+s[b:]
'''
new_cursor='''# Changing cursor size restarts the helper so the in-game overlay matches it.
_,a,b=method_span(s,'ModernConfigApp','evento_cursor_tamanho');chunk=s[a:b]
if '_cursor_overlay_stop(persist=False)' not in chunk:
    chunk=chunk.rstrip()+''' + "'''\n        if bool(getattr(self,\"cursor_overlay_enabled\",False)):\n            try:self._cursor_overlay_stop(persist=False);self.after(90,lambda:self._cursor_overlay_start(silent=True))\n            except Exception:pass\n'''" + '''
s=s[:a]+chunk+s[b:]
'''
if old_cursor not in s:
    raise SystemExit('v3.20.11 patchfix: old cursor-size block not found')
s=s.replace(old_cursor,new_cursor,1)

p.write_text(s,encoding='utf-8')
print('v3.20.11 language + cursor patch anchors fixed')
