import os, sys, re
import shutil, json
import subprocess, time
import urllib.request
import platform


# 构建前需要下载的资源的路径
CMAKE_DOWNLOAD_LINK = "https://github.com/Kitware/CMake/releases/download/v3.29.4/cmake-3.29.4-windows-x86_64.zip"
GH_DOWNLOAD_LINK = "https://github.com/cli/cli/releases/download/v2.50.0/gh_2.50.0_windows_386.zip"
BROTLI_X32_DOWNLOAD_LINK = "https://github.com/google/brotli/releases/latest/download/brotli-x86-windows-dynamic.zip"
BROTLI_X64_DOWNLOAD_LINK = "https://github.com/google/brotli/releases/latest/download/brotli-x64-windows-dynamic.zip"
LOCALE_EMULATOR_DOWNLOAD_LINK = "https://github.com/xupefei/Locale-Emulator/releases/download/v2.5.0.1/Locale.Emulator.2.5.0.1.zip"
NTLEA_DOWNLOAD_LINK = "https://github.com/zxyacb/ntlea/releases/download/0.46/ntleas046_x64.7z"
CURL_X32_DOWNLOAD_LINK = "https://curl.se/windows/dl-8.7.1_7/curl-8.7.1_7-win32-mingw.zip"
CURL_X64_DOWNLOAD_LINK = "https://curl.se/windows/dl-8.7.1_7/curl-8.7.1_7-win64-mingw.zip"
VC_LTL5_GITHUB_LINK = "https://github.com/Chuyu-Team/VC-LTL5.git"
MINI_AUDIO_GITHUB_LINK = "https://github.com/HIllya51/miniaudio.git"
TINY_MP3_GITHUB_LINK = "https://github.com/HIllya51/tinymp3.git"
WIL_GITHUB_LINK = "https://github.com/microsoft/wil.git"
MECAB_DOWNLOAD_LINK = "https://github.com/HIllya51/RESOURCES/releases/download/common/mecab.zip"
OCR_DOWNLOAD_LINK = "https://github.com/HIllya51/RESOURCES/releases/download/common/ocr.zip"
MAGPIE_DOWNLOAD_LINK = "https://github.com/HIllya51/RESOURCES/releases/download/common/magpie.zip"
OCR_MODEL_DOWNLOAD_DIR = "https://github.com/HIllya51/RESOURCES/releases/download/ocr_models"
VALID_OCR_LANGS = ["cht", "en", "ja", "ko", "ru", "zh"]


# 根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# 临时文件目录
TEMP_FILES_ROOT_DIR = os.path.join(ROOT_DIR, 'temp')
# File目录
FILES_ROOT_DIR = os.path.join(ROOT_DIR, "LunaTranslator/files")
# Plugin目录
PLUGIN_ROOT_DIR = os.path.join(ROOT_DIR, "LunaTranslator/files/plugins")
PLUGIN_DIRS = ["DLL32", "DLL64", "Locale_Remulator", "LunaHook", "Magpie", "NTLEAS"]
PLUGIN_DLL32_DIR = os.path.join(PLUGIN_ROOT_DIR, "DLL32")
PLUGIN_DLL64_DIR = os.path.join(PLUGIN_ROOT_DIR, "DLL64")


# 7zip命令
ZIP_EXE_PATH = "7z"
# cmake命令
CMAKE_EXE_PATH = "cmake"
# gh命令
GH_EXE_PATH = "gh"
loginGhOnce = False


def IsCommandExist(command):
    # 检查环境变量中是否有对应的命令
    commandPath = shutil.which(command)
    return commandPath is not None


def ForceHave7Zip():
    # 环境变量中没有7zip需要下载一个到工程目录
    if IsCommandExist("7z"):
        return
    os.chdir(ROOT_DIR)
    zipRootDir = "7zip"
    if not os.path.exists(zipRootDir):
        os.mkdir(zipRootDir)
    os.chdir(zipRootDir)
    # 先下载一个7zr.exe，但这个不能解压zip
    if not os.path.exists("7zr.exe"):
        subprocess.run("curl -L -O https://www.7-zip.org/a/7zr.exe")
    # 下载7zip-extra后用7zr.exe解压
    if not os.path.exists("7zip_extra/x64/7za.exe"):
        subprocess.run("curl -L -O https://www.7-zip.org/a/7z2406-extra.7z")
        subprocess.run("7zr.exe x 7z2406-extra.7z -o7zip_extra")
    x64 = platform.architecture()[0] == "64bit"
    global ZIP_EXE_PATH
    if x64:
        ZIP_EXE_PATH = os.path.join(ROOT_DIR, zipRootDir, "7zip_extra/x64/7za.exe")
    else:
        ZIP_EXE_PATH = os.path.join(ROOT_DIR, zipRootDir, "7zip_extra/7za.exe")


def ForceHaveCMake():
    # 要编译VS2022项目，避免本地cmake版本过低，这里下载一个比较新的
    os.chdir(ROOT_DIR)
    cmakeRootDir = "cmake"
    if not os.path.exists(cmakeRootDir):
        os.mkdir(cmakeRootDir)
    os.chdir(cmakeRootDir)
    cmakeFileName = GetNetResourceFileName(CMAKE_DOWNLOAD_LINK)
    global CMAKE_EXE_PATH
    if not os.path.exists(f"{os.path.splitext(cmakeFileName)[0]}/bin/cmake.exe"):
        subprocess.run(f"curl -L -O {CMAKE_DOWNLOAD_LINK}")
        subprocess.run(f"{ZIP_EXE_PATH} x {cmakeFileName}")
    CMAKE_EXE_PATH = os.path.join(ROOT_DIR, cmakeRootDir, f"{os.path.splitext(cmakeFileName)[0]}/bin/cmake.exe")


def ForceHaveGH():
    # 要访问api.github.com最好通过gh命令，不然有访问限制
    global GH_EXE_PATH
    os.chdir(ROOT_DIR)
    ghRootDir = "gh"
    if not os.path.exists(ghRootDir):
        os.mkdir(ghRootDir)
    os.chdir(ghRootDir)
    if not os.path.exists("bin/gh.exe"):
        subprocess.run(f"curl -L -O {GH_DOWNLOAD_LINK}")
        subprocess.run(f"{ZIP_EXE_PATH} x {GetNetResourceFileName(GH_DOWNLOAD_LINK)}")
    GH_EXE_PATH = os.path.join(ROOT_DIR, ghRootDir, "bin/gh.exe")


def GetNetResourceFileName(resourceUrl, includeExt=True):
    splitResult = resourceUrl.split("/")
    if includeExt:
        return splitResult[-1]
    else:
        fileName, fileExt = os.path.splitext(splitResult[-1])
        return fileName


def DownloadNetResource(resourceUrl, forceDownload=False):
    fileName = GetNetResourceFileName(resourceUrl)
    if forceDownload and os.path.exists(fileName):
        os.remove(fileName)
    if not os.path.exists(fileName):
        subprocess.run(f"curl -L -O {resourceUrl}")
    return fileName


def ExtractFile(fileName, expandDir=None, deleteOldDir=True, deleteZip=False):
    fileNameWithoutExt = os.path.splitext(fileName)[0]
    if expandDir is not None:
        if os.path.exists(expandDir) and deleteOldDir:
            shutil.rmtree(expandDir, ignore_errors=True)
        if os.path.exists(fileName):
            subprocess.run(f"{ZIP_EXE_PATH} x {fileName} -o{expandDir}")
            if deleteZip:
                os.remove(fileName)
        return expandDir
    else:
        if os.path.exists(fileNameWithoutExt) and deleteOldDir:
            shutil.rmtree(fileNameWithoutExt, ignore_errors=True)
        if os.path.exists(fileName):
            subprocess.run(f"{ZIP_EXE_PATH} x {fileName}")
            if deleteZip:
                os.remove(fileName)
        return fileNameWithoutExt


def MoveFile(srcFile, dstDir, dstFileName=None):
    fileName = os.path.basename(srcFile)
    dstFilePath = os.path.join(dstDir, fileName) if dstFileName is None else os.path.join(dstDir, dstFileName)
    os.makedirs(dstDir, exist_ok=True)
    if os.path.exists(dstFilePath):
        os.remove(dstFilePath)
    if os.path.exists(srcFile):
        shutil.move(srcFile, dstFilePath)
    else:
        print(f"Move file failed, file not existed, Path:{srcFile}")


def CreatePluginDirs():
    os.chdir(FILES_ROOT_DIR)
    if not os.path.exists("plugins"):
        os.mkdir("plugins")
    os.chdir("plugins")
    for pluginDir in PLUGIN_DIRS:
        if not os.path.exists(pluginDir):
            os.mkdir(pluginDir)


def InstallVCLTL():
    # 不安装VC-LTL了，直接拉取GitHub工程编译（bug：cmake的string需要5个参数）
    os.chdir(os.path.join(ROOT_DIR, 'plugins/libs'))
    if not os.path.exists("VC-LTL"):
        os.system(f"git clone {VC_LTL5_GITHUB_LINK} VC-LTL")


def InstallThirdLibs():
    os.chdir(os.path.join(ROOT_DIR, "plugins/libs"))
    isEmptyFolder = lambda folder: len(os.listdir(folder)) == 0
    if isEmptyFolder("miniaudio"):
        os.system(f"git clone {MINI_AUDIO_GITHUB_LINK}")
    if isEmptyFolder("tinymp3"):
        os.system(f"git clone {TINY_MP3_GITHUB_LINK}")
    if isEmptyFolder("wil"):
        os.system(f"git clone {WIL_GITHUB_LINK}")


def DownloadBrotli():
    os.chdir(TEMP_FILES_ROOT_DIR)
    fileName32bit = DownloadNetResource(BROTLI_X32_DOWNLOAD_LINK)
    fileName64bit = DownloadNetResource(BROTLI_X64_DOWNLOAD_LINK)
    expandDir32bit = ExtractFile(fileName32bit, "brotli32")
    expandDir64bit = ExtractFile(fileName64bit, "brotli64")
    MoveFile(f"{expandDir32bit}/brotlicommon.dll", PLUGIN_DLL32_DIR)
    MoveFile(f"{expandDir32bit}/brotlidec.dll", PLUGIN_DLL32_DIR)
    MoveFile(f"{expandDir64bit}/brotlicommon.dll", PLUGIN_DLL64_DIR)
    MoveFile(f"{expandDir64bit}/brotlidec.dll", PLUGIN_DLL64_DIR)


def DownloadLocaleRemulator():
    os.chdir(TEMP_FILES_ROOT_DIR)
    expandDir = "LR"
    if not os.path.exists(expandDir):
        jsonData = GetGithubApiAsJson("https://api.github.com/repos/InWILL/Locale_Remulator/releases/latest")
        if not jsonData:
            print("Request https://api.github.com/repos/InWILL/Locale_Remulator/releases/latest failed")
            return
        for asset in jsonData["assets"]:
            if "browser_download_url" in asset:
                DownloadNetResource(asset["browser_download_url"])
                expandDir = ExtractFile(asset["name"], expandDir)
    for dirPath, dirNames, fileNames in os.walk(expandDir):
        for fileName in fileNames:
            if fileName in ["LRHookx64.dll", "LRHookx32.dll"]:
                MoveFile(os.path.join(dirPath, fileName), os.path.join(PLUGIN_ROOT_DIR, "Locale_Remulator"))


def MoveDirectoryContents(srcDir, dstDir):
    ignoreDir = lambda dirName: dirName == ".git"
    try:
        os.makedirs(dstDir, exist_ok=True)
        shutil.copytree(srcDir, dstDir, ignore=shutil.ignore_patterns(*filter(ignoreDir, os.listdir(srcDir))), dirs_exist_ok=True)
    except:
        print(sys.exc_info()[0])


def DownloadCommon():
    os.chdir(TEMP_FILES_ROOT_DIR)
    DownloadLocaleRemulator()
    mecabFileName = DownloadNetResource(MECAB_DOWNLOAD_LINK)
    ocrFileName = DownloadNetResource(OCR_DOWNLOAD_LINK)
    magpieFileName = DownloadNetResource(MAGPIE_DOWNLOAD_LINK)
    expandDir = "ALL"
    ExtractFile(mecabFileName, expandDir)
    ExtractFile(ocrFileName, expandDir, False)
    ExtractFile(magpieFileName, expandDir, False)
    MoveDirectoryContents(f"{expandDir}/ALL", PLUGIN_ROOT_DIR)


def DownloadLocaleEmulator():
    os.chdir(TEMP_FILES_ROOT_DIR)
    fileName = DownloadNetResource(LOCALE_EMULATOR_DOWNLOAD_LINK)
    expandDir = ExtractFile(fileName, "LocaleEmulator")
    MoveFile(f"{expandDir}/LoaderDll.dll", PLUGIN_ROOT_DIR)
    MoveFile(f"{expandDir}/LocaleEmulator.dll", PLUGIN_ROOT_DIR)


def DownloadNtlea():
    os.chdir(TEMP_FILES_ROOT_DIR)
    fileName = DownloadNetResource(NTLEA_DOWNLOAD_LINK)
    expandDir = ExtractFile(fileName, "ntlea")
    MoveFile(f"{expandDir}/x86/ntleai.dll", os.path.join(PLUGIN_ROOT_DIR, "NTLEAS"))
    MoveFile(f"{expandDir}/x64/ntleak.dll", os.path.join(PLUGIN_ROOT_DIR, "NTLEAS"))


def DownloadCurl():
    os.chdir(TEMP_FILES_ROOT_DIR)
    fileName32bit = DownloadNetResource(CURL_X32_DOWNLOAD_LINK)
    fileName64bit = DownloadNetResource(CURL_X64_DOWNLOAD_LINK)
    expandDir32bit = ExtractFile(fileName32bit, "curl-win32")
    expandDir64bit = ExtractFile(fileName64bit, "curl-win64")
    MoveFile(f"{expandDir32bit}/{os.path.splitext(fileName32bit)[0]}/bin/libcurl.dll", PLUGIN_DLL32_DIR)
    MoveFile(f"{expandDir64bit}/{os.path.splitext(fileName64bit)[0]}/bin/libcurl-x64.dll", PLUGIN_DLL64_DIR)


def DownloadOCRModel(locale):
    if locale not in VALID_OCR_LANGS:
        return
    os.chdir(FILES_ROOT_DIR)
    if not os.path.exists("ocr"):
        os.mkdir("ocr")
    os.chdir("ocr")
    fileName = locale + ".zip"
    fileName = DownloadNetResource(f"{OCR_MODEL_DOWNLOAD_DIR}/{fileName}")
    ExtractFile(fileName, deleteZip=True)


def GetGithubApiAsJson(apiUrl):
    # 使用gh时需要跟随登录步骤先登录GitHub
    print("Please login GitHub first")
    global loginGhOnce
    if not loginGhOnce:
        loginGhOnce = True
        subprocess.run(f"{GH_EXE_PATH} auth login")
    result = subprocess.run(f"{GH_EXE_PATH} api --method GET {apiUrl}", stdout=subprocess.PIPE)
    return json.loads(result.stdout.decode('utf-8'))


def BuildLunaHook():
    os.chdir(TEMP_FILES_ROOT_DIR)
    expandDir = "Release_English"
    if not os.path.exists(expandDir):
        jsonData = GetGithubApiAsJson("https://api.github.com/repos/HIllya51/LunaHook/releases/latest")
        if not jsonData:
            print("Request https://api.github.com/repos/HIllya51/LunaHook/releases/latest failed")
            return
        for asset in jsonData["assets"]:
            if asset["name"] == "Release_English.zip":
                fileName = DownloadNetResource(asset['browser_download_url'])
                expandDir = ExtractFile(fileName)
    lunaHookDir = os.path.join(PLUGIN_ROOT_DIR, "LunaHook")
    MoveFile(f"{expandDir}/LunaHook32.dll", lunaHookDir)
    MoveFile(f"{expandDir}/LunaHost32.dll", lunaHookDir)
    MoveFile(f"{expandDir}/LunaHook64.dll", lunaHookDir)
    MoveFile(f"{expandDir}/LunaHost64.dll", lunaHookDir)


def BuildPlugins():
    os.chdir(os.path.join(ROOT_DIR, "plugins/scripts"))
    subprocess.run(f'{CMAKE_EXE_PATH} ../CMakeLists.txt -G "Visual Studio 17 2022" -A win32 -T host=x86 -B ../build/x86 -DCMAKE_SYSTEM_VERSION=10.0.26621.0')
    subprocess.run(f"{CMAKE_EXE_PATH} --build ../build/x86 --config Release --target ALL_BUILD -j 14")
    subprocess.run("python copytarget.py 1")
    subprocess.run(f'{CMAKE_EXE_PATH} ../CMakeLists.txt -G "Visual Studio 17 2022" -A x64 -T host=x64 -B ../build/x64 -DCMAKE_SYSTEM_VERSION=10.0.26621.0')
    subprocess.run(f"{CMAKE_EXE_PATH} --build ../build/x64 --config Release --target ALL_BUILD -j 14")
    subprocess.run("python copytarget.py 0")


def DownloadStyleSheets():
    os.chdir(TEMP_FILES_ROOT_DIR)
    if not os.path.exists("stylesheets"):
        os.system("git clone https://github.com/HIllya51/stylesheets")
    MoveDirectoryContents("stylesheets", os.path.join(ROOT_DIR, "LunaTranslator/files/themes"))


if __name__ == "__main__":
    # if sys.argv[1] == "loadversion":
    #     os.chdir(ROOT_DIR)
    #     with open("plugins/CMakeLists.txt", "r", encoding="utf8") as ff:
    #         pattern = r"set\(VERSION_MAJOR\s*(\d+)\s*\)\nset\(VERSION_MINOR\s*(\d+)\s*\)\nset\(VERSION_PATCH\s*(\d+)\s*\)"
    #         match = re.findall(pattern, ff.read())[0]
    #         version_major, version_minor, version_patch = match
    #         versionstring = f"v{version_major}.{version_minor}.{version_patch}"
    #         print("version=" + versionstring)
    #         exit()
    # arch = sys.argv[1]
    # isdebug = len(sys.argv) > 2 and int(sys.argv[2])
    ForceHave7Zip()
    ForceHaveCMake()
    ForceHaveGH()
    os.chdir(ROOT_DIR)
    # os.system("git submodule update --init --recursive")
    os.makedirs("temp", exist_ok=True)
    CreatePluginDirs()
    DownloadStyleSheets()
    DownloadBrotli()
    DownloadLocaleEmulator()
    DownloadNtlea()
    DownloadCurl()
    DownloadOCRModel("ja")
    DownloadCommon()
    BuildLunaHook()
    if os.path.exists(TEMP_FILES_ROOT_DIR):
        shutil.rmtree(TEMP_FILES_ROOT_DIR, ignore_errors=True)
    InstallVCLTL()
    InstallThirdLibs()
    BuildPlugins()
    os.chdir(ROOT_DIR)
    # if arch == "x86":
    #     py37Path = "C:\\hostedtoolcache\\windows\\Python\\3.7.9\\x86\\python.exe"
    # else:
    #     py37Path = "C:\\hostedtoolcache\\windows\\Python\\3.7.9\\x64\\python.exe"
    py37Path = os.path.join(os.environ.get("LOCALAPPDATA"), "Programs/Python/Python37/python.exe")
    if not os.path.exists(py37Path):
        print(f"Python37 not exist | Path:{py37Path}")
        exit()
    os.chdir(os.path.join(ROOT_DIR, "LunaTranslator"))
    subprocess.run(f"{py37Path} -m pip install --upgrade pip")
    subprocess.run(f"{py37Path} -m pip install -r requirements.txt")
    subprocess.run(f'{py37Path} retrieval.py {int(platform.architecture()[0] == "32bit")}')
