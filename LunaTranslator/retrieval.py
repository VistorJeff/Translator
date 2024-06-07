import modulefinder, shutil, os, sys, pefile
import builtins
import subprocess
from typing import List, Set


x86 = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if x86:
    DOWNLEVEL = "C:/Windows/SysWOW64/downlevel"
    RUNTIME = "../build/LunaTranslator_x86/LunaTranslator/runtime"
    DST_ROOT_DIR = "../build/LunaTranslator_x86"
    LAUNCH = "../plugins/builds/_x86"
    APPROPRIATE_DLL_DIR = "DLL32"
    NON_APPROPRIATE_DLL_DIR = "DLL64"
    # py37Path = "C:/hostedtoolcache/windows/Python/3.7.9/x86/python.exe"
    PY37_EXE_PATH = os.path.join(os.environ.get("LOCALAPPDATA"), "Programs/Python/Python37-32/python.exe")
    WEBVIEW_DLL_RELATIVE_PATH = "Lib/site-packages/webviewpy/platform/win32/x86/webview.dll"
else:
    DOWNLEVEL = "C:/Windows/system32/downlevel"
    RUNTIME = "../build/LunaTranslator/LunaTranslator/runtime"
    DST_ROOT_DIR = "../build/LunaTranslator"
    LAUNCH = "../plugins/builds/_x64"
    APPROPRIATE_DLL_DIR = "DLL64"
    NON_APPROPRIATE_DLL_DIR = "DLL32"
    # py37Path = "C:/hostedtoolcache/windows/Python/3.7.9/x64/python.exe"
    PY37_EXE_PATH = os.path.join(os.environ.get("LOCALAPPDATA"), "Programs/Python/Python37/python.exe")
    WEBVIEW_DLL_RELATIVE_PATH = "Lib/site-packages/webviewpy/platform/win32/x64/webview.dll"
# if os.path.exists(py37Path) == False:
#     py37Path = py37Pathlocal
PY37_ROOT_DIR = os.path.dirname(PY37_EXE_PATH)
WEBVIEW_DLL_ABS_PATH = os.path.join(PY37_ROOT_DIR, WEBVIEW_DLL_RELATIVE_PATH)


def GetImportTable(filePath) -> List[str]:
    pe = pefile.PE(filePath)
    importDlls = []
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dllName = entry.dll.decode("utf-8")
            importDlls.append(dllName)
    return importDlls


def GetDependencies(fileName) -> List[str]:
    saveOpen = builtins.open
    def __open(*arg, **kwarg):
        if len(arg) > 1:
            mode = arg[1]
        else:
            mode = ""
        if "b" not in mode:
            kwarg["encoding"] = "utf8"
        return saveOpen(*arg, **kwarg)
    builtins.open = __open
    finder = modulefinder.ModuleFinder()
    finder.run_script(fileName)
    dependencies = []
    for name, module in finder.modules.items():
        if module.__file__ is not None:
            dependencies.append(module.__file__)
    builtins.open = saveOpen
    return dependencies


def CopyCheck(src: str, dstDir):
    if not os.path.exists(src):
        return
    if src.lower().endswith("_ssl.pyd"):
        return
    print(f"Src:{src} Dst:{dstDir}")
    if not os.path.exists(dstDir):
        os.makedirs(dstDir, exist_ok=True)
    if os.path.isdir(src):
        dstDir = os.path.join(dstDir, os.path.basename(src))
        if os.path.exists(dstDir):
            shutil.rmtree(dstDir)
        shutil.copytree(src, dstDir)
        return
    shutil.copy(src, dstDir)


print("==================== Start copying program files ====================")
if os.path.exists(DST_ROOT_DIR):
    shutil.rmtree(DST_ROOT_DIR, ignore_errors=True)
CopyCheck(os.path.join(LAUNCH, "LunaTranslator.exe"), DST_ROOT_DIR)
CopyCheck(os.path.join(LAUNCH, "LunaTranslator_admin.exe"), DST_ROOT_DIR)
CopyCheck(os.path.join(LAUNCH, "LunaTranslator_debug.exe"), DST_ROOT_DIR)
CopyCheck("LunaTranslator", DST_ROOT_DIR)
CopyCheck("files", DST_ROOT_DIR)
try:
    shutil.rmtree(os.path.join(DST_ROOT_DIR, "files/plugins", NON_APPROPRIATE_DLL_DIR))
except:
    pass
CopyCheck("../LICENSE", DST_ROOT_DIR)
CopyCheck(WEBVIEW_DLL_ABS_PATH, os.path.join(DST_ROOT_DIR, "files/plugins", APPROPRIATE_DLL_DIR))
print("==================== Finish copying program files ====================")


print("==================== Start caculating dependencies ====================")
allDependencies: Set[str] = set()
for dirPath, dirNames, fileNames in os.walk("./LunaTranslator"):
    for fileName in fileNames:
        if not fileName.endswith(".py"):
            continue
        base = os.path.basename(dirPath)
        if base in [
            "tts",
            "transoptimi",
            "translator",
            "scalemethod",
            "ocrengines",
            "winhttp",
            "libcurl",
            "network",
            "hiraparse",
            "cishu",
            "textoutput",
        ]:
            continue
        print(base, fileName)
        dependencies = GetDependencies(os.path.join(dirPath, fileName))
        allDependencies = allDependencies.union(set(dependencies))
print("==================== Finish caculating dependencies ====================")


print("==================== Start copying dependencies ====================")
for dependency in allDependencies:
    if dependency.startswith("./"):
        continue
    print(dependency)
    end = dependency[len(PY37_ROOT_DIR) + 1 :]
    if end.lower().startswith("lib"):
        end = end[4:]
        if end.lower().startswith("site-packages"):
            end = end[len("site-packages") + 1 :]
    elif end.lower().startswith("dlls"):
        end = end[5:]
    print(end)
    dstDir = os.path.join(RUNTIME, os.path.dirname(end))
    CopyCheck(dependency, dstDir)

with open(os.path.join(RUNTIME, "python37._pth"), "w") as ff:
    ff.write(".\n..")

CopyCheck(os.path.join(PY37_ROOT_DIR, "python3.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "python37.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "DLLs/sqlite3.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/encodings"), RUNTIME)
CopyCheck(os.path.join(DOWNLEVEL, "ucrtbase.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/vcruntime140.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/vcruntime140_1.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/msvcp140.dll"), RUNTIME)
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/msvcp140_1.dll"), RUNTIME)

for dirNames in os.listdir(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5")):
    if dirNames.startswith("sip"):
        CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5", dirNames), os.path.join(RUNTIME, "PyQt5"))

CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/Qt5Core.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/bin"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/Qt5Svg.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/bin"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/Qt5Gui.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/bin"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/bin/Qt5Widgets.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/bin"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/plugins/iconengines"), os.path.join(RUNTIME, "PyQt5/Qt5/plugins"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/plugins/imageformats"), os.path.join(RUNTIME, "PyQt5/Qt5/plugins"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/plugins/platforms/qoffscreen.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/plugins/platforms"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/plugins/platforms/qwindows.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/plugins/platforms"))
CopyCheck(os.path.join(PY37_ROOT_DIR, "Lib/site-packages/PyQt5/Qt5/plugins/styles/qwindowsvistastyle.dll"), os.path.join(RUNTIME, "PyQt5/Qt5/plugins/styles"))
print("==================== Finish copying dependencies ====================")


print("==================== Start fixing imports ====================")
collects: List[str] = []
for dirPath, dirNames, fileNames in os.walk(DST_ROOT_DIR):
    for fileName in fileNames:
        collects.append(os.path.join(dirPath, fileName))
for fileName in collects:
    if fileName.endswith(".pyc") or fileName.endswith("Thumbs.db"):
        os.remove(fileName)
    elif fileName.endswith(".exe") or fileName.endswith(".pyd") or fileName.endswith(".dll"):
        try:
            pe = pefile.PE(fileName)
            importTable = pe.DIRECTORY_ENTRY_IMPORT
            imports: List[str] = []
            for entry in importTable:
                if entry.dll.decode("utf-8").lower().startswith("api"):
                    imports.append(entry.dll.decode("utf-8"))
            pe.close()
        except:
            continue
        if fileName.endswith("Magpie.Core.exe"):
            continue
        # pefile好像有bug，仅对于QtWidgets.pyd这个文件，只能读取到导入了Qt5Widgets.dll
        if fileName.endswith("QtWidgets.pyd"):
            if "api-ms-win-crt-runtime-l1-1-0.dll" not in imports:
                imports.append("api-ms-win-crt-runtime-l1-1-0.dll")
            if "api-ms-win-crt-heap-l1-1-0.dll" not in imports:
                imports.append("api-ms-win-crt-heap-l1-1-0.dll")
            # imports += ["api-ms-win-crt-runtime-l1-1-0.dll", "api-ms-win-crt-heap-l1-1-0.dll"]
        print(f"File:{fileName} Imports:{imports}")
        if len(imports) == 0:
            continue
        with open(fileName, "rb") as ff:
            bs = bytearray(ff.read())
        for dll in imports:
            if dll.lower().startswith("api-ms-win-core"):
                # 其实对于api-ms-win-core-winrt-XXX实际上是到ComBase.dll之类的，不过此项目中不包含这些
                realDll = "kernel32.dll"
            elif dll.lower().startswith("api-ms-win-crt"):
                realDll = "ucrtbase.dll"
            dll = dll.encode()
            realDll = realDll.encode()
            idx = bs.find(dll)
            bs[idx : idx + len(dll)] = realDll + b"\0" * (len(dll) - len(realDll))
        with open(fileName, "wb") as ff:
            ff.write(bs)
print("==================== Finish fixing imports ====================")


print("==================== Start packing executable ====================")

print("========== Checking 7z command ==========")
_7zipCommand = "7z"
_7zipCmdPath = shutil.which("7z")
if _7zipCmdPath is None:
    if os.path.exists("../7zip"):
        _7zipCmdPath = os.path.abspath("../7zip/7zip_extra/7za.exe") if x86 else os.path.abspath("../7zip/7zip_extra/x64/7za.exe")
    else:
        if not os.path.exists("7zip"):
            os.mkdir("7zip")
        os.chdir("7zip")
        # 先下载一个7zr.exe，但这个不能解压zip
        if not os.path.exists("7zr.exe"):
            subprocess.run("curl -L -O https://www.7-zip.org/a/7zr.exe")
        # 下载7zip-extra后用7zr.exe解压
        if not os.path.exists("7zip_extra/x64/7za.exe"):
            subprocess.run("curl -L -O https://www.7-zip.org/a/7z2406-extra.7z")
            subprocess.run("7zr.exe x 7z2406-extra.7z -o7zip_extra")
        _7zipCmdPath = os.path.abspath("7zip_extra/7za.exe") if x86 else os.path.abspath("7zip_extra/x64/7za.exe")
        _7zipCommand = _7zipCmdPath
        os.chdir("..")
print(f"7Zip command path:{_7zipCmdPath}")

print("========== Compressing ==========")
rootDirName = os.path.basename(DST_ROOT_DIR)
dst7zFilePath = os.path.join(DST_ROOT_DIR, "..", rootDirName + ".7z")
# if os.path.exists(rf"{DST_ROOT_DIR}\..\{rootDirName}.zip"):
#     os.remove(rf"{DST_ROOT_DIR}\..\{rootDirName}.zip")
if os.path.exists(dst7zFilePath):
    os.remove(dst7zFilePath)
# os.system(
#     rf'"C:\Program Files\7-Zip\7z.exe" a -m0=Deflate -mx9 {DST_ROOT_DIR}\..\{rootDirName}.zip {DST_ROOT_DIR}'
# )
os.system(f"{_7zipCommand} a -m0=LZMA2 -mx9 {dst7zFilePath} {DST_ROOT_DIR}")

print("========== Checking 7Zip sfx ==========")
# 下载msi解压得到SFX文件
_7ZIP_MSI_DOWNLOAD_LINK = "https://www.7-zip.org/a/7z2406.msi" if x86 else "https://www.7-zip.org/a/7z2406-x64.msi"
if not os.path.exists("7zip"):
    os.mkdir("7zip")
os.chdir("7zip")
_7zipMsiFileName = _7ZIP_MSI_DOWNLOAD_LINK.split("/")[-1]
if not os.path.exists(_7zipMsiFileName):
    subprocess.run(f"curl -L -O {_7ZIP_MSI_DOWNLOAD_LINK}")
if os.path.exists(_7zipMsiFileName):
    if os.path.exists("msi"):
        shutil.rmtree("msi")
    subprocess.run(f"{_7zipCommand} x {_7zipMsiFileName} -omsi")
_7zipSfxFilePath = os.path.abspath("msi/_7z.sfx")
if os.path.exists(_7zipSfxFilePath):
    print(f"SFX file path:{_7zipSfxFilePath}")
else:
    print("No SFX file !!!")
    exit()
os.chdir("..")

print("========== Packing installer executable ==========")
dstExeFilePath = os.path.join(DST_ROOT_DIR, "..", rootDirName + ".exe")
config = """
;!@Install@!UTF-8!


;!@InstallEnd@!
"""
if os.path.exists(dstExeFilePath):
    os.remove(dstExeFilePath)
with open(_7zipSfxFilePath, "rb") as ff:
    sfx = ff.read()
with open(dst7zFilePath, "rb") as ff:
    data = ff.read()
with open(dstExeFilePath, "wb") as ff:
    ff.write(sfx)
    ff.write(config.encode("utf8"))
    ff.write(data)
print(f"Executable file path:{dstExeFilePath}")
print("==================== Finish packing executable ====================")
