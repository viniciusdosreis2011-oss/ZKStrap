from pathlib import Path
import ast, os

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')

methods = r'''
    def _owner_cleanup_fmt_bytes(self,n):
        try:n=float(max(0,int(n or 0)))
        except Exception:n=0.0
        units=("B","KB","MB","GB","TB")
        i=0
        while n>=1024.0 and i<len(units)-1:
            n/=1024.0;i+=1
        return (f"{n:.0f} {units[i]}" if i<2 else f"{n:.2f} {units[i]}")

    def _owner_cleanup_is_admin(self):
        try:return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:return False

    def _owner_cleanup_specs(self):
        L=self._L
        local=os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        programdata=os.environ.get("PROGRAMDATA") or r"C:\\ProgramData"
        windir=os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\\Windows"
        temp=os.environ.get("TEMP") or os.environ.get("TMP") or os.path.join(local,"Temp")
        return [
            {
                "key":"crash_dumps",
                "title":L("DUMPS DE CRASH / BSOD","CRASH / BSOD DUMPS","DUMPS DE CRASH / BSOD","崩溃 / BSOD 转储","DUMPS CRASH / BSOD"),
                "desc":L("Inclui MEMORY.DMP, Minidump, CrashDumps e relatórios WER. Pode ocupar vários GB. Ao limpar, você perde apenas dados de diagnóstico de crashes antigos.","Includes MEMORY.DMP, Minidump, CrashDumps and WER reports. They can use several GB. Cleaning removes old crash diagnostics only.","Incluye MEMORY.DMP, Minidump, CrashDumps e informes WER. Pueden ocupar varios GB. Al limpiar solo se eliminan diagnósticos de fallos antiguos.","包括 MEMORY.DMP、Minidump、CrashDumps 和 WER 报告，可能占用数 GB。清理后只会丢失旧崩溃的诊断数据。","Inclut MEMORY.DMP, Minidump, CrashDumps et les rapports WER. Ils peuvent occuper plusieurs Go. Le nettoyage supprime uniquement les diagnostics d'anciens crashs."),
                "paths":[
                    ("file",os.path.join(windir,"MEMORY.DMP"),1),
                    ("dir",os.path.join(windir,"Minidump"),0),
                    ("dir",os.path.join(local,"CrashDumps"),0),
                    ("dir",os.path.join(programdata,"Microsoft","Windows","WER","ReportArchive"),0),
                    ("dir",os.path.join(programdata,"Microsoft","Windows","WER","ReportQueue"),0),
                ],
            },
            {
                "key":"shader_cache",
                "title":L("CACHE DE SHADERS NVIDIA / DIRECTX","NVIDIA / DIRECTX SHADER CACHE","CACHÉ DE SHADERS NVIDIA / DIRECTX","NVIDIA / DIRECTX 着色器缓存","CACHE SHADERS NVIDIA / DIRECTX"),
                "desc":L("DXCache, GLCache, ComputeCache e D3DSCache. É recriado automaticamente; o primeiro jogo depois da limpeza pode recompilar shaders e dar pequenas travadas temporárias.","DXCache, GLCache, ComputeCache and D3DSCache. They rebuild automatically; the first game after cleanup may recompile shaders and stutter briefly.","DXCache, GLCache, ComputeCache y D3DSCache. Se regeneran automáticamente; el primer juego puede recompilar shaders y tener pequeños tirones temporales.","DXCache、GLCache、ComputeCache 和 D3DSCache 会自动重建。清理后第一次运行游戏时可能会重新编译着色器并短暂卡顿。","DXCache, GLCache, ComputeCache et D3DSCache. Ils se recréent automatiquement ; le premier jeu peut recompiler les shaders et saccader brièvement."),
                "paths":[
                    ("dir",os.path.join(local,"NVIDIA","DXCache"),0),
                    ("dir",os.path.join(local,"NVIDIA","GLCache"),0),
                    ("dir",os.path.join(local,"NVIDIA","ComputeCache"),0),
                    ("dir",os.path.join(local,"NVIDIA Corporation","NV_Cache"),0),
                    ("dir",os.path.join(programdata,"NVIDIA Corporation","NV_Cache"),0),
                    ("dir",os.path.join(local,"D3DSCache"),0),
                ],
            },
            {
                "key":"user_temp",
                "title":L("TEMPORÁRIOS DO USUÁRIO","USER TEMP FILES","TEMPORALES DEL USUARIO","用户临时文件","FICHIERS TEMPORAIRES UTILISATEUR"),
                "desc":L("Arquivos da pasta TEMP com mais de 24 horas. Arquivos novos e em uso ficam de fora.","Files in your TEMP folder older than 24 hours. New and in-use files are left alone.","Archivos de TEMP con más de 24 horas. Los archivos nuevos y en uso no se tocan.","仅清理 TEMP 中超过 24 小时的文件；新文件和正在使用的文件不会处理。","Fichiers du dossier TEMP âgés de plus de 24 h. Les fichiers récents et utilisés sont laissés tranquilles."),
                "paths":[("dir",temp,24)],
            },
            {
                "key":"windows_temp",
                "title":L("TEMPORÁRIOS DO WINDOWS","WINDOWS TEMP FILES","TEMPORALES DE WINDOWS","Windows 临时文件","FICHIERS TEMPORAIRES WINDOWS"),
                "desc":L("Somente arquivos de Windows\\Temp com mais de 24 horas. Alguns itens podem exigir que o ZKStrap seja aberto como administrador.","Only files in Windows\\Temp older than 24 hours. Some items may require running ZKStrap as administrator.","Solo archivos de Windows\\Temp con más de 24 horas. Algunos pueden requerir ejecutar ZKStrap como administrador.","仅清理 Windows\\Temp 中超过 24 小时的文件；部分项目可能需要以管理员身份运行 ZKStrap。","Uniquement les fichiers de Windows\\Temp âgés de plus de 24 h. Certains peuvent nécessiter d'exécuter ZKStrap en administrateur."),
                "paths":[("dir",os.path.join(windir,"Temp"),24)],
            },
        ]

    def _owner_cleanup_iter_files(self,spec):
        now=time.time()
        seen=set()
        for kind,raw_path,min_age_hours in spec.get("paths",[]):
            try:path=os.path.abspath(os.path.expandvars(os.path.expanduser(str(raw_path))))
            except Exception:continue
            key=os.path.normcase(path)
            if key in seen:continue
            seen.add(key)
            if kind=="file":
                try:
                    if not os.path.isfile(path) or os.path.islink(path):continue
                    st=os.stat(path,follow_symlinks=False)
                    if min_age_hours and (now-st.st_mtime)<float(min_age_hours)*3600:continue
                    yield path,int(st.st_size)
                except Exception:continue
                continue
            if not os.path.isdir(path) or os.path.islink(path):continue
            try:
                for base,dirs,files in os.walk(path,topdown=True,followlinks=False):
                    dirs[:]=[d for d in dirs if not os.path.islink(os.path.join(base,d))]
                    for name in files:
                        fp=os.path.join(base,name)
                        try:
                            if os.path.islink(fp):continue
                            st=os.stat(fp,follow_symlinks=False)
                            if min_age_hours and (now-st.st_mtime)<float(min_age_hours)*3600:continue
                            yield fp,int(st.st_size)
                        except Exception:continue
            except Exception:continue

    def _owner_cleanup_scan(self):
        if bool(getattr(self,"_owner_cleanup_busy",False)):return
        self._owner_cleanup_busy=True
        try:
            lbl=getattr(self,"_owner_cleanup_status",None)
            if lbl is not None and lbl.winfo_exists():lbl.configure(text=self._L("Analisando espaço seguro para liberar...","Scanning safe reclaimable space...","Analizando espacio seguro para liberar...","正在扫描可安全释放的空间...","Analyse de l'espace libérable en toute sécurité..."))
            btn=getattr(self,"_owner_cleanup_scan_btn",None)
            if btn is not None and btn.winfo_exists():btn.configure(state="disabled")
            clean=getattr(self,"_owner_cleanup_clean_btn",None)
            if clean is not None and clean.winfo_exists():clean.configure(state="disabled")
        except Exception:pass
        def work():
            sizes={};counts={}
            for spec in self._owner_cleanup_specs():
                total=0;count=0
                for _,size in self._owner_cleanup_iter_files(spec):total+=max(0,int(size));count+=1
                sizes[spec["key"]]=total;counts[spec["key"]]=count
            self.after(0,lambda:self._owner_cleanup_finish_scan(sizes,counts))
        threading.Thread(target=work,daemon=True).start()

    def _owner_cleanup_finish_scan(self,sizes,counts):
        self._owner_cleanup_sizes=dict(sizes or {});self._owner_cleanup_counts=dict(counts or {});self._owner_cleanup_busy=False
        try:
            total=sum(int(v or 0) for v in self._owner_cleanup_sizes.values())
            labels=getattr(self,"_owner_cleanup_size_labels",{}) or {}
            for key,lbl in labels.items():
                if lbl is not None and lbl.winfo_exists():lbl.configure(text=self._owner_cleanup_fmt_bytes(self._owner_cleanup_sizes.get(key,0)))
            status=getattr(self,"_owner_cleanup_status",None)
            if status is not None and status.winfo_exists():
                suffix="" if self._owner_cleanup_is_admin() else self._L("  // alguns arquivos do Windows podem exigir ADMIN","  // some Windows files may require ADMIN","  // algunos archivos de Windows pueden requerir ADMIN","  // 部分 Windows 文件可能需要管理员权限","  // certains fichiers Windows peuvent nécessiter ADMIN")
                status.configure(text=self._L("Pode liberar até ","Can safely reclaim up to ","Puede liberar de forma segura hasta ","最多可安全释放 ","Peut libérer en toute sécurité jusqu'à ")+self._owner_cleanup_fmt_bytes(total)+suffix)
            for attr in ("_owner_cleanup_scan_btn","_owner_cleanup_clean_btn"):
                b=getattr(self,attr,None)
                if b is not None and b.winfo_exists():b.configure(state="normal")
        except Exception:pass

    def _owner_cleanup_delete_selected(self):
        if bool(getattr(self,"_owner_cleanup_busy",False)):return
        vars_map=getattr(self,"_owner_cleanup_vars",{}) or {}
        selected=[spec for spec in self._owner_cleanup_specs() if bool(vars_map.get(spec["key"]) and vars_map[spec["key"]].get())]
        if not selected:
            self.show_toast(self._L("LIMPEZA SEGURA","SAFE CLEANUP","LIMPIEZA SEGURA","安全清理","NETTOYAGE SÛR"),self._L("Selecione pelo menos uma categoria.","Select at least one category.","Selecciona al menos una categoría.","请至少选择一个分类。","Sélectionnez au moins une catégorie."),kind="warning")
            return
        known=getattr(self,"_owner_cleanup_sizes",{}) or {}
        total=sum(int(known.get(x["key"],0) or 0) for x in selected)
        names="\n".join("• "+str(x["title"]) for x in selected)
        msg=self._L(
            "Excluir permanentemente os arquivos descartáveis destas categorias?\n\n{names}\n\nEspaço estimado: {size}\n\nCaches serão recriados quando necessário. Dumps de crash são apenas diagnóstico. O ZKStrap NUNCA toca WinSxS, Windows\\Installer, Downloads, Documentos ou arquivos pessoais.",
            "Permanently delete disposable files from these categories?\n\n{names}\n\nEstimated space: {size}\n\nCaches rebuild when needed. Crash dumps are diagnostics only. ZKStrap NEVER touches WinSxS, Windows\\Installer, Downloads, Documents, or personal files.",
            "¿Eliminar permanentemente los archivos descartables de estas categorías?\n\n{names}\n\nEspacio estimado: {size}\n\nLas cachés se regeneran cuando haga falta. Los dumps son solo diagnóstico. ZKStrap NUNCA toca WinSxS, Windows\\Installer, Descargas, Documentos ni archivos personales.",
            "永久删除这些分类中的可丢弃文件吗？\n\n{names}\n\n预计空间：{size}\n\n缓存会在需要时自动重建；崩溃转储仅用于诊断。ZKStrap 绝不会触碰 WinSxS、Windows\\Installer、下载、文档或个人文件。",
            "Supprimer définitivement les fichiers jetables de ces catégories ?\n\n{names}\n\nEspace estimé : {size}\n\nLes caches se recréent au besoin. Les dumps servent uniquement au diagnostic. ZKStrap ne touche JAMAIS WinSxS, Windows\\Installer, Téléchargements, Documents ni les fichiers personnels."
        ).format(names=names,size=self._owner_cleanup_fmt_bytes(total))
        if not messagebox.askyesno(self._L("LIMPEZA SEGURA","SAFE CLEANUP","LIMPIEZA SEGURA","安全清理","NETTOYAGE SÛR"),msg,parent=getattr(self,"_owner_panel",self)):return
        self._owner_cleanup_busy=True
        try:
            status=getattr(self,"_owner_cleanup_status",None)
            if status is not None and status.winfo_exists():status.configure(text=self._L("Limpando arquivos descartáveis...","Cleaning disposable files...","Limpiando archivos descartables...","正在清理可丢弃文件...","Nettoyage des fichiers jetables..."))
            for attr in ("_owner_cleanup_scan_btn","_owner_cleanup_clean_btn"):
                b=getattr(self,attr,None)
                if b is not None and b.winfo_exists():b.configure(state="disabled")
        except Exception:pass
        def work():
            freed=0;deleted=0;failed=0
            for spec in selected:
                files=list(self._owner_cleanup_iter_files(spec))
                for fp,size in files:
                    try:
                        os.remove(fp);freed+=max(0,int(size));deleted+=1
                    except FileNotFoundError:pass
                    except Exception:failed+=1
                for kind,raw_path,_ in spec.get("paths",[]):
                    if kind!="dir":continue
                    try:
                        root=os.path.abspath(os.path.expandvars(os.path.expanduser(str(raw_path))))
                        if not os.path.isdir(root) or os.path.islink(root):continue
                        for base,dirs,_files in os.walk(root,topdown=False,followlinks=False):
                            if os.path.normcase(base)==os.path.normcase(root):continue
                            try:os.rmdir(base)
                            except Exception:pass
                    except Exception:pass
            self.after(0,lambda:self._owner_cleanup_finish_delete(freed,deleted,failed))
        threading.Thread(target=work,daemon=True).start()

    def _owner_cleanup_finish_delete(self,freed,deleted,failed):
        self._owner_cleanup_busy=False
        try:
            msg=self._L("Liberado: ","Freed: ","Liberado: ","已释放：","Libéré : ")+self._owner_cleanup_fmt_bytes(freed)+self._L("  // arquivos removidos: ","  // files removed: ","  // archivos eliminados: ","  // 已删除文件：","  // fichiers supprimés : ")+str(int(deleted))
            if failed:msg+=self._L("  // ignorados/sem acesso: ","  // skipped/no access: ","  // omitidos/sin acceso: ","  // 跳过/无权限：","  // ignorés/sans accès : ")+str(int(failed))
            status=getattr(self,"_owner_cleanup_status",None)
            if status is not None and status.winfo_exists():status.configure(text=msg)
            self.show_toast(self._L("LIMPEZA CONCLUÍDA","CLEANUP COMPLETE","LIMPIEZA COMPLETA","清理完成","NETTOYAGE TERMINÉ"),msg,kind="success",duration=4200)
            self.after(250,self._owner_cleanup_scan)
        except Exception:pass
'''

anchor='    def _owner_refresh_panel_status(self):\n'
if '_owner_cleanup_specs' not in s:
    if anchor not in s: raise SystemExit('owner cleanup method anchor missing')
    s=s.replace(anchor,methods+'\n'+anchor,1)

ui_anchor=';internal=self._owner_admin_card(ds,pal,L("ARQUIVOS INTERNOS / DEBUG"'
if 'LIMPEZA SEGURA // DISCO' not in s:
    idx=s.find(ui_anchor)
    if idx<0: raise SystemExit('owner data/debug UI anchor missing')
    cleanup_ui=''';cleanup=self._owner_admin_card(ds,pal,L("LIMPEZA SEGURA // DISCO","SAFE DISK CLEANUP","LIMPIEZA SEGURA // DISCO","安全磁盘清理","NETTOYAGE DISQUE SÛR"),L("Analisa e remove somente caches, temporários e dumps conhecidos. Nada de pastas críticas do Windows ou arquivos pessoais.","Scans and removes only known caches, temp files, and dumps. No critical Windows folders or personal files.","Analiza y elimina solo cachés, temporales y dumps conocidos. Nada de carpetas críticas de Windows ni archivos personales.","仅扫描并清理已知缓存、临时文件和转储，不会触碰 Windows 关键目录或个人文件。","Analyse et supprime uniquement les caches, temporaires et dumps connus. Aucun dossier Windows critique ni fichier personnel."));self._owner_cleanup_vars={};self._owner_cleanup_size_labels={};self._owner_cleanup_sizes={};self._owner_cleanup_counts={}
        for spec in self._owner_cleanup_specs():
            row=ctk.CTkFrame(cleanup,fg_color=pal["card"],corner_radius=10,border_width=1,border_color=pal["border"]);row.pack(fill="x",padx=8,pady=4);var=ctk.BooleanVar(value=True);self._owner_cleanup_vars[spec["key"]]=var;ctk.CTkCheckBox(row,text="",variable=var,fg_color=pal["accent"],hover_color=pal["accent2"],width=28).pack(side="left",padx=(10,4),pady=10);tx=ctk.CTkFrame(row,fg_color="transparent");tx.pack(side="left",fill="x",expand=True,padx=(2,8),pady=8);ctk.CTkLabel(tx,text=spec["title"],text_color=pal["text"],font=ctk.CTkFont(size=10,weight="bold"),anchor="w").pack(fill="x");ctk.CTkLabel(tx,text=spec["desc"],text_color=pal["muted"],font=ctk.CTkFont(size=8),wraplength=760,justify="left",anchor="w").pack(fill="x",pady=(2,0));sz=ctk.CTkLabel(row,text="—",text_color=pal["accent"],font=ctk.CTkFont(family="Consolas",size=11,weight="bold"),width=112,anchor="e");sz.pack(side="right",padx=12);self._owner_cleanup_size_labels[spec["key"]]=sz
        self._owner_cleanup_status=ctk.CTkLabel(cleanup,text=L("Pronto para analisar.","Ready to scan.","Listo para analizar.","准备扫描。","Prêt à analyser."),text_color=pal["muted"],font=ctk.CTkFont(family="Consolas",size=8),anchor="w");self._owner_cleanup_status.pack(fill="x",padx=10,pady=(5,5));cr=ctk.CTkFrame(cleanup,fg_color="transparent");cr.pack(fill="x",padx=8,pady=(2,8));self._owner_cleanup_scan_btn=ctk.CTkButton(cr,text=L("ANALISAR ESPAÇO","SCAN SPACE","ANALIZAR ESPACIO","扫描空间","ANALYSER L'ESPACE"),command=self._owner_cleanup_scan,fg_color=pal["card"],hover_color=pal["border"],border_width=1,border_color=pal["accent"],text_color=pal["accent"],height=38);self._owner_cleanup_scan_btn.pack(side="left",expand=True,fill="x",padx=(0,4));self._owner_cleanup_clean_btn=ctk.CTkButton(cr,text=L("LIMPAR SELECIONADOS","CLEAN SELECTED","LIMPIAR SELECCIONADOS","清理所选","NETTOYER LA SÉLECTION"),command=self._owner_cleanup_delete_selected,fg_color=pal["accent"],hover_color=pal["accent2"],text_color="#08080B",height=38,font=ctk.CTkFont(weight="bold"));self._owner_cleanup_clean_btn.pack(side="left",expand=True,fill="x",padx=(4,0));self.after(120,self._owner_cleanup_scan);internal=self._owner_admin_card(ds,pal,L("ARQUIVOS INTERNOS / DEBUG"'''
    s=s[:idx]+cleanup_ui+s[idx+len(';internal=self._owner_admin_card(ds,pal,L("ARQUIVOS INTERNOS / DEBUG"'):]

p.write_text(s,encoding='utf-8')
ast.parse(s)
print('v3.20.14 admin safe disk cleanup applied')
