from pathlib import Path
import ast
import os

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')

def lines_pos(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos

def app_class(text):
    tree=ast.parse(text);cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.20.4 ani: class missing')
    return tree,cls

if 'APP_VERSION = "3.20.4"' not in s:raise SystemExit('v3.20.4 ani: wrong base')

helpers=r'''    def _ani_read_frames(self,path):
        frames=[];delays=[]
        try:
            import io,struct
            from PIL import Image
            data=Path(path).read_bytes()
            if data[:4]!=b"RIFF" or data[8:12]!=b"ACON":return frames,delays
            rates=[];pos=12
            while pos+8<=len(data):
                cid=data[pos:pos+4];size=struct.unpack_from('<I',data,pos+4)[0];payload=data[pos+8:pos+8+size]
                if cid==b'rate' and len(payload)>=4:
                    rates=[max(1,int(v))*1000//60 for v in struct.unpack('<'+'I'*(len(payload)//4),payload[:(len(payload)//4)*4])]
                pos+=8+size+(size&1)
            pos=0
            while True:
                i=data.find(b'icon',pos)
                if i<0 or i+8>len(data):break
                size=struct.unpack_from('<I',data,i+4)[0];payload=data[i+8:i+8+size];pos=i+8+size+(size&1)
                try:
                    im=Image.open(io.BytesIO(payload)).convert('RGBA');frames.append(im.copy())
                except Exception:pass
            delays=[rates[i] if i<len(rates) else 85 for i in range(len(frames))]
        except Exception:pass
        return frames,delays

    def _ani_preview_load(self,path):
        lab=getattr(self,'ani_preview_label',None);stat=getattr(self,'ani_preview_status',None)
        if lab is None:return
        self._ani_preview_generation=int(getattr(self,'_ani_preview_generation',0) or 0)+1;gen=self._ani_preview_generation
        if not path or not os.path.isfile(path):
            try:lab.configure(image=None,text='ANI');stat.configure(text=self._L('Nenhum .ANI importado ainda.','No .ANI imported yet.','Todavía no hay .ANI importado.','尚未导入 .ANI。','Aucun .ANI importé.'))
            except Exception:pass
            return
        try:
            from PIL import Image
            ext=os.path.splitext(path)[1].lower();frames=[];delays=[]
            if ext=='.ani':frames,delays=self._ani_read_frames(path)
            else:
                im=Image.open(path).convert('RGBA');frames=[im];delays=[500]
            rendered=[]
            for im in frames[:64]:
                box=Image.new('RGBA',(112,112),(0,0,0,0));im.thumbnail((92,92),Image.Resampling.LANCZOS);box.alpha_composite(im,((112-im.width)//2,(112-im.height)//2));rendered.append(ctk.CTkImage(light_image=box,dark_image=box,size=(112,112)))
            if not rendered:raise RuntimeError('no frames decoded')
            self._ani_preview_frames=rendered;self._ani_preview_delays=delays[:len(rendered)]
            try:stat.configure(text=self._L('ANIMADO','ANIMATED','ANIMADO','动画','ANIMÉ')+f'  •  {len(rendered)} frames  •  '+os.path.basename(path))
            except Exception:pass
            def tick(i=0):
                if gen!=getattr(self,'_ani_preview_generation',None):return
                try:
                    if not lab.winfo_exists():return
                    lab.configure(image=rendered[i%len(rendered)],text='')
                    delay=max(35,min(500,int(self._ani_preview_delays[i%len(self._ani_preview_delays)] if self._ani_preview_delays else 85)))
                    self.after(delay,lambda:tick(i+1))
                except Exception:pass
            tick()
        except Exception as exc:
            try:lab.configure(image=None,text='ANI');stat.configure(text=self._L('Não consegui decodificar este .ANI.','Could not decode this .ANI.','No pude decodificar este .ANI.','无法解析此 .ANI。','Impossible de décoder ce .ANI.')+f'  ({exc})')
            except Exception:pass

    def _pick_ani_preview(self):
        try:
            from tkinter import filedialog as fd
            src=fd.askopenfilename(title=self._L('Importar cursor animado','Import animated cursor','Importar cursor animado','导入动画光标','Importer un curseur animé'),filetypes=[('Animated Cursor','*.ani'),('Cursor','*.cur'),('All files','*.*')])
            if not src:return
            ext=os.path.splitext(src)[1].lower()
            if ext not in ('.ani','.cur'):raise ValueError(self._L('Use um arquivo .ANI ou .CUR.','Use an .ANI or .CUR file.','Usa un archivo .ANI o .CUR.','请使用 .ANI 或 .CUR 文件。','Utilisez un fichier .ANI ou .CUR.'))
            import shutil
            dst_dir=os.path.join(os.environ.get('LOCALAPPDATA',os.path.expanduser('~')),'ZKSTRAP','ANI_PREVIEW');os.makedirs(dst_dir,exist_ok=True)
            dst=os.path.join(dst_dir,'preview'+ext);shutil.copy2(src,dst);self.config_data['ani_preview_path']=dst;self.salvar_config_app();self._ani_preview_load(dst)
        except Exception as exc:
            try:self.show_toast('ANI',str(exc),kind='error')
            except Exception:pass
'''
_,cls=app_class(s);_,pos=lines_pos(s);insert_at=pos[cls.end_lineno];s=s[:insert_at]+"\n"+helpers.rstrip()+"\n"+s[insert_at:]

anchor='        self.after(40,self._refresh_cursor_preview)\n'
if anchor not in s:raise SystemExit('v3.20.4 ani: cursor anchor missing')
ui='''        self.after(40,self._refresh_cursor_preview)
        ani_card=ctk.CTkFrame(cursor_card,fg_color=t["card_active"],corner_radius=13,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.30));ani_card.pack(fill="x",padx=16,pady=(2,10))
        ani_box=ctk.CTkFrame(ani_card,width=135,height=135,fg_color=self._mix_hex(t["card_active"],t["accent"],.06),corner_radius=13);ani_box.pack(side="left",padx=12,pady=12);ani_box.pack_propagate(False)
        self.ani_preview_label=ctk.CTkLabel(ani_box,text="ANI",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=20,weight="bold"));self.ani_preview_label.place(relx=.5,rely=.5,anchor="center")
        ani_body=ctk.CTkFrame(ani_card,fg_color="transparent");ani_body.pack(side="left",fill="both",expand=True,padx=(2,12),pady=12)
        ctk.CTkLabel(ani_body,text=self._L("CURSOR ANIMADO // ANI LAB","ANIMATED CURSOR // ANI LAB","CURSOR ANIMADO // ANI LAB","动画光标 // ANI LAB","CURSEUR ANIMÉ // ANI LAB"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x")
        ctk.CTkLabel(ani_body,text=self._L("Importe um .ANI e veja a animação real dentro do ZKStrap. Os packs do Roblox continuam separados porque o jogo usa imagens PNG próprias para o cursor.","Import an .ANI and see the real animation inside ZKStrap. Roblox packs stay separate because the game uses its own PNG cursor images.","Importa un .ANI y mira la animación real dentro de ZKStrap. Los packs de Roblox siguen separados porque el juego usa sus propias imágenes PNG.","导入 .ANI 并在 ZKStrap 内查看真实动画。Roblox 光标包保持独立，因为游戏使用自己的 PNG 光标图像。","Importez un .ANI et voyez l’animation réelle dans ZKStrap. Les packs Roblox restent séparés car le jeu utilise ses propres images PNG."),wraplength=650,justify="left",anchor="w",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(fill="x",pady=(4,5))
        self.ani_preview_status=ctk.CTkLabel(ani_body,text="",text_color=t["text"],font=ctk.CTkFont(size=9,weight="bold"),anchor="w");self.ani_preview_status.pack(fill="x",pady=(2,8))
        ctk.CTkButton(ani_body,text=self._L("IMPORTAR .ANI / .CUR","IMPORT .ANI / .CUR","IMPORTAR .ANI / .CUR","导入 .ANI / .CUR","IMPORTER .ANI / .CUR"),command=self._pick_ani_preview,height=36,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(weight="bold")).pack(fill="x")
        self.after(50,lambda:self._ani_preview_load(str(self.config_data.get('ani_preview_path','') or '')))
'''
s=s.replace(anchor,ui,1)
for needle in ('def _ani_read_frames(self,path):','def _pick_ani_preview(self):','CURSOR ANIMADO // ANI LAB','ani_preview_path'):
    if needle not in s:raise SystemExit('v3.20.4 ani: missing '+needle)
ast.parse(s);path.write_text(s,encoding='utf-8');print('Applied v3.20.4 ANI preview lab')
