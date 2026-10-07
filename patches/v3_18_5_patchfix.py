from pathlib import Path

p = Path('patches/v3_18_5.py')
s = p.read_text(encoding='utf-8')
start = s.index('# Add official links/tools to About.')
end = s.index('# Trigger the network probe after the pages exist.')
block = r'''# Add official links/tools to About. Discord only appears after a public invite is configured.
about_anchor = '        # Compatibilidade com funções antigas que esperavam estas referências.\n'
about_insert = r''' + "'''" + r'''        links=self._section_card(body,"LINKS & SUPORTE" if pt else "LINKS & SUPPORT","Atalhos oficiais do projeto e suporte." if pt else "Official project and support shortcuts.")
        lr=ctk.CTkFrame(links,fg_color="transparent"); lr.pack(fill="x",padx=14,pady=(5,6))
        ctk.CTkButton(lr,text="YOUTUBE",command=lambda:webbrowser.open(PUBLIC_YOUTUBE_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(lr,text="GITHUB",command=lambda:webbrowser.open(PUBLIC_GITHUB_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=4)
        if PUBLIC_DISCORD_URL:
            ctk.CTkButton(lr,text="DISCORD",command=lambda:webbrowser.open(PUBLIC_DISCORD_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(4,0))
        lr2=ctk.CTkFrame(links,fg_color="transparent"); lr2.pack(fill="x",padx=14,pady=(0,14))
        ctk.CTkButton(lr2,text="REPORTAR BUG" if pt else "REPORT BUG",command=lambda:self.show_page("feedback"),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=38).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(lr2,text="VERIFICAR ATUALIZAÇÃO" if pt else "CHECK UPDATE",command=lambda:(self.show_page("updates"),self.after(120,lambda:self._update_check_async(silent=False))),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(4,0))
''' + "'''" + r''' + about_anchor
rep(about_anchor, about_insert, 'about links')

'''
s = s[:start] + block + s[end:]
p.write_text(s, encoding='utf-8')
print('v3.18.5 patch bootstrap fixed')
