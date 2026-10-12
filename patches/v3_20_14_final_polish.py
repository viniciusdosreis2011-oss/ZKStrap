from pathlib import Path
import os, hashlib
root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
p = root / 'ZKStrap_v3_18_0.py'
s = p.read_text(encoding='utf-8')
repls = {
    'tab_first=tabs.add("First Run Lab")': 'tab_first=tabs.add(L("First Run Lab","First Run Lab","Laboratorio de primer inicio","首次运行实验室","Laboratoire du premier lancement"))',
    'prog=self._owner_admin_card(ps,pal,"PROGRESSION LAB",L(': 'prog=self._owner_admin_card(ps,pal,L("LAB DE PROGRESSÃO","PROGRESSION LAB","LAB DE PROGRESIÓN","进度实验室","LAB DE PROGRESSION"),L(',
    'ctk.CTkButton(ir,text="OWNER VAULT",command=lambda:self._owner_open_folder(_owner_vault_dir())': 'ctk.CTkButton(ir,text=L("COFRE OWNER","OWNER VAULT","BÓVEDA OWNER","OWNER 保管库","COFFRE OWNER"),command=lambda:self._owner_open_folder(_owner_vault_dir())',
    'win.title("OWNER // Blox Fruits Loadout")': 'win.title(self._L("OWNER // Build Blox Fruits","OWNER // Blox Fruits Loadout","OWNER // Build Blox Fruits","OWNER // Blox Fruits 配装","OWNER // Build Blox Fruits"))',
    'text="ZKSTRAP // COMPACT"': 'text=self._L("ZKSTRAP // COMPACTO","ZKSTRAP // COMPACT","ZKSTRAP // COMPACTO","ZKSTRAP // 紧凑","ZKSTRAP // COMPACT")',
    'first_desc=L("v1.0 nasceu como uma ferramenta simples para aplicar configurações/FastFlags no Roblox, detectar a pasta version-* e facilitar ajustes de desempenho.","v1.0 started as a simple tool to apply Roblox settings/FastFlags, detect the version-* folder and simplify performance tweaks.","v1.0 nació como una herramienta simple para aplicar ajustes/FastFlags en Roblox, detectar la carpeta version-* y facilitar optimizaciones.","v1.0 最初只是一个简单工具，用于应用 Roblox 设置/FastFlags、检测 version-* 文件夹并简化性能调整。","La v1.0 est née comme un outil simple pour appliquer des réglages/FastFlags Roblox, détecter le dossier version-* et faciliter les optimisations.")': 'first_desc=L("A primeira versão nasceu como uma ferramenta simples para aplicar configurações/FastFlags no Roblox, detectar a pasta version-* e facilitar ajustes de desempenho.","The first version started as a simple tool to apply Roblox settings/FastFlags, detect the version-* folder and simplify performance tweaks.","La primera versión nació como una herramienta simple para aplicar ajustes/FastFlags en Roblox, detectar la carpeta version-* y facilitar optimizaciones.","最初版本只是一个简单工具，用于应用 Roblox 设置/FastFlags、检测 version-* 文件夹并简化性能调整。","La première version est née comme un outil simple pour appliquer des réglages/FastFlags Roblox, détecter le dossier version-* et faciliter les optimisations.")',
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit(f'polish anchor missing: {old[:90]}')
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8',newline='\n')
print('polished', p, 'sha256', hashlib.sha256(p.read_bytes()).hexdigest())
