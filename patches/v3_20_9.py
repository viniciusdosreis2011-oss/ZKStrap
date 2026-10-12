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
    if cls is None:raise SystemExit('v3.20.9: ModernConfigApp missing')
    return tree,cls


def method_span(text,name):
    _,cls=app_class(text)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:raise SystemExit('v3.20.9: missing '+name)
    _,pos=lines_pos(text)
    return node,pos[node.lineno-1],pos[node.end_lineno]


def replace_method(name,new_src):
    global s
    _,a,b=method_span(s,name)
    s=s[:a]+new_src.rstrip()+"\n\n"+s[b:]


if 'APP_VERSION = "3.20.8"' not in s:raise SystemExit('v3.20.9: expected v3.20.8 base')
s=s.replace('APP_VERSION = "3.20.8"','APP_VERSION = "3.20.9"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Progressive Sidebar Order Restore"',s,count=1)
if n!=1:raise SystemExit('v3.20.9: timestamp')

# v3.20.8 remembered pack options but not the original sibling position.
# pack_forget() + pack() therefore appended every newly unlocked tab below all
# section headers. Store the creation/sibling index as well so a tab can be put
# back exactly where it originally lived.
replace_method('_tutorial_nav_capture',r'''    def _tutorial_nav_capture(self):
        """Snapshot each real nav button including its ORIGINAL sibling position."""
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
                master=btn.master
                try:children=list(master.winfo_children());index=children.index(btn)
                except Exception:index=999999
                stash[key]={"widget":btn,"manager":manager,"info":info,"master":master,"index":index}
            except Exception:pass
        self._tutorial_nav_stash=stash
        return stash
''')

replace_method('_tutorial_nav_show',r'''    def _tutorial_nav_show(self,key):
        item=(getattr(self,"_tutorial_nav_stash",{}) or {}).get(key)
        if not item:return
        btn=item.get("widget");manager=item.get("manager","");info=dict(item.get("info") or {})
        try:
            if str(btn.winfo_manager() or ""):
                try:btn.configure(state="normal")
                except Exception:pass
                return
            if manager=="pack":
                info.pop("in",None);info.pop("in_",None)
                master=item.get("master") or getattr(btn,"master",None)
                before=None
                if master is not None:
                    try:
                        siblings=list(master.winfo_children())
                        original_index=int(item.get("index",999999))
                        # winfo_children() keeps widget creation order even after
                        # pack_forget(). Find the first later sibling that is still
                        # packed and insert immediately before it.
                        for sibling in siblings[original_index+1:]:
                            if sibling is btn:continue
                            try:
                                if str(sibling.winfo_manager() or "")=="pack":
                                    before=sibling;break
                            except Exception:pass
                    except Exception:pass
                if before is not None:btn.pack(before=before,**info)
                else:btn.pack(**info)
            elif manager=="grid":
                try:btn.grid()
                except Exception:
                    info.pop("in",None);info.pop("in_",None);btn.grid(**info)
            elif manager=="place":
                info.pop("in",None);info.pop("in_",None);btn.place(**info)
            try:btn.configure(state="normal")
            except Exception:pass
        except Exception:pass
''')

replace_method('_tutorial_nav_restore_all',r'''    def _tutorial_nav_restore_all(self):
        stash=dict(getattr(self,"_tutorial_nav_stash",{}) or {})
        # Restore in original sibling order. _tutorial_nav_show also uses before=
        # so section headers, spacers and other sidebar widgets never move.
        ordered=sorted(stash.keys(),key=lambda k:int((stash.get(k) or {}).get("index",999999)))
        for key in ordered:self._tutorial_nav_show(key)
        try:
            self.update_idletasks()
            nav=getattr(self,"nav_scroll",None);canvas=getattr(nav,"_parent_canvas",None)
            if canvas is not None:
                try:canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception:pass
                canvas.yview_moveto(0.0)
        except Exception:pass
        self._tutorial_nav_stash={}
''')

# Normalize the real app after the floating guide is destroyed. This is intentionally
# lightweight: do not rebuild the whole interface (which could race the setup-choice
# modal); simply restore nav geometry, return home and reset the sidebar viewport.
replace_method('_tutorial_close',r'''    def _tutorial_close(self,mark_complete=True,voltar_home=True):
        self._tutorial_preview_token=int(getattr(self,"_tutorial_preview_token",0) or 0)+1
        self._tutorial_nav_restore_all()
        self._tutorial_max_unlocked=0
        result=self._tutorial_close_legacy_3208(mark_complete=mark_complete,voltar_home=voltar_home)
        def normalize_after_tutorial():
            try:
                if voltar_home:self.show_page("home",animate=False)
            except Exception:pass
            try:
                self.update_idletasks()
                nav=getattr(self,"nav_scroll",None);canvas=getattr(nav,"_parent_canvas",None)
                if canvas is not None:
                    try:canvas.configure(scrollregion=canvas.bbox("all"))
                    except Exception:pass
                    canvas.yview_moveto(0.0)
            except Exception:pass
        try:self.after(35,normalize_after_tutorial)
        except Exception:pass
        return result
''')

# When a page unlocks, keep the sidebar viewport near the newly unlocked real button
# without changing widget order. Early steps stay pinned at the top.
replace_method('_tutorial_apply_real_unlock',r'''    def _tutorial_apply_real_unlock(self,idx):
        """Unlock the REAL ZKStrap sidebar progressively in its native order."""
        steps=self._tutorial_steps();idx=max(0,min(int(idx),len(steps)-1))
        max_idx=max(idx,int(getattr(self,"_tutorial_max_unlocked",0) or 0))
        self._tutorial_max_unlocked=max_idx
        self._tutorial_nav_capture()
        ordered=[str(step[0]) for step in steps]
        allowed=set(ordered[:max_idx+1])
        for key in list((getattr(self,"nav_buttons",{}) or {}).keys()):
            if str(key) in allowed:self._tutorial_nav_show(key)
            else:self._tutorial_nav_hide(key)
        try:
            self.update_idletasks()
            nav=getattr(self,"nav_scroll",None);canvas=getattr(nav,"_parent_canvas",None)
            if canvas is not None:
                try:canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception:pass
                if idx<=2:canvas.yview_moveto(0.0)
        except Exception:pass
        return max_idx
''')

# Validation: order-aware pack restore must exist and the old plain append restore
# must no longer be the active implementation.
tree,cls=app_class(s);names=[n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
for unique in ('_tutorial_nav_capture','_tutorial_nav_show','_tutorial_nav_restore_all','_tutorial_apply_real_unlock','_tutorial_close'):
    if names.count(unique)!=1:raise SystemExit(f'v3.20.9: {unique} count={names.count(unique)}')
for needle in (
    'APP_VERSION = "3.20.9"',
    'Progressive Sidebar Order Restore',
    '"master":master,"index":index',
    'btn.pack(before=before,**info)',
    'ordered=sorted(stash.keys()',
    'canvas.yview_moveto(0.0)',
    'normalize_after_tutorial',
    'Unlock the REAL ZKStrap sidebar progressively in its native order.',
):
    if needle not in s:raise SystemExit('v3.20.9: missing '+needle)
if 'RedrawWindow(' in s:raise SystemExit('v3.20.9: unsafe repaint')
ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied v3.20.9 progressive sidebar order/restore fix')
