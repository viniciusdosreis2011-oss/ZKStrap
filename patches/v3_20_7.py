from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def lines_pos(text):
    lines=text.splitlines(True);pos=[0];total=0
    for line in lines:
        total+=len(line);pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:raise SystemExit('v3.20.7: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.7: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


if 'APP_VERSION = "3.20.6"' not in s:raise SystemExit('v3.20.7: expected v3.20.6 base')
s=s.replace('APP_VERSION = "3.20.6"','APP_VERSION = "3.20.7"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Non Recursive Tutorial Preview Capture"',s,count=1)
if n!=1:raise SystemExit('v3.20.7: timestamp')

# v3.20.6 could capture the tutorial overlay itself because ImageGrab ran in the
# same event turn as place_forget(). Windows/DWM had not necessarily repainted
# the underlying app yet. Split capture into two phases: hide + render page,
# then wait briefly for the real window to repaint before grabbing pixels.
replace_method('_tutorial_capture_preview',r'''    def _tutorial_capture_preview(self,page,token):
        if token!=getattr(self,"_tutorial_preview_token",None):return
        cover=getattr(self,"_tutorial_panel",None)
        if cover is None:return
        try:
            # Hide the guide first and render only the requested real page.
            cover.place_forget()
            self.show_page(page,animate=False)
            self.update_idletasks()
            # Do not grab in this same event turn. Give DWM time to replace the
            # tutorial pixels, otherwise the preview becomes tutorial-in-tutorial.
            self.after(55,lambda p=page,tok=token,cov=cover:self._tutorial_capture_preview_finish(p,tok,cov))
        except Exception:
            try:cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift()
            except Exception:pass
            self._tutorial_preview_failed(token)

    def _tutorial_capture_preview_finish(self,page,token,cover):
        if token!=getattr(self,"_tutorial_preview_token",None):
            try:cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift()
            except Exception:pass
            return
        try:
            # Flush a full Tk event pass after the delay so native child windows
            # are painted before ImageGrab reads the screen.
            self.update()
            from PIL import ImageGrab,ImageOps,Image
            host=self.main_container
            x=int(host.winfo_rootx());y=int(host.winfo_rooty())
            w=max(2,int(host.winfo_width()));h=max(2,int(host.winfo_height()))
            shot=ImageGrab.grab(bbox=(x,y,x+w,y+h)).convert("RGBA")
            if token!=getattr(self,"_tutorial_preview_token",None):return

            # Focus on the actual page content instead of repeating the whole app
            # chrome/sidebar inside the tutorial sample.
            sw,sh=shot.size
            left=max(0,int(sw*.155));top=max(0,int(sh*.075))
            right=max(left+2,int(sw*.985));bottom=max(top+2,int(sh*.97))
            shot=shot.crop((left,top,right,bottom))
            shot=ImageOps.fit(shot,(820,390),method=Image.Resampling.LANCZOS)
            img=ctk.CTkImage(light_image=shot,dark_image=shot,size=(820,390))
            self._tutorial_preview_img=img
            lab=getattr(self,"_tutorial_preview_label",None)
            if lab is not None and lab.winfo_exists():
                lab.configure(image=img,text="")
        except Exception:
            self._tutorial_preview_failed(token)
        finally:
            try:
                if cover is not None and cover.winfo_exists():
                    cover.place(x=0,y=0,relwidth=1,relheight=1);cover.lift()
            except Exception:pass

    def _tutorial_preview_failed(self,token):
        if token!=getattr(self,"_tutorial_preview_token",None):return
        try:
            lab=getattr(self,"_tutorial_preview_label",None)
            if lab is not None and lab.winfo_exists():
                lab.configure(image=None,text=self._L(
                    "Não consegui gerar a prévia desta aba.",
                    "I couldn't generate this tab preview.",
                    "No pude generar la vista previa de esta pestaña.",
                    "无法生成此页面预览。",
                    "Impossible de générer l’aperçu de cet onglet."
                ))
        except Exception:pass
''')

# Slow captures should never queue up when the user clicks Next repeatedly.
# Reset the preview label immediately and use a slightly delayed capture request;
# token validation in both phases discards all stale work.
replace_method('_tutorial_render_step',r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps();idx=max(0,min(int(getattr(self,'_tutorial_step_index',0) or 0),len(steps)-1));self._tutorial_step_index=idx;page,title,body,tip=steps[idx][:4];self._tutorial_step_ready=True
        try:
            self._tutorial_title.configure(text=title);self._tutorial_body.configure(text=body);self._tutorial_tip.configure(text=tip)
            self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
            self._tutorial_progress.set((idx+1)/max(1,len(steps)))
            self._tutorial_prev.configure(state='disabled' if idx==0 else 'normal')
            lab=getattr(self,'_tutorial_preview_label',None)
            if lab is not None and lab.winfo_exists():
                lab.configure(image=None,text=self._L("Carregando prévia...","Loading preview...","Cargando vista previa...","正在加载预览...","Chargement de l’aperçu..."))
        except Exception:pass
        label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("PRÓXIMO  →","NEXT  →","SIGUIENTE  →","下一步  →","SUIVANT  →")
        try:self._tutorial_next.configure(state='normal',text=label);self._tutorial_refresh_unlocks()
        except Exception:pass
        self._tutorial_preview_token=int(getattr(self,'_tutorial_preview_token',0) or 0)+1;token=self._tutorial_preview_token
        try:self.after(8,lambda p=page,tok=token:self._tutorial_capture_preview(p,tok))
        except Exception:pass
''')

# Make the guide sample area a little less dominant: the tutorial should explain
# the current feature, not look like a full copy of the entire application.
_,a,b=method_span(s,'_abrir_tutorial_ui_3205')
chunk=s[a:b]
chunk=chunk.replace("shell=ctk.CTkFrame(cover,width=1260,height=690", "shell=ctk.CTkFrame(cover,width=1180,height=680",1)
chunk=chunk.replace("rail=ctk.CTkFrame(body,width=225", "rail=ctk.CTkFrame(body,width=205",1)
chunk=chunk.replace("guide=ctk.CTkFrame(center,height=185", "guide=ctk.CTkFrame(center,height=205",1)
chunk=chunk.replace("wraplength=870", "wraplength=800",2)
s=s[:a]+chunk+s[b:]

# Structural validation.
tree,cls=app_class(s);names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_tutorial_capture_preview','_tutorial_capture_preview_finish','_tutorial_preview_failed','_tutorial_render_step','_abrir_tutorial_ui_3205'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.7: {unique} count={names.count(unique)}')
for needle in (
    'APP_VERSION = "3.20.7"',
    'self.after(55,lambda p=page,tok=token,cov=cover:self._tutorial_capture_preview_finish',
    'Focus on the actual page content instead of repeating the whole app',
    'shot=shot.crop((left,top,right,bottom))',
    'size=(820,390)',
    'Carregando prévia...',
):
    if needle not in s:raise SystemExit('v3.20.7: missing '+needle)
if 'ImageGrab.grab' not in s:raise SystemExit('v3.20.7: preview grab missing')
if 'RedrawWindow(' in s:raise SystemExit('v3.20.7: unsafe repaint')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied v3.20.7 non-recursive tutorial preview fix')
