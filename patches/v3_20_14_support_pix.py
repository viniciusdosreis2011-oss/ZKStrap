from pathlib import Path
import ast, os, textwrap

root=Path(os.environ.get("ZK_SOURCE_DIR","."))
p=root/"ZKStrap_v3_18_0.py"
s=p.read_text(encoding="utf-8")
_ZK_SUPPORT_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAhIAAAISAQAAAACxRhsSAAAE1klEQVR4nO2dUY7bOgxFL2sD+bSBLmCWYu+gSyq6pO7AXsosoID8GUAG+yFKovIy0wc09ssLrj6COHEOZICgyCtSEcXfjvXLXyMAMsgggwwyyCCDDDLIqAyx0UNmADJv9gGAXbCOgMi4i8jov5X5wfMgg4wPhqqqYlJV1dApMES4yyl06Z2qRthLusw/W57lWch4fcZm3lEXdKo/RkDmIUKX4Vr8aee0ARHpj5gHGWTcG/3NtUwBkOm9j4rtaxSgU5l0F0xLueXn4+dBBhmfjVs7VWDvgeEqiiECKT6VTmUdA+SweZBBxr9hDKq6AAC2i71bpU+RKjBcBVPYJYWlC5Ai1QPmQQYZnzBWkZzMA5B5u6h8DwCw9cD0flFgu6jMWw+ZsRc14MHzIIOMuyOt+y5BWscOad23d7F8AQGGCG3uf9A8yCDj02ECUwDSer4kw+xyGADAjHWIUA0wXWop+hV1KTIOZyQ7Na1UYwlIIzAFAECXZVKYnJpvsV/STsk4nmH+FMWLmrPUJOzfKP71UpeBOj8ZpzGKP7Ul32f0wWIBTBqRw4DqT8vNz/IsZLwuw8Wn9qLq/KnZbv427VYlV5o3T2mnZBzPyP5US6akZoTAUNxmALJ15l8sjE/JOI/R5FG5DsWHpjWtqgYMS7pop2ScxMhFLIDTUl/AMyf5tzqRggwhYp2SsYpDJ9HFV3UcqY7FX4LzESZR5FxJsMHpGllT9mTFveqefNpiP+Q+GmnZJzD8Pk+UNxma6L12xqaLmC+T8ZpDJfv14w+K1R+U8rs2d3XUecn4yyGU5nyJ9VjllEVqlLNx3yfjPMZReJPXjSNsvhPYRdMoVOZ637UdlGZHz0PMsi4O1Jdn1WSbl8j1vFXj3UMilTZb59BV+kisI35vreYy/ue5VnIeHWGl/MDoMsmAtNUI3IsehWsY9dWUz12HmSQ8cHI+VGVn2oylRtMU7qEptvE7aA+y7OQ8boMV8+v67dfvQJ7r9i6KFa7D2AVAFN63ylSI+qgkNSD+izPQsbLM1YRSb1QdWVPl9Kj6fKzBlVdNhH77MmehYwXZPi+k1ahSgX8aeStKKdGKfVTMs5jlDqUsm8PmMRfWvhSDV8pPbXNU9BOyTiN0Rac5v1Q64VCTv+HUqpSdYGcftFOyTieUVZ7LzWpHXfmy/e8EAXW9ZFxLqOp69PYqFGhsdilJFNTtWzaKRmnMJw/zfFpG4YOdRu1VklFJ7vSTsk4nuGz/KmecKq+Q9++CEBtl2K9FBlnMkpdX20hbQ+bqAfzBsCZMtd9Mk5kuIb95jyU3DNVG/eQbvFBAvMoMk5ilECzyfdrJTQA1yRlR6MDcN1TtFMyDme4db9GpTdHS7nO09qQQv2UjNMZ9f9OML33wPqmfpMf2MVk//fef/boeZBBxqeMKYuoMJvcRTXsUg9Iw/p2zZfJgPO508/2LGS8IKM9X6o0PYe21jR37/k+Kvbvk/HfMWTeLpqK+9YRZrE/pKz2W5+7+7eLfsB4xDzIIKMZN/7U75beetH2H894Xh8Z5zMGE1F1QafmVOWiMqd0ySJVkberpH88W8dD5kEGGXeHqVFpdFl+QlfkfH9Amp0+NbSV1c/yLGS8LkP0z/f8YazP8ixkkEEGGWSQQQYZZPz/Gb8BDwxHMSMHqtsAAAAASUVORK5CYII='

def _class_and_lines(src):
    t=ast.parse(src)
    cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=="ModernConfigApp")
    return t,cls,src.splitlines(True)

def _normalize_method(body):
    raw=textwrap.dedent(body).strip("\n").splitlines()
    return "\n".join(raw)+"\n"

def replace_method(src,name,body):
    t,cls,lines=_class_and_lines(src)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f"support-page method missing: {name}")
    start=sum(len(x) for x in lines[:node.lineno-1]); end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:start]+textwrap.indent(_normalize_method(body),"    ")+src[end:]

anchor='PUBLIC_DISCORD_URL = ""  # preencher só quando houver um convite público oficial\n'
if "_ZK_SUPPORT_QR_B64 =" not in s:
    if anchor not in s: raise SystemExit("support QR anchor missing")
    s=s.replace(anchor,anchor+f'_ZK_SUPPORT_QR_B64 = "{_ZK_SUPPORT_QR_B64}"\n',1)

# Give Support its own clean heart identity instead of sharing the generic info icon.
_support_icon_old = '''
        elif key in ("support","about","info"):
            d.ellipse((14,14,50,50),outline=ac,width=3); line((32,28,32,43),fg,3); dot(32,22,2,fg)
'''
_support_icon_new = '''
        elif key == "support":
            # Minimal line-heart, matching the clean professional icon family.
            line((32,50,15,33),ac,3); d.arc((13,15,34,37),180,350,fill=ac,width=3); d.arc((30,15,51,37),190,360,fill=ac,width=3); line((49,31,32,50),ac,3)
        elif key in ("about","info"):
            d.ellipse((14,14,50,50),outline=ac,width=3); line((32,28,32,43),fg,3); dot(32,22,2,fg)
'''
if _support_icon_old in s:
    s=s.replace(_support_icon_old,_support_icon_new,1)
else:
    raise SystemExit("clean support icon anchor missing")

support_method = '''def _lazy_build_page_support(self):
    if "support" in getattr(self,"pages",{}): return self.pages.get("support")
    t=TEMAS[self.tema_atual]
    st=self._theme_style()
    L=self._L
    _, body = self._page_shell(
        "support",
        L("APOIE O ZKSTRAP","SUPPORT ZKSTRAP","APOYA ZKSTRAP","支持 ZKSTRAP","SOUTENEZ ZKSTRAP"),
        L(
            "Se o ZKStrap te ajuda, uma contribuição fortalece o projeto e acelera melhorias reais.",
            "If ZKStrap helps you, a contribution strengthens the project and speeds up real improvements.",
            "Si ZKStrap te ayuda, una contribución fortalece el proyecto y acelera mejoras reales.",
            "如果 ZKStrap 对你有帮助，你的支持会让项目更稳、更快地实现真正的改进。",
            "Si ZKStrap vous aide, votre soutien renforce le projet et accélère de vraies améliorations."
        )
    )

    def _mix(a,b,r=.5):
        try:return self._mix_hex(a,b,r)
        except Exception:return a

    hero=ctk.CTkFrame(body,fg_color=t["card"],corner_radius=max(18,st.get("card_radius",16)),border_width=1,border_color=_mix(t.get("border",t["accent"]),t["accent"],.38))
    hero.pack(fill="x",padx=6,pady=(8,10))
    ctk.CTkFrame(hero,height=4,fg_color=_mix(t["card"],t["accent"],.78),corner_radius=3).pack(fill="x",padx=14)
    hwrap=ctk.CTkFrame(hero,fg_color="transparent"); hwrap.pack(fill="x",padx=20,pady=18)
    hleft=ctk.CTkFrame(hwrap,fg_color="transparent"); hleft.pack(side="left",fill="both",expand=True,padx=(0,14))
    ctk.CTkLabel(hleft,text=L("APOIO // PRÓXIMOS PASSOS","SUPPORT // NEXT STEPS","APOYO // PRÓXIMOS PASOS","支持 // 下一步","SOUTIEN // PROCHAINES ÉTAPES"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"),anchor="w").pack(fill="x")
    ctk.CTkLabel(hleft,text=L("AJUDE O ZKSTRAP A IR MAIS LONGE","HELP ZKSTRAP GO FURTHER","AYUDA A ZKSTRAP A LLEGAR MÁS LEJOS","帮助 ZKSTRAP 走得更远","AIDEZ ZKSTRAP À ALLER PLUS LOIN"),text_color=t["text"],font=ctk.CTkFont(size=22,weight="bold"),anchor="w",justify="left").pack(fill="x",pady=(5,7))
    ctk.CTkLabel(hleft,text=L(
        "Com essa ajuda, eu consigo investir em IAs para PvP e para o próprio app, APIs, hospedagem e outros recursos pagos que ajudam ideias maiores a sair do papel.",
        "With your support, I can invest in AI tools for PvP and for the app itself, APIs, hosting, and other paid resources that help bigger ideas become real.",
        "Con tu apoyo, puedo invertir en herramientas de IA para PvP y para la propia app, APIs, alojamiento y otros recursos de pago que ayudan a convertir ideas mayores en realidad.",
        "有了你的支持，我可以投入 PvP 与应用内 AI 工具、API、托管服务，以及其他需要付费才能实现的功能，让更大的想法真正落地。",
        "Grâce à votre soutien, je peux investir dans des outils d’IA pour le PvP et l’application, des API, l’hébergement et d’autres ressources payantes qui permettent de concrétiser des idées plus ambitieuses."
    ),text_color=t.get("muted",t["text"]),font=ctk.CTkFont(size=12),wraplength=610,justify="left",anchor="w").pack(fill="x")
    badge=ctk.CTkLabel(hleft,text=L("  APOIO OPCIONAL  ","  OPTIONAL SUPPORT  ","  APOYO OPCIONAL  ","  自愿支持  ","  SOUTIEN FACULTATIF  "),fg_color=_mix(t["card_active"],t["accent"],.16),text_color=t["accent"],corner_radius=9,font=ctk.CTkFont(family="Consolas",size=9,weight="bold"))
    badge.pack(anchor="w",pady=(12,0))
    ctk.CTkLabel(hleft,text=L(
        "O ZKStrap continua gratuito. Apoiar é totalmente opcional e não libera vantagem exclusiva.",
        "ZKStrap remains free. Supporting is completely optional and does not unlock exclusive advantages.",
        "ZKStrap sigue siendo gratuito. Apoyar es totalmente opcional y no desbloquea ventajas exclusivas.",
        "ZKStrap 仍然免费。支持完全自愿，也不会解锁任何专属优势。",
        "ZKStrap reste gratuit. Le soutien est entièrement facultatif et ne débloque aucun avantage exclusif."
    ),text_color=t.get("muted",t["text"]),font=ctk.CTkFont(size=10),wraplength=600,justify="left",anchor="w").pack(fill="x",pady=(7,0))

    pix=ctk.CTkFrame(hwrap,fg_color=_mix(t["card"],t.get("card_active",t["card"]),.56),corner_radius=18,border_width=1,border_color=_mix(t.get("border",t["accent"]),t["accent"],.48),width=300)
    pix.pack(side="right",fill="y",padx=(6,0))
    top=ctk.CTkFrame(pix,fg_color="transparent"); top.pack(fill="x",padx=16,pady=(14,8))
    ctk.CTkLabel(top,text="PIX",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=13,weight="bold"),anchor="w").pack(side="left")
    ctk.CTkLabel(top,text=L("VALOR LIVRE","ANY AMOUNT","VALOR LIBRE","金额自定","MONTANT LIBRE"),fg_color=_mix(t["card_active"],t["accent"],.12),text_color=t["accent"],corner_radius=8,font=ctk.CTkFont(size=9,weight="bold"),padx=8,pady=3).pack(side="right")
    qwrap=ctk.CTkFrame(pix,fg_color="#ffffff",corner_radius=14,border_width=1,border_color="#e6e6e6")
    qwrap.pack(padx=20,pady=(2,9))
    try:
        from PIL import Image
        raw=base64.b64decode(_ZK_SUPPORT_QR_B64)
        qim=Image.open(BytesIO(raw)).convert("RGB").resize((220,220),Image.Resampling.NEAREST)
        self._zk_support_qr_ctk=ctk.CTkImage(light_image=qim,dark_image=qim,size=(220,220))
        ctk.CTkLabel(qwrap,text="",image=self._zk_support_qr_ctk,fg_color="#ffffff").pack(padx=10,pady=10)
    except Exception:
        ctk.CTkLabel(qwrap,text="PIX",text_color="#111111",fg_color="#ffffff",font=ctk.CTkFont(size=42,weight="bold"),width=220,height=220).pack(padx=10,pady=10)
    ctk.CTkLabel(pix,text=L("ESCANEIE PELO CELULAR","SCAN WITH YOUR PHONE","ESCANEA CON EL CELULAR","用手机扫描","SCANNEZ AVEC VOTRE TÉLÉPHONE"),text_color=t["text"],font=ctk.CTkFont(size=11,weight="bold")).pack(padx=14,pady=(1,3))
    ctk.CTkLabel(pix,text=L("Abra o app do seu banco e aponte para o QR Code.","Open your banking app and scan the QR Code.","Abre la app de tu banco y escanea el código QR.","打开你的银行应用并扫描二维码。","Ouvrez votre application bancaire et scannez le QR Code."),text_color=t.get("muted",t["text"]),font=ctk.CTkFont(size=9),wraplength=245,justify="center").pack(padx=14,pady=(0,13))

    use=self._section_card(
        body,
        L("O QUE ESSA AJUDA DESTRAVA","WHAT YOUR SUPPORT HELPS UNLOCK","LO QUE TU APOYO AYUDA A DESBLOQUEAR","你的支持能推动什么","CE QUE VOTRE SOUTIEN AIDE À DÉBLOQUER"),
        L("A ideia é transformar o apoio em melhorias concretas no projeto.","The goal is to turn support into concrete project improvements.","La idea es convertir el apoyo en mejoras concretas del proyecto.","目标是把支持真正转化为项目改进。","L’objectif est de transformer le soutien en améliorations concrètes du projet.")
    )
    grid=ctk.CTkFrame(use,fg_color="transparent"); grid.pack(fill="x",padx=10,pady=(4,12))
    for c in (0,1): grid.grid_columnconfigure(c,weight=1,uniform="supportgrid")
    items=[
        ("combo",L("IA PARA PVP","AI FOR PVP","IA PARA PVP","PVP AI","IA POUR LE PVP"),L("Ferramentas futuras para analisar builds, combos e decisões de PvP.","Future tools for analyzing builds, combos, and PvP decisions.","Herramientas futuras para analizar builds, combos y decisiones de PvP.","用于分析配装、连招和 PvP 决策的未来工具。","De futurs outils pour analyser les builds, combos et décisions PvP.")),
        ("cpu",L("IA NO APP","AI IN THE APP","IA EN LA APP","应用内 AI","IA DANS L’APP"),L("Automação inteligente e ajuda contextual em recursos futuros.","Smart automation and contextual assistance in future features.","Automatización inteligente y ayuda contextual en futuras funciones.","面向未来功能的智能自动化与上下文辅助。","Automatisation intelligente et aide contextuelle dans de futures fonctions.")),
        ("network",L("INFRA & APIS","INFRA & APIS","INFRA Y APIS","基础设施与 API","INFRA & API"),L("Hospedagem, serviços online e integrações que exigem custo.","Hosting, online services, and integrations that have real operating costs.","Alojamiento, servicios online e integraciones que tienen costos reales.","托管、在线服务和需要实际成本的集成。","Hébergement, services en ligne et intégrations ayant un coût réel.")),
        ("cache",L("SERVIÇOS ONLINE","ONLINE SERVICES","SERVICIOS ONLINE","在线服务","SERVICES EN LIGNE"),L("Backends para estatísticas, sincronização e funções conectadas quando fizer sentido.","Backends for statistics, synchronization, and connected features when they make sense.","Backends para estadísticas, sincronización y funciones conectadas cuando tengan sentido.","用于统计、同步和联网功能的后端服务。","Des backends pour les statistiques, la synchronisation et les fonctions connectées lorsque cela a du sens.")),
        ("maintenance",L("ESTABILIDADE & TESTES","STABILITY & TESTING","ESTABILIDAD Y PRUEBAS","稳定性与测试","STABILITÉ & TESTS"),L("Mais tempo e recursos para testes, correções e manutenção de builds futuras.","More time and resources for testing, fixes, and maintaining future builds.","Más tiempo y recursos para pruebas, correcciones y mantenimiento de futuras builds.","为测试、修复和维护未来版本投入更多资源。","Plus de temps et de ressources pour les tests, les corrections et la maintenance des futures versions.")),
        ("update",L("NOVOS RECURSOS","NEW FEATURES","NUEVOS RECURSOS","新功能","NOUVELLES FONCTIONS"),L("Ferramentas e melhorias maiores que precisam de investimento para sair do papel.","Larger tools and improvements that need investment to become real.","Herramientas y mejoras mayores que necesitan inversión para hacerse realidad.","让更大型的工具与改进真正落地。","Des outils et améliorations plus ambitieux qui nécessitent un investissement pour voir le jour.")),
    ]
    for idx,(ikey,title,desc) in enumerate(items):
        r,c=divmod(idx,2)
        card=ctk.CTkFrame(grid,fg_color=_mix(t["card"],t.get("card_active",t["card"]),.42),corner_radius=14,border_width=1,border_color=_mix(t.get("border",t["accent"]),t["accent"],.22))
        card.grid(row=r,column=c,sticky="nsew",padx=(0,5) if c==0 else (5,0),pady=5)
        row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=12,pady=12)
        img=self._ui_pictogram_ctk(ikey,30)
        ib=ctk.CTkFrame(row,width=44,height=44,corner_radius=12,fg_color=_mix(t.get("icon_bg",t["card_active"]),t["accent"],.08),border_width=1,border_color=_mix(t.get("border",t["accent"]),t["accent"],.28)); ib.pack(side="left",padx=(0,11)); ib.pack_propagate(False)
        ctk.CTkLabel(ib,text="" if img else "•",image=img,text_color=t["accent"]).place(relx=.5,rely=.5,anchor="center")
        tx=ctk.CTkFrame(row,fg_color="transparent"); tx.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(tx,text=title,text_color=t["text"],font=ctk.CTkFont(size=11,weight="bold"),anchor="w").pack(fill="x")
        ctk.CTkLabel(tx,text=desc,text_color=t.get("muted",t["text"]),font=ctk.CTkFont(size=9),wraplength=340,justify="left",anchor="w").pack(fill="x",pady=(3,0))

    thanks=self._section_card(
        body,
        L("OBRIGADO POR FORTALECER O PROJETO","THANK YOU FOR SUPPORTING THE PROJECT","GRACIAS POR FORTALECER EL PROYECTO","感谢你支持这个项目","MERCI DE SOUTENIR LE PROJET"),
        L("Depois de apoiar pelo celular, você pode tocar no botão abaixo.","After supporting from your phone, you can use the button below.","Después de apoyar desde el celular, puedes usar el botón de abajo.","在手机完成支持后，你可以点击下面的按钮。","Après avoir soutenu depuis votre téléphone, vous pouvez utiliser le bouton ci-dessous.")
    )
    thank_msg=ctk.CTkFrame(thanks,fg_color=_mix(t["card"],t["accent"],.08),corner_radius=13,border_width=1,border_color=_mix(t.get("border",t["accent"]),t["accent"],.25))
    thank_label=ctk.CTkLabel(thank_msg,text=L(
        "Valeu de verdade por fortalecer o ZKStrap. Seu apoio faz diferença no projeto e me ajuda a continuar investindo em melhorias, recursos novos e ideias cada vez melhores pro app. Obrigado por fazer parte disso.",
        "Thank you for genuinely supporting ZKStrap. Your support makes a real difference and helps me keep investing in improvements, new features, and better ideas for the app. Thanks for being part of it.",
        "Gracias de verdad por apoyar ZKStrap. Tu ayuda marca una diferencia real y me permite seguir invirtiendo en mejoras, nuevas funciones e ideas cada vez mejores para la app. Gracias por formar parte de esto.",
        "真的感谢你支持 ZKStrap。你的支持会对项目产生实际帮助，让我能继续投入改进、新功能和更好的想法。谢谢你成为这个项目的一部分。",
        "Merci sincèrement de soutenir ZKStrap. Votre aide fait une vraie différence et me permet de continuer à investir dans des améliorations, de nouvelles fonctions et de meilleures idées pour l’application. Merci d’en faire partie."
    ),text_color=t["text"],font=ctk.CTkFont(size=11),wraplength=840,justify="left",anchor="w")
    thank_label.pack(fill="x",padx=14,pady=13)

    def _show_support_thanks():
        try:
            if not thank_msg.winfo_ismapped(): thank_msg.pack(fill="x",padx=12,pady=(2,10))
            btn.configure(text=L("OBRIGADO PELO APOIO","THANK YOU FOR THE SUPPORT","GRACIAS POR EL APOYO","感谢支持","MERCI POUR VOTRE SOUTIEN"),state="disabled",fg_color=_mix(t["card_active"],t["accent"],.24),text_color=t["accent"])
            try:self.show_toast(L("VALEU DE VERDADE","THANK YOU","GRACIAS DE VERDAD","真的谢谢你","MERCI SINCÈREMENT"),L("Seu apoio fortalece o ZKStrap.","Your support strengthens ZKStrap.","Tu apoyo fortalece ZKStrap.","你的支持让 ZKStrap 更强大。","Votre soutien renforce ZKStrap."),kind="success",duration=3200)
            except Exception:pass
        except Exception:pass

    btn=ctk.CTkButton(thanks,text=L("JÁ APOIEI","I'VE SUPPORTED","YA APOYÉ","我已支持","J’AI SOUTENU"),command=_show_support_thanks,fg_color=t["accent"],hover_color=t["hover"],text_color="#070707",height=44,corner_radius=11,font=ctk.CTkFont(size=11,weight="bold"))
    btn.pack(fill="x",padx=12,pady=(4,7))
    ctk.CTkLabel(thanks,text=L(
        "O ZKStrap não acessa seu banco nem confirma pagamentos. O botão acima só exibe a mensagem de agradecimento.",
        "ZKStrap does not access your bank or verify payments. The button above only displays the thank-you message.",
        "ZKStrap no accede a tu banco ni verifica pagos. El botón de arriba solo muestra el mensaje de agradecimiento.",
        "ZKStrap 不会访问你的银行账户，也不会验证付款。上面的按钮只用于显示感谢信息。",
        "ZKStrap n’accède pas à votre banque et ne vérifie pas les paiements. Le bouton ci-dessus affiche uniquement le message de remerciement."
    ),text_color=t.get("muted",t["text"]),font=ctk.CTkFont(size=8),wraplength=850,justify="left",anchor="w").pack(fill="x",padx=14,pady=(0,12))

    return self.pages.get("support")'''

s=replace_method(s,"_lazy_build_page_support",support_method)
p.write_text(s,encoding="utf-8")
ast.parse(s)
print("v3.20.14 support Pix page applied: QR + 5 languages + 6 investment cards + thank-you flow")
