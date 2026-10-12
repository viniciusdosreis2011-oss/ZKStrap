from pathlib import Path
import os
p=Path(os.environ.get('ZK_SOURCE_DIR','.'))/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')
needle="""    user32=ctypes.windll.user32;gdi32=ctypes.windll.gdi32
    IMAGE_CURSOR=2;LR_LOADFROMFILE=0x0010;DI_NORMAL=0x0003
    hcur=user32.LoadImageW(None,str(path),IMAGE_CURSOR,0,0,LR_LOADFROMFILE)"""
repl="""    user32=ctypes.windll.user32;gdi32=ctypes.windll.gdi32
    IMAGE_CURSOR=2;LR_LOADFROMFILE=0x0010;DI_NORMAL=0x0003
    # Explicit 64-bit handle signatures: ctypes defaults to c_int otherwise and can truncate GDI handles.
    user32.LoadImageW.argtypes=[wintypes.HINSTANCE,wintypes.LPCWSTR,wintypes.UINT,ctypes.c_int,ctypes.c_int,wintypes.UINT];user32.LoadImageW.restype=wintypes.HANDLE
    user32.GetIconInfo.argtypes=[wintypes.HANDLE,ctypes.c_void_p];user32.GetIconInfo.restype=wintypes.BOOL
    user32.DrawIconEx.argtypes=[wintypes.HDC,ctypes.c_int,ctypes.c_int,wintypes.HANDLE,ctypes.c_int,ctypes.c_int,wintypes.UINT,wintypes.HBRUSH,wintypes.UINT];user32.DrawIconEx.restype=wintypes.BOOL
    gdi32.CreateCompatibleDC.argtypes=[wintypes.HDC];gdi32.CreateCompatibleDC.restype=wintypes.HDC
    gdi32.CreateDIBSection.argtypes=[wintypes.HDC,ctypes.c_void_p,wintypes.UINT,ctypes.POINTER(ctypes.c_void_p),wintypes.HANDLE,wintypes.DWORD];gdi32.CreateDIBSection.restype=wintypes.HBITMAP
    gdi32.SelectObject.argtypes=[wintypes.HDC,wintypes.HANDLE];gdi32.SelectObject.restype=wintypes.HANDLE
    gdi32.DeleteObject.argtypes=[wintypes.HANDLE];gdi32.DeleteObject.restype=wintypes.BOOL
    gdi32.DeleteDC.argtypes=[wintypes.HDC];gdi32.DeleteDC.restype=wintypes.BOOL
    hcur=user32.LoadImageW(None,str(path),IMAGE_CURSOR,0,0,LR_LOADFROMFILE)"""
if needle not in s:raise SystemExit('v3.20.13 winapi: native ANI anchor not found')
s=s.replace(needle,repl,1)
compile(s,str(p),'exec')
p.write_text(s,encoding='utf-8')
print('Applied v3.20.13 64-bit Win32 ANI fallback hardening')
