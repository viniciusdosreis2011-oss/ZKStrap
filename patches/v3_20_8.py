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
    if cls is None:raise SystemExit('v3.20.8: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.8: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


def rename_method(name,new_name):
    global s
    _,a,b=method_span(s,name)
    chunk=s[a:b]
    chunk,n=re.subn(r'^(\s*)def\s+'+re.escape(name)+r'\s*\(',r'\1def '+new_name+'(',chunk,count=1,flags=re.M)
    if n!=1:raise SystemExit('v3.20.8: rename failed '+name)
    s=s[:a]+chunk+s[b:]


if 'APP_VERSION = "3.20.7"' not in s:raise SystemExit('v3.20.8: expected v3.20.7 base')
s=s.replace('APP_VERSION = "3.20.7"','APP_VERSION = "3.20.8"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Real App Progressive Tutorial Unlock"',s,count=1)
if n!=1:raise SystemExit('v3.20.8: timestamp')

# Preserve the established completion/setup behavior, but guarantee that every
# nav item hidden by the progressive tutorial is restored on finish/skip/error.
rename_method('_tutorial_close','_tutorial_close_legacy_3208')

helpers=r'''    def _tutorial_nav_capture(self):
        """Snapshot navigation geometry once so future tabs can truly disappear."""
        if isinstance(getattr(self,"_tutorial_nav_stash",None),dict) and self._tutorial_nav_stash:
            return self._tutorial_nav_stash
        stash={}
        for key,btn in dict(getattr(self,"nav_buttons",{}) or {}).items():
            try:
                manager=str(btn.winfo_manager() or "")
                info={}
                if manager=="pack":info=dict(btn.pack_info())
                elif manager=="grid":info=dict(btn.grid_info())
                elif manager=="place":info=dict(btn.place_info())
                stash[key]={"widget":btn,"manager":manager,"info":info}
            except Exception:pass
        self._tutorial_nav_stash=stash
        return stash

    def _tutorial_nav_hide(self,key):
        item=(getattr(self,"_tutorial_nav_stash",{}) or {}).get(key)
        if not item:return
        btn=item.get("widget")
        try:
            mgr=str(btn.winfo_manager() or "")
            if mgr=="pack":btn.pack_forget()
            elif mgr=="grid":btn.grid_remove()
            elif mgr=="place":btn.place_forget()
        except Exception:pass

    def _tutorial_nav_show(self,key):
        item=(getattr(self,"_tutorial_nav_stash",{}) or {}).get(key)
        if not item:return
        btn=item.get("widget");manager=item.get("manager","");info=dict(item.get("info") or {})
        try:
            if str(btn.winfo_manager() or ""):
                try:btn.configure(state="normal")
                except Exception:pass
                return
            if manager=="pack":
                info.pop("in",None);info.pop("in_",None);btn.pack(**info)
            elif manager=="grid":
                # grid_remove remembers geometry on Tk; grid() is the safest restore.
                try:btn.grid()
                except Exception:
                    info.pop("in",None);info.pop("in_",None);btn.grid(**info)
            elif manager=="place":
                info.pop("in",None);info.pop("in_",None);btn.place(**info)
            try:btn.configure(state="normal")
            except Exception:pass
        except Exception:pass

    def _tutorial_nav_restore_all(self):
        stash=dict(getattr(self,"_tutorial_nav_stash",{}) or {})
        for key in stash:self._tutorial_nav_show(key)
        self._tutorial_nav_stash={}
        try:self.update_idletasks()
        except Exception:pass

    def _tutorial_apply_real_unlock(self,idx):
        """Unlock the REAL ZKStrap sidebar progressively; no screenshot/sample UI."""
        steps=self._tutorial_steps();idx=max(0,min(int(idx),len(steps)-1))
        max_idx=max(idx,int(getattr(self,"_tutorial_max_unlocked",0) or 0))
        self._tutorial_max_unlocked=max_idx
        self._tutorial_nav_capture()
        ordered=[str(step[0]) for step in steps]
        allowed=set(ordered[:max_idx+1])
        # During guided boot, destinations outside the guide also stay hidden.
        for key in list((getattr(self,"nav_buttons",{}) or {}).keys()):
            if str(key) in allowed:self._tutorial_nav_show(key)
            else:self._tutorial_nav_hide(key)
        try:
            nav=getattr(self,"nav_scroll",None);canvas=getattr(nav,"_parent_canvas",None)
            if canvas is not None and idx<=1:canvas.yview_moveto(0.0)
        except Exception:pass
        return max_idx

    def _tutorial_close(self,mark_complete=True,voltar_home=True):
        self._tutorial_preview_token=int(getattr(self,"_tutorial_preview_token",0) or 0)+1
        self._tutorial_nav_restore_all()
        self._tutorial_max_unlocked=0
        return self._tutorial_close_legacy_3208(mark_complete=mark_complete,voltar_home=voltar_home)
'''
_,cls=app_class(s);_,pos=lines_pos(s);insert_at=pos[cls.end_lineno]
s=s[:insert_at]+"\n"+helpers.rstrip()+"\n"+s[insert_at:]

# The tutorial now lives ON the real app. Only a compact guide card floats above
# it; the old full-screen shell, fake unlock rail and screenshot preview are gone.
replace_method('_abrir_tutorial_ui_3205',r'''    def _abrir_tutorial_ui_3205(self, primeiro_acesso=False):
        try:self._fechar_busca_universal()
        except Exception:pass
        try:self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception:pass
        self._tutorial_first_run=bool(primeiro_acesso)
        self._tutorial_replay=not bool(primeiro_acesso)
        self._tutorial_step_index=0
        self._tutorial_max_unlocked=0
        self._tutorial_step_ready=True
        self._tutorial_preview_token=int(getattr(self,"_tutorial_preview_token",0) or 0)+1
        self._tutorial_nav_stash={}
        self._tutorial_nav_capture()

        steps=self._tutorial_steps()
        if not steps:return
        first_page=str(steps[0][0])
        self._tutorial_apply_real_unlock(0)
        try:self.show_page(first_page,animate=False)
        except Exception:pass

        t=TEMAS[self.tema_atual];L=self._L
        # Compact controller only. It deliberately does NOT cover the application.
        card=ctk.CTkFrame(self,width=465,height=245,fg_color=t.get("panel",t["card"]),corner_radius=20,border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.72))
        card.place(relx=.985,rely=.975,anchor="se");card.pack_propagate(False);card.lift();self._tutorial_panel=card
        cap=ctk.CTkFrame(card,height=4,fg_color=t["accent"],corner_radius=0);cap.pack(fill="x")
        top=ctk.CTkFrame(card,fg_color="transparent");top.pack(fill="x",padx=15,pady=(13,3))
        ctk.CTkLabel(top,text="ZKSTRAP // GUIA NO APP",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        self._tutorial_count=ctk.CTkLabel(top,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"));self._tutorial_count.pack(side="right")
        self._tutorial_title=ctk.CTkLabel(card,text="",anchor="w",text_color=t["text"],font=ctk.CTkFont(size=18,weight="bold"));self._tutorial_title.pack(fill="x",padx=15,pady=(5,1))
        self._tutorial_body=ctk.CTkLabel(card,text="",anchor="w",justify="left",wraplength=425,text_color=t["text"],font=ctk.CTkFont(size=10));self._tutorial_body.pack(fill="x",padx=15,pady=(2,1))
        self._tutorial_tip=ctk.CTkLabel(card,text="",anchor="w",justify="left",wraplength=425,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9));self._tutorial_tip.pack(fill="x",padx=15,pady=(2,5))
        self._tutorial_progress=ctk.CTkProgressBar(card,height=5,progress_color=t["accent"],fg_color=t["card_active"]);self._tutorial_progress.pack(fill="x",padx=15,pady=(5,7))
        foot=ctk.CTkFrame(card,fg_color="transparent");foot.pack(fill="x",padx=15,pady=(0,13),side="bottom")
        self._tutorial_prev=ctk.CTkButton(foot,text="←",width=45,height=32,command=lambda:self._tutorial_move(-1),fg_color=t["card_active"],hover_color=t["hover"]);self._tutorial_prev.pack(side="left")
        self._tutorial_skip=ctk.CTkButton(foot,text=L("SAIR","EXIT","SALIR","退出","QUITTER"),width=66,height=32,command=self._tutorial_skip_click,fg_color="transparent",border_width=1,border_color=t["card_active"]);self._tutorial_skip.pack(side="left",padx=6)
        self._tutorial_next=ctk.CTkButton(foot,text="",width=155,height=32,command=lambda:self._tutorial_move(1),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=9,weight="bold"));self._tutorial_next.pack(side="right")
        self._tutorial_render_step()
''')

replace_method('_tutorial_render_step',r'''    def _tutorial_render_step(self):
        steps=self._tutorial_steps()
        if not steps:return
        idx=max(0,min(int(getattr(self,"_tutorial_step_index",0) or 0),len(steps)-1));self._tutorial_step_index=idx
        page,title,body,tip=steps[idx][:4]
        self._tutorial_step_ready=True
        self._tutorial_apply_real_unlock(idx)
        try:self.show_page(str(page),animate=False)
        except Exception:pass
        try:
            self._tutorial_title.configure(text=title)
            self._tutorial_body.configure(text=body)
            self._tutorial_tip.configure(text=tip)
            self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
            self._tutorial_progress.set((idx+1)/max(1,len(steps)))
            self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
            label=self._L("FINALIZAR  ✓","FINISH  ✓","FINALIZAR  ✓","完成  ✓","TERMINER  ✓") if idx==len(steps)-1 else self._L("LIBERAR PRÓXIMA  →","UNLOCK NEXT  →","DESBLOQUEAR SIGUIENTE  →","解锁下一项  →","DÉVERROUILLER LA SUITE  →")
            self._tutorial_next.configure(state="normal",text=label)
            panel=getattr(self,"_tutorial_panel",None)
            if panel is not None and panel.winfo_exists():panel.lift()
        except Exception:pass
''')

replace_method('_tutorial_move',r'''    def _tutorial_move(self,delta):
        steps=self._tutorial_steps();cur=int(getattr(self,"_tutorial_step_index",0) or 0);nxt=cur+int(delta)
        if nxt>=len(steps):
            self._tutorial_close(mark_complete=True)
            return
        self._tutorial_step_index=max(0,nxt)
        self._tutorial_render_step()
''')

# Dead preview helpers can remain for compatibility, but make sure the active
# tutorial does not call or expose them anywhere.
tree,cls=app_class(s);names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_tutorial_nav_capture','_tutorial_apply_real_unlock','_tutorial_nav_restore_all','_tutorial_close','_tutorial_close_legacy_3208','_abrir_tutorial_ui_3205','_tutorial_render_step','_tutorial_move'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.8: {unique} count={names.count(unique)}')

_,a,b=method_span(s,'_abrir_tutorial_ui_3205');active=s[a:b]
for forbidden in ('AMOSTRA REAL DA ABA','LIVE TAB SAMPLE','_tutorial_preview_label','_tutorial_capture_preview','DESBLOQUEADO'):
    if forbidden in active:raise SystemExit('v3.20.8: old tutorial shell remains: '+forbidden)
for needle in (
    'APP_VERSION = "3.20.8"',
    'Real App Progressive Tutorial Unlock',
    'ZKSTRAP // GUIA NO APP',
    'self._tutorial_apply_real_unlock(idx)',
    'self.show_page(str(page),animate=False)',
    'LIBERAR PRÓXIMA  →',
    'btn.pack_forget()',
    'self._tutorial_nav_restore_all()',
):
    if needle not in s:raise SystemExit('v3.20.8: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.8: unsafe repaint')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied v3.20.8 real-app progressive tutorial unlock')
