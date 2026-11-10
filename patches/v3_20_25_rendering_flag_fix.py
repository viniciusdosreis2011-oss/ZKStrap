from pathlib import Path
import ast
import os
import re

root = Path(os.environ.get("ZK_SOURCE_DIR", "."))
path = root / "ZKStrap_v3_18_0.py"
s = path.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"v3.20.25: expected one {label}, found {count}")
    s = s.replace(old, new, 1)

def method_span(text, class_name, method_name):
    tree = ast.parse(text)
    cls = next(
        (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name),
        None,
    )
    if cls is None:
        raise SystemExit(f"v3.20.25: class {class_name} missing")
    node = next(
        (
            n for n in cls.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == method_name
        ),
        None,
    )
    if node is None:
        raise SystemExit(f"v3.20.25: method {class_name}.{method_name} missing")
    lines = text.splitlines(True)
    offsets = [0]
    total = 0
    for line in lines:
        total += len(line)
        offsets.append(total)
    return offsets[node.lineno - 1], offsets[node.end_lineno]

def replace_method(class_name, method_name, source):
    global s
    start, end = method_span(s, class_name, method_name)
    s = s[:start] + source.rstrip() + "\n\n" + s[end:]

if 'APP_VERSION = "3.20.24"' not in s:
    raise SystemExit("v3.20.25: expected v3.20.24 base")

s = s.replace('APP_VERSION = "3.20.24"', 'APP_VERSION = "3.20.25"', 1)
s, n = re.subn(
    r'BUILD_TIMESTAMP = "[^"]*"',
    'BUILD_TIMESTAMP = "Roblox FRM Override Removed"',
    s,
    count=1,
)
if n != 1:
    raise SystemExit("v3.20.25: BUILD_TIMESTAMP missing")

# Roblox's Nov 5, 2026 graphics-quality change made this override also pin
# draw distance. Keep the key in the managed-key set below so applying settings
# removes stale copies from ClientAppSettings.json, but never write it again.
replace_once(
    '            "DFIntDebugFRMQualityLevelOverride": 1,\n',
    '',
    "base-module FRM override",
)
replace_once(
    '        "flags": {"DFIntDebugFRMQualityLevelOverride": 1},',
    '        "flags": {},',
    "legacy minimum-FRM module",
)
replace_once(
    '            "DFIntDebugFRMQualityLevelOverride": 1, "DFIntTextureQualityOverride": 0,',
    '            "DFIntTextureQualityOverride": 0,',
    "legacy whitelist FRM override",
)
replace_once(
    '            "DFIntDebugFRMQualityLevelOverride": "1", "DFIntRenderPostFxBasePixelCount": "-1",',
    '            "DFIntRenderPostFxBasePixelCount": "-1",',
    "legacy gray-sky FRM override",
)

replace_once(
    '        "tooltip_pt": "Força o nível FRM de qualidade para 1.",',
    '        "tooltip_pt": "Obsoleto: o Roblox agora controla a qualidade FRM e a distância de renderização.",',
    "legacy FRM tooltip PT",
)
replace_once(
    '        "tooltip_en": "Forces FRM graphics quality level to 1.",',
    '        "tooltip_en": "Deprecated: Roblox now controls FRM quality and draw distance.",',
    "legacy FRM tooltip EN",
)
replace_once(
    'for _batata_key in ("textures", "grass", "msaa", "lod", "frm_low", "gray_sky", "voxelizer", "d3d11"):',
    'for _batata_key in ("textures", "grass", "msaa", "lod", "gray_sky", "voxelizer", "d3d11"):',
    "aggressive profile module list",
)
replace_once(
    '"Combina textura mínima, MSAA 0, qualidade 3D 1, grama/LOD mínimos, céu cinza, voxelizer pausado e D3D11. Pode deixar o visual bem feio; JSON personalizado ainda sobrescreve valores conflitantes."',
    '"Combina textura mínima, MSAA 0, grama/LOD mínimos, céu cinza, voxelizer pausado e D3D11. A qualidade FRM e a distância ficam sob controle do Roblox."',
    "aggressive profile tooltip PT",
)
replace_once(
    '"Combines minimum textures, MSAA 0, 3D quality 1, minimum grass/LOD, gray sky, paused voxelizer and D3D11. Visuals may look very rough; custom JSON still overrides conflicting values."',
    '"Combines minimum textures, MSAA 0, minimum grass/LOD, gray sky, paused voxelizer and D3D11. FRM quality and draw distance remain under Roblox control."',
    "aggressive profile tooltip EN",
)
replace_once(
    '"Junta textura mínima, MSAA 0, grama/LOD mínimos, FRM baixo, voxelizer e D3D11 em um único botão. O céu cinza agora é opcional e separado."',
    '"Junta textura mínima, MSAA 0, grama/LOD mínimos, voxelizer e D3D11. A qualidade FRM fica sob controle do Roblox."',
    "performance profile tooltip PT",
)
replace_once(
    '"Combines minimum textures, MSAA 0, minimum grass/LOD, low FRM, voxelizer and D3D11 in one switch. Gray sky stays separate so you can choose normal or gray visuals."',
    '"Combines minimum textures, MSAA 0, minimum grass/LOD, voxelizer and D3D11 in one switch. FRM quality stays under Roblox control; gray sky remains separate."',
    "performance profile tooltip EN",
)

# Migrate settings saved by older versions, regardless of their previous FRM value.
replace_once(
    '        for k in ("texture", "msaa", "frm", "grass", "lod"):\n'
    '            self.advanced_values.setdefault(k, "Auto")',
    '        for k in ("texture", "msaa", "frm", "grass", "lod"):\n'
    '            self.advanced_values.setdefault(k, "Auto")\n'
    '        self.advanced_values["frm"] = "Auto"',
    "advanced-values initialization",
)

replace_method("ModernConfigApp", "obter_flags_avancadas", r'''    def obter_flags_avancadas(self):
        vals = dict(getattr(self, "advanced_values", {}))
        try:
            for key, menu in getattr(self, "advanced_menus", {}).items():
                vals[key] = str(menu.get())
        except Exception:
            pass

        # FRMQualityOverride is intentionally no longer user-configurable.
        # Roblox's post-Nov-5 quality system couples this override to draw distance.
        vals["frm"] = "Auto"

        flags = {}
        if vals.get("texture", "Auto") != "Auto":
            flags["DFFlagTextureQualityOverrideEnabled"] = True
            flags["DFIntTextureQualityOverride"] = int(vals["texture"])
        if vals.get("msaa", "Auto") != "Auto":
            flags["FIntDebugForceMSAASamples"] = int(vals["msaa"])
        if vals.get("grass", "Auto") != "Auto":
            distance = int(vals["grass"])
            flags["FIntFRMMaxGrassDistance"] = distance
            flags["FIntFRMMinGrassDistance"] = distance
        if vals.get("lod", "Auto") != "Auto":
            distance = int(vals["lod"])
            flags["DFIntCSGLevelOfDetailSwitchingDistance"] = distance
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL12"] = distance
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL23"] = distance
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL34"] = distance

        self.advanced_values = vals
        return flags
''')

replace_once(
    'data["advanced_values"].update({"texture":"0","msaa":"0","frm":"1","grass":"0","lod":"0"})',
    'data["advanced_values"].update({"texture":"0","msaa":"0","frm":"Auto","grass":"0","lod":"0"})',
    "FPS Max preset FRM value",
)
replace_once(
    'data["advanced_values"].update({"texture":"1","msaa":"0","frm":"2","grass":"0","lod":"1"})',
    'data["advanced_values"].update({"texture":"1","msaa":"0","frm":"Auto","grass":"0","lod":"1"})',
    "Weak PC preset FRM value",
)

# ADVANCED_MANAGED_KEYS deliberately retains DFIntDebugFRMQualityLevelOverride.
# _salvar_flags_compiladas() removes managed keys before writing active settings,
# so the next explicit Apply removes an old override while preserving other flags.

tree = ast.parse(s)
modules_node = next(
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "FLAG_MODULES" for t in n.targets)
)
modules = ast.literal_eval(modules_node.value)
if "DFIntDebugFRMQualityLevelOverride" in modules["base"]["flags"]:
    raise SystemExit("v3.20.25: base module still contains the FRM override")
if modules["frm_low"]["flags"]:
    raise SystemExit("v3.20.25: deprecated FRM module is not empty")

managed_node = next(
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "ADVANCED_MANAGED_KEYS" for t in n.targets)
)
managed_keys = ast.literal_eval(managed_node.value)
if "DFIntDebugFRMQualityLevelOverride" not in managed_keys:
    raise SystemExit("v3.20.25: stale FRM override will not be cleaned on Apply")

if s.count("DFIntDebugFRMQualityLevelOverride") != 2:
    raise SystemExit(
        "v3.20.25: unexpected FRM override reference remains; expected only "
        "the client allowlist and managed-key cleanup entry"
    )

method_tree = ast.parse(s)
app = next(n for n in method_tree.body if isinstance(n, ast.ClassDef) and n.name == "ModernConfigApp")
advanced = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == "obter_flags_avancadas")
if "DFIntDebugFRMQualityLevelOverride" in ast.get_source_segment(s, advanced):
    raise SystemExit("v3.20.25: advanced settings still write the FRM override")

compile(s, str(path), "exec")
path.write_text(s, encoding="utf-8")
print("v3.20.25: FRM override removed from active profiles; stale key cleanup preserved.")
