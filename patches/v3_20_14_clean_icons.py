from pathlib import Path
import ast, os, textwrap, re, hashlib

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')

def _class_and_lines(src):
    t=ast.parse(src)
    cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
    return t,cls,src.splitlines(True)

def _normalize_method(body):
    raw=textwrap.dedent(body).strip('\n').splitlines()
    return '\n'.join(raw)+'\n'

def replace_method(src,name,body):
    t,cls,lines=_class_and_lines(src)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'clean-icons method missing: {name}')
    start=sum(len(x) for x in lines[:node.lineno-1]); end=sum(len(x) for x in lines[:node.end_lineno])
    return src[:start]+textwrap.indent(_normalize_method(body),'    ')+src[end:]

def insert_after_docstring(src,name,statement):
    t,cls,lines=_class_and_lines(src)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'clean-icons insert anchor missing: {name}')
    if node.body and isinstance(node.body[0],ast.Expr) and isinstance(getattr(node.body[0],'value',None),ast.Constant) and isinstance(node.body[0].value.value,str):
        anchor=node.body[0].end_lineno
    else:
        anchor=node.lineno
    pos=sum(len(x) for x in lines[:anchor])
    return src[:pos]+textwrap.indent(statement.rstrip()+'\n','        ')+src[pos:]

clean_icon_method = r'''def _ui_pictogram_ctk(self, key, size=34):
    """Clean professional line icon system. Audio intentionally shares one icon."""
    try:
        from PIL import Image, ImageDraw
        t=TEMAS[self.tema_atual]
        key=str(key or "generic").lower().strip()
        cache=getattr(self,"_zk_pictogram_cache",None)
        if not isinstance(cache,dict):
            cache={}; self._zk_pictogram_cache=cache
        ck=("clean-v2",key,int(size),str(t.get("accent","#a855f7")),str(t.get("text","#ffffff")))
        if ck in cache:return cache[ck]
        n=64
        im=Image.new("RGBA",(n,n),(0,0,0,0)); d=ImageDraw.Draw(im)
        def col(v,alpha=255):
            v=str(v or "#ffffff")
            if v.startswith("#") and len(v)>=7:
                return (int(v[1:3],16),int(v[3:5],16),int(v[5:7],16),alpha)
            return (255,255,255,alpha)
        ac=col(t.get("accent","#a855f7"),235); fg=col(t.get("text","#ffffff"),220); mu=col(t.get("muted","#8a8a96"),150)
        def line(points,fill=ac,width=3): d.line(points,fill=fill,width=width,joint="curve")
        def rr(box,r=6,outline=ac,width=3,fill=None): d.rounded_rectangle(box,radius=r,outline=outline,width=width,fill=fill)
        def dot(x,y,r=3,fill=ac): d.ellipse((x-r,y-r,x+r,y+r),fill=fill)
        if key.startswith("audio:") or key in ("audio","music","sound"):
            for x,h in ((13,20),(24,34),(35,26),(46,40)): line((x,32-h//2,x,32+h//2),ac,5)
        elif key in ("textures","texture"):
            for y in range(2):
                for x in range(2): rr((12+x*22,12+y*22,28+x*22,28+y*22),3,ac if (x+y)%2==0 else fg,2)
        elif key in ("grass","vegetation"):
            line((13,49,20,26),fg); line((24,49,31,17),ac); line((35,49,40,25),fg); line((45,49,52,20),ac); line((10,50,55,50),mu,2)
        elif key in ("msaa","antialias"):
            line((12,48,48,14),ac,4); line((18,49,54,15),fg,2); dot(14,18,2,mu); dot(49,45,2,mu)
        elif key == "lod":
            rr((12,16,31,35),3,ac,3); rr((33,29,52,48),3,fg,3); line((28,36,36,28),mu,2); line((28,40,36,48),mu,2)
        elif key in ("frm_low","quality"):
            d.polygon([(32,11),(52,24),(52,46),(32,55),(12,46),(12,24)],outline=ac); line((12,24,32,36,52,24),fg,3); line((32,36,32,55),mu,2)
        elif key in ("voxelizer","lighting","light"):
            rr((18,18,46,46),4,ac,3); line((10,24,18,24),mu,2); line((46,24,54,24),mu,2); line((10,40,18,40),mu,2); line((46,40,54,40),mu,2); dot(32,32,5,fg)
        elif key in ("d3d11","gpu"):
            rr((15,18,49,46),6,ac,3); line((22,27,42,27),fg,2); line((22,36,37,36),fg,2)
            for x in (21,29,37,45): line((x,12,x,18),mu,2); line((x,46,x,52),mu,2)
        elif key in ("dpi","resolution","display"):
            rr((10,13,54,43),5,ac,3); line((25,50,39,50),fg,3); line((32,43,32,50),fg,3); line((16,34,25,25,34,34,43,25,50,32),mu,2)
        elif key in ("performance_boost","fps","performance"):
            d.arc((10,10,54,54),195,345,fill=ac,width=4); line((32,36,46,23),fg,4); dot(32,36,4,ac); line((17,42,47,42),mu,2)
        elif key == "fps_unlock":
            rr((11,16,53,44),5,ac,3); line((19,31,28,31),fg,3); line((34,25,44,25,44,37,34,37),fg,3); line((26,50,38,50),mu,3)
        elif key in ("gray_sky","sky"):
            d.arc((12,24,35,47),180,345,fill=fg,width=3); d.arc((24,15,49,45),185,345,fill=ac,width=3); line((14,45,51,45),mu,2)
        elif key in ("ping_boost","ping","network"):
            d.arc((11,16,53,58),205,335,fill=ac,width=3); d.arc((19,24,45,50),210,330,fill=fg,width=3); d.arc((27,32,37,42),215,325,fill=mu,width=3); dot(32,45,3,ac)
        elif key in ("telemetry_off","privacy"):
            d.ellipse((13,20,51,44),outline=ac,width=3); dot(32,32,6,fg); line((15,49,49,15),mu,4)
        elif key in ("micro_opt","cpu"):
            rr((18,18,46,46),5,ac,3); rr((25,25,39,39),3,fg,2)
            for x in (23,32,41): line((x,10,x,18),mu,2); line((x,46,x,54),mu,2)
            for y in (23,32,41): line((10,y,18,y),mu,2); line((46,y,54,y),mu,2)
        elif key in ("draco_aura","blox"):
            d.ellipse((14,14,50,50),outline=ac,width=3); d.ellipse((22,22,42,42),outline=fg,width=2); line((32,8,32,16),mu,2); line((32,48,32,56),mu,2)
        elif key in ("cursor","mouse"):
            d.polygon([(15,10),(15,48),(25,39),(32,54),(39,50),(32,36),(49,35)],outline=ac); line((17,13,45,33),fg,2)
        elif key in ("font","fonte"):
            line((18,49,29,16),ac,4); line((29,16,40,49),ac,4); line((22,37,36,37),fg,3); line((43,24,52,24),mu,2); line((47,24,47,48),mu,2)
        elif key in ("cache","storage"):
            d.ellipse((15,13,49,25),outline=ac,width=3); line((15,19,15,45),ac,3); line((49,19,49,45),ac,3); d.arc((15,35,49,51),0,180,fill=fg,width=3)
        elif key in ("update","updates"):
            d.arc((13,13,51,51),35,250,fill=ac,width=4); d.polygon([(12,17),(25,16),(18,28)],fill=fg); line((35,18,44,23),mu,2)
        elif key in ("theme","palette","customize"):
            d.ellipse((12,13,52,51),outline=ac,width=3); dot(24,24,3,fg); dot(37,21,3,mu); dot(44,33,3,fg); d.arc((28,34,48,54),80,230,fill=ac,width=3)
        elif key == "spotify":
            d.ellipse((12,12,52,52),outline=ac,width=3); d.arc((20,21,46,36),205,335,fill=fg,width=3); d.arc((22,28,44,40),205,335,fill=fg,width=3); d.arc((24,35,42,45),205,335,fill=fg,width=2)
        elif key in ("combo","build"):
            rr((11,18,29,36),4,ac,3); rr((35,28,53,46),4,fg,3); line((28,28,37,36),mu,3)
        elif key in ("roulette","random"):
            d.ellipse((13,13,51,51),outline=ac,width=3); line((32,13,32,51),mu,2); line((13,32,51,32),mu,2); dot(32,32,4,fg)
        elif key in ("creator","camera"):
            rr((11,20,53,47),5,ac,3); d.ellipse((25,25,39,39),outline=fg,width=3); line((20,20,25,14,39,14,44,20),mu,2)
        elif key in ("setups","sliders","settings"):
            for y,x in ((18,24),(32,40),(46,29)): line((12,y,52,y),mu,2); dot(x,y,4,ac if y!=32 else fg)
        elif key in ("maintenance","tools"):
            d.arc((12,12,38,38),40,250,fill=ac,width=4); line((32,34,51,53),fg,5); rr((44,44,55,55),3,fg,2)
        elif key in ("recovery","reset","roblox_tools"):
            d.arc((13,13,51,51),75,340,fill=ac,width=4); d.polygon([(12,19),(26,18),(18,30)],fill=fg); rr((24,25,42,43),4,mu,2)
        elif key in ("feedback","bug"):
            rr((14,16,50,43),7,ac,3); line((23,43,20,51,31,43),ac,3); dot(25,29,2,fg); dot(32,29,2,fg); dot(39,29,2,fg)
        elif key in ("support","about","info"):
            d.ellipse((14,14,50,50),outline=ac,width=3); line((32,28,32,43),fg,3); dot(32,22,2,fg)
        elif key in ("home","dashboard","status"):
            rr((12,12,29,29),4,ac,3); rr((35,12,52,29),4,fg,3); rr((12,35,29,52),4,fg,3); rr((35,35,52,52),4,ac,3)
        elif key in ("first_run","onboarding"):
            d.polygon([(18,51),(31,14),(44,51)],outline=ac); line((24,37,38,37),fg,3); dot(31,28,3,mu)
        else:
            h=hashlib.sha1(key.encode('utf-8','ignore')).digest(); rr((13,13,51,51),9,ac,3)
            y1=21+(h[0]%9); y2=34+(h[1]%9); x1=19+(h[2]%9); x2=37+(h[3]%9)
            line((19,y1,45,y1),fg,2); line((19,y2,45,y2),mu,2); dot(x1,27,3,ac); dot(x2,40,3,fg)
        img=ctk.CTkImage(light_image=im,dark_image=im,size=(int(size),int(size)))
        cache[ck]=img
        if len(cache)>240:
            for old in list(cache)[:-160]:cache.pop(old,None)
        return img
    except Exception:
        return None'''

section_card_method = r'''def _section_card(self,parent,title,description=""):
    t=TEMAS[self.tema_atual]; st=self._theme_style(); radius=max(14,st["card_radius"]); border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.34)
    card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border); card.pack(fill="x",padx=6,pady=8)
    ctk.CTkFrame(card,height=3,fg_color=self._mix_hex(t["card"],t["accent"],.72),corner_radius=2).pack(fill="x",padx=12)
    content=ctk.CTkFrame(card,fg_color="transparent"); content.pack(fill="both",expand=True,padx=16,pady=(10,12))
    head=ctk.CTkFrame(content,fg_color=self._mix_hex(t["card"],t.get("icon_bg",t["card_active"]),.62),corner_radius=12,border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.18)); head.pack(fill="x",pady=(0,6))
    icon=ctk.CTkFrame(head,width=48,height=48,corner_radius=12,fg_color=self._mix_hex(t.get("icon_bg",t["card_active"]),t["accent"],.08),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.36)); icon.pack(side="left",padx=(8,10),pady=7); icon.pack_propagate(False)
    text=str(title or "").upper()
    if "ROBLOX" in text: im=self._roblox_logo_ctk(31)
    else:
        key="section:"+text
        rules=((("INÍCIO","HOME","DASHBOARD","STATUS"),"home"),(("FPS","DESEMPENHO","PERFORMANCE","GRÁFICO","GRAPHIC"),"performance"),(("CURSOR",),"cursor"),(("FONTE","FONT"),"font"),(("PING","LATÊNCIA","LATENCY","REDE","NETWORK"),"network"),(("UPDATE","ATUALIZA"),"update"),(("CACHE",),"cache"),(("ÁUDIO","AUDIO","MÚSICA","MUSIC","SOUND","IDENTIDADE"),"audio"),(("RESOLU","DISPLAY"),"resolution"),(("SPOTIFY",),"spotify"),(("COMBO","BUILD","LOADOUT"),"combo"),(("ROULETTE","ROLETA"),"roulette"),(("CREATOR","CRIADOR"),"creator"),(("SETUP",),"setups"),(("TEMA","THEME","PERSONAL"),"theme"),(("MANUTEN","MAINTEN","FERRAMENT"),"maintenance"),(("RECUPERA","RESET","RESTAUR","ROBLOX TOOLS"),"recovery"),(("BUG","SUGEST","FEEDBACK"),"feedback"),(("SUPPORT","APOIO","SOBRE","ABOUT"),"about"),(("FIRST RUN","PRIMEIRO ACESSO","ONBOARD"),"first_run"))
        for words,k in rules:
            if any(w in text for w in words): key=k; break
        im=self._ui_pictogram_ctk(key,31)
    if im is not None: ctk.CTkLabel(icon,text="",image=im).pack(fill="both",expand=True)
    else: ctk.CTkLabel(icon,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=17,weight="bold")).pack(fill="both",expand=True)
    tw=ctk.CTkFrame(head,fg_color="transparent"); tw.pack(side="left",fill="x",expand=True,pady=7); ctk.CTkLabel(tw,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=14,weight="bold"),anchor="w").pack(anchor="w",fill="x")
    if description:
        full=str(description); short=self._ui_compact_copy(full,92); ctk.CTkButton(head,text="i",width=30,height=30,corner_radius=9,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["accent"],.35),text_color=t["accent"],command=lambda tt=title,dd=full:messagebox.showinfo(str(tt),str(dd),parent=self)).pack(side="right",padx=10); ctk.CTkLabel(content,text=short,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=8),wraplength=980,justify="left",anchor="w").pack(fill="x",anchor="w",padx=4,pady=(0,3))
    return content'''

s=replace_method(s,'_ui_pictogram_ctk',clean_icon_method)
s=replace_method(s,'_section_card',section_card_method)
lines=s.splitlines(True); filtered=[]
for ln in lines:
    if '("ai",L("ZK ASSIST"' in ln: continue
    if '{"title":"ZK Assist"' in ln: continue
    if '{"title":"PvP Coach"' in ln and '"page":"ai"' in ln: continue
    if '("ai","ZK ASSIST"),' in ln: continue
    filtered.append(ln)
s=''.join(filtered)
s=s.replace('"spotify": self._lazy_build_page_spotify, "ai": self._lazy_build_page_ai, "theme": self._lazy_build_page_theme','"spotify": self._lazy_build_page_spotify, "theme": self._lazy_build_page_theme')
s=s.replace('ZK Assist, ', '').replace('ZK Assist,','')
s=insert_after_docstring(s,'show_page','if key=="ai": key="feedback"')
ast.parse(s)
if '"page":"ai"' in s: raise SystemExit('clean-icons: an AI search route is still visible')
if '("ai","ZK ASSIST")' in s: raise SystemExit('clean-icons: AI nav entry still visible')
if '"ai": self._lazy_build_page_ai' in s: raise SystemExit('clean-icons: AI lazy builder still exposed')
if 'if key=="ai": key="feedback"' not in s: raise SystemExit('clean-icons: stale AI redirect missing')
p.write_text(s,encoding='utf-8',newline='\n')
print('v3.20.14 clean/pro icon pass applied')
print('source_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
