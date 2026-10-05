#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_localai_win.py  --  INSTALLEUR MAITRE  (v1.9.0)
======================================================
Portage Windows natif et autonome de LocalAI (sans Docker, sans WSL).
Phase 2 : Python embarqué (LiteLLM), routage, backends multi-modaux.
Phase 3 : détection GPU, variantes llama.cpp (CUDA/Vulkan/CPU), profils.
Phase 4 : pipeline RAG local (NumPy seul, sans faiss) + Agent Hub LiteLLM
          (modèle virtuel, Token Saver, bascule cloud BYOK).

Sandbox (v3.1.1) : detectee DYNAMIQUEMENT -- dossier du script, ou --root <chemin>.
Produit deploye  : <sandbox>\\AiTron\\   (reconstructible, effacable, PORTABLE).

Section 1.1 : archive_installer() est la TOUTE PREMIERE instruction de main().
Section 1.4 : AITRON_DEPLOY_CODE subit la triple validation AST avant ecriture.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

__version__ = "3.1.3"

# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# v3.1.1 -- PORTABILITE TOTALE : detection DYNAMIQUE du repertoire de la sandbox.
# Le script peut etre lance de n'importe ou (dossier du script, cle USB,
# C:\AiTron\, D:\Projets\AiTron\, partage reseau, ou via --root <chemin>).
# Plus AUCUN chemin en dur (l'ancien G:\V1\LocalAI-Projet\ est supprime).
# ---------------------------------------------------------------------------
def _detect_sandbox():
    """La sandbox est le dossier qui contient le script (compatible exec/import)."""
    me = globals().get("__file__")
    if me:
        sandbox = os.path.dirname(os.path.abspath(me))
    else:                       # exec()/import sans __file__ (outils) : repli CWD
        sandbox = os.path.abspath(os.getcwd())
    if os.path.basename(sandbox).lower() == "installeur":
        sandbox = os.path.dirname(sandbox)
    return sandbox


def _detect_sandbox_with_args(argv):
    """Priorite 1 : --root <chemin>. Priorite 2 : dossier du script (auto)."""
    for i, arg in enumerate(argv):
        if arg == "--root" and i + 1 < len(argv):
            root = os.path.abspath(argv[i + 1])
            if os.path.isdir(root):
                return root
            raise RuntimeError("--root : dossier introuvable : %s" % root)
    return _detect_sandbox()


try:
    SANDBOX = _detect_sandbox_with_args(sys.argv[1:])
except RuntimeError as _exc:
    sys.stderr.write("ERREUR DE PORTABILITE : %s\n" % _exc)
    raise SystemExit(2)
BLACKBOX   = os.path.join(SANDBOX, "Installeur")
DEV_DIR    = os.path.join(SANDBOX, "dev")
QUARANTINE = os.path.join(SANDBOX, "dev", "old")
LOGDIR     = os.path.join(SANDBOX, "log")
PRODUCT    = os.path.join(SANDBOX, "AiTron")
BUILD      = os.path.join(SANDBOX, "build")


def _ensure_sandbox_tree():
    """v3.1.1 (Section 1.3) -- cree la sandbox et ses sous-arborescences si absentes.

    Premier lancement dans un dossier neuf ou sur cle USB : l'installeur part d'un
    dossier vide. Installeur\\ + dev\\ + dev\\old\\ + log\\ + build\\ sont crees a
    la demande (idempotent, jamais d'erreur si deja presents).
    """
    for d in (SANDBOX, BLACKBOX, DEV_DIR, QUARANTINE, LOGDIR, BUILD):
        os.makedirs(d, exist_ok=True)
    return SANDBOX


def _detect_stage():
    """v3.1.0 -- ISOLATION DE STAGING (mandat d'audit dynamique).

    Si ce script est execute depuis <SANDBOX>\\dev\\test_dynamique\\, le produit (AiTron\\) et
    les journaux d'installation (log\\) sont deployes DANS ce dossier de laboratoire : le
    produit stable de la racine n'est ni lu en ecriture, ni remplace, ni arrete.
    BUILD (sources/caches) et Installeur\\ (boite noire) restent ceux de la racine.
    Execute depuis la racine, le comportement est strictement celui de la v3.0.0.
    """
    me = globals().get("__file__")
    if not me:                      # exec()/import sans __file__ (outils de validation) : racine
        return None
    here = os.path.dirname(os.path.abspath(me))
    root = os.path.dirname(os.path.dirname(here))
    if (os.path.basename(here).lower() == "test_dynamique"
            and os.path.normcase(os.path.normpath(root)) == os.path.normcase(os.path.normpath(SANDBOX))):
        return here
    return None


STAGE = _detect_stage()
if STAGE:
    PRODUCT = os.path.join(STAGE, "AiTron")
    LOGDIR = os.path.join(STAGE, "log")

INSTALLER_NAME = "install_AiTron_v3.py"
CHARTE_NAME    = "CHARTE.md"

LOCALAI_TAG     = "v4.11.0"
LOCALAI_VERSION = "v4.11.0-win.1"

LLAMACPP_TAG    = "b11375"
LLAMACPP_ZIP    = "llama-b11375-bin-win-cpu-x64.zip"
LLAMACPP_URL    = ("https://github.com/ggml-org/llama.cpp/releases/download/"
                   "b11375/llama-b11375-bin-win-cpu-x64.zip")
LLAMACPP_SHA256 = "90c6721cb0b8d37658b00da9f3e0521e1749c2e5593fb2553a397cc835f1fa9d"

MODEL_FILE   = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODEL_URL    = ("https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/"
                "resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf?download=true")
MODEL_SHA256 = "6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83"

CORE_EXE   = "local-ai.exe"
BRIDGE_EXE = "cloud-proxy.exe"
# ---------------------------------------------------------------------------
# v3.1.2 (Section 2) -- FALLBACKS DE TELECHARGEMENT des binaires du coeur.
# Ordre : build\out\ (local) -> dev\old\test_dynamique\ (staging) -> produit
# deploye -> telechargement GitHub Releases (URLs PERENNES + SHA-256 ci-dessous).
# Le garde-fou d'integrite PE "MZ" est CONSERVE (applique a tout .exe telecharge).
# ---------------------------------------------------------------------------
FALLBACK_LOCAL_AI_URL        = "https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/local-ai.exe"
FALLBACK_CLOUD_PROXY_URL     = "https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/cloud-proxy.exe"
FALLBACK_LOCAL_AI_SHA256     = "0F55C48379F971A6108339C9D90291A76D8DD21CDCE283AD8EF972C4E3855B34"
FALLBACK_CLOUD_PROXY_SHA256  = "BFCB28047F97F4DD4D6374938971BAA2F2711BFA6992C866EEED078B88F50F0C"

# ---------------------------------------------------------------------------
# Phase 2 (v1.2.0) : Python embarque, LiteLLM, backends multi-modaux, ports
# ---------------------------------------------------------------------------
PYTHON_EMBED_RELEASES = ["3.11.9", "3.11.8", "3.12.4"]
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip"
PYTHON_EMBED_FILE = "python-3.11.9-embed-amd64.zip"
PYTHON_EMBED_SHA256 = "009d6bf7e3b2ddca3d784fa09f90fe54336d5b60f0e0f305c37f400bf83cfd3b"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
GET_PIP_FILE = "get-pip.py"
LITELLM_VERSION = "1.103.2"

WHISPER_CPP_RELEASES = ["v1.9.2", "v1.9.1", "v1.9.0"]
WHISPER_CPP_TAG = "v1.9.2"
WHISPER_CPP_URL = "https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.2/whisper-bin-Win32.zip"
WHISPER_CPP_FILE = "whisper-bin-Win32.zip"
WHISPER_CPP_SHA256 = "de170719aebcb4794d695d449e179002db1fe03b862f21f5c34b2909a7cf8f22"
WHISPER_MODEL_FILE = "ggml-base.bin"
WHISPER_MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
WHISPER_MODEL_SHA256 = "60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"

SD_CPP_RELEASES = ["master-929-3f8527a", "master-previous", "master-stable"]
SD_CPP_TAG = "master-929-3f8527a"
SD_CPP_URL = "https://github.com/leejet/stable-diffusion.cpp/releases/download/master-929-3f8527a/sd-master-3f8527a-bin-win-cpu-x64.zip"
SD_CPP_FILE = "sd-win-cpu-x64.zip"
SD_CPP_SHA256 = "5e7caca2080321b25a12c1fa4175cb7d953f2b182309f8f73bfc9c725231d26c"
SD_TURBO_FILE = "sd-turbo.safetensors"
SD_TURBO_URL = "https://huggingface.co/stabilityai/sd-turbo/resolve/main/sd_turbo.safetensors"
# Modele image LEGER (< 2 Go, v1.4.1) : quantisation Q8_0 de SD-Turbo (compatible sd.cpp).
SD_TURBO_LIGHT_FILE = "sd_turbo-f16-q8_0.gguf"
SD_TURBO_LIGHT_URL = ("https://huggingface.co/Green-Sky/SD-Turbo-GGUF/resolve/main/"
                      "sd_turbo-f16-q8_0.gguf")
SD_TURBO_LIGHT_SHA256 = "d50be7655f0a554cf8041c145d88b210bd5f3c545423119dee62ae08cae51580"
SD_TURBO_LIGHT_MB = 1880

# --- Phase 5 (v1.5.0) : VISION locale (GGUF + projecteur mmproj apparie) ----------
# Chaque modele multimodal exige DEUX fichiers : le modele principal et son projecteur.
# Le telechargement est atomique : les deux fichiers ou rien (voir model_manager.ps1).
VLM_QWEN_FILE = "Qwen2-VL-2B-Instruct-Q4_K_M.gguf"
VLM_QWEN_MMPROJ = "mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf"
VLM_QWEN_BASE = "https://huggingface.co/ggml-org/Qwen2-VL-2B-Instruct-GGUF/resolve/main/"
VLM_QWEN_SHA256 = "5745685d2e607a82a0696c1118e56a2a1ae0901da450fd9cd4f161c6b62867d7"
VLM_QWEN_MMPROJ_SHA256 = "a0ad91f00a7a80dcf84d719a61b00ee2e07b71794f4ee2dfa81a254621a8c418"
VLM_QWEN_MB = 942
VLM_QWEN_MMPROJ_MB = 676

VLM_SMOL_FILE = "SmolVLM-500M-Instruct-Q8_0.gguf"
VLM_SMOL_MMPROJ = "mmproj-SmolVLM-500M-Instruct-Q8_0.gguf"
VLM_SMOL_BASE = "https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/"
VLM_SMOL_SHA256 = "9d4612de6a42214499e301494a3ecc2be0abdd9de44e663bda63f1152fad1bf4"
VLM_SMOL_MMPROJ_SHA256 = "d1eb8b6b23979205fdf63703ed10f788131a3f812c7b1f72e0119d5d81295150"
VLM_SMOL_MB = 420
VLM_SMOL_MMPROJ_MB = 100
VLM_PORT = 8095

# --- Phase 5 (v1.5.0) : SDK MCP officiel (isole : runtime\mcp\packages) -----------
MCP_VERSION = "2.3.0"
MCP_SPEC = "2024-11-05"

# --- Phase 8 (v1.8.0) : acceleration universelle NPU via DirectML ------------------
# DirectML est la couche de virtualisation de calcul native de Windows : elle adresse
# NPU Intel / NPU AMD XDNA2 / GPU sans SDK constructeur. Repli CPU obligatoire (QA).
ONNX_MODEL_FILE = "mnist-8.onnx"
ONNX_MODEL_URL = ("https://github.com/onnx/models/raw/main/validated/vision/classification/"
                  "mnist/model/mnist-8.onnx")
ONNX_MODEL_SHA256 = "2f06e72de813a8635c9bc0397ac447a601bdbfa7df4bebc278723b958831c9bf"
ONNX_MODEL_MB = 1

# --- Phase 9 (v1.9.0) : Speculative Decoding TEXT-ONLY ----------------------------
# Contrainte upstream : le modele DRAFT doit partager le TOKENIZER du principal, et le
# pipeline de draft est desactive des qu'un projecteur multimodal (--mmproj) est charge.
# Paire retenue : Qwen2.5 (meme famille de tokenizer) 1.5B principal + 0.5B draft.
SPEC_MODEL_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
SPEC_MODEL_URL = ("https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/"
                  "qwen2.5-1.5b-instruct-q4_k_m.gguf")
SPEC_MODEL_SHA256 = "6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e"
SPEC_MODEL_MB = 1065
SPEC_DRAFT_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
SPEC_DRAFT_URL = ("https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
                  "qwen2.5-0.5b-instruct-q4_k_m.gguf")
SPEC_DRAFT_SHA256 = "74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db"
SPEC_DRAFT_MB = 471

KOKORO_RELEASES = ["model-files-v1.1", "model-files-v1.0"]
KOKORO_TAG = "model-files-v1.1"
KOKORO_BASE_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/"
KOKORO_MODEL_FILE = "kokoro-v1.1-zh.onnx"
KOKORO_VOICES_FILE = "voices-v1.1-zh.bin"
KOKORO_MODEL_SHA256 = "859f9ded9f53be16c24857cdab3254a45da53c3afd5ba6ef134c7de3f822e326"
KOKORO_VOICES_SHA256 = "14cb6186c99e4f6016871405f62046c5df863ae27465cbdc4ee08be7dd703acd"

# Ports logiques (l'ordre de recherche d'un port libre suit cet ordre)
DEFAULT_PORTS = {
    "localai": 8080,
    "llama": 8090,
    "whisper": 8091,
    "sd": 8092,
    "tts": 8093,
    "litellm": 4000,
}

# ---------------------------------------------------------------------------
# Phase 3 (v1.3.0) : variantes GPU de llama.cpp + profils materiels
# ---------------------------------------------------------------------------
LLAMACPP_BASE_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b11375"
LLAMA_VARIANT_URLS = {
    "cpu":    LLAMACPP_BASE_URL + "/llama-b11375-bin-win-cpu-x64.zip",
    "vulkan": LLAMACPP_BASE_URL + "/llama-b11375-bin-win-vulkan-x64.zip",
    "cuda":   LLAMACPP_BASE_URL + "/llama-b11375-bin-win-cuda-12.4-x64.zip",
    "hip":    LLAMACPP_BASE_URL + "/llama-b11375-bin-win-rocm-10.0-x64.zip",
}
LLAMA_VARIANT_FILES = {
    "cpu": "llama-cpu.zip",
    "vulkan": "llama-vulkan.zip",
    "cuda": "llama-cuda.zip",
    "hip": "llama-hip.zip",
}
LLAMA_VARIANT_SHA256 = {
    "vulkan": "36ab68f330ee4ccde52c035167d54fc80f65410114df06d7c0a65eb03509f7f8",
    "cuda":   "74b9eca35bd514abc1d34b9a33e1844b3fa88f35e0b49fcea023375466d3417c",
}
CUDART_URL = LLAMACPP_BASE_URL + "/cudart-llama-bin-win-cuda-12.4-x64.zip"
CUDART_FILE = "cudart.zip"
CUDART_SHA256 = "8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6"

SD_CPP_CUDA_URL = ("https://github.com/leejet/stable-diffusion.cpp/releases/download/"
                   "master-929-3f8527a/sd-master-3f8527a-bin-win-cuda12-x64.zip")
SD_CPP_CUDA_FILE = "sd-cuda.zip"
SD_CPP_CUDA_SHA256 = "217d6dead9abd3f827fc338268555cc179234e7e6330ef21ecb1c985e19d2dc7"

PROFILE_NAMES = ["soft", "normal", "hard", "auto", "custom"]

BLACKBOX_INSTALLER = "install_AiTron_v3_%s.py.txt"
BLACKBOX_CHARTE    = "CHARTE_%s.md"


def _ts():
    return time.strftime("%Y%m%d_%H%M%S")


class Log(object):
    """Journalisation double : console + fichier append-only (Section 6.4)."""

    def __init__(self, path):
        self.path = path
        self.fh = None
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.fh = open(path, "a", encoding="utf-8")
        except Exception:
            self.fh = None

    def _w(self, level, msg):
        line = "[%s] %-5s %s" % (time.strftime("%H:%M:%S"), level, msg)
        try:
            print(line)
        except Exception:
            pass
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()

    def info(self, m):
        self._w("INFO", m)

    def warn(self, m):
        self._w("WARN", m)

    def error(self, m):
        self._w("ERROR", m)

    def ok(self, m):
        self._w("OK", m)

    def close(self):
        if self.fh:
            self.fh.close()


def archive_installer():
    """Section 1.2 -- Boite noire ante-execution.

    Copie physique du script maitre vers Installeur\\ au format strict
    install_AiTron_v3_AAAAMMJJ_HHMMSS.py.txt, et de CHARTE.md vers
    CHARTE_AAAAMMJJ_HHMMSS.md. DOIT etre la 1re instruction de main().
    """
    os.makedirs(BLACKBOX, exist_ok=True)
    stamp = _ts()
    archived = []
    src_script = os.path.join(SANDBOX, INSTALLER_NAME)
    if os.path.isfile(src_script):
        dst = os.path.join(BLACKBOX, BLACKBOX_INSTALLER % stamp)
        shutil.copy2(src_script, dst)
        archived.append(("installer", dst))
    src_charte = os.path.join(SANDBOX, CHARTE_NAME)
    if os.path.isfile(src_charte):
        dst = os.path.join(BLACKBOX, BLACKBOX_CHARTE % stamp)
        shutil.copy2(src_charte, dst)
        archived.append(("charte", dst))
    return archived


def validate_deploy_code(code_string):
    """Section 1.4 -- triple validation AST (parse + compile + py_compile)."""
    tree = ast.parse(code_string)                       # 1. ast.parse
    compile(code_string, "<AITRON_DEPLOY_CODE>", "exec")  # 2. compile
    tmpdir = os.path.join(BUILD, "tmp")
    os.makedirs(tmpdir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".py", dir=tmpdir)   # 3. py_compile
    os.close(fd)
    cfile = tmp + "c"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(code_string)
        py_compile.compile(tmp, cfile=cfile, doraise=True)
    finally:
        for p in (tmp, cfile):
            try:
                os.remove(p)
            except OSError:
                pass
    return len(tree.body)


AITRON_DEPLOY_CODE = r'''
# ===========================================================================
# AITRON_DEPLOY_CODE -- code de deploiement embarque (compile par l'installeur)
# Contrainte (Section 0.2) : aucun delimiteur triple-guillemet n'apparait ici.
# ===========================================================================
import hashlib as _hashlib
import json as _json
import os as _os
import shutil as _shutil
import subprocess as _subprocess
import time as _time
import urllib.request as _urlreq
import zipfile as _zipfile

LAUNCHER_BAT = r"""@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title AiTron V3 (portage natif)

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "AITRON_MODELS_PATH=%ROOT%\models"
set "AITRON_BACKENDS_PATH=%ROOT%\backends"
set "AITRON_CONFIG_DIR=%ROOT%\configuration"
set "AITRON_ADDRESS=127.0.0.1:8080"
set "AITRON_DISABLE_GALLERY_ENDPOINT=true"
set "AITRON_AUTOLOAD_BACKEND_GALLERIES=false"
set "AITRON_AUTOLOAD_GALLERIES=false"
set "AITRON_LOG_LEVEL=info"
set "AITRON_BACKENDS_SYSTEM_PATH=%ROOT%\backends-system"
set "AITRON_DATA_PATH=%ROOT%\data"
set "AITRON_GENERATED_CONTENT_PATH=%ROOT%\data\generated"
set "AITRON_UPLOAD_PATH=%ROOT%\data\uploads"
set "AITRON_EXTERNAL_GRPC_BACKENDS=cloud-proxy:%ROOT%\backends\llama-cpp\cloud-proxy.exe"
set "LLAMA_PORT=8090"

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
if not exist "%ROOT%\backends-system" mkdir "%ROOT%\backends-system"

echo ===============================================================================
echo  AiTron V3 - portage natif (sans Docker, sans WSL)
echo ===============================================================================

rem --- 1. Verification des composants critiques ---
set "MISSING=0"
for %%F in ("%ROOT%\local-ai.exe" "%ROOT%\backends\llama-cpp\llama-server.exe" "%ROOT%\backends\llama-cpp\cloud-proxy.exe" "%ROOT%\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf") do (
  if not exist %%F (
    echo [ERREUR] Composant manquant : %%F
    set "MISSING=1"
  )
)
if "!MISSING!"=="1" (
  echo.
  echo Lancez "python install_localai_win.py" pour reconstruire le produit deploye.
  pause
  exit /b 1
)

rem --- 2. Demarrage du moteur d'inference llama.cpp (llama-server) ---
echo [1/3] Demarrage du moteur llama.cpp ^(llama-server^) sur 127.0.0.1:%LLAMA_PORT% ...
start "localai-llama-server" /min "%ROOT%\backends\llama-cpp\llama-server.exe" ^
  -m "%ROOT%\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf" ^
  --host 127.0.0.1 --port %LLAMA_PORT% --ctx-size 4096 --threads %NUMBER_OF_PROCESSORS% ^
  --log-file "%ROOT%\logs\llama-server.log"

rem --- 3. Attente de la disponibilite du backend ---
echo [2/3] Attente de la disponibilite du moteur d'inference ...
set "READY="
for /L %%I in (1,1,120) do (
  if not defined READY (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:%LLAMA_PORT%/health'; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>&1
    if !errorlevel! equ 0 set "READY=1"
    if not defined READY timeout /t 1 /nobreak >nul
  )
)
if not defined READY (
  echo [AVERTISSEMENT] Le moteur d'inference ne repond pas encore. Poursuite du demarrage.
)

rem --- 4. Lancement du coeur LocalAI ---
echo [3/3] Lancement du coeur LocalAI sur http://127.0.0.1:8080 ...
echo       API : http://127.0.0.1:8080/v1/models
echo       Arret : fermez cette fenetre OU executez stop.bat
echo.
"%ROOT%\local-ai.exe" run ^
  --address 127.0.0.1:8080 ^
  --models-path "%ROOT%\models" ^
  --backends-path "%ROOT%\backends" ^
  --external-grpc-backends "cloud-proxy:%ROOT%\backends\llama-cpp\cloud-proxy.exe"

echo.
echo [LocalAI] Coeur arrete. Nettoyage du moteur d'inference ...
call "%ROOT%\stop.bat" silent
endlocal
"""

STOP_BAT = r"""@echo off
rem stop.bat - Arrete proprement TOUS les services LocalAI (zero zombie).
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "SILENT=%~1"
if not "%SILENT%"=="silent" echo [LocalAI] Arret de tous les services (coeur, moteurs, LiteLLM, TTS) ...

rem 1. Arret par PID traces (data\pids.txt)
set "PIDS=%ROOT%\data\pids.txt"
if exist "%PIDS%" (
  for /f "usebackq tokens=1,2" %%A in ("%PIDS%") do taskkill /PID %%B /T /F >nul 2>&1
  del /q "%PIDS%" >nul 2>&1
)

rem 2. Filet de securite : binaires connus du produit
taskkill /IM local-ai.exe /T /F >nul 2>&1
taskkill /IM cloud-proxy.exe /T /F >nul 2>&1
taskkill /IM llama-server.exe /T /F >nul 2>&1
taskkill /IM whisper-server.exe /T /F >nul 2>&1
taskkill /IM sd-server.exe /T /F >nul 2>&1

rem 2b. Services Python rattaches au produit (TTS, LiteLLM)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like ('%ROOT%\*') -and $_.Name -eq 'python.exe' -and $_.CommandLine -notlike '*i18n.py* run *' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1

set "LEFT="
for /f "delims=" %%P in ('tasklist /FI "IMAGENAME eq local-ai.exe" /NH 2^>nul ^| findstr /I "local-ai.exe"') do set "LEFT=1"
for /f "delims=" %%P in ('tasklist /FI "IMAGENAME eq cloud-proxy.exe" /NH 2^>nul ^| findstr /I "cloud-proxy.exe"') do set "LEFT=1"
for /f "delims=" %%P in ('tasklist /FI "IMAGENAME eq llama-server.exe" /NH 2^>nul ^| findstr /I "llama-server.exe"') do set "LEFT=1"
for /f "delims=" %%P in ('tasklist /FI "IMAGENAME eq whisper-server.exe" /NH 2^>nul ^| findstr /I "whisper-server.exe"') do set "LEFT=1"
for /f "delims=" %%P in ('tasklist /FI "IMAGENAME eq sd-server.exe" /NH 2^>nul ^| findstr /I "sd-server.exe"') do set "LEFT=1"

if "%SILENT%"=="silent" (
  if defined LEFT exit /b 2
  exit /b 0
)
if defined LEFT (
  echo [AVERTISSEMENT] Des processus sont encore presents.
  endlocal
  exit /b 2
)
echo [LocalAI] Tous les processus sont arretes. Zero zombie.
endlocal
exit /b 0
"""

MODEL_YAML = r"""name: llama-3.2-1b-instruct
# Le coeur LocalAI achemine les requetes chat vers le backend gRPC natif Windows
# "cloud-proxy" (enregistre via --external-grpc-backends), lequel transmet au
# moteur d'inference llama.cpp (llama-server.exe) via une API OpenAI-compatible.
backend: cloud-proxy
context_size: 4096
f16: false
parameters:
  model: Llama-3.2-1B-Instruct-Q4_K_M.gguf
proxy:
  upstream_url: http://127.0.0.1:8090/v1/chat/completions
  mode: translate
  provider: openai
  upstream_model: llama-3.2-1b-instruct
"""

BACKEND_README = r"""backends\llama-cpp\ -- Backend d'inference llama.cpp (Windows natif)
======================================================================

Ce dossier est le backend "llama.cpp" fonctionnel du produit AiTron V3.
Il est remplacable individuellement (Section 0.4 : arborescence ouverte).

Contenu et roles
----------------
* llama-server.exe (+ llama.dll, ggml*.dll, libomp.dll, mtmd.dll, ...)
    -> moteur d'inference llama.cpp officiel (ggml-org), build Windows CPU x64.
* cloud-proxy.exe
    -> backend gRPC NATIF WINDOWS (compile depuis les sources LocalAI, Go,
       CGO_ENABLED=0). Il expose le service gRPC "Backend" attendu par le coeur
       LocalAI, et relaie les requetes vers le moteur llama.cpp via HTTP
       (mode "translate", provider "openai").

Pourquoi cette composition ?
----------------------------
Le backend llama.cpp historique de LocalAI (backend/cpp/llama-cpp) est un
serveur C++/gRPC compile sous Linux (Docker). Il n'est pas compilable nativement
sur Windows sans une chaine gRPC C++ complete. La solution retenue compose donc :

    coeur LocalAI (local-ai.exe)  --gRPC-->  cloud-proxy.exe  --HTTP-->  llama-server.exe

Les deux binaires (coeur + bridge) sont compiles localement depuis les sources
officielles LocalAI v4.11.0. Le moteur llama.cpp provient des releases officielles
ggml-org (build b11375).

Remplacement
------------
* Moteur llama.cpp  : remplacer les fichiers du dossier par une nouvelle release
  ggml-org "llama-<tag>-bin-win-cpu-x64.zip" (garder les DLL ensemble).
* Bridge gRPC       : recompiler cloud-proxy (voir INSTALLATION.md) puis copier.
* Modele            : deposer un autre fichier .gguf dans ..\..\models\ et adapter
  models\llama-3.2-1b-instruct.yaml (parametre model + upstream_model).
"""

WHISPER_README = r"""backends\whisper-cpp\ -- Backend speech-to-text (whisper.cpp)
===============================================================
Service HTTP autonome (port 8091) servant une API compatible OpenAI :
  POST /v1/audio/transcriptions   (multipart : file, model)
  (route obtenue via --inference-path /v1/audio/transcriptions ; reponse {"text": "..."})

Contenu :
  * whisper-server.exe (+ whisper.dll, ggml*.dll, SDL2.dll, ...) : binaire
    officiel ggml-org (release v1.9.2, Windows x64).
Modele : ..\..\models\ggml-base.bin (Whisper Base, ggml).

Lancement isole (test) :
  whisper-server.exe -m ..\..\models\ggml-base.bin --host 127.0.0.1 --port 8091 --inference-path /v1/audio/transcriptions

Remplacement : deposer une release ggml-org plus recente
"whisper-bin-Win32.zip" (garder les DLL ensemble).
"""

SD_README = r"""backends\stable-diffusion\ -- Backend image (stable-diffusion.cpp)
=====================================================================
Service HTTP autonome (port 8092) servant une API compatible OpenAI :
  POST /v1/images/generations

Contenu :
  * sd-server.exe, sd-cli.exe, stable-diffusion.dll, ggml*.dll, libwebp*.dll
    -> binaires officiels leejet/stable-diffusion.cpp (Windows CPU x64).
Modele : ..\..\models\sd-turbo.safetensors  (NON telecharge par defaut : volumineux).

Lancement isole (test) :
  sd-server.exe -m ..\..\models\sd-turbo.safetensors --listen-ip 127.0.0.1 --listen-port 8092

Telecharger le modele : Run-LocalAI.bat pull sd-turbo
Remplacement : release leejet/stable-diffusion.cpp "sd-<tag>-bin-win-cpu-x64.zip".
"""

TTS_README = r"""backends\tts\ -- Backend text-to-speech (kokoro-onnx)
=====================================================
Service HTTP autonome (port 8093) servi par le Python embarque
(..\..\runtime\python\python.exe) executant tts_server.py :
  POST /v1/audio/speech        -> WAV
  GET  /health, /v1/models

Fichiers :
  * tts_server.py                       serveur HTTP (stdlib + kokoro-onnx)
  * ..\..\models\kokoro-v1.1-zh.onnx    modele Kokoro (ONNX)
  * ..\..\models\voices-v1.1-zh.bin     banque de voix

Lancement isole (test) :
  ..\..\runtime\python\python.exe tts_server.py --port 8093 ^
      --model ..\..\models\kokoro-v1.1-zh.onnx ^
      --voices ..\..\models\voices-v1.1-zh.bin
"""

FREEPORT_PS1 = r"""# freeport.ps1 - trouve un port TCP libre a partir de <Start>
param([int]$Start = 8080)
$p = $Start
while ($p -lt ($Start + 200)) {
  try {
    $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $p)
    $l.Start(); $l.Stop()
    Write-Output $p
    exit 0
  } catch { $p++ }
}
Write-Output $Start
exit 1
"""

SPAWN_PS1 = r"""# spawn.ps1 - demarre un service et enregistre son PID (suivi d'arret propre)
param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Exe,
  [string]$Arguments = "",
  [string]$WorkDir = "",
  [string]$OutLog = ""
)
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
if (-not $WorkDir) { $WorkDir = Split-Path -Parent $Exe }
$dataDir = Join-Path $root 'data'
$logsDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $dataDir, $logsDir | Out-Null
$p = $null
if ($Arguments -and $Arguments.Trim().Length -gt 0) {
  if ($OutLog) { $p = Start-Process -FilePath $Exe -ArgumentList $Arguments -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $OutLog }
  else        { $p = Start-Process -FilePath $Exe -ArgumentList $Arguments -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru }
} else {
  $p = Start-Process -FilePath $Exe -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru
}
Add-Content -Path (Join-Path $dataDir 'pids.txt') -Value ("{0} {1}" -f $Name, $p.Id)
Write-Output $p.Id
"""

MODEL_MANAGER_PS1 = r"""# model_manager.ps1 - Model Manager (catalogue JSON multi-modal)
param(
  [Parameter(Mandatory=$true)][ValidateSet('list','pull','show','remove')][string]$Action,
  [string]$Id
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$catalog = Join-Path $root 'models\models-catalog.json'
$modelsDir = Join-Path $root 'models'
if (-not (Test-Path $catalog)) { Write-Host "[model-manager] catalogue introuvable : $catalog"; exit 2 }
$cat = Get-Content $catalog -Raw | ConvertFrom-Json

function Show-Model($m) {
  $flag = $(if ($m.recommended) { '[recommande]' } else { '' })
  Write-Host ("  {0,-26} {1,-6} {2,-11} {3,6} Mo  {4}" -f $m.id, $m.modality, $m.format, $m.size_mb, $flag)
}

switch ($Action) {
  'list' {
    Write-Host "Catalogue de modeles ($($cat.models.Count)) :"
    foreach ($m in $cat.models) { Show-Model $m }
    Write-Host ""
    Write-Host "Telecharger : Run-LocalAI.bat pull <id>"
  }
  'show' {
    $m = $cat.models | Where-Object { $_.id -eq $Id }
    if (-not $m) { Write-Host "[model-manager] inconnu : $Id"; exit 3 }
    $m | ConvertTo-Json -Depth 5
  }
  'remove' {
    $m = $cat.models | Where-Object { $_.id -eq $Id }
    if (-not $m) { Write-Host "[model-manager] inconnu : $Id"; exit 3 }
    $dest = Join-Path $modelsDir $m.filename
    if (Test-Path $dest) { Remove-Item $dest -Force; Write-Host "[model-manager] supprime : $dest" }
    else { Write-Host "[model-manager] absent : $dest" }
  }
  'pull' {
    if (-not $Id) { Write-Host "[model-manager] usage : pull <id>"; exit 2 }
    $m = $cat.models | Where-Object { $_.id -eq $Id }
    if (-not $m) { Write-Host "[model-manager] modele inconnu : $Id"; exit 3 }

    $jobs = New-Object System.Collections.ArrayList
    [void]$jobs.Add([pscustomobject]@{ label = $m.name; file = $m.filename; url = $m.source; sha = "$($m.sha256)".ToLower(); mb = $m.size_mb })
    if ($m.multimodal -and $m.mmproj) {
      [void]$jobs.Add([pscustomobject]@{ label = "$($m.name) [projecteur mmproj]"; file = $m.mmproj.filename; url = $m.mmproj.source; sha = "$($m.mmproj.sha256)".ToLower(); mb = $m.mmproj.size_mb })
      Write-Host ("[model-manager] modele multimodal : acquisition ATOMIQUE de {0} fichiers (les deux ou rien)" -f $jobs.Count)
    }
    if ($m.draft) {
      [void]$jobs.Add([pscustomobject]@{ label = "$($m.name) [modele draft]"; file = $m.draft.filename; url = $m.draft.source; sha = "$($m.draft.sha256)".ToLower(); mb = $m.draft.size_mb })
      Write-Host ("[model-manager] paire texte draft : acquisition ATOMIQUE de {0} fichiers (principal + draft, speculatif)" -f $jobs.Count)
    }

    $todo = New-Object System.Collections.ArrayList
    foreach ($j in $jobs) {
      $d = Join-Path $modelsDir $j.file
      if (Test-Path $d) {
        $h = (Get-FileHash $d -Algorithm SHA256).Hash.ToLower()
        if ($h -eq $j.sha) { Write-Host "[model-manager] deja present et valide : $($j.file)"; continue }
        Write-Host "[model-manager] $($j.file) present mais hash different -> retelechargement"
      }
      [void]$todo.Add($j)
    }
    if ($todo.Count -eq 0) { exit 0 }

    $parts = New-Object System.Collections.ArrayList
    foreach ($j in $todo) {
      $d = Join-Path $modelsDir $j.file
      $tmp = "$d.part"
      if (Test-Path $tmp) { Remove-Item $tmp -Force }
      Write-Host ("[model-manager] telechargement {0} ({1} Mo) ..." -f $j.label, $j.mb)
      & curl.exe -L --retry 3 --retry-all-errors --progress-bar -o $tmp $j.url
      if ($LASTEXITCODE -ne 0) {
        Write-Host "[model-manager] ECHEC du telechargement (code $LASTEXITCODE) -> annulation atomique"
        foreach ($p in $parts) { if (Test-Path $p.tmp) { Remove-Item $p.tmp -Force } }
        if (Test-Path $tmp) { Remove-Item $tmp -Force }
        exit 4
      }
      $h2 = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
      if ($j.sha -and ($h2 -ne $j.sha)) {
        Write-Host "[model-manager] SHA-256 INVALIDE pour $($j.file) : attendu $($j.sha), obtenu $h2 -> annulation atomique"
        foreach ($p in $parts) { if (Test-Path $p.tmp) { Remove-Item $p.tmp -Force } }
        Remove-Item $tmp -Force
        exit 5
      }
      [void]$parts.Add([pscustomobject]@{ tmp = $tmp; dest = $d; file = $j.file })
    }

    # Bascule atomique : tous les fichiers sont verifies -> on publie alors seulement.
    foreach ($p in $parts) {
      Move-Item $p.tmp $p.dest -Force
      Write-Host "[model-manager] OK : $($p.dest)"
    }
    if ($parts.Count -gt 1) { Write-Host "[model-manager] paire modele + projecteur publiee (atomique)." }
  }
}
"""

VRAM_WATCHDOG_PY = r"""# vram_watchdog.py - surveillance continue de la VRAM (v1.4.1)
# Thread/processus daemon : echantillonne la VRAM, alerte, agit de facon preventive.
import argparse
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SANDBOX = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(ROOT, "logs")
STATUS = os.path.join(DATA, "vram-status.json")
ACTION = os.path.join(DATA, "vram-action.json")
VRAMLOG = os.path.join(LOGS, "vram.log")
CRASHLOG = os.path.join(SANDBOX, "dev", "crash.log")
PIDS = os.path.join(DATA, "pids.txt")
LLAMA_CMD = os.path.join(DATA, "llama-cmd.json")

DEFAULT_ALERT_PCT = 15.0
DEFAULT_CRIT_PCT = 5.0
DEFAULT_RECOVER_PCT = 20.0
CONFIG = os.path.join(ROOT, "config")
PROFILE = os.path.join(CONFIG, "profile.json")
PEERS = os.path.join(CONFIG, "peers.json")
DEFAULT_RPC_PORT = 50052
HOT_RELOAD_S = 5.0


def _read_profile():
    # Profil appris (v2.0.0b) : lu AU VOL, jamais obligatoire.
    try:
        with open(PROFILE, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return None


def _pct(env_name, default):
    try:
        return float(os.environ.get(env_name, default))
    except Exception:
        return default


def log(level, msg, crash=False):
    line = "[%s] [GPU_VRAM] [%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), level, msg)
    try:
        with open(VRAMLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass
    if crash:
        try:
            with open(CRASHLOG, "a", encoding="utf-8") as fh:
                fh.write("[%s] [GPU_VRAM] [%s] %s\n---\n" % (time.strftime("%Y%m%d_%H%M%S"), level, msg))
        except Exception:
            pass


def read_vram():
    # 1. nvidia-smi (le plus fiable) ; 2. WMI (VRAM totale seulement)
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            first = out.stdout.strip().splitlines()[0]
            total, used, free = [int(x.strip()) for x in first.split(",")[:3]]
            return {"source": "nvidia-smi", "total_mb": total, "used_mb": used, "free_mb": free}
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$v=Get-CimInstance Win32_VideoController | Where-Object { $_.AdapterRAM -gt 0 } | "
             "Select-Object -First 1; if($v){ [int]([math]::Round($v.AdapterRAM/1MB,0)) }"],
            capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip().isdigit():
            total = int(out.stdout.strip())
            return {"source": "wmi", "total_mb": total, "used_mb": 0, "free_mb": total}
    except Exception:
        pass
    return None


def write_json(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass


def find_pid(name):
    try:
        with open(PIDS, encoding="utf-8-sig") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == name:
                    return int(parts[1])
    except Exception:
        pass
    return None


def relaunch_llama_cpu(log_path):
    # Action preventive : relance le moteur en CPU pur (-ngl 0) pour liberer la VRAM.
    try:
        with open(LLAMA_CMD, encoding="utf-8-sig") as fh:
            spec = json.load(fh)
    except Exception as exc:
        return False, "commande moteur inconnue (%s)" % exc
    exe = spec.get("exe")
    args = list(spec.get("args") or [])
    workdir = spec.get("workdir") or (os.path.dirname(exe) if exe else ROOT)
    if not exe or not os.path.isfile(exe):
        return False, "binaire moteur introuvable"
    new_args = []
    replaced = False
    i = 0
    while i < len(args):
        if args[i] == "-ngl" and i + 1 < len(args):
            new_args.extend(["-ngl", "0"])
            replaced = True
            i += 2
            continue
        new_args.append(args[i])
        i += 1
    if not replaced:
        new_args.extend(["-ngl", "0"])
    old = find_pid("llama")
    if old:
        subprocess.run(["taskkill", "/PID", str(old), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    out = open(log_path, "ab")
    proc = subprocess.Popen([exe] + new_args, cwd=workdir, stdout=out, stderr=subprocess.STDOUT)
    try:
        with open(PIDS, "a", encoding="utf-8") as fh:
            fh.write("llama %d\n" % proc.pid)
    except Exception:
        pass
    return True, "llama-server relance en CPU pur (-ngl 0), pid %d" % proc.pid


def _federated_targets():
    # Noeuds RPC distants DECLARES (config\peers.json) ET reellement joignables (test TCP court).
    # Aucune donnee d'inference n'est transmise ici : simple verification de disponibilite.
    try:
        with open(PEERS, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except Exception:
        return []
    out = []
    for _k, p in (data.get("peers") or {}).items():
        if not isinstance(p, dict):
            continue
        host = p.get("ip") or p.get("host")
        try:
            port = int(p.get("rpc_port") or DEFAULT_RPC_PORT)
        except (TypeError, ValueError):
            port = DEFAULT_RPC_PORT
        if not host or host in ("127.0.0.1", "localhost"):
            continue  # notre propre noeud : pas de deport vers soi-meme
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            out.append((host, port, p))
        except Exception:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass
    out.sort(key=lambda t: (t[2].get("latency_ms") if t[2].get("latency_ms") is not None else 1e9))
    return out


def federated_relaunch(log_path):
    # ROUTAGE FEDERE LOCAL (v2.1.0b) : l'hote sature -> le calcul est deporte en injectant
    # l'argument EXACT --rpc <IP>:<Port> attendu par le coeur RPC natif de llama.cpp.
    # Le transport et la parallelisation restent delegues a 100% a llama.cpp.
    targets = _federated_targets()
    if not targets:
        return False, "aucun noeud RPC distant joignable (calcul local conserve)"
    try:
        with open(LLAMA_CMD, encoding="utf-8-sig") as fh:
            spec = json.load(fh)
    except Exception as exc:
        return False, "commande moteur inconnue (%s)" % exc
    exe = spec.get("exe")
    args = list(spec.get("args") or [])
    workdir = spec.get("workdir") or (os.path.dirname(exe) if exe else ROOT)
    if not exe or not os.path.isfile(exe):
        return False, "binaire moteur introuvable"
    if "--rpc" in args:
        return False, "routage federe deja actif"
    rpc_val = ",".join("%s:%d" % (h, p) for h, p, _ in targets)
    new_args = list(args) + ["--rpc", rpc_val]
    old = find_pid("llama")
    if old:
        subprocess.run(["taskkill", "/PID", str(old), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    out = open(log_path, "ab")
    proc = subprocess.Popen([exe] + new_args, cwd=workdir, stdout=out, stderr=subprocess.STDOUT)
    try:
        with open(PIDS, "a", encoding="utf-8") as fh:
            fh.write("llama %d\n" % proc.pid)
    except Exception:
        pass
    return True, "llama-server relance avec routage federe (--rpc %s), pid %d" % (rpc_val, proc.pid)


def sample_loop(interval, alert, crit, recover, action_enabled):
    state = "ok"
    log_path = os.path.join(LOGS, "llama-server.log")
    base = (alert, crit, recover)  # valeurs de reference (usine / ligne de commande)
    hot = {"at": 0.0, "applied": base}
    while True:
        # Profil apprenant continu (v2.0.0b) : relecture PERIODIQUE de config\profile.json.
        # Profil present -> seuils appris appliques A CHAUD ; profil efface (reset-profile)
        # -> retour IMMEDIAT aux valeurs d'usine. Aucun redemarrage necessaire.
        now = time.time()
        if now - hot["at"] >= HOT_RELOAD_S:
            hot["at"] = now
            pr = _read_profile()
            want = base
            if pr:
                try:
                    want = (float(pr["vram_alert_pct"]), float(pr["vram_crit_pct"]),
                            float(pr["vram_recover_pct"]))
                except (KeyError, TypeError, ValueError):
                    want = base
            if want != hot["applied"]:
                hot["applied"] = want
                alert, crit, recover = want
                if pr and pr.get("source") == "usine":
                    kind = "d'usine '%s'" % pr.get("factory")
                elif pr:
                    kind = "appris"
                else:
                    kind = "d'usine (retour)"
                log("INFO", "profil %s applique A CHAUD : alerte<%.1f%% critique<%.1f%% "
                            "reprise>%.1f%%%s" % (kind, alert, crit, recover,
                                                  (" (ngl=%s)" % pr.get("ngl")) if pr else ""),
                    crash=True)
        st = read_vram()
        if st and st.get("total_mb"):
            free_pct = 100.0 * st["free_mb"] / st["total_mb"]
            if free_pct < crit:
                if state != "critical":
                    state = "critical"
                    log("CRITICAL", "VRAM critique : %.1f%% libre (< %.0f%%)" % (free_pct, crit), crash=True)
                    acted = False
                    msg = "action desactivee (--no-action)"
                    if action_enabled:
                        # Escalade v2.1.0b : ROUTAGE FEDERE d'abord (deport du calcul vers un
                        # noeud RPC distant) ; a defaut, repli CPU pur (-ngl 0).
                        acted, msg = federated_relaunch(log_path)
                        if not acted:
                            acted, msg = relaunch_llama_cpu(log_path)
                    write_json(ACTION, {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "trigger": "critical",
                                        "free_pct": round(free_pct, 2),
                                        "action": ("routage-federe (--rpc)"
                                                   if "--rpc" in msg else "relaunch-llama-cpu (ngl=0)"),
                                        "applied": acted, "detail": msg})
                    log("WARN", "action preventive : %s" % msg, crash=True)
            elif free_pct < alert:
                if state == "ok":
                    state = "alert"
                    log("WARN", "VRAM faible : %.1f%% libre (< %.0f%%)" % (free_pct, alert), crash=True)
            elif free_pct > recover and state != "ok":
                state = "ok"
                log("INFO", "VRAM revenue a la normale : %.1f%% libre (> %.0f%%)" % (free_pct, recover))
            st.update({"free_pct": round(free_pct, 2), "state": state, "alert_pct": alert,
                       "crit_pct": crit, "recover_pct": recover, "watchdog": "running",
                       "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
            write_json(STATUS, st)
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser(description="Watchdog VRAM (v1.4.1)")
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--alert", type=float, default=_pct("AITRON_VRAM_ALERT_PCT", DEFAULT_ALERT_PCT))
    ap.add_argument("--crit", type=float, default=_pct("AITRON_VRAM_CRIT_PCT", DEFAULT_CRIT_PCT))
    ap.add_argument("--recover", type=float, default=_pct("AITRON_VRAM_RECOVER_PCT", DEFAULT_RECOVER_PCT))
    ap.add_argument("--no-action", action="store_true", help="ne pas appliquer l'action preventive")
    ap.add_argument("--once", action="store_true", help="un seul echantillon puis sortie")
    args = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    if args.once:
        st = read_vram() or {}
        if st.get("total_mb"):
            st["free_pct"] = round(100.0 * st["free_mb"] / st["total_mb"], 2)
        write_json(STATUS, st)
        print(json.dumps(st, ensure_ascii=False))
        return 0
    log("INFO", "watchdog VRAM demarre (intervalle %.1fs ; alerte<%.0f%% critique<%.0f%% reprise>%.0f%%)"
        % (args.interval, args.alert, args.crit, args.recover))
    try:
        sample_loop(args.interval, args.alert, args.crit, args.recover, not args.no_action)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

RAG_INGEST_PY = r"""# rag_ingest.py - pipeline RAG local unifie (NumPy seul, sans faiss)
# Extraction multi-format -> chunking -> embeddings (moteur llama.cpp) -> index a plat.
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAG_DIR = os.path.join(ROOT, "runtime", "rag")
MODEL_FILE = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
TEXT_EXT = {".txt", ".md", ".json", ".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h",
            ".hpp", ".java", ".cs", ".sh", ".bat", ".ps1", ".yaml", ".yml", ".toml", ".ini",
            ".cfg", ".csv", ".xml", ".html", ".css", ".sql", ".rb", ".php"}
DOC_EXT = {".pdf", ".docx", ".xlsx"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def _log(msg):
    print("[rag] " + msg, flush=True)


def _http_json(url, payload=None, timeout=900):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ready(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % port, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def ensure_embed_server(port):
    # Reutilise le moteur si deja pret, sinon demarre une instance --embeddings.
    if _ready(port):
        return None
    exe = os.path.join(ROOT, "backends", "llama-cpp", "llama-server.exe")
    model = os.path.join(ROOT, "models", MODEL_FILE)
    if not os.path.isfile(exe) or not os.path.isfile(model):
        raise RuntimeError("moteur ou modele introuvable pour les embeddings")
    for sub in ("data", "logs"):
        os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
    out = open(os.path.join(ROOT, "logs", "embed-server.log"), "ab")
    proc = subprocess.Popen(
        [exe, "-m", model, "-ngl", "99", "--embeddings", "--pooling", "mean",
         "--host", "127.0.0.1", "--port", str(port), "-c", "2048"],
        cwd=os.path.dirname(exe), stdout=out, stderr=subprocess.STDOUT)
    with open(os.path.join(ROOT, "data", "pids.txt"), "a", encoding="utf-8") as fh:
        fh.write("embed-server %d\n" % proc.pid)
    deadline = time.time() + 180
    while time.time() < deadline:
        if _ready(port):
            _log("serveur d'embeddings pret (pid %d, port %d)" % (proc.pid, port))
            return proc
        time.sleep(0.5)
    raise RuntimeError("le serveur d'embeddings ne repond pas")


def embed_texts(texts, port, batch=32):
    vectors = []
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        res = _http_json("http://127.0.0.1:%d/v1/embeddings" % port,
                         {"input": chunk, "model": "local"})
        rows = sorted(res.get("data", []), key=lambda d: d.get("index", 0))
        vectors.extend([r["embedding"] for r in rows])
    return vectors
def _image_meta(path):
    # Dimensions lues dans l'en-tete binaire : aucune dependance externe (ni PIL, ni ImageMagick).
    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)
    w = h = 0
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w = int.from_bytes(head[16:20], "big")
                h = int.from_bytes(head[20:24], "big")
            elif head[:2] == b"\xff\xd8":
                fh.seek(2)
                while True:
                    b = fh.read(1)
                    if not b:
                        break
                    if b != b"\xff":
                        continue
                    marker = fh.read(1)
                    while marker == b"\xff":
                        marker = fh.read(1)
                    if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3"):
                        fh.read(3)
                        h = int.from_bytes(fh.read(2), "big")
                        w = int.from_bytes(fh.read(2), "big")
                        break
                    ln = fh.read(2)
                    if len(ln) < 2:
                        break
                    fh.seek(int.from_bytes(ln, "big") - 2, 1)
            elif head[:4] == b"GIF8":
                w = int.from_bytes(head[6:8], "little")
                h = int.from_bytes(head[8:10], "little")
            elif head[:2] == b"BM":
                w = int.from_bytes(head[18:22], "little")
                h = int.from_bytes(head[22:26], "little")
    except Exception:
        pass
    return {"kind": "image", "format": ext.lstrip("."), "width": w, "height": h,
            "bytes": size, "megapixels": round((w * h) / 1000000.0, 3) if (w and h) else 0}


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        meta = _image_meta(path)
        return ("[image %s %dx%d px, %d octets, %.3f MP] fichier image indexe : %s"
                % (meta["format"], meta["width"], meta["height"], meta["bytes"],
                   meta["megapixels"], os.path.basename(path)))
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if ext == ".docx":
        import docx
        document = docx.Document(path)
        return "\n".join(p.text for p in document.paragraphs)
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        lines = []
        for ws in wb.worksheets:
            lines.append("# feuille: %s" % ws.title)
            for row in ws.iter_rows(values_only=True):
                cells = ["" if c is None else str(c) for c in row]
                if any(cells):
                    lines.append("\t".join(cells))
        return "\n".join(lines)
    # v3.1.0 (D2) : cp1252 AVANT latin-1. latin-1 decode 0x80-0x9F en caracteres de controle
    # (oe -> \x9c) ; cp1252 restitue les ligatures et la typographie (oe, guillemets, euro).
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, encoding=enc) as fh:
                return fh.read()
        except UnicodeDecodeError:
            continue
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def chunk_text(text, size=2048, overlap=0.10):
    size = max(256, int(size))
    step = max(1, int(size * (1.0 - float(overlap))))
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        piece = text[i:i + size].strip()
        if piece:
            chunks.append(piece)
        if i + size >= n:
            break
        i += step
    return chunks


def iter_files(input_dir):
    only = TEXT_EXT | DOC_EXT | IMAGE_EXT
    for base, _dirs, names in os.walk(input_dir):
        for name in sorted(names):
            if os.path.splitext(name)[1].lower() in only:
                yield os.path.join(base, name)


def _update_registry(collection, manifest):
    reg_path = os.path.join(RAG_DIR, "collections.json")
    reg = {}
    if os.path.isfile(reg_path):
        try:
            with open(reg_path, encoding="utf-8") as fh:
                reg = json.load(fh)
        except Exception:
            reg = {}
    reg[collection] = {"chunks": manifest["chunks"], "dim": manifest["dim"],
                       "updated_at": manifest["created_at"]}
    with open(reg_path, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, indent=2, ensure_ascii=False)
def build_index(input_dir, collection, port, chunk_size, overlap, no_start):
    if not os.path.isdir(input_dir):
        raise RuntimeError("dossier introuvable : %s" % input_dir)
    import numpy as np
    files = list(iter_files(input_dir))
    _log("%d fichier(s) candidat(s) dans %s" % (len(files), input_dir))
    records = []
    errors = []
    images = 0
    for path in files:
        try:
            text = extract_text(path)
        except Exception as exc:
            errors.append({"file": path, "error": str(exc)})
            _log("ECHEC extraction %s : %s" % (path, exc))
            continue
        meta = {}
        if os.path.splitext(path)[1].lower() in IMAGE_EXT:
            meta = _image_meta(path)
            images += 1
            _log("image indexee : %s (%dx%d px, %.3f MP)"
                 % (os.path.basename(path), meta["width"], meta["height"], meta["megapixels"]))
        for idx, piece in enumerate(chunk_text(text, chunk_size, overlap)):
            records.append({"source": os.path.relpath(path, input_dir).replace(os.sep, "/"),
                            "chunk": idx, "chars": len(piece), "text": piece, "meta": meta})
    if not records:
        raise RuntimeError("aucun contenu exploitable dans %s" % input_dir)
    if not no_start:
        ensure_embed_server(port)
    _log("embeddings de %d chunks ..." % len(records))
    t0 = time.time()
    vectors = embed_texts([r["text"] for r in records], port)
    dt = time.time() - t0
    arr = np.asarray(vectors, dtype=np.float32)
    np.save(os.path.join(RAG_DIR, "index-%s.npy" % collection), arr)
    with open(os.path.join(RAG_DIR, "chunks-%s.jsonl" % collection), "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    manifest = {"collection": collection, "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "input_dir": input_dir, "files": len(files), "images": images,
                "chunks": len(records),
                "dim": int(arr.shape[1]), "chunk_size": chunk_size, "overlap": overlap,
                "vector_backend": "numpy-cosine (faiss proscrit)",
                "embedding_source": "llama.cpp /v1/embeddings (--pooling mean)",
                "duration_s": round(dt, 2), "errors": errors}
    with open(os.path.join(RAG_DIR, "manifest-%s.json" % collection), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    _update_registry(collection, manifest)
    _log("index '%s' : %d chunks x %d dims en %.1fs" % (collection, len(records), arr.shape[1], dt))
    _log("fichiers a plat : index-%s.npy / chunks-%s.jsonl / manifest-%s.json"
         % (collection, collection, collection))
    return 0


def search(query, collection, port, topk, no_start):
    import numpy as np
    vpath = os.path.join(RAG_DIR, "index-%s.npy" % collection)
    cpath = os.path.join(RAG_DIR, "chunks-%s.jsonl" % collection)
    if not os.path.isfile(vpath):
        raise RuntimeError("index '%s' inexistant : lancer 'Run-LocalAI.bat index <dossier>'" % collection)
    V = np.load(vpath)
    chunks = []
    with open(cpath, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                chunks.append(json.loads(line))
    if not no_start:
        ensure_embed_server(port)
    q = np.asarray(embed_texts([query], port)[0], dtype=np.float32)
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    qn = q / (np.linalg.norm(q) + 1e-9)
    sims = Vn @ qn
    order = np.argsort(-sims)[:max(1, topk)]
    print("=== RAG '%s' : %d resultat(s) (similarite cosinus) ===" % (collection, len(order)))
    for rank, idx in enumerate(order, 1):
        c = chunks[int(idx)]
        print("%2d. [%.4f] %s#%s (%d car.)"
              % (rank, float(sims[int(idx)]), c["source"], c["chunk"], c["chars"]))
        print("     " + " ".join(c["text"][:220].split()))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Pipeline RAG local (NumPy seul, sans faiss)")
    ap.add_argument("--input", help="dossier a indexer")
    ap.add_argument("--collection", default="default")
    ap.add_argument("--chunk-size", type=int, default=2048)
    ap.add_argument("--overlap", type=float, default=0.10)
    ap.add_argument("--port", type=int, default=8094)
    ap.add_argument("--query", help="requete de recherche (au lieu d'indexer)")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--no-start-server", action="store_true")
    args = ap.parse_args()
    os.makedirs(RAG_DIR, exist_ok=True)
    try:
        if args.query:
            return search(args.query, args.collection, args.port, args.topk, args.no_start_server)
        if not args.input:
            ap.error("--input est requis pour l'indexation")
        return build_index(args.input, args.collection, args.port, args.chunk_size,
                           args.overlap, args.no_start_server)
    except Exception as exc:
        _log("ERREUR : %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""



TTS_SERVER_PY = r"""# tts_server.py - service HTTP TTS (kokoro-onnx) pour AiTron V3
# Expose /health, /v1/models et /v1/audio/speech (compatible OpenAI).
import argparse
import io
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ENGINE = None
DEFAULT_VOICE = "af_maple"
VOICES = []
PROVIDER = "cpu"
PROVIDERS = ["CPUExecutionProvider"]


def _candidate_providers():
    try:
        import onnxruntime as ort
        avail = ort.get_available_providers()
    except Exception:
        avail = ["CPUExecutionProvider"]
    cands = []
    for name in ("DmlExecutionProvider", "CUDAExecutionProvider"):
        if name in avail:
            cands.append([name, "CPUExecutionProvider"])
    cands.append(["CPUExecutionProvider"])
    return cands


def _try_load(providers, model_path, voices_path):
    import onnxruntime as ort
    original = ort.InferenceSession

    def patched(*a, **kw):
        kw.setdefault("providers", providers)
        return original(*a, **kw)

    ort.InferenceSession = patched
    try:
        from kokoro_onnx import Kokoro
        engine = Kokoro(model_path, voices_path)
        raw = engine.get_voices()
        if isinstance(raw, dict):
            voices = sorted(str(x) for x in raw.keys())
        elif isinstance(raw, (list, tuple, set)):
            voices = sorted(str(x) for x in raw)
        else:
            voices = []
        probe = "af_maple" if "af_maple" in voices else (voices[0] if voices else None)
        if probe:
            engine.create("ok", voice=probe, speed=1.0, lang="en-us")
        return engine, voices
    finally:
        ort.InferenceSession = original


def load_engine(model_path, voices_path):
    # Charge Kokoro en essayant DirectML/CUDA puis CPU (repli automatique).
    global ENGINE, DEFAULT_VOICE, VOICES, PROVIDER, PROVIDERS
    last = None
    for provs in _candidate_providers():
        try:
            engine, voices = _try_load(provs, model_path, voices_path)
            ENGINE, VOICES, PROVIDERS = engine, voices, provs
            PROVIDER = provs[0]
            break
        except Exception as exc:
            last = "%s: %s" % (provs[0], exc)
            ENGINE = None
    if ENGINE is None:
        raise RuntimeError("TTS : aucun provider ONNX fonctionnel (%s)" % last)
    if VOICES:
        DEFAULT_VOICE = "af_maple" if "af_maple" in VOICES else VOICES[0]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send_json(200, {"status": "ok", "provider": PROVIDER, "voices": len(VOICES)})
        elif self.path.startswith("/v1/models"):
            self._send_json(200, {"object": "list", "data": [{"id": "kokoro", "object": "model"}]})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/v1/audio/speech"):
            self._send_json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as exc:
            self._send_json(400, {"error": "bad request: %s" % exc})
            return
        text = (req.get("input") or "").strip()
        if not text:
            self._send_json(400, {"error": "input is required"})
            return
        voice = req.get("voice") or DEFAULT_VOICE
        speed = float(req.get("speed") or 1.0)
        lang = req.get("lang") or "en-us"
        try:
            import soundfile as sf
            samples, sr = ENGINE.create(text, voice=voice, speed=speed, lang=lang)
            buf = io.BytesIO()
            sf.write(buf, samples, sr, format="WAV")
            data = buf.getvalue()
        except Exception as exc:
            self._send_json(500, {"error": "tts failed: %s" % exc})
            return
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--voices", required=True)
    args = ap.parse_args()
    load_engine(args.model, args.voices)
    print("[tts] kokoro pret (provider: %s, voix: %d, defaut: %s) sur %s:%d" % (PROVIDER, len(VOICES), DEFAULT_VOICE, args.host, args.port), flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
"""

LITELLM_LAUNCH_PY = r"""# litellm_launch.py - lanceur LiteLLM (UTF-8 + sys.path des callbacks)
# Le Python embarque est en mode isole (._pth) : PYTHONPATH est ignore.
# Lancer ce script depuis config\ place ce dossier dans sys.path[0], ce qui
# rend complexity_router importable pour le chargement des callbacks.
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import litellm  # noqa: E402

if __name__ == "__main__":
    # Entry point officiel : litellm=litellm:run_server (click lit sys.argv[1:])
    litellm.run_server()
"""

COMPLEXITY_ROUTER_PY = r"""# complexity_router.py - callback LiteLLM : routage local/externe par complexite.
# Regle "Token Saver" : prompt court -> modele local ; sinon -> modele externe
# (si une cle cloud est configuree), sinon repli local.
import os

from litellm.integrations.custom_logger import CustomLogger


class ComplexityRouter(CustomLogger):
    VIRTUALS = ("smart", "localai", "auto")
    # Modeles de litellm-config.yaml dont le contenu quitte la machine (D5, v3.1.0).
    CLOUD_DIRECT = ("openrouter-claude", "gpt-4o", "claude-sonnet", "deepseek")

    def __init__(self):
        super().__init__()
        self.local = os.environ.get("AITRON_ROUTE_LOCAL", "local-llama")
        try:
            self.threshold = int(os.environ.get("AITRON_ROUTE_WORDS", "3"))
        except Exception:
            self.threshold = 3
        try:
            self.ctx_limit = int(os.environ.get("AITRON_ROUTE_CONTEXT", "6000"))
        except Exception:
            self.ctx_limit = 6000
        self.log_path = os.environ.get("AITRON_ROUTING_LOG", "")
        # --- Filtre de confidentialite PII (v1.7.0) : BEST-EFFORT ---
        self.pii_enabled = str(os.environ.get("AITRON_PII_FILTER", "1")).lower() not in (
            "0", "false", "no", "off")
        self.pii_levels = os.environ.get("AITRON_PII_LEVELS", "1,2,3")
        try:
            self.pii_port = int(os.environ.get("LLAMA_PORT", "8090") or 8090)
        except Exception:
            self.pii_port = 8090
        try:
            from pii_filter import PIIFilter
            self._PIIFilter = PIIFilter
        except Exception:
            self._PIIFilter = None

    def _text(self, data):
        parts = []
        for m in (data.get("messages") or []):
            if not isinstance(m, dict):
                continue
            c = m.get("content")
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, list):
                for p in c:
                    if isinstance(p, dict) and isinstance(p.get("text"), str):
                        parts.append(p["text"])
        return " ".join(parts)

    def _cloud_model(self):
        # Preference : OpenRouter > DeepSeek > OpenAI > Anthropic (premiere cle presente)
        if os.environ.get("OPENROUTER_API_KEY"):
            return os.environ.get("AITRON_ROUTE_CLOUD", "openrouter-claude")
        if os.environ.get("DEEPSEEK_API_KEY"):
            return "deepseek"
        if os.environ.get("OPENAI_API_KEY"):
            return "gpt-4o"
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "claude-sonnet"
        return None

    def _record(self, requested, selected, reason, tokens):
        if not self.log_path:
            return
        try:
            import json as _json
            import time as _time
            line = _json.dumps({"at": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "requested": requested, "selected": selected,
                                "reason": reason, "approx_tokens": tokens}, ensure_ascii=False)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            pass

    def _pii(self, no_filter=False):
        # Instancie le filtre si le module est present et le filtre actif.
        if self._PIIFilter is None or not self.pii_enabled or no_filter:
            return None
        try:
            levels = tuple(int(x) for x in str(self.pii_levels).split(",") if x.strip().isdigit())
            return self._PIIFilter(levels=levels or (1, 2), port=self.pii_port)
        except Exception:
            return None

    def _mask_in_place(self, data):
        # Le contenu ne doit quitter la machine que MASQUE (protection BEST-EFFORT).
        meta = data.get("metadata")
        if not isinstance(meta, dict):
            meta = {}
            data["metadata"] = meta
        flag = str(meta.get("no_pii_filter", "")).lower() in ("1", "true", "yes", "on")
        flt = self._pii(no_filter=flag)
        if flt is None:
            self._record_pii("filtre PII inactif (desactive ou module absent)", 0)
            return
        mapping, count = {}, 0
        for m in (data.get("messages") or []):
            if not isinstance(m, dict):
                continue
            c = m.get("content")
            if isinstance(c, str):
                masked, mp = flt.redact(c)
                if mp:
                    m["content"] = masked
                    mapping.update(mp)
                    count += len(mp)
            elif isinstance(c, list):
                for p in c:
                    if isinstance(p, dict) and isinstance(p.get("text"), str):
                        masked, mp = flt.redact(p["text"])
                        if mp:
                            p["text"] = masked
                            mapping.update(mp)
                            count += len(mp)
        if mapping:
            meta["_pii_map"] = mapping
            meta["_pii_count"] = count
        self._record_pii("masquage avant debordement cloud", len(mapping))

    def _record_pii(self, reason, n):
        if not self.log_path:
            return
        try:
            import json as _json
            import time as _time
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(_json.dumps({"at": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      "pii": reason, "masques": n,
                                      "niveaux": self.pii_levels, "actif": self.pii_enabled},
                                     ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _restore_in_response(self, response, mapping):
        # Demasquage transparent : l'utilisateur local retrouve ses valeurs d'origine.
        try:
            for ch in (response.get("choices") or []):
                msg = ch.get("message") or {}
                c = msg.get("content")
                if isinstance(c, str):
                    for token, original in mapping.items():
                        c = c.replace(token, original)
                    msg["content"] = c
        except Exception:
            pass

    def _decide(self, data):
        if not isinstance(data, dict):
            return data
        requested = data.get("model")
        if requested not in self.VIRTUALS:
            # v3.1.0 (D5) : un modele CLOUD demande DIRECTEMENT (openrouter-claude, gpt-4o,
            # claude-sonnet, deepseek...) quitte aussi la machine : le masquage PII s'applique
            # donc a TOUTE route non locale, pas seulement aux modeles virtuels. Seuls le modele
            # local et les modeles inconnus (rejetes par la gateway) restent intacts.
            if requested in self.CLOUD_DIRECT:
                self._mask_in_place(data)
            return data
        text = self._text(data)
        words = len(text.split())
        approx = max(1, len(text) // 4)
        cloud = self._cloud_model()
        if approx > self.ctx_limit:
            selected = cloud or self.local
            reason = "contexte sature (%d tok > %d)" % (approx, self.ctx_limit)
        elif words < self.threshold:
            selected = self.local
            reason = "prompt court (%d mots < %d)" % (words, self.threshold)
        elif cloud:
            selected = cloud
            reason = "prompt complexe (%d mots)" % words
        else:
            selected = self.local
            reason = "prompt complexe (%d mots), aucune cle cloud -> local" % words
        data["model"] = selected
        self._record(requested, selected, reason, approx)
        # Filtre PII : masquage uniquement si le contenu quitte la machine (route cloud).
        if selected != self.local:
            self._mask_in_place(data)
        return data

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        try:
            return self._decide(data)
        except Exception:
            return data

    async def async_post_call_success_hook(self, user_api_key_dict, data, response):
        # Restaure les jetons masques dans la reponse renvoyee a l'utilisateur local.
        try:
            meta = (data or {}).get("metadata") or {}
            mapping = meta.get("_pii_map") or {}
            if mapping:
                self._restore_in_response(response, mapping)
        except Exception:
            pass
        return response


proxy_handler_instance = ComplexityRouter()
"""

LITELLM_CONFIG_YAML = r"""# litellm-config.yaml -- Gateway de routage LocalAI (local/externe, BYOK)
# Les cles externes sont lues depuis l'environnement, charge par Run-LocalAI.bat
# depuis config\cloud-keys.env (jamais de cle en dur ici).

model_list:
  # ------------------- Modeles LOCAUX (coeur LocalAI) -------------------
  - model_name: local-llama
    litellm_params:
      model: openai/llama-3.2-1b-instruct
      api_base: os.environ/AITRON_API_BASE
      api_key: os.environ/AITRON_LOCAL_KEY

  # ------------------- Modeles EXTERNES (BYOK) -------------------
  - model_name: openrouter-claude
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: os.environ/OPENROUTER_API_KEY

  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: deepseek
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY

  # ------------------- Modele VIRTUEL unique (Token Saver) -------------------
  # Point d'entree unique cote client : le callback complexity_router.py choisit
  # local (prompt court) ou cloud (prompt complexe / contexte sature).
  - model_name: localai
    litellm_params:
      model: openai/llama-3.2-1b-instruct
      api_base: os.environ/AITRON_API_BASE
      api_key: os.environ/AITRON_LOCAL_KEY

  # Alias equivalent (compatibilite v1.2.0/v1.3.0)
  - model_name: smart
    litellm_params:
      model: openai/llama-3.2-1b-instruct
      api_base: os.environ/AITRON_API_BASE
      api_key: os.environ/AITRON_LOCAL_KEY

litellm_settings:
  callbacks: ["complexity_router.proxy_handler_instance"]
  drop_params: true
  num_retries: 2

general_settings:
  master_key: sk-local
"""

CLOUD_KEYS_ENV = r"""# cloud-keys.env -- Cles API externes (BYOK). NE JAMAIS VERSIONNER.
# Renseignez uniquement les fournisseurs desires, puis relancez : Run-LocalAI.bat start
# Toute clee laissee vide desactive le modele externe correspondant.
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
"""

KEYS_ENV = r"""# keys.env -- Cles API externes (BYOK). NE JAMAIS VERSIONNER.
# Genere/edite par : Run-LocalAI.bat key-set <provider> <valeur>
# Fournisseurs : OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
"""

KEY_SET_PS1 = r"""# key_set.ps1 - injecte une cle API dans config\keys.env (sans alterer le reste)
param(
  [Parameter(Mandatory=$true)][string]$Provider,
  [Parameter(Mandatory=$true)][string]$Value
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$envPath = Join-Path $root 'config\keys.env'
New-Item -ItemType Directory -Force -Path (Join-Path $root 'config') | Out-Null
$map = @{
  'openrouter' = 'OPENROUTER_API_KEY'
  'openai'     = 'OPENAI_API_KEY'
  'anthropic'  = 'ANTHROPIC_API_KEY'
  'deepseek'   = 'DEEPSEEK_API_KEY'
}
$key = $map[$Provider.ToLower()]
if (-not $key) {
  Write-Host ("[key-set] fournisseur inconnu : {0} (attendu : openrouter|openai|anthropic|deepseek)" -f $Provider)
  exit 2
}
$lines = @()
if (Test-Path $envPath) { $lines = @(Get-Content $envPath) }
if ($lines.Count -eq 0) { $lines = @('# keys.env - cles API externes (BYOK). NE JAMAIS VERSIONNER.') }
$out = @()
$found = $false
foreach ($l in $lines) {
  if ($l -match ('^\s*' + [regex]::Escape($key) + '\s*=')) { $out += ($key + '=' + $Value); $found = $true }
  else { $out += $l }
}
if (-not $found) { $out += ($key + '=' + $Value) }
[IO.File]::WriteAllText($envPath, (($out -join "`r`n") + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("[key-set] {0} mis a jour dans {1} (valeur masquee)" -f $key, $envPath)
Write-Host "[key-set] relancez 'Run-LocalAI.bat start' pour appliquer."
exit 0
"""

PROXY_LOGS_PS1 = r"""# proxy_logs.ps1 - logs de routage (LiteLLM + Token Saver)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$routing = Join-Path $root 'logs\routing.jsonl'
$litellm = Join-Path $root 'logs\litellm.log'
$litellmErr = Join-Path $root 'logs\litellm.log.err'

Write-Host "=== Token Saver : dernieres decisions de routage ==="
if (Test-Path $routing) {
  Get-Content $routing -Tail 20 | ForEach-Object {
    try {
      $j = $_ | ConvertFrom-Json
      Write-Host ("  {0}  {1,-12} -> {2,-16} ({3})" -f $j.at, $j.requested, $j.selected, $j.reason)
    } catch { Write-Host ("  " + $_) }
  }
} else {
  Write-Host "  (aucune decision : envoyez une requete sur http://127.0.0.1:4000/v1/chat/completions)"
}
Write-Host ""
Write-Host "=== LiteLLM : dernieres lignes ==="
if (Test-Path $litellm) { Get-Content $litellm -Tail 15 } else { Write-Host "  (logs\litellm.log absent)" }
if (Test-Path $litellmErr) { Get-Content $litellmErr -Tail 10 }
exit 0
"""

PII_FILTER_PY = r"""# pii_filter.py - filtre de confidentialite PII hybride BEST-EFFORT (v1.7.0)
# Niveau 1 : regex deterministes (emails, IP, cles API connues, JWT, cle PEM, cartes bancaires).
# Niveau 2 : heuristiques d'entropie de Shannon (mots de passe complexes, cles custom en clair).
# Niveau 3 : NER local leger via le moteur local (llama-server) - personnes, adresses, organisations.
# AVERTISSEMENT : protection BEST-EFFORT, ce n'est PAS une garantie d'etancheite a 100 %
# (voir INSTALLATION.md, section "Filtre de confidentialite"). Activation/desactivation :
# AITRON_PII_FILTER=0 ou le drapeau --no-pii-filter du proxy.
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")

LEVEL1 = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("IPV4", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b")),
    ("IPV6", re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    ("API_KEY_OPENAI", re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}\b")),
    ("API_KEY_GITHUB", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("API_KEY_AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("API_KEY_SLACK", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("PRIVATE_KEY_PEM", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]{20,}?-----END [A-Z ]*PRIVATE KEY-----")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
]

ENTROPY_MIN_LEN = 20
ENTROPY_BITS = 3.5
NONSPACE = re.compile(r"\S{%d,}" % ENTROPY_MIN_LEN)

NER_PROMPT = (
    "Tu identifies les entites nommees de type PERSONNE, ADRESSE ou ORGANISATION dans le texte. "
    "Reponds UNIQUEMENT par un tableau JSON contenant les chaines EXACTES trouvees, sans texte "
    "autour, par exemple [\"Jean Dupont\",\"12 rue de la Paix\"]. Si aucune entite : [].\n"
    "Texte :\n%s\nJSON :"
)


def _audit(kind, level, token, preview, extra=None):
    # Transparence : chaque operation de masquage est journalisee (categorie PRIVACY_FILTER).
    line = ("[%s] [PRIVACY_FILTER] [INFO] " % time.strftime("%Y%m%d_%H%M%S")
            + json.dumps({"masked": kind, "level": level, "token": token,
                          "preview": preview, "note": extra or
                          "protection BEST-EFFORT : ne garantit pas l'etancheite a 100 %"},
                         ensure_ascii=False))
    try:
        with open(CRASHLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n---\n")
    except Exception:
        pass
    return line


def _luhn(num):
    digits = [int(c) for c in re.sub(r"\D", "", num)]
    if len(digits) < 13:
        return False
    total, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _shannon(s):
    if not s:
        return 0.0
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = float(len(s))
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _mixed(tok):
    low = any(c.islower() for c in tok)
    up = any(c.isupper() for c in tok)
    dig = any(c.isdigit() for c in tok)
    sym = any(not c.isalnum() for c in tok)
    return (low and up and dig) or (dig and sym) or (up and sym)


def _http(url, payload=None, timeout=120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def level1_scan(text):
    found = []
    for kind, rx in LEVEL1:
        for m in rx.finditer(text):
            tok = m.group(0)
            if kind == "CREDIT_CARD" and not _luhn(tok):
                continue
            found.append((kind, 1, m.start(), m.end(), tok))
    return found


def level2_scan(text, spans):
    # Jetons non separes par des espaces : mots de passe complexes, cles custom en clair.
    found = []
    for m in NONSPACE.finditer(text):
        tok, s, e = m.group(0), m.start(), m.end()
        if any(not (e <= a or s >= b) for (_k, _l, a, b, _t) in spans):
            continue
        if tok.startswith("[PII-") or not _mixed(tok):
            continue
        if _shannon(tok) >= ENTROPY_BITS:
            found.append(("HIGH_ENTROPY_SECRET", 2, s, e, tok))
    return found


def _json_array(raw):
    start = raw.find("[")
    if start < 0:
        return []
    blob, depth = "", 0
    for i in range(start, len(raw)):
        if raw[i] == "[":
            depth += 1
        elif raw[i] == "]":
            depth -= 1
            if depth == 0:
                blob = raw[start:i + 1]
                break
    if not blob:
        tail = raw[start:]
        last = tail.rfind("\"")
        if last < 0:
            return []
        blob = tail[:last + 1] + "]"
    for attempt in (blob, re.sub(r",\s*([\]}])", r"\1", blob)):
        try:
            data = json.loads(attempt)
            return data if isinstance(data, list) else []
        except Exception:
            continue
    return []


def level3_scan(text, port, timeout=120):
    # NER leger : le moteur LOCAL extrait les entites nommees (aucun envoi externe).
    try:
        res = _http("http://127.0.0.1:%d/v1/chat/completions" % port,
                    {"model": "local",
                     "messages": [{"role": "user", "content": NER_PROMPT % text[:1500]}],
                     "max_tokens": 192, "temperature": 0}, timeout=timeout)
        raw = res["choices"][0]["message"]["content"]
    except Exception:
        return []
    out = []
    for n in _json_array(raw):
        if isinstance(n, str) and len(n.strip()) >= 4:
            for m in re.finditer(re.escape(n.strip()), text):
                out.append(("NAMED_ENTITY", 3, m.start(), m.end(), m.group(0)))
    return out

class PIIFilter:
    # Filtre hybride BEST-EFFORT : regex (N1) + entropie (N2) + NER local (N3).
    def __init__(self, levels=(1, 2, 3), port=8090, enabled=True, audit=True):
        self.levels = tuple(levels)
        self.port = int(port)
        self.audit = audit
        env_off = str(os.environ.get("AITRON_PII_FILTER", "1")).lower() in ("0", "false", "no", "off")
        self.enabled = bool(enabled) and not env_off
        self.deactivated_by = "AITRON_PII_FILTER=0" if env_off else (None if enabled else "--no-pii-filter")
        self.stats = {}

    def redact(self, text):
        # Retourne (texte_masque, mapping) ; le mapping permet le demasquage de la reponse.
        if not self.enabled or not text:
            return text, {}
        hits = level1_scan(text) if 1 in self.levels else []
        if 2 in self.levels:
            hits = hits + level2_scan(text, hits)
        if 3 in self.levels:
            hits = hits + level3_scan(text, self.port)
        # Selection gauche -> droite (le plus a gauche gagne) puis reconstruction en un passage.
        hits.sort(key=lambda h: h[2])
        kept = []
        for h in hits:
            if h[4].startswith("[PII-") or (kept and h[2] < kept[-1][3]):
                continue
            kept.append(h)
        parts, cursor, counters, mapping = [], 0, {}, {}
        for kind, lvl, a, b, tok in kept:
            counters[kind] = counters.get(kind, 0) + 1
            token = "[PII-%s-%d]" % (kind, counters[kind])
            parts.append(text[cursor:a])
            parts.append(token)
            mapping[token] = tok
            self.stats[kind] = self.stats.get(kind, 0) + 1
            if self.audit:
                _audit(kind, lvl, token, (tok[:6] + "...") if len(tok) > 9 else "***")
            cursor = b
        parts.append(text[cursor:])
        return "".join(parts), mapping

    def restore(self, text, mapping):
        if not mapping:
            return text
        out = text
        for token, original in mapping.items():
            out = out.replace(token, original)
        return out

    def summary(self):
        return dict(self.stats)

SAMPLE = ("Contact : jean.dupont@exemple.fr, IP 192.168.1.42 et 10.0.0.7. "
          "Cle OpenAI : sk-proj-abc123XYZ456def789GHI012jkl345. "
          "Jeton GitHub : ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. "
          "Mot de passe technique : Xk9$mQ2!vB7#pL4@wZ8rT1.")


def selftest(with_ner=False):
    print("=== autotest du filtre PII (BEST-EFFORT) ===")
    f = PIIFilter(levels=((1, 2, 3) if with_ner else (1, 2)), enabled=True)
    masked, mapping = f.redact(SAMPLE)
    print("--- avant ---"); print(SAMPLE)
    print("--- masque ---"); print(masked)
    print("--- jetons ---"); print(json.dumps(mapping, ensure_ascii=False, indent=2))
    back = f.restore(masked, mapping)
    print("--- restaure ---")
    print(back)
    ok = (back == SAMPLE
          and any("EMAIL" in k for k in mapping)
          and any("IPV4" in k for k in mapping)
          and any("OPENAI" in k for k in mapping)
          and any("GITHUB" in k for k in mapping)
          and any("HIGH_ENTROPY" in k for k in mapping))
    print("reversibilite : %s" % ("IDENTIQUE" if back == SAMPLE else "ECHEC"))
    print("types masques : %s" % ", ".join(sorted(k.split("-")[1] for k in mapping)))
    print("VERDICT : %s" % ("VERT" if ok else "A REVOIR"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Filtre de confidentialite PII hybride (BEST-EFFORT)")
    ap.add_argument("mode", nargs="?", default="test", choices=["test", "redact", "levels"])
    ap.add_argument("text", nargs="?")
    ap.add_argument("--levels", default="1,2,3")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--with-ner", action="store_true")
    ap.add_argument("--no-pii-filter", dest="disabled", action="store_true",
                    help="desactive le filtre (transparence utilisateur)")
    a = ap.parse_args()
    if a.mode == "levels":
        print("Niveau 1 (regex deterministes) : " + ", ".join(k for k, _ in LEVEL1))
        print("Niveau 2 (entropie) : seuil %.1f bits, longueur min %d, jeu de caracteres mixte exige"
              % (ENTROPY_BITS, ENTROPY_MIN_LEN))
        print("Niveau 3 (NER local) : moteur llama-server sur le port %d" % a.port)
        print("Statut : %s" % ("DESACTIVE (--no-pii-filter)" if a.disabled else "actif"))
        return 0
    if a.mode == "redact":
        if not a.text:
            ap.error("texte requis")
        f = PIIFilter(levels=tuple(int(x) for x in a.levels.split(",")), port=a.port,
                      enabled=not a.disabled)
        masked, mapping = f.redact(a.text)
        print(masked)
        print(json.dumps({"tokens": mapping, "stats": f.summary(), "enabled": f.enabled,
                          "desactive_par": f.deactivated_by}, ensure_ascii=False))
        return 0
    return selftest(with_ner=a.with_ner)


if __name__ == "__main__":
    sys.exit(main())
"""

ONNX_PROVIDER_PY = r"""# onnx_provider.py - acceleration universelle NPU via DirectML, avec repli CPU (v1.8.0)
# Priorite 1 : NPU Intel (DirectML / OpenVINO natif Windows 11)
# Priorite 2 : NPU AMD Ryzen AI (XDNA2) via les couches DirectML unifiees
# Repli QA   : CPU, TOUJOURS disponible, avec avertissement consigne (categorie GPU_DETECT).
# Les taches d'extraction semantique LEGERES (NER du filtre PII, outils MCP legers) sont
# adressees a ce provider ; le moteur llama.cpp reste le moteur principal (GPU Vulkan).
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")
ONNX_DIR = os.path.join(ROOT, "runtime", "onnx")
MODEL = os.path.join(ONNX_DIR, "mnist-8.onnx")
DATA = os.path.join(ROOT, "data")
STATUS = os.path.join(DATA, "onnx-status.json")


def _audit(level, msg):
    line = "[%s] [GPU_DETECT] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    try:
        with open(CRASHLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n---\n")
    except Exception:
        pass
    return line


def _ort():
    try:
        import onnxruntime as ort
        return ort
    except Exception:
        return None


def detect():
    # Renvoie le provider retenu et le motif (deterministe et auditable).
    ort = _ort()
    if ort is None:
        return {"available": False, "providers": [], "selected": "cpu", "device": "cpu",
                "reason": "onnxruntime absent"}
    provs = list(ort.get_available_providers())
    if "DmlExecutionProvider" in provs:
        return {"available": True, "providers": provs, "selected": "dml", "device": "npu/dml",
                "reason": "DirectML disponible (NPU Intel / NPU AMD XDNA2 / GPU universel)"}
    return {"available": True, "providers": provs, "selected": "cpu", "device": "cpu",
            "reason": "DirectML absent (pilote ou materiel incompatible) -> repli CPU"}


class Accelerator:
    # Point d'entree des taches semantiques legeres.

    def __init__(self, model=MODEL):
        self.model = model
        self.info = detect()
        self.session = None
        self.io = None
        self.latency_ms = None
        if self.info["selected"] == "cpu":
            _audit("WARN", "Acceleration DirectML indisponible (%s) : bascule automatique sur CPU "
                           "pour les taches semantiques legeres. Session utilisateur preservee."
                   % self.info["reason"])

    def open(self):
        ort = _ort()
        if ort is None or not os.path.isfile(self.model):
            return None
        acc = [p for p in ("DmlExecutionProvider", "CPUExecutionProvider")
               if p in self.info["providers"]]
        providers = acc or ["CPUExecutionProvider"]
        try:
            self.session = ort.InferenceSession(self.model, providers=providers)
        except Exception as exc:
            _audit("WARN", "Initialisation DirectML impossible (%s) -> repli CPU immediat." % exc)
            self.info["selected"] = "cpu"
            self.info["device"] = "cpu"
            self.info["reason"] = "echec d'initialisation DirectML -> repli CPU"
            try:
                self.session = ort.InferenceSession(self.model, providers=["CPUExecutionProvider"])
            except Exception as exc2:
                _audit("ERROR", "InferenceSession impossible : %s" % exc2)
                return None
        try:
            self.io = {"in": self.session.get_inputs()[0], "out": self.session.get_outputs()[0]}
        except Exception:
            return self.session
        return self.session

    def probe(self, runs=3):
        # Inference REELLE sur le modele sonde : valide le provider et mesure sa latence.
        if self.session is None and self.open() is None:
            return {"ok": False, "error": "aucune session ONNX disponible"}
        try:
            import numpy as np
        except Exception as exc:
            return {"ok": False, "error": "numpy indisponible (%s)" % exc}
        x = np.zeros([1, 1, 28, 28], dtype=np.float32)
        x[0, 0, 10:18, 10:18] = 1.0
        runs = max(1, int(runs))
        t0 = time.time()
        out = None
        for _ in range(runs):
            out = self.session.run([self.io["out"].name], {self.io["in"].name: x})
        self.latency_ms = round((time.time() - t0) * 1000.0 / runs, 2)
        try:
            pred = int(np.argmax(np.asarray(out[0]).reshape(-1)))
        except Exception:
            pred = -1
        return {"ok": True, "device": self.info["device"], "selected": self.info["selected"],
                "providers": self.info["providers"], "latency_ms": self.latency_ms,
                "runs": runs, "prediction": pred, "model": os.path.basename(self.model)}

    def status(self):
        return {"device": self.info["device"], "selected": self.info["selected"],
                "reason": self.info["reason"], "providers": self.info["providers"],
                "latency_ms": self.latency_ms, "model": os.path.basename(self.model)}

def _ports():
    p = {}
    try:
        with open(os.path.join(ROOT, "data", "runtime.env"), encoding="utf-8-sig") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    if k.strip().endswith("_PORT") and v.strip().isdigit():
                        p[k.strip()[:-5].lower()] = int(v.strip())
    except Exception:
        pass
    return p


def _hw_profile():
    try:
        with open(os.path.join(ROOT, "config", "hardware-profile.json"), encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _services():
    out = {}
    try:
        with open(os.path.join(ROOT, "data", "pids.txt"), encoding="utf-8-sig") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2:
                    out[parts[0]] = int(parts[1])
    except Exception:
        pass
    return out


SEMANTIC_TASKS = ("NER du filtre PII (niveau 3)",
                  "outils MCP legers (localai_semantic_probe)")


def hardware_status():
    prof, ports, svc = _hw_profile(), _ports(), _services()
    acc = Accelerator()
    st = acc.status()
    gpu = prof.get("gpu") or {}
    params = prof.get("params") or {}
    print("=== Repartition des charges d'inference (v1.8.0) ===")
    print("  Machine       : %s | %s" % ((prof.get("cpu") or {}).get("name"), gpu.get("name")))
    print("")
    print("  [MOTEUR PRINCIPAL] llama.cpp - inference de texte")
    print("    backend GPU : %s  (%s)" % (prof.get("active_variant"), prof.get("variant_reason")))
    print("    couches     : ngl=%s threads=%s ctx=%s"
          % (params.get("ngl"), params.get("threads"), params.get("ctx")))
    print("    service     : llama-server PID=%s (port %s)"
          % (svc.get("llama", "-"), ports.get("llama", "-")))
    print("")
    print("  [TACHES SEMANTIQUES DEPORTEES] extraction legere")
    print("    provider    : %s  ->  %s" % (st["selected"], st["device"]))
    print("    motif       : %s" % st["reason"])
    print("    providers   : %s" % (", ".join(st["providers"]) or "(aucun)"))
    lat = (" (%s ms/inference)" % st["latency_ms"]) if st["latency_ms"] else " (non mesure)"
    print("    modele sonde: %s%s" % (st["model"], lat))
    print("    taches      : %s" % ", ".join(SEMANTIC_TASKS))
    print("")
    print("  [AUTRES SERVICES]")
    alias = {"local-ai": "localai", "vram-watchdog": None, "peer-discovery": None}
    for name in ("vision", "failover", "sd", "whisper", "tts", "litellm", "local-ai", "vram-watchdog",
                 "peer-discovery"):
        if svc.get(name):
            key = alias.get(name, name)
            print("    %-15s PID=%-7s port=%s"
                  % (name, svc.get(name), ports.get(key, "-") if key else "-"))
    print("")
    print("  [REPLI QA] Si DirectML est indisponible, les taches semantiques basculent")
    print("             AUTOMATIQUEMENT sur le CPU (transparent, session preservee) et")
    print("             l'avertissement est consigne dans dev\\crash.log (categorie GPU_DETECT).")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Acceleration NPU/GPU universelle via DirectML")
    ap.add_argument("mode", nargs="?", default="status",
                    choices=["status", "probe", "hardware", "write"])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.mode == "hardware":
        return hardware_status()
    acc = Accelerator()
    if a.mode == "status":
        st = acc.status()
    elif a.mode == "probe":
        st = acc.probe(a.runs)
    else:
        st = acc.probe(a.runs)
        try:
            os.makedirs(DATA, exist_ok=True)
            with open(STATUS, "w", encoding="utf-8") as fh:
                json.dump({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "accelerator": st,
                           "tasks": list(SEMANTIC_TASKS)}, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass
    print(json.dumps(st, ensure_ascii=False, indent=2))
    if a.mode == "probe" and st.get("ok"):
        print("VERDICT : provider %s operationnel (%s ms/inference sur le modele sonde)"
              % (st.get("selected"), st.get("latency_ms")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

LEARN_PROFILE_PY = r"""# learn_profile.py - profil apprenant continu (v2.0.0b)
# Analyse la telemetrie REELLE des sessions (logs\history.jsonl, logs\vram.log,
# logs\failover.jsonl, config\hardware-profile.json) pour ajuster A CHAUD les seuils de
# securite du watchdog VRAM et la profondeur d'offload (-ngl) dans config\profile.json.
# Garde-fou QA : 'reset' restaure instantanement les profils d'usine (SOFT/NORMAL/HARD).
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "logs")
CONFIG = os.path.join(ROOT, "config")
DATA = os.path.join(ROOT, "data")
HISTORY = os.path.join(LOGS, "history.jsonl")
VRAMLOG = os.path.join(LOGS, "vram.log")
FAILLOG = os.path.join(LOGS, "failover.jsonl")
HWP = os.path.join(CONFIG, "hardware-profile.json")
PROFILE = os.path.join(CONFIG, "profile.json")
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")

FACTORY = {
    "soft":   {"vram_alert_pct": 20.0, "vram_crit_pct": 10.0, "vram_recover_pct": 30.0, "ngl_factor": 0.6},
    "normal": {"vram_alert_pct": 15.0, "vram_crit_pct": 5.0,  "vram_recover_pct": 20.0, "ngl_factor": 1.0},
    "hard":   {"vram_alert_pct": 10.0, "vram_crit_pct": 3.0,  "vram_recover_pct": 15.0, "ngl_factor": 1.0},
}
MIN_SAMPLES = 2


def _log(level, msg):
    line = "[%s] [PROFILE_LEARN] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    try:
        with open(CRASHLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n---\n")
    except Exception:
        pass
    return line


def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return default


def _read_jsonl(path, limit=4000):
    out = []
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
    except Exception:
        pass
    return out[-limit:]


def _history():
    return _read_jsonl(HISTORY)


def observe(note=""):
    # Enregistre une observation reelle de la session dans l'historique consolide.
    st = _read_json(os.path.join(DATA, "vram-status.json"), {}) or {}
    hw = _read_json(HWP, {}) or {}
    par = hw.get("params") or {}
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "vram_total_mb": st.get("total_mb"), "vram_free_mb": st.get("free_mb"),
           "vram_free_pct": st.get("free_pct"), "state": st.get("state"),
           "ngl": par.get("ngl"), "ctx": par.get("ctx"), "threads": par.get("threads"),
           "profile": hw.get("profile"), "variant": hw.get("active_variant"),
           "note": note}
    if rec["vram_free_pct"] is None:
        _log("WARN", "observation ignoree : statut VRAM indisponible (pile arretee ?)")
        return {"ok": False, "reason": "statut VRAM indisponible"}
    try:
        os.makedirs(LOGS, exist_ok=True)
        with open(HISTORY, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}
    _log("INFO", "observation enregistree : %s%% VRAM libre, ngl=%s"
         % (rec["vram_free_pct"], rec["ngl"]))
    return {"ok": True, "observation": rec}

def _vram_pct_from_log():
    pcts, crit = [], 0
    try:
        with open(VRAMLOG, encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                if "CRITICAL" in line:
                    crit += 1
                if "libre" in line and "%" in line:
                    try:
                        seg = line.split("libre")[1]
                        pcts.append(float(seg.split("(")[1].split("%")[0].strip()))
                    except Exception:
                        continue
    except Exception:
        pass
    return pcts, crit


def analyze(apply=True):
    # Croise l'historique consolide, le journal du watchdog et les bascules de failover.
    hw = _read_json(HWP, {}) or {}
    par = hw.get("params") or {}
    ngl_max = int(par.get("ngl") or 0)
    base = str(hw.get("profile") or "normal").lower()
    if base not in FACTORY:
        base = "normal"
    fac = FACTORY[base]
    pcts = [r.get("vram_free_pct") for r in _history()
            if isinstance(r.get("vram_free_pct"), (int, float))]
    log_pcts, crit = _vram_pct_from_log()
    pcts += log_pcts
    fo = _read_jsonl(FAILLOG)
    fo_sw = sum(1 for r in fo if isinstance(r.get("event"), dict) and r["event"].get("failover"))
    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source_profile": base,
           "samples": len(pcts), "watchdog_critical_events": crit, "failover_switches": fo_sw}
    if pcts:
        out["vram_free_pct"] = {"min": round(min(pcts), 2), "avg": round(sum(pcts) / len(pcts), 2),
                                "max": round(max(pcts), 2)}
    if len(pcts) < MIN_SAMPLES:
        learned = dict(fac)
        out["source"] = ("usine (donnees insuffisantes : %d observation(s) < %d)"
                         % (len(pcts), MIN_SAMPLES))
    else:
        # Seuil d'alerte ancre sur le MINIMUM reellement observe, avec marge bornee.
        alert = max(8.0, min(25.0, round(min(pcts) + 5.0, 1)))
        learned = {"vram_alert_pct": alert,
                   "vram_crit_pct": max(3.0, min(12.0, round(alert - 8.0, 1))),
                   "vram_recover_pct": max(alert + 5.0, min(40.0, round(alert + 10.0, 1))),
                   "ngl_factor": fac.get("ngl_factor", 1.0)}
        out["source"] = "appris (%d observations reelles)" % len(pcts)
    ngl = ngl_max
    if crit and ngl_max > 0:
        ngl = max(0, int(round(ngl_max * 0.8)))
        out["ngl_note"] = ("%d evenement(s) critique(s) VRAM -> offload reduit de %d a %d"
                           % (crit, ngl_max, ngl))
    learned["ngl"] = ngl
    learned["vram_total_mb"] = (hw.get("gpu") or {}).get("vram_total_mb")
    learned["learned_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out["learned"] = learned
    if apply:
        try:
            os.makedirs(CONFIG, exist_ok=True)
            with open(PROFILE, "w", encoding="utf-8") as fh:
                json.dump(learned, fh, indent=2, ensure_ascii=False)
            _log("INFO", "profil appris ecrit : alerte<%.1f%% critique<%.1f%% reprise>%.1f%% ngl=%s"
                 % (learned["vram_alert_pct"], learned["vram_crit_pct"],
                    learned["vram_recover_pct"], learned["ngl"]))
        except Exception as exc:
            _log("ERROR", "ecriture du profil impossible : %s" % exc)
    return out

def reset(factory="normal"):
    # Garde-fou QA : retour INSTANTANE aux profils d'usine. Le profil appris est efface, puis les
    # valeurs d'usine sont ECRITES dans config\profile.json afin que le watchdog les applique A
    # CHAUD sans redemarrage (et non pas seulement au prochain demarrage).
    if factory not in FACTORY:
        raise RuntimeError("profil d'usine inconnu : '%s' (soft|normal|hard)" % factory)
    fac = FACTORY[factory]
    hw = _read_json(HWP, {}) or {}
    learned_was = os.path.isfile(PROFILE)
    applied = {"vram_alert_pct": fac["vram_alert_pct"], "vram_crit_pct": fac["vram_crit_pct"],
               "vram_recover_pct": fac["vram_recover_pct"], "ngl_factor": fac["ngl_factor"],
               "ngl": (hw.get("params") or {}).get("ngl"),
               "vram_total_mb": (hw.get("gpu") or {}).get("vram_total_mb"),
               "factory": factory, "source": "usine",
               "reset_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        os.makedirs(CONFIG, exist_ok=True)
        with open(PROFILE, "w", encoding="utf-8") as fh:
            json.dump(applied, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        _log("ERROR", "reset-profile : ecriture impossible : %s" % exc)
        return {"ok": False, "reason": str(exc)}
    _log("INFO", "reset-profile : profil appris efface=%s ; usine '%s' applique A CHAUD "
                 "(alerte<%.0f%% critique<%.0f%% reprise>%.0f%%)."
         % (learned_was, factory, fac["vram_alert_pct"], fac["vram_crit_pct"],
            fac["vram_recover_pct"]))
    return {"ok": True, "learned_erased": learned_was, "factory": factory, "applied": applied}


def show_status():
    learned = _read_json(PROFILE)
    print("=== Profil apprenant continu (v2.0.0b) ===")
    if learned:
        is_fac = learned.get("source") == "usine"
        print("  Etat           : %s" % (
            "USINE (profil '%s' applique a chaud)" % learned.get("factory")
            if is_fac else "APPRIS (config\\profile.json)"))
        print("  Seuils VRAM    : alerte < %.1f %% | critique < %.1f %% | reprise > %.1f %%"
              % (learned.get("vram_alert_pct", 0), learned.get("vram_crit_pct", 0),
                 learned.get("vram_recover_pct", 0)))
        print("  Offload -ngl   : %s" % learned.get("ngl"))
        print("  %s : %s" % ("Reinitialise le" if is_fac else "Appris le      ",
                              learned.get("reset_at") or learned.get("learned_at")))
    else:
        print("  Etat           : USINE (aucun profil applique)")
    print("  Profils d'usine :")
    for k in sorted(FACTORY):
        f = FACTORY[k]
        print("    %-7s alerte<%.0f%% critique<%.0f%% reprise>%.0f%% facteur-ngl=%.2f"
              % (k, f["vram_alert_pct"], f["vram_crit_pct"], f["vram_recover_pct"], f["ngl_factor"]))
    print("  Historique     : logs\\history.jsonl (%d observation(s))" % len(_history()))
    print("  Ajustement     : A CHAUD (le watchdog relit config\\profile.json a chaque cycle)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Profil apprenant continu (v2.0.0b)")
    ap.add_argument("mode", nargs="?", default="status",
                    choices=["status", "observe", "analyze", "reset"])
    ap.add_argument("factory_pos", nargs="?", default=None,
                    help="profil d'usine (soft|normal|hard) pour 'reset'")
    ap.add_argument("--note", default="")
    ap.add_argument("--factory", default="normal",
                    help="profil d'usine applique par 'reset' (soft|normal|hard)")
    ap.add_argument("--dry-run", action="store_true", help="analyse sans ecrire le profil")
    a = ap.parse_args()
    if a.mode == "status":
        return show_status()
    try:
        if a.mode == "observe":
            res = observe(a.note)
        elif a.mode == "analyze":
            res = analyze(apply=not a.dry_run)
        else:
            res = reset(a.factory_pos or a.factory)
    except Exception as exc:
        print("[profile] ERREUR : %s" % exc)
        return 1
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

I18N_HELP = {
    "fr": [
        "=== AiTron -- aide du CLI (@VER@) ===",
        "  start              Demarre la pile complete (coeur, moteurs, gateway, watchdog)",
        "  stop               Arrete tous les services",
        "  restart            Redemarre la pile",
        "  status             Etat des services (PID, ports, URL)",
        "  profile            Affiche le profil materiel detecte",
        "  set-profile <p>    Change le profil : soft|normal|hard|auto|custom",
        "  benchmark [cpu]    Mesure les tokens/s (GPU par defaut)",
        "  vram-status        VRAM totale/utilisee/libre, seuils et watchdog",
        "  index <dossier>    Indexe un dossier (RAG multi-format)",
        "  rag-query <texte>  Recherche cosinus dans l'index RAG",
        "  graph-index <d>    Indexe un graphe GraphRAG (extraction par le LLM local)",
        "  graph-show         Statistiques du graphe GraphRAG local",
        "  mcp-list           Serveurs et outils MCP actifs",
        "  mcp-call <s> <o>   Invoque un outil MCP",
        "  quantize <m> <t>   Quantization locale (llama-quantize)",
        "  privacy-test       Autotest du filtre PII (masquage/demasquage)",
        "  hardware-status    Repartition des charges (GPU principal vs taches semantiques)",
        "  vault-status       Espace hermetique AES-256 : fichiers scelles/en clair",
        "  vault-seal         Chiffre la zone semantique (mot de passe jamais stocke)",
        "  vault-unseal       Ouvre la zone semantique pour la session",
        "  vault-test         Autotest du coffre (scellement, ouverture, integrite)",
        "  learn-profile      Profil apprenant : recalcule les seuils VRAM et le -ngl",
        "  profile-status     Etat du profil (appris vs usine SOFT/NORMAL/HARD)",
        "  reset-profile      GARDE-FOU : restaure les profils d'usine",
        "  peer-status        Noeuds RPC federes disponibles (IP, port, latence)",
        "  peer-scan          Scan reseau (broadcast UDP non invasif)",
        "  peer-test          Autotest de la decouverte RPC (boucle locale)",
        "  lang [fr|en|list]  Affiche ou change la langue de l'interface (FR/EN)",
        "  help               Affiche cette aide",
        "",
        "  URL par defaut : http://127.0.0.1:4000  (gateway LiteLLM)",
        "                  http://127.0.0.1:8080/v1 (API AiTron directe)",
    ],
    "en": [
        "=== AiTron -- CLI help (@VER@) ===",
        "  start              Starts the full stack (core, engines, gateway, watchdog)",
        "  stop               Stops every service",
        "  restart            Restarts the stack",
        "  status             Services status (PID, ports, URLs)",
        "  profile            Shows the detected hardware profile",
        "  set-profile <p>    Changes the profile: soft|normal|hard|auto|custom",
        "  benchmark [cpu]    Measures tokens/s (GPU by default)",
        "  vram-status        Total/used/free VRAM, thresholds and watchdog",
        "  index <folder>     Indexes a folder (multi-format RAG)",
        "  rag-query <text>   Cosine search inside the RAG index",
        "  graph-index <d>    Indexes a GraphRAG graph (extraction by the local LLM)",
        "  graph-show         Local GraphRAG graph statistics",
        "  mcp-list           Active MCP servers and tools",
        "  mcp-call <s> <o>   Calls an MCP tool",
        "  quantize <m> <t>   Local quantization (llama-quantize)",
        "  privacy-test       Self-test of the PII filter (mask/unmask)",
        "  hardware-status    Workload split (main GPU vs semantic tasks)",
        "  vault-status       AES-256 vault: sealed / plaintext files state",
        "  vault-seal         Encrypts the semantic zone (password never stored)",
        "  vault-unseal       Opens the semantic zone for the session",
        "  vault-test         Vault self-test (seal, open, integrity)",
        "  learn-profile      Learning profile: recomputes VRAM thresholds and -ngl",
        "  profile-status     Profile state (learned vs factory SOFT/NORMAL/HARD)",
        "  reset-profile      SAFETY: restores the factory profiles",
        "  peer-status        Available federated RPC nodes (IP, port, latency)",
        "  peer-scan          Network scan (non-invasive UDP broadcast)",
        "  peer-test          RPC discovery self-test (loopback)",
        "  lang [fr|en|list]  Shows or changes the interface language (FR/EN)",
        "  help               Shows this help",
        "",
        "  Default URLs: http://127.0.0.1:4000  (LiteLLM gateway)",
        "                http://127.0.0.1:8080/v1 (direct AiTron API)",
    ],
}

I18N_LABELS = {
    "fr": {
        "banner_title": "=== AiTron -- portage Windows natif demarre ===",
        "lbl_api": "API AiTron", "lbl_gateway": "Gateway LiteLLM", "lbl_vision": "Vision (VLM)",
        "lbl_stop": "Arret", "lbl_whisper": "Whisper (STT)", "lbl_images": "Images", "lbl_tts": "TTS",
        "msg_unknown": "[Run-LocalAI] Commande inconnue :",
        "msg_backends_hdr": "Backends installes dans",
        "msg_backends_n1": "(Moteur texte : backends\\llama-cpp ; Audio : backends\\whisper-cpp ;",
        "msg_backends_n2": " Image : backends\\stable-diffusion ; TTS : backends\\tts)",
        "msg_help_tip": "Astuce : 'lang en' bascule l'interface en anglais immediatement.",
        "msg_lang_now": "[Run-LocalAI] Langue active :",
        "msg_lang_set": "[Run-LocalAI] Langue basculee :",
        "msg_lang_bad": "[Run-LocalAI] Langue inconnue (utilisez : fr, en ou list)",
        "msg_help_header": "Run-LocalAI.bat - AiTron V3 (interface francaise) - sans Docker, sans WSL",
        "msg_help_usage": "Usage : Run-LocalAI.bat <commande> [arguments]",
    },
    "en": {
        "banner_title": "=== AiTron -- native Windows port started ===",
        "lbl_api": "AiTron API", "lbl_gateway": "LiteLLM gateway", "lbl_vision": "Vision (VLM)",
        "lbl_stop": "Stop", "lbl_whisper": "Whisper (STT)", "lbl_images": "Images", "lbl_tts": "TTS",
        "msg_unknown": "[Run-LocalAI] Unknown command:",
        "msg_backends_hdr": "Backends installed in",
        "msg_backends_n1": "(Text engine: backends\\llama-cpp ; Audio: backends\\whisper-cpp ;",
        "msg_backends_n2": " Image: backends\\stable-diffusion ; TTS: backends\\tts)",
        "msg_help_tip": "Tip: 'lang fr' switches the interface back to French at once.",
        "msg_lang_now": "[Run-LocalAI] Active language:",
        "msg_lang_set": "[Run-LocalAI] Language switched:",
        "msg_lang_bad": "[Run-LocalAI] Unknown language (use: fr, en or list)",
        "msg_help_header": "Run-LocalAI.bat - AiTron V3 (English interface) - no Docker, no WSL",
        "msg_help_usage": "Usage: Run-LocalAI.bat <command> [arguments]",
    },
}

I18N_PY = r"""# i18n.py - internationalisation FR/EN a TROIS COUCHES (v2.1.1)
# Couche 1 : dictionnaire TRANSLATIONS embarque ici = SOURCE DE VERITE ULTIME.
# Couche 2 : fichiers i18n\fr.json et i18n\en.json (generes a l'installation) :
#            ils SURCHARGENT l'embarque et restent personnalisables par l'utilisateur.
# Couche 3 : constante I18N_REV. Si la revision du script differe de celle lue sur le disque,
#            les cles d'aide et de documentation (tip_* / help_*) sont RAFRAICHIES depuis
#            l'embarque pour propager les mises a jour textuelles ; les autres cles restent
#            intactes, sous le controle de l'utilisateur.
# Langue active (CURRENT_LANG) par priorite : AITRON_LANG -> config\lang.json "lang" -> "fr".
import argparse
import json
import os
import sys
import time

I18N_REV = "2"
DEFAULT_LANG = "fr"
LANGS = ("fr", "en")

TRANSLATIONS = {
    "fr": {
        "banner_title": "AiTron - portage Windows natif (sans Docker ni WSL)",
        "banner_api": "API AiTron",
        "banner_gateway": "Gateway LiteLLM",
        "banner_vision": "Vision (VLM)",
        "banner_stop": "Arret",
        "lang_current": "Langue active",
        "lang_available": "Langues disponibles",
        "lang_switched": "Langue basculee vers",
        "lang_unknown": "Langue inconnue",
        "lang_hint": "Usage : lang [fr|en|list]",
        "msg_ok": "OK",
        "msg_error": "ERREUR",
        "tip_lang": "Astuce : 'lang en' bascule l'interface en anglais immediatement.",
        "tip_models": "Astuce : le modele 1B repond vite ; le modele 7B repond mieux.",
        "help_start": "Demarre la pile complete (coeur, moteurs, gateway, watchdog)",
        "help_stop": "Arrete tous les services",
        "help_restart": "Redemarre la pile",
        "help_status": "Etat des services (PID, ports, URL)",
        "help_index": "Indexe un dossier (RAG multi-format : txt/py/pdf/docx/xlsx)",
        "help_ragquery": "Recherche cosinus dans l'index RAG",
        "help_graphindex": "Indexe un graphe GraphRAG (extraction par le LLM local)",
        "help_graphshow": "Statistiques du graphe GraphRAG local",
        "help_quantize": "Quantization locale (llama-quantize) : F16 -> Q4_K_M/Q8_0/...",
        "help_privacy": "Autotest du filtre PII (masquage/demasquage)",
        "help_hwstatus": "Repartition des charges (GPU principal vs taches semantiques)",
        "help_specstatus": "Etat du Speculative Decoding (TEXT-ONLY) + budget VRAM",
        "help_vaultstatus": "Espace hermetique AES-256 : fichiers scelles/en clair",
        "help_vaultseal": "Chiffre la zone semantique (mot de passe jamais stocke)",
        "help_vaultunseal": "Ouvre la zone semantique pour la session",
        "help_vaulttest": "Autotest du coffre (scellement, ouverture, integrite)",
        "help_learnprofile": "Profil apprenant : recalcule les seuils VRAM et le -ngl",
        "help_profilestatus": "Etat du profil (appris vs usine SOFT/NORMAL/HARD)",
        "help_resetprofile": "GARDE-FOU : restaure les profils d'usine",
        "help_peerstatus": "Noeuds RPC federes disponibles (IP, port, latence)",
        "help_peerscan": "Scan reseau (broadcast UDP non invasif)",
        "help_peertest": "Autotest de la decouverte RPC (boucle locale)",
        "help_benchmark": "Mesure les tokens/s (GPU par defaut, ou CPU)",
        "help_profile": "Affiche le profil materiel detecte (GPU/CPU, params)",
        "help_setprofile": "Change le profil : soft|normal|hard|auto|custom",
        "help_vramstatus": "VRAM totale/utilisee/libre, seuils et watchdog",
        "help_mcp": "Serveurs et outils MCP actifs",
        "help_lang": "Affiche ou change la langue de l'interface (fr|en|list)",
        "help_help": "Affiche cette aide",
    },
    "en": {
        "banner_title": "AiTron - native Windows port (no Docker, no WSL)",
        "banner_api": "LocalAI API",
        "banner_gateway": "LiteLLM gateway",
        "banner_vision": "Vision (VLM)",
        "banner_stop": "Stop",
        "lang_current": "Active language",
        "lang_available": "Available languages",
        "lang_switched": "Language switched to",
        "lang_unknown": "Unknown language",
        "lang_hint": "Usage: lang [fr|en|list]",
        "msg_ok": "OK",
        "msg_error": "ERROR",
        "tip_lang": "Tip: 'lang fr' switches the interface back to French at once.",
        "tip_models": "Tip: the 1B model answers fast; the 7B model answers better.",
        "help_start": "Starts the full stack (core, engines, gateway, watchdog)",
        "help_stop": "Stops every service",
        "help_restart": "Restarts the stack",
        "help_status": "Services status (PID, ports, URLs)",
        "help_index": "Indexes a folder (multi-format RAG: txt/py/pdf/docx/xlsx)",
        "help_ragquery": "Cosine search inside the RAG index",
        "help_graphindex": "Indexes a GraphRAG graph (extraction by the local LLM)",
        "help_graphshow": "Local GraphRAG graph statistics",
        "help_quantize": "Local quantization (llama-quantize): F16 -> Q4_K_M/Q8_0/...",
        "help_privacy": "Self-test of the PII filter (mask/unmask)",
        "help_hwstatus": "Workload split (main GPU vs semantic tasks)",
        "help_specstatus": "Speculative Decoding status (TEXT-ONLY) + VRAM budget",
        "help_vaultstatus": "AES-256 vault: sealed / plaintext files state",
        "help_vaultseal": "Encrypts the semantic zone (password never stored)",
        "help_vaultunseal": "Opens the semantic zone for the session",
        "help_vaulttest": "Vault self-test (seal, open, integrity)",
        "help_learnprofile": "Learning profile: recomputes VRAM thresholds and -ngl",
        "help_profilestatus": "Profile state (learned vs factory SOFT/NORMAL/HARD)",
        "help_resetprofile": "SAFETY: restores the factory profiles",
        "help_peerstatus": "Available federated RPC nodes (IP, port, latency)",
        "help_peerscan": "Network scan (non-invasive UDP broadcast)",
        "help_peertest": "RPC discovery self-test (loopback)",
        "help_benchmark": "Measures tokens/s (GPU by default, or CPU)",
        "help_profile": "Shows the detected hardware profile (GPU/CPU, params)",
        "help_setprofile": "Changes the profile: soft|normal|hard|auto|custom",
        "help_vramstatus": "Total/used/free VRAM, thresholds and watchdog",
        "help_mcp": "Active MCP servers and tools",
        "help_lang": "Shows or changes the interface language (fr|en|list)",
        "help_help": "Shows this help",
    },
}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
I18N_DIR = os.path.join(ROOT, "i18n")
CONFIG = os.path.join(ROOT, "config")
LANG_JSON = os.path.join(CONFIG, "lang.json")
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")

_cache = {"lang": None, "data": None}


def _log(level, msg, crash=False):
    line = "[%s] [I18N] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    if crash:
        try:
            with open(CRASHLOG, "a", encoding="utf-8") as fh:
                fh.write(line + "\n---\n")
        except Exception:
            pass
    return line


def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return default


def available_langs():
    return list(LANGS)


def current_lang():
    # Priorite : variable d'environnement -> config\lang.json -> defaut.
    env = (os.environ.get("AITRON_LANG") or "").strip().lower()
    if env in LANGS:
        return env
    cfg = _read_json(LANG_JSON, {}) or {}
    lg = str(cfg.get("lang") or "").strip().lower()
    if lg in LANGS:
        return lg
    return DEFAULT_LANG


def _load(lang):
    # Couche 1 : embarque (toujours disponible).
    base = dict(TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANG])
    # Couche 2 : surcharge par fichier externe ; JSON invalide -> repli couche 1.
    path = os.path.join(I18N_DIR, "%s.json" % lang)
    if not os.path.isfile(path):
        return base
    ext = _read_json(path)
    if not isinstance(ext, dict):
        _log("WARN", "i18n '%s' illisible ou JSON invalide -> repli sur l'embarque (couche 1)"
             % path, crash=True)
        return base
    rev_disk = str(ext.get("_i18n_rev") or "0")
    refreshed = 0
    for k, v in ext.items():
        if k.startswith("_") or not isinstance(v, str):
            continue
        if k.startswith(("help_", "tip_")) and rev_disk != I18N_REV:
            # Couche 3 : cle d'aide/documentation -> rafraichie depuis l'embarque.
            refreshed += 1
            continue
        base[k] = v
    if refreshed:
        _log("INFO", "I18N_REV disque=%s / script=%s -> %d cle(s) help_/tip_ rafraichies"
             % (rev_disk, I18N_REV, refreshed))
    return base


def tr(key, **kwargs):
    lang = current_lang()
    if _cache["lang"] != lang or _cache["data"] is None:
        _cache["lang"] = lang
        _cache["data"] = _load(lang)
    val = _cache["data"].get(key)
    if val is None:
        val = (TRANSLATIONS.get(DEFAULT_LANG) or {}).get(key, key)
    try:
        return val.format(**kwargs) if kwargs else val
    except Exception:
        return val


def set_lang(lang):
    lang = str(lang or "").strip().lower()
    if lang not in LANGS:
        return False, "inconnue"
    try:
        os.makedirs(CONFIG, exist_ok=True)
        cur = _read_json(LANG_JSON, {}) or {}
        cur["lang"] = lang
        cur["i18n_rev"] = I18N_REV
        with open(LANG_JSON, "w", encoding="utf-8") as fh:
            json.dump(cur, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        _log("ERROR", "ecriture de config\\lang.json impossible : %s" % exc, crash=True)
        return False, str(exc)
    _cache["lang"] = None
    _cache["data"] = None
    _log("INFO", "langue basculee vers '%s' (config\\lang.json ecrit)" % lang, crash=True)
    return True, lang


def write_defaults(force=False):
    # Genere i18n\fr.json et i18n\en.json depuis l'embarque (couche 2).
    written = []
    try:
        os.makedirs(I18N_DIR, exist_ok=True)
    except Exception as exc:
        return written, str(exc)
    for lg in LANGS:
        path = os.path.join(I18N_DIR, "%s.json" % lg)
        keep = False
        if os.path.isfile(path) and not force and os.path.getsize(path) > 0:
            try:
                with open(path, encoding="utf-8-sig") as fh:
                    keep = isinstance(json.load(fh), dict)
            except Exception:
                keep = False
        if keep:
            continue
        data = {"_i18n_rev": I18N_REV, "_comment": "Surcharge utilisateur (couche 2) ; les cles "
                "help_*/tip_* sont rafraichies automatiquement si _i18n_rev change."}
        data.update(TRANSLATIONS.get(lg) or {})
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            written.append(path)
        except Exception as exc:
            return written, str(exc)
    return written, None


# v3.1.0 (D6) : COUCHE DE LOCALISATION DE SORTIE. Les scripts d'etat (PowerShell/Python) ont
# leurs libelles ecrits en francais ; en mode EN, 'i18n.py run <commande>' execute la commande et
# traduit sa sortie ligne a ligne (phrases les plus longues d'abord). En FR : passe-plat exact.
OUT_EN = []
OUT_EN += [
    ("=== Etat des services LocalAI", "=== AiTron services status"),
    ("Disponibilite des endpoints :", "Endpoint availability:"),
    ("Ports resolus :", "Resolved ports:"),
    ("Profil materiel :", "Hardware profile:"),
    ("(recommande ", "(recommended "),
    ("- variante ", "- variant "),
    ("Fichier runtime :", "Runtime file:"),
    ("=== Profil materiel LocalAI", "=== AiTron hardware profile"),
    ("Mo libres", "MB free"),
    ("recommande:", "recommended:"),
    ("Profil :", "Profile:"),
    ("marge=", "margin="),
    ("Variante active :", "Active variant:"),
    ("Variantes dispo :", "Available variants:"),
    ("besoin ~", "needed ~"),
    (" Mo / libre ", " MB / free "),
    ("=== Etat VRAM LocalAI", "=== AiTron VRAM status"),
    ("Utilisee :", "Used     :"),
    ("Libre    :", "Free     :"),
    ("Etat     :", "State    :"),
    ("Seuils   :", "Thresholds:"),
    ("alerte <", "alert <"),
    ("alerte<", "alert<"),
    ("critique <", "critical <"),
    ("critique<", "critical<"),
    ("reprise >", "recovery >"),
    ("reprise>", "recovery>"),
    ("Watchdog : inactif (aucun statut : demarrez avec", "Watchdog : inactive (no status: start with"),
    ("Derniere action :", "Last action:"),
    ("VRAM non detectee (GPU absent ou pilote manquant)", "VRAM not detected (GPU missing or driver absent)"),
]
OUT_EN += [
    ("=== Repartition des charges d'inference", "=== Inference workload split"),
    ("[MOTEUR PRINCIPAL] llama.cpp - inference de texte", "[MAIN ENGINE] llama.cpp - text inference"),
    ("backend GPU :", "GPU backend :"),
    ("couches     :", "layers      :"),
    ("[TACHES SEMANTIQUES DEPORTEES] extraction legere", "[OFFLOADED SEMANTIC TASKS] light extraction"),
    ("motif       : DirectML absent (pilote ou materiel incompatible) -> repli CPU",
     "reason      : DirectML absent (driver or hardware incompatible) -> CPU fallback"),
    ("motif       :", "reason      :"),
    ("modele sonde:", "probe model :"),
    ("non mesure", "not measured"),
    ("taches      : NER du filtre PII (niveau 3), outils MCP legers",
     "tasks       : PII filter NER (level 3), light MCP tools"),
    ("[AUTRES SERVICES]", "[OTHER SERVICES]"),
    ("[REPLI QA] Si DirectML est indisponible, les taches semantiques basculent",
     "[QA FALLBACK] If DirectML is unavailable, semantic tasks switch"),
    ("AUTOMATIQUEMENT sur le CPU (transparent, session preservee) et",
     "AUTOMATICALLY to the CPU (transparent, session preserved) and"),
    ("l'avertissement est consigne dans dev\\crash.log (categorie GPU_DETECT).",
     "the warning is logged in dev\\crash.log (category GPU_DETECT)."),
    ("VERDICT : provider", "VERDICT: provider"),
    ("operationnel", "operational"),
    ("sur le modele sonde", "on the probe model"),
]
OUT_EN += [
    ("=== autotest du filtre PII (BEST-EFFORT) ===", "=== PII filter self-test (BEST-EFFORT) ==="),
    ("--- avant ---", "--- before ---"),
    ("--- masque ---", "--- masked ---"),
    ("--- jetons ---", "--- tokens ---"),
    ("--- restaure ---", "--- restored ---"),
    ("reversibilite : IDENTIQUE", "reversibility: IDENTICAL"),
    ("types masques :", "masked types:"),
    ("Cle OpenAI :", "OpenAI key:"),
    ("Jeton GitHub :", "GitHub token:"),
    ("Mot de passe technique :", "Technical password:"),
    ("Contact :", "Contact:"),
    ("Niveau 1 (regex deterministes)", "Level 1 (deterministic regex)"),
    ("Niveau 2 (entropie) : seuil", "Level 2 (entropy): threshold"),
    ("longueur min", "min length"),
    ("jeu de caracteres mixte exige", "mixed character set required"),
    ("Niveau 3 (NER local) : moteur llama-server sur le port", "Level 3 (local NER): llama-server engine on port"),
    ("Statut : actif", "Status: active"),
    ("DESACTIVE", "DISABLED"),
    ("=== Espace hermetique souverain", "=== Sovereign sealed space"),
    ("sel aleatoire", "random salt"),
    ("Scelles    :", "Sealed     :"),
    ("En clair   :", "Plaintext  :"),
    ("Etat       :", "State      :"),
    ("fichier(s)", "file(s)"),
    ("Portee     : AU REPOS uniquement (chiffre apres 'stop', ouvert pour la session)",
     "Scope      : AT REST only (encrypted after 'stop', open for the session)"),
    ("ouvert pour la session", "open for the session"),
    ("scelle (au repos)", "sealed (at rest)"),
    ("Cle        : jamais stockee (PBKDF2 a la volee) ; RAM = meilleur effort (GC)",
     "Key        : never stored (PBKDF2 on the fly); RAM = best effort (GC)"),
    ("=== autotest du coffre souverain", "=== sovereign vault self-test"),
    ("scellement     :", "sealing        :"),
    ("ouverture      :", "opening        :"),
    ("integrite      :", "integrity      :"),
    ("IDENTIQUE", "IDENTICAL"),
    ("octets", "bytes"),
    ("mauvais mot de passe refuse :", "wrong password refused:"),
    ("cle sur disque : JAMAIS (derivee a la volee)", "key on disk    : NEVER (derived on the fly)"),
    ("VERDICT         : VERT", "VERDICT         : GREEN"),
    ("VERDICT : VERT", "VERDICT: GREEN"),
    ("A REVOIR", "TO REVIEW"),
    ("ECHEC", "FAILED"),
    ("CORROMPU", "CORRUPTED"),
]
OUT_EN += [
    ("=== Profil apprenant continu", "=== Continuous learning profile"),
    ("Etat           :", "State          :"),
    ("USINE", "FACTORY"),
    ("applique a chaud", "applied live"),
    ("(aucun profil applique)", "(no profile applied)"),
    ("Seuils VRAM    :", "VRAM thresholds:"),
    ("Reinitialise le :", "Reset on       :"),
    ("Appris le      :", "Learned on     :"),
    ("Profils d'usine :", "Factory profiles:"),
    ("facteur-ngl=", "ngl-factor="),
    ("Historique     :", "History        :"),
    ("observation(s)", "observation(s)"),
    ("Ajustement     : A CHAUD (le watchdog relit config\\profile.json a chaque cycle)",
     "Adjustment     : LIVE (the watchdog re-reads config\\profile.json each cycle)"),
    ("=== AiTron - noeuds RPC federes", "=== AiTron - federated RPC nodes"),
    ("Noeud local     :", "Local node      :"),
    ("Binaire RPC     :", "RPC binary      :"),
    ("(moteur natif llama.cpp)", "(native llama.cpp engine)"),
    ("Dernier scan    :", "Last scan       :"),
    ("(attente", "(wait"),
    ("Noeuds distants : AUCUN (etat normal sur un poste isole)",
     "Remote nodes    : NONE (normal state on an isolated machine)"),
    ("Noeuds distants :", "Remote nodes    :"),
    ("latence=", "latency="),
    ("Argument moteur : (aucun : calcul 100% local)", "Engine argument : (none: 100% local compute)"),
    ("Argument moteur :", "Engine argument :"),
    ("Transport       : delegue a 100% au coeur RPC natif de llama.cpp (ggml-rpc-server)",
     "Transport       : 100% delegated to the native llama.cpp RPC core (ggml-rpc-server)"),
    ("=== Autotest decouverte RPC", "=== RPC discovery self-test"),
    ("Protocole       : AITRON-PEER/1 (UDP unicast sur boucle locale, aucun envoi reseau)",
     "Protocol        : AITRON-PEER/1 (UDP unicast on loopback, no network send)"),
    ("Requete recue   :", "Request received:"),
    ("Reponse         :", "Response        :"),
    ("Champs utiles   :", "Useful fields   :"),
    ("binaire=", "binary="),
    ("Transport       : AUCUNE donnee d'inference transmise (decouverte seule)",
     "Transport       : NO inference data sent (discovery only)"),
    ("Argument genere :", "Generated arg   :"),
]
OUT_EN += [
    ("=== Decoding speculatif", "=== Speculative decoding"),
    ("Etat        :", "State       :"),
    ("inactif", "inactive"),
    ("Modele      :", "Model       :"),
    ("Raison      :", "Reason      :"),
    ("aucun etat enregistre (pile non demarree)", "no state recorded (stack not started)"),
    ("Regle       : TEXT-ONLY uniquement (jamais avec --mmproj : limitation llama.cpp)",
     "Rule        : TEXT-ONLY only (never with --mmproj: llama.cpp limitation)"),
    ("Mesure      : Run-LocalAI.bat benchmark  (comparer avec AITRON_SPEC=0)",
     "Measure     : Run-LocalAI.bat benchmark  (compare with AITRON_SPEC=0)"),
    ("VRAM libre  :", "Free VRAM   :"),
    ("=== Graphe GraphRAG local", "=== Local GraphRAG graph"),
    ("Construit le :", "Built on     :"),
    ("Moteur       : llama-server /v1/chat/completions (extraction NER/RE par LLM local)",
     "Engine       : llama-server /v1/chat/completions (NER/RE extraction by local LLM)"),
    ("Fichiers     :", "Files        :"),
    ("echecs :", "failures :"),
    ("Noeuds       :", "Nodes        :"),
    ("Aretes LLM   :", "LLM edges    :"),
    ("| Aretes :", "| Edges :"),
    ("structurelles (imports)", "structural (imports)"),
    ("Noeuds les plus connectes :", "Most connected nodes:"),
    ("degre=", "degree="),
    ("Langue active    :", "Active language  :"),
    ("Codes disponibles:", "Available codes  :"),
    ("Priorite         :", "Priority         :"),
    ("defaut", "default"),
    ("Backends installes dans", "Backends installed in"),
    ("(Moteur texte :", "(Text engine :"),
    ("Audio :", "Audio :"),
    ("Image :", "Image :"),
    ("Langue basculee vers", "Language switched to"),
    ("(etat=", "(state="),
    (", maj=", ", upd="),
    ("graphe absent : lancer", "graph missing: run"),
    ("<dossier>", "<folder>"),
    ("Langues         :", "Languages       :"),
    ("Repli embarque  :", "Embedded fallback:"),
    ("VERDICT         : VERT", "VERDICT         : GREEN"),
    ("=== Autotest i18n", "=== i18n self-test"),
    ("desactive par defaut : aucun gain mesure sur profil GPU-bound",
     "disabled by default: no measured gain on a GPU-bound profile"),
    ("(voir dev\\DECISIONS.md D-039) ; activer avec AITRON_SPEC=1",
     "(see dev\\DECISIONS.md D-039); enable with AITRON_SPEC=1"),
    ("desactive explicitement (config\\spec-decoding.json / AITRON_SPEC=0)",
     "explicitly disabled (config\\spec-decoding.json / AITRON_SPEC=0)"),
    ("modele principal introuvable", "main model not found"),
    ("modele draft introuvable -> decoding standard", "draft model not found -> standard decoding"),
    ("modele multimodal : le decoding speculatif est desactive par llama.cpp",
     "multimodal model: speculative decoding is disabled by llama.cpp"),
    ("VRAM libre insuffisante", "insufficient free VRAM"),
    ("requis) -> repli SANS draft", "required) -> fallback WITHOUT draft"),
    ("texte pur, tokenizer partage, VRAM suffisante", "text-only, shared tokenizer, enough VRAM"),
    ("Mo libres >=", "MB free >="),
    ("aucune paire principal/draft declaree dans le catalogue", "no main/draft pair declared in the catalogue"),
    ("Relations    : est (", "Relations    : is ("),
    (", fait (", ", does ("),
    ("Retourne l'etat VRAM selon le seuil d'alerte.", "Returns the VRAM state according to the alert threshold."),
    ("seuil d'alerte", "alert threshold"),
    ("l'etat VRAM", "the VRAM state"),
]
OUT_EN += [
    ("Arret d'une instance eventuelle avant demarrage ...", "Stopping any running instance before start ..."),
    ("ports ->", "ports ->"),
    ("profil=", "profile="),
    ("variante=", "variant="),
    ("Profil materiel absent : detection initiale ...", "Hardware profile missing: initial detection ..."),
    ("profil materiel illisible -> valeurs par defaut", "hardware profile unreadable -> default values"),
    ("cle(s) cloud chargee(s) (cloud-keys.env / keys.env)", "cloud key(s) loaded (cloud-keys.env / keys.env)"),
    ("decoding speculatif ACTIF", "speculative decoding ACTIVE"),
    ("decoding speculatif inactif :", "speculative decoding inactive:"),
    ("decoding speculatif : decision indisponible -> decoding standard",
     "speculative decoding: decision unavailable -> standard decoding"),
    ("llama-server indisponible (binaire/modele absent) -> texte local indisponible",
     "llama-server unavailable (binary/model missing) -> local text unavailable"),
    ("whisper indisponible (binaire/modele absent)", "whisper unavailable (binary/model missing)"),
    ("sd-server present, modele SD absent -> Run-LocalAI.bat pull sd-turbo-light",
     "sd-server present, SD model missing -> Run-LocalAI.bat pull sd-turbo-light"),
    ("modele=", "model="),
    ("moteur VISION", "VISION engine"),
    ("moteur vision inactif (Run-LocalAI.bat pull qwen2-vl-2b pour l'activer)",
     "vision engine inactive (Run-LocalAI.bat pull qwen2-vl-2b to enable it)"),
    ("proxy FAILOVER SSE", "SSE FAILOVER proxy"),
    ("bufferisation + bascule locale/cloud", "buffering + local/cloud switch"),
    ("coeur LocalAI pret :", "LocalAI core ready:"),
    ("gateway LiteLLM pret :", "LiteLLM gateway ready:"),
    ("config LiteLLM absente -> gateway non demarree", "LiteLLM config missing -> gateway not started"),
    ("watchdog VRAM desactive (--no-watchdog)", "VRAM watchdog disabled (--no-watchdog)"),
    ("watchdog VRAM PID=", "VRAM watchdog PID="),
    ("decouverte RPC desactivee (--no-peers)", "RPC discovery disabled (--no-peers)"),
    ("decouverte RPC PID=", "RPC discovery PID="),
    ("annonce UDP non invasive, port", "non-invasive UDP announce, port"),
    ("filtre de confidentialite PII desactive pour cette session.", "PII privacy filter disabled for this session."),
    ("[LocalAI] Arret de tous les services (coeur, moteurs, LiteLLM, TTS) ...",
     "[AiTron] Stopping all services (core, engines, LiteLLM, TTS) ..."),
    ("[LocalAI] Tous les processus sont arretes. Zero zombie.", "[AiTron] All processes stopped. Zero zombie."),
    ("[AVERTISSEMENT] Des processus sont encore presents.", "[WARNING] Some processes are still present."),
    ("=== AiTron - portage Windows natif (sans Docker ni WSL)", "=== AiTron - native Windows port (no Docker, no WSL)"),
    ("API AiTron    :", "AiTron API    :"),
    ("Arret          :", "Stop           :"),
]
_OUT_SORTED = []
_YESNO = None


def localize_line(text):
    # Identite hors EN ; en EN, traduction par table (motifs les plus longs d'abord).
    global _OUT_SORTED
    if current_lang() != "en":
        return text
    if not _OUT_SORTED:
        _OUT_SORTED = sorted(OUT_EN, key=lambda p: -len(p[0]))
    for fr, en in _OUT_SORTED:
        if fr in text:
            text = text.replace(fr, en)
    # OUI/NON : mots entiers seulement (NONE, NONFUNCTIONAL... restent intacts).
    global _YESNO
    if _YESNO is None:
        import re as _re
        _YESNO = (_re.compile(r"\bOUI\b"), _re.compile(r"\bNON\b"))
    text = _YESNO[0].sub("YES", text)
    text = _YESNO[1].sub("NO", text)
    return text


def _emit(s):
    try:
        sys.stdout.buffer.write(s.encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        sys.stdout.write(s)


def _cli_localize(mode, rest):
    # 'run <cmd...>' : execute et traduit la sortie (code retour conserve) ; 'filter' : stdin.
    if mode == "filter":
        for raw in iter(sys.stdin.buffer.readline, b""):
            _emit(localize_line(raw.decode("utf-8", "replace")))
        return 0
    if not rest:
        return 2
    import subprocess
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if current_lang() != "en":
        return subprocess.call(rest, env=env)
    try:
        proc = subprocess.Popen(rest, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    except OSError as exc:
        print("[i18n] commande introuvable : %s" % exc)
        return 127
    for raw in iter(proc.stdout.readline, b""):
        _emit(localize_line(raw.decode("utf-8", "replace")))
    return proc.wait()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("run", "filter"):
        return _cli_localize(sys.argv[1], sys.argv[2:])
    ap = argparse.ArgumentParser(description="i18n FR/EN (v2.1.1)")
    ap.add_argument("mode", nargs="?", default="status",
                    choices=["status", "list", "get", "set", "init", "selftest"])
    ap.add_argument("lang", nargs="?", default=None)
    ap.add_argument("--force", action="store_true", help="regenerer les fichiers i18n")
    a = ap.parse_args()
    if a.mode == "list":
        print("\n".join(available_langs()))
        return 0
    if a.mode == "get":
        print(current_lang())
        return 0
    if a.mode == "set":
        ok, info = set_lang(a.lang)
        if not ok:
            print("%s : %s" % (tr("lang_unknown"), info))
            print(tr("lang_hint"))
            return 2
        print("%s : %s" % (tr("lang_switched"), info))
        return 0
    if a.mode == "init":
        written, err = write_defaults(force=a.force)
        print("fichiers i18n ecrits : %s"
              % (", ".join(os.path.basename(w) for w in written) or "aucun"))
        if err:
            print("avertissement : %s" % err)
        return 0
    if a.mode == "selftest":
        ok = True
        print("=== Autotest i18n (v2.1.1) ===")
        print("  I18N_REV        : %s" % I18N_REV)
        print("  Langues         : %s" % ", ".join(available_langs()))
        for lg in LANGS:
            os.environ["AITRON_LANG"] = lg
            _cache["lang"] = None
            v = tr("help_start")
            good = bool(v) and v != "help_start"
            ok = ok and good
            print("  [%s] help_start : %s" % (lg, v[:66]))
        os.environ.pop("AITRON_LANG", None)
        _cache["lang"] = None
        print("  Repli embarque  : %s" % tr("help_start")[:66])
        print("  VERDICT         : %s" % ("VERT" if ok else "ROUGE"))
        return 0 if ok else 1
    cfg = _read_json(LANG_JSON, {}) or {}
    print("=== i18n (v2.1.1) ===")
    print("  Langue active    : %s" % current_lang())
    print("  Codes disponibles: %s" % ", ".join(available_langs()))
    print("  i18n\\fr.json     : %s"
          % ("present" if os.path.isfile(os.path.join(I18N_DIR, "fr.json")) else "absent"))
    print("  i18n\\en.json     : %s"
          % ("present" if os.path.isfile(os.path.join(I18N_DIR, "en.json")) else "absent"))
    print("  config\\lang.json : lang=%s rev=%s" % (cfg.get("lang") or "-", cfg.get("i18n_rev") or "-"))
    print("  Priorite         : AITRON_LANG -> config\\lang.json -> defaut '%s'" % DEFAULT_LANG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

PEER_DISCOVERY_PY = r"""# peer_discovery.py - decouverte reseau des noeuds RPC (v2.1.0a)
# Broadcast UDP NON INVASIF, en pur Python (aucune dependance externe) : identifie uniquement
# les adresses IP des noeuds distants capables d'heberger un serveur RPC ggml (moteur RPC natif
# de llama.cpp). Ce module ne transporte AUCUNE donnee d'inference : le transport et la
# parallelisation du calcul sont delegues a 100% au coeur RPC natif de llama.cpp.
import argparse
import json
import os
import socket
import sys
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SANDBOX = os.path.dirname(ROOT)
CONFIG = os.path.join(ROOT, "config")
DATA = os.path.join(ROOT, "data")
PEERS = os.path.join(CONFIG, "peers.json")
HWP = os.path.join(CONFIG, "hardware-profile.json")
CRASHLOG = os.path.join(SANDBOX, "dev", "crash.log")

MAGIC = "AITRON-PEER/1"
KIND_QUERY = "query"
KIND_REPLY = "reply"
PEER_PORT = int(os.environ.get("AITRON_PEER_PORT", "47653"))
RPC_PORT = int(os.environ.get("AITRON_RPC_PORT", "50052"))
SCAN_WAIT_S = float(os.environ.get("AITRON_PEER_WAIT", "3.0"))
STALE_S = 90.0
RPC_BIN = "ggml-rpc-server.exe"


def _log(level, msg, crash=False):
    line = "[%s] [PEER_DISCOVERY] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    if crash:
        try:
            with open(CRASHLOG, "a", encoding="utf-8") as fh:
                fh.write(line + "\n---\n")
        except Exception:
            pass
    return line


def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return default


def node_id():
    # Identite stable du noeud : nom d'hote + empreinte materielle courte (aucune donnee perso).
    try:
        mac = uuid.getnode()
    except Exception:
        mac = 0
    return "%s-%06x" % (socket.gethostname().lower(), mac & 0xFFFFFF)


def _models():
    try:
        cat = _read_json(os.path.join(ROOT, "models", "models-catalog.json"), {}) or {}
        out = []
        for m in (cat.get("models") or []):
            if isinstance(m, dict) and m.get("name"):
                out.append(m["name"])
            elif isinstance(m, str):
                out.append(m)
        return out[:24]
    except Exception:
        return []


def _version():
    try:
        with open(os.path.join(ROOT, "manifest.json"), encoding="utf-8-sig") as fh:
            return (json.load(fh) or {}).get("installer_version") or "?"
    except Exception:
        return "?"


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def local_identity(rpc_port=None, extra=None):
    st = _read_json(os.path.join(DATA, "vram-status.json"), {}) or {}
    ident = {"magic": MAGIC, "kind": KIND_REPLY, "id": node_id(),
             "host": local_ip(), "hostname": socket.gethostname(),
             "rpc_port": int(rpc_port or RPC_PORT), "version": _version(),
             "models": _models(), "vram_free_mb": st.get("free_mb"),
             "rpc_binary": RPC_BIN, "ts": time.time()}
    if extra:
        ident.update(extra)
    return ident

def _socket(bind_port, broadcast=True, timeout=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if broadcast:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(("", int(bind_port)))
    if timeout is not None:
        s.settimeout(float(timeout))
    return s


def _send_query(s, port=None):
    msg = json.dumps({"magic": MAGIC, "kind": KIND_QUERY, "id": node_id(),
                      "host": local_ip(), "rpc_port": RPC_PORT, "ts": time.time()}).encode("utf-8")
    for target in ("255.255.255.255", "<broadcast>"):
        try:
            s.sendto(msg, (target, int(port or PEER_PORT)))
        except Exception:
            continue


def scan(wait=None, port=None, peers_path=None, keep_local=True):
    # Decouverte : emet UNE requete en broadcast et collecte les reponses (aucun autre trafic).
    wait = float(wait if wait is not None else SCAN_WAIT_S)
    port = int(port or PEER_PORT)
    dst = peers_path or PEERS
    s = _socket(0, broadcast=True, timeout=0.4)
    found = {}
    t0 = time.time()
    _send_query(s, port)
    while time.time() - t0 < wait:
        try:
            data, addr = s.recvfrom(8192)
        except socket.timeout:
            continue
        except Exception:
            break
        try:
            msg = json.loads(data.decode("utf-8", "replace"))
        except Exception:
            continue
        if not isinstance(msg, dict) or msg.get("magic") != MAGIC or msg.get("kind") != KIND_REPLY:
            continue
        msg["ip"] = addr[0]
        msg["latency_ms"] = round((time.time() - t0) * 1000.0, 1)
        msg["seen_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        found[msg.get("id") or addr[0]] = msg
    s.close()
    if not keep_local:
        found.pop(node_id(), None)
    prev = _read_json(dst, {}) or {}
    now = time.time()
    peers = {}
    for k, v in (prev.get("peers") or {}).items():
        try:
            if (now - float(v.get("ts") or 0)) < STALE_S:
                peers[k] = v
        except Exception:
            continue
    peers.update(found)
    out = {"magic": MAGIC, "node": local_identity(), "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "scan_wait_s": wait, "count": len(peers), "peers": peers}
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        _log("ERROR", "ecriture de peers.json impossible : %s" % exc, crash=True)
    _log("INFO", "scan reseau : %d noeud(s) RPC en %.1fs (id local=%s)"
         % (len(peers), wait, node_id()), crash=True)
    return out


def announce(interval=20.0, count=None, port=None):
    # Daemon de presence : repond aux requetes de decouverte et diffuse sa presence.
    port = int(port or PEER_PORT)
    s = _socket(port, broadcast=True, timeout=1.0)
    _log("INFO", "annonce de presence demarree (id=%s, port=%d, rpc=%d, binaire=%s)"
         % (node_id(), port, RPC_PORT, RPC_BIN))
    n, last = 0, 0.0
    try:
        while count is None or n < count:
            n += 1
            now = time.time()
            if now - last >= interval:
                last = now
                try:
                    s.sendto(json.dumps(local_identity(), ensure_ascii=False).encode("utf-8"),
                             ("255.255.255.255", port))
                except Exception:
                    pass
            try:
                data, addr = s.recvfrom(8192)
            except Exception:
                continue
            try:
                msg = json.loads(data.decode("utf-8", "replace"))
            except Exception:
                continue
            if isinstance(msg, dict) and msg.get("magic") == MAGIC and msg.get("kind") == KIND_QUERY:
                try:
                    s.sendto(json.dumps(local_identity(), ensure_ascii=False).encode("utf-8"), addr)
                except Exception:
                    pass
    except KeyboardInterrupt:
        pass
    finally:
        s.close()
    return n

def peers(peers_path=None):
    data = _read_json(peers_path or PEERS, {}) or {}
    out = []
    for k, v in (data.get("peers") or {}).items():
        if isinstance(v, dict) and v.get("id") != node_id():
            out.append(v)
    out.sort(key=lambda p: (p.get("latency_ms") if p.get("latency_ms") is not None else 1e9))
    return out


def _addr(p):
    return "%s:%s" % (p.get("ip") or p.get("host"), p.get("rpc_port") or RPC_PORT)


def reachable(host, port, timeout=1.0):
    # Test TCP court : le noeud sert-il reellement un RPC ggml ? (aucune donnee transmise)
    if not host:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(float(timeout))
        try:
            s.connect((host, int(port)))
            return True
        finally:
            s.close()
    except Exception:
        return False


def best_peer(peers_path=None):
    # Meilleur noeud distant (latence la plus faible), au format "host:port" attendu par --rpc.
    pl = peers(peers_path)
    return _addr(pl[0]) if pl else None


def rpc_arg(peers_path=None):
    # Argument EXACT a injecter dans la ligne de commande du moteur principal (routage federe).
    pl = peers(peers_path)
    if not pl:
        return None
    return "--rpc " + ",".join(_addr(p) for p in pl)


def status(peers_path=None):
    data = _read_json(peers_path or PEERS, {}) or {}
    me = local_identity()
    pl = peers(peers_path)
    print("=== AiTron - noeuds RPC federes (v2.1.0a) ===")
    print("  Noeud local     : %s (%s) rpc=%d" % (me["id"], me["host"], me["rpc_port"]))
    print("  Binaire RPC     : %s (moteur natif llama.cpp)" % RPC_BIN)
    print("  Dernier scan    : %s (attente %.1fs)" % (data.get("scanned_at") or "-", data.get("scan_wait_s") or 0))
    if not pl:
        print("  Noeuds distants : AUCUN (etat normal sur un poste isole)")
    else:
        print("  Noeuds distants : %d" % len(pl))
        for p in pl:
            host = p.get("ip") or p.get("host")
            ok = reachable(host, p.get("rpc_port") or RPC_PORT)
            print("    - %-15s rpc=%-6s latence=%-8s %-14s %s v%s vram=%sMo"
                  % (host, p.get("rpc_port"), p.get("latency_ms"),
                     ("joignable" if ok else "INJOIGNABLE"), p.get("hostname"),
                     p.get("version"), p.get("vram_free_mb")))
    print("  Argument moteur : %s" % (rpc_arg(peers_path) or "(aucun : calcul 100% local)"))
    print("  Transport       : delegue a 100% au coeur RPC natif de llama.cpp (ggml-rpc-server)")
    return 0


def selftest():
    # Autotest local du protocole : une requete emise, une reponse validee, sur la boucle locale.
    print("=== Autotest decouverte RPC (v2.1.0a) ===")
    print("  Protocole       : %s (UDP unicast sur boucle locale, aucun envoi reseau)" % MAGIC)
    srv = _socket(0, broadcast=False, timeout=3.0)
    port = srv.getsockname()[1]
    ident = local_identity()
    got = {}

    def responder():
        try:
            data, addr = srv.recvfrom(8192)
            got["query"] = json.loads(data.decode("utf-8", "replace"))
            srv.sendto(json.dumps(ident, ensure_ascii=False).encode("utf-8"), addr)
        except Exception as exc:
            got["error"] = str(exc)

    th = threading.Thread(target=responder, daemon=True)
    th.start()
    cli = _socket(0, broadcast=False, timeout=3.0)
    q = json.dumps({"magic": MAGIC, "kind": KIND_QUERY, "id": node_id(), "ts": time.time()}).encode("utf-8")
    t0 = time.time()
    cli.sendto(q, ("127.0.0.1", port))
    rep = None
    try:
        data, _ = cli.recvfrom(8192)
        rep = json.loads(data.decode("utf-8", "replace"))
    except Exception as exc:
        print("  Reponse         : ECHEC (%s)" % exc)
    lat = round((time.time() - t0) * 1000.0, 1)
    th.join(timeout=2.0)
    cli.close()
    srv.close()
    ok = bool(rep and rep.get("magic") == MAGIC and rep.get("kind") == KIND_REPLY
              and rep.get("id") == node_id())
    if rep:
        qq = got.get("query") or {}
        print("  Requete recue   : kind=%s id=%s" % (qq.get("kind"), qq.get("id")))
        print("  Reponse         : id=%s rpc_port=%s latence=%sms" % (rep.get("id"), rep.get("rpc_port"), lat))
        print("  Champs utiles   : version=%s models=%d vram_free_mb=%s binaire=%s"
              % (rep.get("version"), len(rep.get("models") or []), rep.get("vram_free_mb"),
                 rep.get("rpc_binary")))
    print("  Transport       : AUCUNE donnee d'inference transmise (decouverte seule)")
    print("  Argument genere : %s" % ("--rpc %s:%s" % (rep.get("host"), rep.get("rpc_port"))
                                     if rep else "(indisponible)"))
    print("  VERDICT         : %s" % ("VERT" if ok else "ROUGE"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Decouverte reseau des noeuds RPC (v2.1.0a)")
    ap.add_argument("mode", nargs="?", default="status",
                    choices=["status", "scan", "announce", "selftest", "rpc-arg", "best"])
    ap.add_argument("--wait", type=float, default=SCAN_WAIT_S)
    ap.add_argument("--port", type=int, default=PEER_PORT)
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--count", type=int, default=None)
    ap.add_argument("--no-local", action="store_true", help="exclure le noeud local des resultats")
    ap.add_argument("--peers", default=PEERS)
    a = ap.parse_args()
    try:
        if a.mode == "status":
            return status(a.peers)
        if a.mode == "scan":
            out = scan(a.wait, a.port, a.peers, keep_local=not a.no_local)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        if a.mode == "announce":
            print("annonce terminee (%d cycle(s))" % announce(a.interval, a.count, a.port))
            return 0
        if a.mode == "rpc-arg":
            print(rpc_arg(a.peers) or "(aucun noeud distant -> calcul 100% local)")
            return 0
        if a.mode == "best":
            print(best_peer(a.peers) or "(aucun noeud distant)")
            return 0
        return selftest()
    except Exception as exc:
        print("[peer] ERREUR : %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""

VAULT_PY = r"""# vault.py - espace hermetique AES-256-GCM AU REPOS (v2.0.0a)
# PORTEE STRICTEMENT AU REPOS : les fichiers de la zone semantique sont chiffres a l'arret
# (stop) et dechiffres pour la session (start). Le chiffrement EN MEMOIRE VIVE n'est PAS
# garanti : l'effacement des chaines depend du ramasse-miettes de Python (meilleur effort).
# CLE : JAMAIS stockee sur disque. Derivee par PBKDF2-HMAC-SHA256 (390 000 iterations) a partir
# d'un mot de passe saisi dans la console et d'un sel aleatoire conserve dans l'en-tete du
# conteneur (le sel n'est pas secret, la cle ne l'est jamais).
# Format : MAGIC(8) | version(1) | iterations(4 BE) | sel(16) | nonce(12) | chiffre
import argparse
import getpass
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAG = os.path.join(ROOT, "runtime", "rag")
STORE = os.path.join(ROOT, "runtime", "storage")
DATA = os.path.join(ROOT, "data")
STATE = os.path.join(DATA, "vault-state.json")
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")
AREAS = (RAG, STORE)
EXTS = (".npy", ".json", ".jsonl", ".bin")
MAGIC = b"LAVAULT1"
VERSION = 1
ITERATIONS = 390000
SUFFIX = ".enc"


def _audit(level, msg):
    line = "[%s] [SOUVERAIN_CRYPT] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    try:
        with open(CRASHLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n---\n")
    except Exception:
        pass
    return line


def _aesgcm():
    # AES-GCM authentifie : confidentialite ET integrite (detection de toute corruption).
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM
    except Exception:
        return None


def derive_key(password, salt, iterations=ITERATIONS):
    # PBKDF2-HMAC-SHA256 (stdlib) : la cle n'est jamais ecrite sur le disque.
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)


def _targets():
    out = []
    for area in AREAS:
        if not os.path.isdir(area):
            continue
        for name in sorted(os.listdir(area)):
            p = os.path.join(area, name)
            if os.path.isfile(p) and not name.endswith(SUFFIX) and name.lower().endswith(EXTS):
                out.append(p)
    return out


def _sealed():
    out = []
    for area in AREAS:
        if not os.path.isdir(area):
            continue
        for name in sorted(os.listdir(area)):
            if name.endswith(SUFFIX):
                out.append(os.path.join(area, name))
    return out


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def _state(rec):
    try:
        os.makedirs(DATA, exist_ok=True)
        prev = {}
        if os.path.isfile(STATE):
            try:
                with open(STATE, encoding="utf-8-sig") as fh:
                    prev = json.load(fh)
            except Exception:
                prev = {}
        prev.update(rec)
        prev["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(prev, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass

def seal(password, keep_plain=False):
    # Chiffre la zone semantique, verifie IMMEDIATEMENT la reversibilite, puis supprime le clair.
    AESGCM = _aesgcm()
    if AESGCM is None:
        raise RuntimeError("bibliotheque 'cryptography' absente : coffre indisponible")
    files = _targets()
    if not files:
        _state({"state": "rien a sceller (zone vide)"})
        return {"ok": True, "sealed": 0, "reason": "aucun fichier a chiffrer (zone vide)"}
    salt = os.urandom(16)
    aead = AESGCM(derive_key(password, salt))
    done = []
    for path in files:
        nonce = os.urandom(12)
        header = MAGIC + bytes([VERSION]) + ITERATIONS.to_bytes(4, "big") + salt + nonce
        with open(path, "rb") as fh:
            raw = fh.read()
        enc = aead.encrypt(nonce, raw, header)
        dest = path + SUFFIX
        # v3.1.0 (D3) : ANTI-PERTE STRUCTURELLE. Ecriture dans un fichier temporaire, fsync,
        # RELECTURE DEPUIS LE DISQUE, dechiffrement et comparaison au clair AVANT toute
        # suppression. Le conteneur n'est publie (os.replace) qu'une fois prouve reversible.
        tmp_dest = dest + ".part"
        try:
            with open(tmp_dest, "wb") as fh:  # noqa: audit R3 cible ce chemin (.enc.part)
                fh.write(header + enc)
                fh.flush()
                os.fsync(fh.fileno())
            with open(tmp_dest, "rb") as fh:
                on_disk = fh.read()
            if (len(on_disk) != len(header) + len(enc) or not on_disk.startswith(MAGIC)
                    or aead.decrypt(on_disk[29:41], on_disk[41:], on_disk[:41]) != raw):
                raise ValueError("relecture disque non conforme")
        except Exception as exc:
            try:
                os.remove(tmp_dest)
            except OSError:
                pass
            _audit("ERROR", "scellement annule sur %s : %s (clair CONSERVE)"
                   % (os.path.basename(path), exc))
            raise RuntimeError("verification disque echouee sur %s : coffre annule, clair conserve"
                               % os.path.basename(path))
        os.replace(tmp_dest, dest)
        if not keep_plain:
            os.remove(path)
        done.append({"file": os.path.relpath(path, ROOT), "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()})
    _state({"sealed": len(done), "state": "scelle (au repos)"})
    _audit("INFO", "%d fichier(s) chiffres en AES-256-GCM ; cle derivee a la volee, non stockee"
           % len(done))
    return {"ok": True, "sealed": len(done), "files": done}


def unseal(password, keep_sealed=True):
    # Ouvre la zone pour la session. Les conteneurs scelles sont CONSERVES (source au repos).
    AESGCM = _aesgcm()
    if AESGCM is None:
        raise RuntimeError("bibliotheque 'cryptography' absente : coffre indisponible")
    blobs = _sealed()
    if not blobs:
        return {"ok": True, "unsealed": 0, "reason": "aucun conteneur scelle"}
    done = []
    for blob in blobs:
        with open(blob, "rb") as fh:
            data = fh.read()
        if len(data) < 41 or not data.startswith(MAGIC):
            _audit("ERROR", "conteneur invalide ou tronque : %s" % os.path.basename(blob))
            raise RuntimeError("conteneur invalide : %s" % os.path.basename(blob))
        iterations = int.from_bytes(data[9:13], "big")
        salt, nonce, header, ct = data[13:29], data[29:41], data[:41], data[41:]
        try:
            raw = AESGCM(derive_key(password, salt, iterations)).decrypt(nonce, ct, header)
        except Exception as exc:
            _audit("ERROR", "dechiffrement refuse (mot de passe errone ou conteneur corrompu) : "
                            "%s (%s)" % (os.path.basename(blob), type(exc).__name__))
            raise RuntimeError("mot de passe incorrect ou conteneur corrompu : %s"
                               % os.path.basename(blob))
        dest = blob[:-len(SUFFIX)]
        with open(dest, "wb") as fh:
            fh.write(raw)
        if not keep_sealed:
            os.remove(blob)
        done.append({"file": os.path.relpath(dest, ROOT), "bytes": len(raw)})
    _state({"unsealed": len(done), "state": "ouvert pour la session"})
    _audit("INFO", "%d fichier(s) dechiffres pour la session (conteneurs conserves au repos)"
           % len(done))
    return {"ok": True, "unsealed": len(done), "files": done}

def status():
    st = {}
    try:
        with open(STATE, encoding="utf-8-sig") as fh:
            st = json.load(fh)
    except Exception:
        pass
    return {"plain": [os.path.relpath(p, ROOT) for p in _targets()],
            "sealed": [os.path.relpath(p, ROOT) for p in _sealed()],
            "backend": "AES-256-GCM (cryptography)" if _aesgcm() else "INDISPONIBLE",
            "kdf": "PBKDF2-HMAC-SHA256 (%d iterations, sel aleatoire)" % ITERATIONS,
            "state": st}


def selftest(password="mot-de-passe-de-test-v2.0.0a"):
    # Cycle complet sur une zone TEMPORAIRE : les donnees reelles ne sont jamais touchees.
    global AREAS
    import shutil
    tmpdir = os.path.join(DATA, "_vault_selftest")
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir, exist_ok=True)
    payload = os.urandom(4096)
    target = os.path.join(tmpdir, "probe.bin")
    with open(target, "wb") as fh:
        fh.write(payload)
    saved = AREAS
    AREAS = (tmpdir,)
    sealed_ok = us = same = refused = False
    try:
        seal(password)
        sealed_ok = os.path.isfile(target + SUFFIX) and not os.path.isfile(target)
        us = unseal(password)
        if os.path.isfile(target):
            with open(target, "rb") as fh:
                same = fh.read() == payload
        try:
            unseal("mauvais-mot-de-passe")
        except Exception:
            refused = True
    finally:
        AREAS = saved
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("=== autotest du coffre souverain (v2.0.0a) ===")
    print("  backend        : %s" % ("AES-256-GCM (cryptography)" if _aesgcm() else "INDISPONIBLE"))
    print("  derivation     : PBKDF2-HMAC-SHA256, %d iterations, sel aleatoire" % ITERATIONS)
    print("  scellement     : %s" % ("OK" if sealed_ok else "ECHEC"))
    print("  ouverture      : %s" % ("OK" if us and us.get("unsealed") else "ECHEC"))
    print("  integrite      : %s (4096 octets)" % ("IDENTIQUE" if same else "CORROMPU"))
    print("  mauvais mot de passe refuse : %s" % ("OUI" if refused else "NON"))
    print("  cle sur disque : JAMAIS (derivee a la volee)")
    ok = sealed_ok and bool(us) and bool(us.get("unsealed")) and same and refused
    print("VERDICT : %s" % ("VERT" if ok else "A REVOIR"))
    return 0 if ok else 1


def _password(a):
    env = getattr(a, "password_env", None)
    if env:
        pw = os.environ.get(env)
        if not pw:
            raise RuntimeError("variable d'environnement %s vide" % env)
        return pw
    if getattr(a, "test_password", None):
        return a.test_password
    return getpass.getpass("Mot de passe du coffre (saisie masquee) : ")


def main():
    ap = argparse.ArgumentParser(description="Espace hermetique AES-256-GCM au repos")
    ap.add_argument("mode", nargs="?", default="status",
                    choices=["status", "seal", "unseal", "selftest"])
    ap.add_argument("--password-env", dest="password_env",
                    help="nom d'une variable d'environnement portant le mot de passe (automatisation)")
    ap.add_argument("--test-password", dest="test_password", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.mode == "status":
        st = status()
        print("=== Espace hermetique souverain (v2.0.0a) ===")
        print("  Backend    : %s" % st["backend"])
        print("  Derivation : %s" % st["kdf"])
        print("  Scelles    : %d fichier(s)" % len(st["sealed"]))
        for f in st["sealed"][:10]:
            print("    - %s" % f)
        print("  En clair   : %d fichier(s)" % len(st["plain"]))
        for f in st["plain"][:10]:
            print("    - %s" % f)
        print("  Etat       : %s" % st["state"].get("state", "inconnu"))
        print("  Portee     : AU REPOS uniquement (chiffre apres 'stop', ouvert pour la session)")
        print("  Cle        : jamais stockee (PBKDF2 a la volee) ; RAM = meilleur effort (GC)")
        return 0
    if a.mode == "selftest":
        return selftest()
    try:
        res = seal(_password(a)) if a.mode == "seal" else unseal(_password(a))
    except Exception as exc:
        print("[vault] ERREUR : %s" % exc)
        return 1
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

SPEC_DECODING_PY = r"""# spec_decoding.py - Speculative Decoding TEXT-ONLY : garde VRAM + injection d'arguments (v1.9.0)
# LIMITATION UPSTREAM : llama.cpp n'active PAS le pipeline de draft lorsqu'un projecteur
# multimodal (--mmproj) est charge. Le decoding speculatif est donc reserve aux modeles
# de TEXTE PUR et de CODE. Les modeles vision en sont exclus par construction.
# Regles :
#   - le modele DRAFT doit partager le TOKENIZER du modele principal (meme famille) ;
#   - le modele ne doit pas etre multimodal ;
#   - la VRAM libre doit couvrir principal + draft + cache KV couple, sinon REPLI sans draft.
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
STATUS = os.path.join(DATA, "spec-status.json")
PROFILE = os.path.join(ROOT, "config", "hardware-profile.json")
MODELS = os.path.join(ROOT, "models")
CRASHLOG = os.path.join(os.path.dirname(ROOT), "dev", "crash.log")

DRAFT_MAX = 8
DRAFT_MIN = 2
KV_MB_PER_1K = 60          # estimation prudente du cache KV par millier de tokens
SAFETY_MB = 256            # marge de securite QA


def _log(level, msg):
    line = "[%s] [SPEC_DECODE] [%s] %s" % (time.strftime("%Y%m%d_%H%M%S"), level, msg)
    try:
        with open(CRASHLOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n---\n")
    except Exception:
        pass
    return line


def _profile():
    try:
        with open(PROFILE, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _size_mb(path):
    try:
        return int(os.path.getsize(path) / 1048576)
    except Exception:
        return 0


def _params():
    p = _profile().get("params") or {}
    return {"ngl": int(p.get("ngl") or 0), "ctx": int(p.get("ctx") or 4096),
            "threads": int(p.get("threads") or 0)}


def decide(model_file, draft_file, free_vram_mb=None, force=None):
    # Renvoie la decision : {enabled, reason, args, budget}. Deterministe et tracable.
    prof = _profile()
    gpu = prof.get("gpu") or {}
    if free_vram_mb is None:
        free_vram_mb = int(gpu.get("vram_free_mb") or 0)
    par = _params()
    model_path = model_file if os.path.isabs(model_file) else os.path.join(MODELS, model_file)
    draft_path = draft_file if os.path.isabs(draft_file) else os.path.join(MODELS, draft_file)
    out = {"model": os.path.basename(model_path), "draft": os.path.basename(draft_path),
           "free_vram_mb": free_vram_mb, "ngl": par["ngl"], "ctx": par["ctx"],
           "enabled": False, "reason": "", "args": [], "budget_mb": 0}
    if force is False:
        out["reason"] = "desactive explicitement (config\\spec-decoding.json / AITRON_SPEC=0)"
        return out
    # MESURE REELLE (v1.9.0) : sur un profil GPU-bound (modele entierement offload, variante
    # Vulkan), le draft n'apporte AUCUN gain (21,39 t/s avec vs 21,76 sans, dans le bruit) tout
    # en consommant ~470 Mo de VRAM et un second chargement de modele. L'activation est donc
    # OPT-IN : AITRON_SPEC=1. Le gain attendu du decoding speculatif releve des profils
    # CPU-bound ou limites en bande passante memoire.
    if str(os.environ.get("AITRON_SPEC", "")).strip().lower() not in ("1", "true", "yes", "on"):
        out["reason"] = ("desactive par defaut : aucun gain mesure sur profil GPU-bound "
                         "(voir dev\\DECISIONS.md D-039) ; activer avec AITRON_SPEC=1")
        return out
    if not os.path.isfile(model_path):
        out["reason"] = "modele principal introuvable"
        return out
    if not os.path.isfile(draft_path):
        out["reason"] = "modele draft introuvable -> decoding standard"
        return out
    # 1. TEXTE-ONLY : jamais de draft avec un projecteur multimodal.
    low = os.path.basename(model_path).lower()
    if "vl" in low or "vision" in low or "mmproj" in low:
        out["reason"] = "modele multimodal : le decoding speculatif est desactive par llama.cpp"
        return out
    # 2. Budget VRAM : principal + draft + KV couple + marge.
    m_mb, d_mb = _size_mb(model_path), _size_mb(draft_path)
    kv_mb = int((par["ctx"] / 1000.0) * KV_MB_PER_1K) * 2   # KV couple (principal + draft)
    need = m_mb + d_mb + kv_mb + SAFETY_MB
    out["budget_mb"] = need
    out["detail_mb"] = {"principal": m_mb, "draft": d_mb, "kv_couple": kv_mb, "marge": SAFETY_MB}
    if 0 < free_vram_mb < need:
        out["reason"] = ("VRAM libre insuffisante (%d Mo < %d Mo requis) -> repli SANS draft"
                         % (free_vram_mb, need))
        _log("WARN", out["reason"])
        return out
    out["enabled"] = True
    out["reason"] = ("texte pur, tokenizer partage, VRAM suffisante (%d Mo libres >= %d Mo)"
                     % (free_vram_mb, need))
    # Drapeaux REELS de llama.cpp b11375 : '--draft-max'/'--draft-min' ont ete RETIRES par
    # l'upstream et remplaces par '--spec-draft-n-max'/'--spec-draft-n-min' (le mandat citait
    # les anciens noms). '--model-draft' reste valide (alias de '--spec-draft-model').
    out["args"] = ["--model-draft", draft_path, "--spec-draft-n-max", str(DRAFT_MAX),
                   "--spec-draft-n-min", str(DRAFT_MIN)]
    return out


def status():
    try:
        with open(STATUS, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return {"enabled": False, "reason": "aucun etat enregistre (pile non demarree)",
                "model": "-", "draft": "-"}


def save(dec):
    try:
        os.makedirs(DATA, exist_ok=True)
        rec = dict(dec)
        rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(STATUS, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass

def active_pair():
    # Determine la paire (modele principal, draft) depuis le catalogue et la variante active.
    try:
        with open(os.path.join(MODELS, "models-catalog.json"), encoding="utf-8-sig") as fh:
            cat = json.load(fh)
    except Exception:
        return None, None
    for m in cat.get("models", []):
        d = m.get("draft")
        if d and os.path.isfile(os.path.join(MODELS, m.get("filename", ""))):
            return m.get("filename"), d.get("filename")
    return None, None


def show_status():
    st = status()
    print("=== Decoding speculatif (v1.9.0) ===")
    print("  Etat        : %s" % ("ACTIF" if st.get("enabled") else "inactif"))
    print("  Modele      : %s" % st.get("model", "-"))
    print("  Draft       : %s" % st.get("draft", "-"))
    print("  Raison      : %s" % st.get("reason", "-"))
    if st.get("budget_mb"):
        d = st.get("detail_mb") or {}
        print("  Budget VRAM : %s Mo requis (principal %s + draft %s + KV couple %s + marge %s)"
              % (st.get("budget_mb"), d.get("principal"), d.get("draft"),
                 d.get("kv_couple"), d.get("marge")))
        print("  VRAM libre  : %s Mo" % st.get("free_vram_mb"))
    if st.get("args"):
        print("  Arguments   : %s" % " ".join(str(a) for a in st["args"]))
    print("  Regle       : TEXT-ONLY uniquement (jamais avec --mmproj : limitation llama.cpp)")
    print("  Mesure      : Run-LocalAI.bat benchmark  (comparer avec AITRON_SPEC=0)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Speculative Decoding TEXT-ONLY (garde VRAM)")
    ap.add_argument("mode", nargs="?", default="status", choices=["status", "check", "save"])
    ap.add_argument("--model")
    ap.add_argument("--draft")
    ap.add_argument("--vram-free", type=int, default=None)
    ap.add_argument("--off", action="store_true", help="force la desactivation")
    a = ap.parse_args()
    if a.mode == "status":
        return show_status()
    model, draft = a.model, a.draft
    if not model or not draft:
        m, d = active_pair()
        model = model or m
        draft = draft or d
    if not model or not draft:
        dec = {"enabled": False, "model": model or "-", "draft": draft or "-",
               "reason": "aucune paire principal/draft declaree dans le catalogue"}
        if a.mode == "save":
            save(dec)
        print(json.dumps(dec, ensure_ascii=False, indent=2))
        return 0
    dec = decide(model, draft, a.vram_free, False if a.off else None)
    if a.mode == "save":
        save(dec)
        _log("INFO" if dec["enabled"] else "WARN", "decision : %s (%s)"
             % ("actif" if dec["enabled"] else "inactif", dec["reason"]))
    print(json.dumps(dec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

QUANTIZE_MODEL_PY = r"""# quantize_model.py - quantization locale via llama-quantize.exe (v1.7.0)
# Usage : quantize_model.py run <modele_f16.gguf> <type> [--out chemin] [--threads N] [--async]
#         quantize_model.py list
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "backends", "llama-cpp", "llama-quantize.exe")
MODELS = os.path.join(ROOT, "models")
LOGS = os.path.join(ROOT, "logs")
DATA = os.path.join(ROOT, "data")
HISTORY = os.path.join(DATA, "quantize-history.jsonl")
QLOG = os.path.join(LOGS, "quantize.log")
SUPPORTED = ["Q8_0", "Q6_K", "Q5_K_M", "Q5_K_S", "Q5_0", "Q5_1", "Q4_K_M", "Q4_K_S",
             "Q4_0", "Q4_1", "Q3_K_L", "Q3_K_M", "Q3_K_S", "Q2_K", "IQ4_NL", "IQ4_XS",
             "IQ3_S", "IQ3_XXS", "IQ2_S", "IQ2_XS", "IQ2_XXS", "F16", "BF16", "F32"]


def _log(msg):
    print("[quantize] " + msg, flush=True)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def default_output(src, qtype):
    base = os.path.basename(src)
    stem = os.path.splitext(base)[0]
    for tag in ("-f16", "-F16", "_f16", "-f32", "-F32", "_f32", "f16-", "f32-"):
        stem = stem.replace(tag, "")
    stem = stem.strip("-_")
    return os.path.join(MODELS, "%s-%s.gguf" % (stem.lower(), qtype.lower()))


def _record(rec):
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(HISTORY, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _worker(src, qtype, out, threads):
    # Processus de fond : la compression ne bloque pas le shell de l'utilisateur.
    os.makedirs(LOGS, exist_ok=True)
    with open(QLOG, "ab") as fh:
        fh.write(("\n=== %s : %s -> %s (%s) ===\n"
                  % (time.strftime("%Y-%m-%dT%H:%M:%S"), src, out, qtype)).encode())
        fh.flush()
        args = [EXE, src, out, qtype]
        if threads:
            args.append(str(int(threads)))
        rc = subprocess.call(args, cwd=os.path.dirname(EXE), stdout=fh, stderr=subprocess.STDOUT)
    ok = (rc == 0 and os.path.isfile(out))
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": src, "output": out, "type": qtype,
           "returncode": rc, "ok": ok, "async": True,
           "output_bytes": os.path.getsize(out) if os.path.isfile(out) else 0}
    _record(rec)
    return 0 if ok else 1

def quantize(src, qtype, out=None, threads=0, asynchronous=False):
    if not os.path.isfile(EXE):
        raise RuntimeError("llama-quantize.exe introuvable : %s" % EXE)
    if not os.path.isfile(src):
        raise RuntimeError("modele source introuvable : %s" % src)
    qtype = (qtype or "").upper()
    if qtype not in SUPPORTED:
        raise RuntimeError("type de quantization inconnu : '%s'\n  types valides : %s"
                           % (qtype, ", ".join(SUPPORTED)))
    stem = os.path.basename(src).lower()
    if "f16" not in stem and "f32" not in stem:
        _log("ATTENTION : la source ne porte ni 'f16' ni 'f32' dans son nom.")
        _log("            llama-quantize n'accepte QUE des modeles non quantifies ;")
        _log("            l'echec eventuel sera explicite dans logs\\quantize.log.")
    out = out or default_output(src, qtype)
    src_size = os.path.getsize(src)
    _log("source : %s (%.2f Go)" % (src, src_size / 1073741824.0))
    _log("cible  : %s" % out)
    _log("type   : %s" % qtype)
    if os.path.isfile(out):
        _log("la cible existe deja -> ecrasement")
    if asynchronous:
        # Mode asynchrone : un processus de fond poursuit la compression, le CLI rend la main.
        os.makedirs(DATA, exist_ok=True)
        cmd = [sys.executable, os.path.abspath(__file__), "__worker", src, qtype,
               "--out", out, "--threads", str(int(threads or 0))]
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                creationflags=(0x00000008 | 0x00000200) if os.name == "nt" else 0)
        _log("compression lancee en ARRIERE-PLAN (PID %d)" % proc.pid)
        _log("suivi : logs\\quantize.log | historique : data\\quantize-history.jsonl")
        return 0
    os.makedirs(LOGS, exist_ok=True)
    t0 = time.time()
    with open(QLOG, "ab") as fh:
        fh.write(("\n=== %s : %s -> %s (%s) ===\n"
                  % (time.strftime("%Y-%m-%dT%H:%M:%S"), src, out, qtype)).encode())
        fh.flush()
        args = [EXE, src, out, qtype]
        if threads:
            args.append(str(int(threads)))
        rc = subprocess.call(args, cwd=os.path.dirname(EXE), stdout=fh, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    if rc != 0 or not os.path.isfile(out):
        raise RuntimeError("llama-quantize a echoue (code %d) - details dans logs\\quantize.log" % rc)
    out_size = os.path.getsize(out)
    ratio = (out_size / float(src_size)) if src_size else 0.0
    digest = _sha256(out)
    _log("OK : %s" % out)
    _log("  taille : %.2f Go -> %.2f Go (ratio %.3f, gain %.0f%%)"
         % (src_size / 1073741824.0, out_size / 1073741824.0, ratio, (1 - ratio) * 100))
    _log("  duree  : %.1f s" % dt)
    _log("  sha256 : %s" % digest)
    _record({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": src, "output": out, "type": qtype,
             "source_bytes": src_size, "output_bytes": out_size, "ratio": round(ratio, 4),
             "sha256": digest, "duration_s": round(dt, 1), "returncode": rc, "ok": True,
             "async": False})
    return 0


def show_list():
    print("=== Quantization locale (llama-quantize) ===")
    print("  Binaire : %s%s" % (EXE, "" if os.path.isfile(EXE) else "   [ABSENT]"))
    print("  Types supportes (%d) :" % len(SUPPORTED))
    for i in range(0, len(SUPPORTED), 8):
        print("    " + "  ".join("%-8s" % t for t in SUPPORTED[i:i + 8]))
    print("  Sources non quantifiees detectees dans models\\ :")
    n = 0
    if os.path.isdir(MODELS):
        for name in sorted(os.listdir(MODELS)):
            low = name.lower()
            if not low.endswith(".gguf") or ("f16" not in low and "f32" not in low):
                continue
            if any(t in low for t in ("q8_", "q6_", "q5_", "q4_", "q3_", "q2_", "iq")):
                continue  # deja quantifie : llama-quantize le refuserait
            p = os.path.join(MODELS, name)
            print("    %-52s %6.2f Go" % (name, os.path.getsize(p) / 1073741824.0))
            n += 1
    if not n:
        print("    (aucune : placez un GGUF F16/F32 dans models\\ puis relancez)")
    print("  Historique : data\\quantize-history.jsonl")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Quantization locale via llama-quantize.exe")
    ap.add_argument("mode", nargs="?", default="run", choices=["run", "list", "__worker"])
    ap.add_argument("source", nargs="?")
    ap.add_argument("qtype", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--async", dest="asynchronous", action="store_true",
                    help="lance la compression en arriere-plan et rend la main")
    a = ap.parse_args()
    if a.mode == "list":
        return show_list()
    if a.mode == "__worker":
        return _worker(a.source, a.qtype, a.out or default_output(a.source, a.qtype), a.threads)
    if not a.source or not a.qtype:
        ap.error("usage : quantize <modele_f16.gguf> <type>   (ex : Q4_K_M, Q8_0)   |   quantize list")
    try:
        return quantize(a.source, a.qtype, a.out, a.threads, a.asynchronous)
    except Exception as exc:
        print("[quantize] ERREUR : %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""

FAILOVER_PROXY_PY = r"""# failover_proxy.py - proxy SSE : bufferisation + failover deterministe (v1.6.0)
# Requetes "sensibles/agent" (stream + marqueur) : BUFFERISATION COMPLETE AVANT ENVOI.
#   Une erreur du moteur primaire avant la fin du buffer est interceptee et la requete est
#   rejouee silencieusement sur le modele local secondaire (CPU) puis sur une cle cloud de
#   secours (config\cloud-keys.env) : le client ne voit jamais de flux interrompu.
# Requetes de routine en streaming : FAILOVER SUR ERREUR AVANT LE PREMIER TOKEN
#   (si le primaire est injoignable au demarrage, bascule immediate, puis ouverture du flux).
import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlreq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "config", "failover.json")
FAILLOG = os.path.join(ROOT, "logs", "failover.jsonl")

DEFAULTS = {
    "listen_port": 8081,
    "primary": {"name": "core-local", "base": "http://127.0.0.1:8080/v1"},
    "secondary": {"name": "vision-cpu", "base": "http://127.0.0.1:8095/v1", "model": "vlm"},
    "cloud": {"enabled": True, "base": "https://openrouter.ai/api/v1",
              "model": "openrouter/anthropic/claude-3.5-sonnet",
              "key_env": "OPENROUTER_API_KEY", "keys_file": "config/cloud-keys.env"},
    "buffered": {"models": ["localai", "localai-buffered", "agent", "cline"],
                 "header": "x-localai-buffer", "always": False,
                 "connect_timeout_s": 1.5, "read_timeout_s": 300},
}


def _log(msg):
    try:
        os.makedirs(os.path.dirname(FAILLOG), exist_ok=True)
        with open(FAILLOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": msg},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_cfg():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(CONFIG, encoding="utf-8-sig") as fh:
            user = json.load(fh)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    except Exception:
        pass
    return cfg


def cloud_key(cfg):
    env_name = cfg["cloud"].get("key_env") or ""
    if os.environ.get(env_name):
        return os.environ[env_name]
    try:
        with open(os.path.join(ROOT, cfg["cloud"].get("keys_file") or ""), encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == env_name:
                        return v.strip()
    except Exception:
        pass
    return ""


def tcp_alive(base, timeout):
    try:
        hostport = base.split("//", 1)[1].split("/", 1)[0]
        host, _, port = hostport.partition(":")
        s = socket.create_connection((host, int(port or 80)), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def route_chain(cfg):
    # Ordre deterministe : primaire -> secondaire local (CPU) -> cloud (si cle disponible).
    cfg = load_cfg()
    chain = [dict(cfg["primary"], kind="primary")]
    sec = cfg.get("secondary") or {}
    if sec.get("base"):
        chain.append(dict(sec, kind="secondary"))
    cl = cfg.get("cloud") or {}
    key = cloud_key(cfg) if cl.get("enabled") else ""
    if cl.get("enabled") and key:
        chain.append({"name": "cloud", "base": cl["base"], "model": cl.get("model"),
                      "api_key": key, "kind": "cloud"})
    return chain


def _upstream(target, body, read_timeout, force_json=False, alias=None):
    url = target["base"].rstrip("/") + "/chat/completions"
    payload = dict(body)
    if force_json:
        # Mode bufferise : on demande une reponse JSON complete en amont (pas de SSE).
        payload["stream"] = False
    m = payload.get("model")
    if alias and m in alias:
        payload["model"] = alias[m]
    if target.get("model") and target.get("kind") == "secondary":
        payload["model"] = target["model"]
    headers = {"Content-Type": "application/json"}
    if target.get("api_key"):
        headers["Authorization"] = "Bearer " + target["api_key"]
    req = urlreq.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    return urlreq.urlopen(req, timeout=read_timeout)


def _read_full(target, body, read_timeout, force_json=False, alias=None):
    with _upstream(target, body, read_timeout, force_json, alias) as resp:
        return resp.status, resp.read()


def _sse_from_text(text, model):
    # Reconstruit un flux SSE regulier a partir d'une reponse bufferisee : le client
    # recoit un flux complet et coherent, jamais une coupure au milieu d'une generation.
    parts = []
    words = (text or "").split(" ")
    for i, w in enumerate(words):
        piece = w if i == 0 else " " + w
        parts.append("data: " + json.dumps(
            {"model": model, "object": "chat.completion.chunk",
             "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]},
            ensure_ascii=False) + "\n\n")
    parts.append("data: " + json.dumps(
        {"model": model, "object": "chat.completion.chunk",
         "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}) + "\n\n")
    parts.append("data: [DONE]\n\n")
    return "".join(parts).encode("utf-8")


def _content_of(payload_bytes):
    try:
        d = json.loads(payload_bytes.decode("utf-8"))
        return d["choices"][0]["message"]["content"]
    except Exception:
        return ""

class Handler(BaseHTTPRequestHandler):
    server_version = "LocalAI-Failover/1.6.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except Exception:
            n = 0
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return None

    def do_GET(self):
        cfg = load_cfg()
        if self.path.startswith("/health"):
            return self._send(200, json.dumps(
                {"status": "ok", "service": "failover-proxy",
                 "policy": {"buffered_models": cfg["buffered"]["models"],
                            "header": cfg["buffered"]["header"],
                            "connect_timeout_s": cfg["buffered"]["connect_timeout_s"]}}).encode())
        url = cfg["primary"]["base"].rstrip("/") + self.path
        try:
            with urlreq.urlopen(url, timeout=5) as r:
                return self._send(r.status, r.read())
        except Exception as exc:
            return self._send(502, json.dumps({"error": str(exc)[:160]}).encode())

    def do_POST(self):
        cfg = load_cfg()
        body = self._body()
        if body is None:
            return self._send(400, json.dumps({"error": "JSON invalide"}).encode())
        model = str(body.get("model") or "")
        stream = bool(body.get("stream"))
        pol = cfg["buffered"]
        hdr = str(self.headers.get(pol["header"]) or "").strip().lower()
        if pol.get("always"):
            buffered = True
        elif hdr:
            buffered = hdr not in ("0", "false", "no", "off")
        else:
            buffered = model in (pol.get("models") or [])
        if stream and buffered:
            return self._buffered(cfg, body, model)
        if stream:
            return self._stream(cfg, body, model)
        return self._simple(cfg, body)

    def _simple(self, cfg, body):
        for tgt in route_chain(cfg):
            try:
                code, data = _read_full(tgt, body, cfg["buffered"]["read_timeout_s"])
                return self._send(code, data)
            except Exception as exc:
                _log({"route": tgt["name"], "mode": "simple", "erreur": str(exc)[:160]})
        return self._send(503, json.dumps({"error": "aucun moteur disponible"}).encode())

    def _buffered(self, cfg, body, model):
        # Bufferisation complete AVANT ENVOI : le client ne voit le flux qu'une fois la
        # generation terminee et validee. Toute defaillance est rejouee silencieusement.
        t0 = time.time()
        last = "aucune route"
        alias = cfg["buffered"].get("alias_map") or {}
        for tgt in route_chain(cfg):
            why = None
            if not tcp_alive(tgt["base"], cfg["buffered"]["connect_timeout_s"]):
                why = "port injoignable"
            else:
                try:
                    code, data = _read_full(tgt, body, cfg["buffered"]["read_timeout_s"],
                                            force_json=True, alias=alias)
                    if code >= 500:
                        why = "HTTP %d" % code
                    else:
                        txt = _content_of(data)
                        out = _sse_from_text(txt, model or tgt["name"])
                        ms = int((time.time() - t0) * 1000)
                        _log({"route": tgt["name"], "mode": "bufferise",
                              "failover": tgt["kind"] != "primary", "ms_decision": ms,
                              "caracteres": len(txt)})
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("X-LocalAI-Route", tgt["name"])
                        self.send_header("Content-Length", str(len(out)))
                        self.end_headers()
                        self.wfile.write(out)
                        return
                except urlreq.HTTPError as exc:
                    if 400 <= exc.code < 500:
                        # Erreur de la REQUETE (modele inconnu, JSON invalide) : inutile de basculer.
                        _log({"route": tgt["name"], "mode": "bufferise", "erreur_client": exc.code})
                        try:
                            return self._send(exc.code, exc.read())
                        except Exception:
                            return self._send(exc.code,
                                              json.dumps({"error": "HTTP %d" % exc.code}).encode())
                    why = "HTTP %d" % exc.code
                except Exception as exc:
                    why = str(exc)[:120]
            last = "%s : %s" % (tgt["name"], why)
            _log({"route": tgt["name"], "mode": "bufferise", "echec": last})
        ms = int((time.time() - t0) * 1000)
        _log({"mode": "bufferise", "erreur": last, "ms_decision": ms})
        return self._send(503, json.dumps({"error": "bufferisation impossible",
                                           "detail": last, "ms": ms}).encode())

    def _stream(self, cfg, body, model):
        # Failover SUR ERREUR AVANT LE PREMIER TOKEN : la route est choisie avant d'ouvrir
        # le flux vers le client.
        t0 = time.time()
        last = "aucune route"
        for tgt in route_chain(cfg):
            if not tcp_alive(tgt["base"], cfg["buffered"]["connect_timeout_s"]):
                last = "%s : port injoignable" % tgt["name"]
                continue
            try:
                resp = _upstream(tgt, body, cfg["buffered"]["read_timeout_s"])
            except Exception as exc:
                last = "%s : %s" % (tgt["name"], str(exc)[:120])
                continue
            # v3.1.0 (D9) : lire le 1er evenement SSE COMPLET avant d'engager la reponse client.
            head = b""
            try:
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    head += line
                    if line in (b"\n", b"\r\n") or len(head) > 262144:
                        break
                if not head:
                    raise ValueError("flux vide")
                if not (head.endswith(b"\n\n") or head.endswith(b"\r\n\r\n")):
                    raise ValueError("1er evenement SSE incomplet")
            except Exception as exc:
                last = "%s : flux interrompu avant le 1er evenement (%s)" % (tgt["name"], str(exc)[:80])
                _log({"route": tgt["name"], "mode": "flux", "echec_avant_1er_evenement": last})
                try:
                    resp.close()
                except Exception:
                    pass
                continue
            ms = int((time.time() - t0) * 1000)
            _log({"route": tgt["name"], "mode": "flux", "failover": tgt["kind"] != "primary",
                  "ms_decision": ms})
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.headers.get("Content-Type") or "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-LocalAI-Route", tgt["name"])
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(head)
                self.wfile.flush()
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except Exception as exc:
                _log({"mode": "flux", "erreur_mi_flux": str(exc)[:120]})
            finally:
                try:
                    resp.close()
                except Exception:
                    pass
            return
        _log({"mode": "flux", "erreur": last})
        return self._send(503, json.dumps({"error": "aucun moteur disponible",
                                           "detail": last}).encode())


def main():
    cfg = load_cfg()
    port = int(os.environ.get("AITRON_FAILOVER_PORT") or cfg.get("listen_port") or 8081)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    _log({"event": "demarrage", "port": port, "bufferise": cfg["buffered"]})
    print("[failover] proxy SSE en ecoute sur 127.0.0.1:%d" % port, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

GRAPH_RAG_PY = r"""# graph_rag.py - GraphRAG local : extraction entites/relations par le LLM local (v1.6.0)
# L'extraction NER/RE est DELEGUEE a llama-server.exe via des prompts structures (pas de regex).
# Le graphe (noeuds, aretes, interdependances structurelles du code source) est serialise a plat
# dans runtime\storage\graph_db.json.
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STORE = os.path.join(ROOT, "runtime", "storage")
GRAPH = os.path.join(STORE, "graph_db.json")
LOGS = os.path.join(ROOT, "logs")
TEXT_EXT = {".txt", ".md", ".json", ".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
            ".java", ".cs", ".sh", ".bat", ".ps1", ".yaml", ".yml", ".toml", ".ini", ".cfg",
            ".csv", ".xml", ".html", ".css", ".sql"}
IMPORT_PATTERNS = {
    ".py": (r"^\s*import\s+([A-Za-z_][\w\.]*)", r"^\s*from\s+([A-Za-z_][\w\.]*)\s+import"),
    ".js": (r"^\s*import\s+[^'\"]*from\s+['\"]([^'\"]+)['\"]",),
    ".ts": (r"^\s*import\s+[^'\"]*from\s+['\"]([^'\"]+)['\"]",),
    ".go": (r"^\s*\"([\w\./\-]+)\"",),
    ".ps1": (r"^\s*\.\s+(.+\.ps1)",),
    ".bat": (r"^\s*call\s+(.+\.bat)",),
}


def _log(msg):
    print("[graph] " + msg, flush=True)


def _ports():
    p = {"llama": 8090, "localai": 8080, "embed": 8094}
    try:
        with open(os.path.join(ROOT, "data", "runtime.env"), encoding="utf-8-sig") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    k = k.strip().lower()
                    if k.endswith("_port"):
                        k = k[:-5]
                    if k in p and v.strip().isdigit():
                        p[k] = int(v.strip())
    except Exception:
        pass
    return p


def _http(url, payload=None, timeout=900):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ensure_engine(port):
    # Le moteur de chat doit etre joignable : il porte l'extraction NER/RE.
    try:
        _http("http://127.0.0.1:%d/health" % port, timeout=3)
        return None
    except Exception:
        pass
    exe = os.path.join(ROOT, "backends", "llama-cpp", "llama-server.exe")
    model = os.path.join(ROOT, "models", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
    if not (os.path.isfile(exe) and os.path.isfile(model)):
        raise RuntimeError("moteur/modele introuvable pour le GraphRAG")
    os.makedirs(LOGS, exist_ok=True)
    out = open(os.path.join(LOGS, "graph-engine.log"), "ab")
    proc = subprocess.Popen([exe, "-m", model, "-ngl", "99", "--threads", "8", "-c", "2048",
                             "--host", "127.0.0.1", "--port", str(port)],
                            cwd=os.path.dirname(exe), stdout=out, stderr=subprocess.STDOUT)
    with open(os.path.join(ROOT, "data", "pids.txt"), "a", encoding="utf-8") as fh:
        fh.write("graph-engine %d\n" % proc.pid)
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            _http("http://127.0.0.1:%d/health" % port, timeout=3)
            return proc
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("moteur GraphRAG injoignable")

NER_PROMPT = (
    "Tu extrais un graphe de connaissances. Reponds UNIQUEMENT par un tableau JSON, sans texte "
    "autour, au format exact :\n"
    "[{\"head\":\"entite\",\"type\":\"type_entite\",\"relation\":\"relation\",\"tail\":\"entite\"}]\n"
    "Regles : noms courts (max 3 mots), pas de phrases, 2 a 4 triplets maximum, en francais. "
    "Ferme le tableau des que tu as fini.\n"
    "Texte :\n%s\nJSON :"
)


def _parse_triplets(raw):
    # Extraction tolerante : isole le premier tableau JSON equilibre, nettoie puis reessaie.
    start = raw.find("[")
    if start < 0:
        return []
    depth = 0
    blob = ""
    for i in range(start, len(raw)):
        if raw[i] == "[":
            depth += 1
        elif raw[i] == "]":
            depth -= 1
            if depth == 0:
                blob = raw[start:i + 1]
                break
    if not blob:
        # Sortie tronquee (limite de tokens) : recuperation des objets completes deja emis.
        tail = raw[start:]
        last = tail.rfind("}")
        if last < 0:
            return []
        blob = tail[:last + 1] + "]"
    data = None
    try:
        data = json.loads(blob)
    except Exception:
        try:
            data = json.loads(re.sub(r",\s*([\]}])", r"\1", blob))
        except Exception:
            return []
    out = []
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            h = str(item.get("head", "")).strip()
            t = str(item.get("tail", "")).strip()
            if not h or not t:
                continue
            out.append({"head": h,
                        "htype": (str(item.get("type", "")).strip() or "concept"),
                        "relation": (str(item.get("relation", "")).strip() or "lie_a"),
                        "tail": t})
    return out


def _extract_triplets(text, port, model, max_tokens=256):
    payload = {"model": model,
               "messages": [{"role": "user", "content": NER_PROMPT % text[:1800]}],
               "max_tokens": max_tokens, "temperature": 0}
    res = _http("http://127.0.0.1:%d/v1/chat/completions" % port, payload, timeout=600)
    return _parse_triplets(res["choices"][0]["message"]["content"])


def structural_edges(path, root):
    # Interdependances structurelles du code source (imports/references) : deterministe,
    # complementaire de l'extraction LLM.
    ext = os.path.splitext(path)[1].lower()
    pats = IMPORT_PATTERNS.get(ext)
    if not pats:
        return []
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    edges = []
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                for pat in pats:
                    m = re.match(pat, line)
                    if m:
                        target = m.group(1).replace("\\", "/")
                        if target.endswith(".py"):
                            target = target[:-3]
                        edges.append({"source": rel, "relation": "imports",
                                      "target": target, "kind": "structural"})
                        break
    except Exception:
        pass
    return edges

def chunk_text(text, size=1200, overlap=0.10):
    size = max(256, int(size))
    step = max(1, int(size * (1.0 - float(overlap))))
    out, i, n = [], 0, len(text)
    while i < n:
        piece = text[i:i + size].strip()
        if piece:
            out.append(piece)
        if i + size >= n:
            break
        i += step
    return out


def _norm(name):
    return re.sub(r"\s+", " ", name.strip()).lower()


def _touch(nodes, key, name, ntype, src=None):
    n = nodes.setdefault(key, {"id": key, "name": name, "type": ntype,
                               "mentions": 0, "sources": set()})
    n["mentions"] += 1
    if src:
        n["sources"].add(src)
    return n


def build(input_dir, port, model, max_files, max_chunks, chunk_size, overlap):
    if not os.path.isdir(input_dir):
        raise RuntimeError("dossier introuvable : %s" % input_dir)
    ensure_engine(port)
    stats = {"files": 0, "chunks": 0, "triplets": 0, "echecs": 0}
    nodes, edges = {}, []
    files = list(iter_files(input_dir, TEXT_EXT))[:max_files]
    _log("%d fichier(s) candidat(s) dans %s" % (len(files), input_dir))
    stop = False
    for path in files:
        stats["files"] += 1
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as fh:
                text = fh.read()
        except Exception:
            continue
        rel = os.path.relpath(path, input_dir).replace(os.sep, "/")
        for se in structural_edges(path, input_dir):
            edges.append(se)
            _touch(nodes, _norm(se["source"]), se["source"], "fichier", se["source"])
            _touch(nodes, _norm(se["target"]), se["target"], "module", se["source"])
        for piece in chunk_text(text, chunk_size, overlap):
            if stats["chunks"] >= max_chunks:
                stop = True
                break
            stats["chunks"] += 1
            try:
                trips = _extract_triplets(piece, port, model)
            except Exception as exc:
                stats["echecs"] += 1
                _log("extraction en echec (%s) : %s" % (rel, exc))
                continue
            for t in trips:
                stats["triplets"] += 1
                hk, tk = _norm(t["head"]), _norm(t["tail"])
                _touch(nodes, hk, t["head"], t["htype"], rel)
                _touch(nodes, tk, t["tail"], "concept", rel)
                edges.append({"source": hk, "relation": t["relation"], "target": tk,
                              "kind": "llm", "provenance": rel})
        if stop:
            _log("limite de chunks atteinte (%d)" % max_chunks)
            break
    deg = {}
    for e in edges:
        deg[e["source"]] = deg.get(e["source"], 0) + 1
        deg[e["target"]] = deg.get(e["target"], 0) + 1
    for k, n in nodes.items():
        n["degree"] = deg.get(k, 0)
        n["sources"] = sorted(n["sources"])[:8]
    os.makedirs(STORE, exist_ok=True)
    g = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source_dir": input_dir,
         "engine": "llama-server /v1/chat/completions (extraction NER/RE par LLM local)",
         "model": model, "stats": stats,
         "nodes": sorted(nodes.values(), key=lambda n: -n["degree"]),
         "edges": edges}
    with open(GRAPH, "w", encoding="utf-8") as fh:
        json.dump(g, fh, indent=2, ensure_ascii=False)
    struct = sum(1 for e in edges if e.get("kind") == "structural")
    _log("graphe : %d noeuds / %d aretes (%d triplets LLM, %d structurelles) sur %d chunk(s)"
         % (len(g["nodes"]), len(edges), stats["triplets"], struct, stats["chunks"]))
    _log("serialise a plat : %s" % GRAPH)
    return 0

def iter_files(input_dir, exts):
    for base, _dirs, names in os.walk(input_dir):
        for name in sorted(names):
            if os.path.splitext(name)[1].lower() in exts:
                yield os.path.join(base, name)


def show():
    if not os.path.isfile(GRAPH):
        print("[graph] graphe absent : lancer 'Run-LocalAI.bat graph-index <dossier>'")
        return 2
    with open(GRAPH, encoding="utf-8-sig") as fh:
        g = json.load(fh)
    nodes, edges = g.get("nodes", []), g.get("edges", [])
    s = g.get("stats", {})
    print("=== Graphe GraphRAG local ===")
    print("  Construit le : %s" % g.get("built_at"))
    print("  Source       : %s" % g.get("source_dir"))
    print("  Moteur       : %s" % g.get("engine"))
    print("  Fichiers     : %s | chunks : %s | echecs : %s"
          % (s.get("files"), s.get("chunks"), s.get("echecs")))
    print("  Noeuds       : %d | Aretes : %d" % (len(nodes), len(edges)))
    print("  Aretes LLM   : %d | structurelles (imports) : %d"
          % (sum(1 for e in edges if e.get("kind") == "llm"),
             sum(1 for e in edges if e.get("kind") == "structural")))
    rels = {}
    for e in edges:
        rels[e.get("relation", "?")] = rels.get(e.get("relation", "?"), 0) + 1
    top = sorted(rels.items(), key=lambda kv: -kv[1])[:8]
    print("  Relations    : %s" % ", ".join("%s (%d)" % (k, v) for k, v in top))
    print("  Noeuds les plus connectes :")
    for n in nodes[:10]:
        print("    %-30s degre=%-4d mentions=%-4d type=%s"
              % (n.get("name"), n.get("degree", 0), n.get("mentions", 0), n.get("type")))
    return 0


def main():
    ap = argparse.ArgumentParser(description="GraphRAG local (extraction par LLM local)")
    ap.add_argument("mode", choices=["build", "show"])
    ap.add_argument("--input")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--model", default="local")
    ap.add_argument("--max-files", type=int, default=40)
    ap.add_argument("--max-chunks", type=int, default=24)
    ap.add_argument("--chunk-size", type=int, default=1200)
    ap.add_argument("--overlap", type=float, default=0.10)
    a = ap.parse_args()
    if a.mode == "show":
        return show()
    if not a.input:
        ap.error("--input est requis pour build")
    port = a.port or _ports()["llama"]
    try:
        return build(a.input, port, a.model, a.max_files, a.max_chunks, a.chunk_size, a.overlap)
    except Exception as exc:
        print("[graph] ERREUR : %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""

FAILOVER_SETTINGS_JSON = r"""{
  "listen_port": 8081,
  "primary":   {"name": "core-local", "base": "http://127.0.0.1:8080/v1"},
  "secondary": {"name": "vision-cpu", "base": "http://127.0.0.1:8095/v1", "model": "vlm"},
  "cloud": {
    "enabled": true,
    "base": "https://openrouter.ai/api/v1",
    "model": "openrouter/anthropic/claude-3.5-sonnet",
    "key_env": "OPENROUTER_API_KEY",
    "keys_file": "config/cloud-keys.env"
  },
  "buffered": {
    "models": ["localai", "localai-buffered", "agent", "cline"],
    "header": "x-localai-buffer",
    "always": false,
    "connect_timeout_s": 1.5,
    "read_timeout_s": 300,
    "alias_map": {
      "localai": "llama-3.2-1b-instruct",
      "localai-buffered": "llama-3.2-1b-instruct",
      "agent": "llama-3.2-1b-instruct",
      "cline": "llama-3.2-1b-instruct"
    }
  },
  "note": "Requetes bufferisees (stream + marqueur) : aucune coupure possible, failover local puis cloud."
}
"""

MCP_SETTINGS_JSON = r"""{
  "spec_version": "2024-11-05",
  "client": {
    "name": "localai-agent-hub",
    "version": "__VERSION__",
    "transports": ["stdio", "http"]
  },
  "servers": {
    "localai": {
      "enabled": true,
      "type": "stdio",
      "command": "runtime\\python\\python.exe",
      "args": ["scripts\\mcp_gateway.py", "serve"],
      "description": "Outils natifs LocalAI : RAG, vision, etat des services, VRAM, graphe"
    }
  },
  "tools": [
    {"name": "localai_rag_query", "server": "localai", "enabled": true,
     "description": "Recherche semantique dans l'index RAG local"},
    {"name": "localai_vision_caption", "server": "localai", "enabled": true,
     "description": "Description d'image par le moteur VLM local (llama-server --mmproj)"},
    {"name": "localai_status", "server": "localai", "enabled": true,
     "description": "Etat des services LocalAI (PID, ports, disponibilite)"},
    {"name": "localai_vram_status", "server": "localai", "enabled": true,
     "description": "VRAM totale/utilisee/libre, seuils et watchdog"},
    {"name": "localai_graph_show", "server": "localai", "enabled": true,
     "description": "Statistiques du graphe GraphRAG local (v1.6.0)"},
    {"name": "localai_semantic_probe", "server": "localai", "enabled": true,
     "description": "Sonde de l'accelerateur semantique DirectML/NPU (repli CPU)"}
  ]
}
"""

MCP_GATEWAY_PY = r"""# mcp_gateway.py - passerelle MCP (Model Context Protocol, spec 2024-11-05) - v1.5.0
# S'appuie sur le SDK officiel 'mcp' : fourni par l'extra 'litellm[proxy]' du Python
# embarque (constate : mcp 2.3.0) ou, a defaut, pose par l'installeur dans le prefixe
# isole runtime\mcp\packages. Aucune reimplementation maison du protocole.
# Modes : list | call | serve | selftest
import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MCP_PKGS = os.path.join(ROOT, "runtime", "mcp", "packages")
CONFIG = os.path.join(ROOT, "config", "mcp-settings.json")
RAG_DIR = os.path.join(ROOT, "runtime", "rag")
LOGS = os.path.join(ROOT, "logs")
SPEC_VERSION = "2024-11-05"
DEFAULT_PORTS = {"localai": 8080, "llama": 8090, "vision": 8095, "litellm": 4000,
                 "sd": 8092, "whisper": 8091, "tts": 8093, "embed": 8094}

if os.path.isdir(MCP_PKGS) and MCP_PKGS not in sys.path:
    sys.path.insert(0, MCP_PKGS)


def _log(msg):
    try:
        os.makedirs(LOGS, exist_ok=True)
        with open(os.path.join(LOGS, "mcp.log"), "a", encoding="utf-8") as fh:
            fh.write("[%s] %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except Exception:
        pass


def load_settings():
    try:
        with open(CONFIG, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception:
        return {"spec_version": SPEC_VERSION, "servers": {}, "tools": []}


def ports():
    p = dict(DEFAULT_PORTS)
    try:
        with open(os.path.join(ROOT, "data", "runtime.env"), encoding="utf-8-sig") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    k = k.strip().lower()
                    if k.endswith("_port"):
                        k = k[:-5]
                    if k in p and v.strip().isdigit():
                        p[k] = int(v.strip())
    except Exception:
        pass
    return p


def _http(url, payload=None, timeout=600):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def services():
    out = {}
    try:
        with open(os.path.join(ROOT, "data", "pids.txt"), encoding="utf-8-sig") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2:
                    out[parts[0]] = {"pid": int(parts[1])}
    except Exception:
        pass
    return out

# ---------------- Outils natifs LocalAI (spec MCP 2024-11-05) ----------------
TOOLS = [
    {"name": "localai_rag_query",
     "description": "Recherche semantique dans l'index RAG local (NumPy + embeddings llama.cpp).",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string", "description": "Requete en langage naturel"},
         "collection": {"type": "string", "description": "Collection (defaut: default)"},
         "topk": {"type": "integer", "description": "Nombre de resultats (defaut: 5)"}},
         "required": ["query"]}},
    {"name": "localai_vision_caption",
     "description": "Decrit une image locale via le moteur VLM (llama-server --mmproj).",
     "inputSchema": {"type": "object", "properties": {
         "image_path": {"type": "string"}, "prompt": {"type": "string"}},
         "required": ["image_path"]}},
    {"name": "localai_status",
     "description": "Etat des services LocalAI (PID, ports, disponibilite).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "localai_vram_status",
     "description": "VRAM totale/utilisee/libre, seuils et etat du watchdog.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "localai_graph_show",
     "description": "Statistiques du graphe GraphRAG local (v1.6.0).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "localai_semantic_probe",
     "description": "Sonde l'accelerateur semantique (DirectML/NPU ou repli CPU) : provider et latence.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def ensure_embed_server(port):
    try:
        _http("http://127.0.0.1:%d/health" % port, timeout=2)
        return None
    except Exception:
        pass
    exe = os.path.join(ROOT, "backends", "llama-cpp", "llama-server.exe")
    model = os.path.join(ROOT, "models", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
    if not (os.path.isfile(exe) and os.path.isfile(model)):
        raise RuntimeError("moteur/modele introuvable pour les embeddings")
    os.makedirs(LOGS, exist_ok=True)
    out = open(os.path.join(LOGS, "embed-server.log"), "ab")
    proc = subprocess.Popen([exe, "-m", model, "-ngl", "99", "--embeddings", "--pooling", "mean",
                             "--host", "127.0.0.1", "--port", str(port), "-c", "2048"],
                            cwd=os.path.dirname(exe), stdout=out, stderr=subprocess.STDOUT)
    with open(os.path.join(ROOT, "data", "pids.txt"), "a", encoding="utf-8") as fh:
        fh.write("embed-server %d\n" % proc.pid)
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            _http("http://127.0.0.1:%d/health" % port, timeout=2)
            return proc
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("serveur d'embeddings injoignable")

def tool_rag_query(args):
    import numpy as np
    collection = args.get("collection") or "default"
    port = int(ports()["embed"])
    topk = int(args.get("topk") or 5)
    vpath = os.path.join(RAG_DIR, "index-%s.npy" % collection)
    cpath = os.path.join(RAG_DIR, "chunks-%s.jsonl" % collection)
    if not os.path.isfile(vpath):
        return {"error": "index '%s' inexistant (Run-LocalAI.bat index <dossier>)" % collection}
    ensure_embed_server(port)
    V = np.load(vpath)
    chunks = []
    with open(cpath, encoding="utf-8-sig") as fh:
        for line in fh:
            if line.strip():
                chunks.append(json.loads(line))
    res = _http("http://127.0.0.1:%d/v1/embeddings" % port,
                {"input": [args.get("query", "")], "model": "local"})
    q = np.asarray(res["data"][0]["embedding"], dtype=np.float32)
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    qn = q / (np.linalg.norm(q) + 1e-9)
    sims = Vn @ qn
    order = np.argsort(-sims)[:max(1, topk)]
    out = []
    for idx in order:
        c = chunks[int(idx)]
        out.append({"score": round(float(sims[int(idx)]), 4), "source": c["source"],
                    "chunk": c["chunk"], "chars": c["chars"],
                    "meta": c.get("meta", {}), "text": c["text"][:400]})
    return {"collection": collection, "count": len(out), "results": out}


def tool_vision_caption(args):
    import base64
    path = args.get("image_path")
    if not path or not os.path.isfile(path):
        return {"error": "image introuvable : %s" % path}
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")
    prompt = args.get("prompt") or "Decris cette image en une phrase courte, en francais."
    payload = {"model": "vlm", "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/%s;base64,%s" % (ext, b64)}}]}],
        "max_tokens": 96, "temperature": 0}
    vp = ports()["vision"]
    res = _http("http://127.0.0.1:%d/v1/chat/completions" % vp, payload, timeout=900)
    return {"image": os.path.basename(path), "engine": "llama-server --mmproj (:%d)" % vp,
            "caption": res["choices"][0]["message"]["content"].strip()}

def _alive(pid):
    # Test de vie d'un PID portable : os.kill(pid, 0) leve WinError 87 sous Windows.
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    except Exception:
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False


def tool_status(args):
    p = ports()
    svc = services()
    for name in list(svc.keys()):
        svc[name]["alive"] = _alive(svc[name]["pid"])
    return {"services": svc, "ports": p}


def tool_vram(args):
    try:
        with open(os.path.join(ROOT, "data", "vram-status.json"), encoding="utf-8-sig") as fh:
            return json.load(fh)
    except Exception as exc:
        return {"error": "statut VRAM indisponible (%s)" % exc}


def tool_graph(args):
    path = os.path.join(ROOT, "runtime", "storage", "graph_db.json")
    if not os.path.isfile(path):
        return {"error": "graphe absent : Run-LocalAI.bat graph-index <dossier>"}
    with open(path, encoding="utf-8-sig") as fh:
        g = json.load(fh)
    nodes = g.get("nodes", [])
    return {"nodes": len(nodes), "edges": len(g.get("edges", [])),
            "built_at": g.get("built_at"), "source_dir": g.get("source_dir"),
            "engine": g.get("engine"),
            "top_hubs": sorted(({"id": n.get("id"), "degree": n.get("degree", 0)} for n in nodes),
                               key=lambda d: -d["degree"])[:8]}


def tool_semantic_probe(args):
    # Outil MCP LEGER execute sur l'accelerateur universel (DirectML/NPU, repli CPU).
    import importlib.util
    path = os.path.join(HERE, "onnx_provider.py")
    if not os.path.isfile(path):
        return {"error": "onnx_provider.py absent"}
    spec = importlib.util.spec_from_file_location("onnx_provider_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Accelerator().probe(2)


HANDLERS = {"localai_rag_query": tool_rag_query, "localai_vision_caption": tool_vision_caption,
            "localai_status": tool_status, "localai_vram_status": tool_vram,
            "localai_graph_show": tool_graph, "localai_semantic_probe": tool_semantic_probe}


def call_local(name, args):
    fn = HANDLERS.get(name)
    if not fn:
        return {"error": "outil inconnu : %s" % name}
    try:
        return fn(args or {})
    except Exception as exc:
        return {"error": "%s : %s" % (type(exc).__name__, exc)}

def build_server():
    # Serveur MCP local (spec 2024-11-05) : expose les outils natifs LocalAI en JSON-RPC 2.0.
    from mcp.server.mcpserver import MCPServer
    app = MCPServer("localai", instructions="Outils natifs du portage AiTron V3.")

    @app.tool(name="localai_rag_query",
              description="Recherche semantique dans l'index RAG local.")
    def localai_rag_query(query: str, collection: str = "default", topk: int = 5) -> dict:
        return tool_rag_query({"query": query, "collection": collection, "topk": topk})

    @app.tool(name="localai_vision_caption",
              description="Decrit une image locale via le moteur VLM (--mmproj).")
    def localai_vision_caption(image_path: str, prompt: str = "") -> dict:
        return tool_vision_caption({"image_path": image_path, "prompt": prompt})

    @app.tool(name="localai_status", description="Etat des services LocalAI (PID, ports).")
    def localai_status() -> dict:
        return tool_status({})

    @app.tool(name="localai_vram_status",
              description="VRAM totale/utilisee/libre, seuils et watchdog.")
    def localai_vram_status() -> dict:
        return tool_vram({})

    @app.tool(name="localai_graph_show",
              description="Statistiques du graphe GraphRAG local (v1.6.0).")
    def localai_graph_show() -> dict:
        return tool_graph({})

    @app.tool(name="localai_semantic_probe",
              description="Sonde l'accelerateur semantique (DirectML/NPU ou repli CPU).")
    def localai_semantic_probe() -> dict:
        return tool_semantic_probe({})

    return app


def _server_params(cfg):
    from mcp import StdioServerParameters
    cmd = cfg.get("command") or os.path.join("runtime", "python", "python.exe")
    if not os.path.isabs(cmd):
        cmd = os.path.join(ROOT, cmd)
    raw_args = cfg.get("args") or []
    args = []
    for a in raw_args:
        if os.path.isabs(a):
            args.append(a)
        elif os.path.exists(os.path.join(ROOT, a)) or a.lower().endswith((".py", ".json", ".bat", ".ps1")):
            args.append(os.path.join(ROOT, a))
        else:
            args.append(a)
    env = dict(os.environ)
    env.update(cfg.get("env") or {})
    return StdioServerParameters(command=cmd, args=args, env=env)


async def client_list(only=None):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    out = {}
    for name, cfg in (load_settings().get("servers") or {}).items():
        if only and name != only:
            continue
        if not cfg.get("enabled", True) or cfg.get("type", "stdio") != "stdio":
            out[name] = {"status": "ignore", "type": cfg.get("type", "stdio"), "tools": []}
            continue
        try:
            async with stdio_client(_server_params(cfg)) as (r, w):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    res = await session.list_tools()
                    out[name] = {"status": "up", "spec": SPEC_VERSION,
                                 "tools": [{"name": t.name,
                                            "description": (t.description or "").replace("\n", " ")[:110]}
                                           for t in res.tools]}
        except Exception as exc:
            out[name] = {"status": "erreur", "tools": [],
                         "error": "%s : %s" % (type(exc).__name__, exc)}
    return out


async def client_call(server_name, tool, args):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    cfg = (load_settings().get("servers") or {}).get(server_name)
    if not cfg:
        return {"error": "serveur MCP inconnu : %s" % server_name}
    async with stdio_client(_server_params(cfg)) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            res = await session.call_tool(tool, args or {})
            texts = []
            for c in (res.content or []):
                texts.append(getattr(c, "text", ""))
            return {"server": server_name, "tool": tool,
                    "isError": bool(getattr(res, "is_error", False)), "content": texts}

def selftest():
    print("=== selftest passerelle MCP (spec %s) ===" % SPEC_VERSION)
    try:
        import mcp
        print("  SDK mcp importe : %s" % os.path.dirname(os.path.dirname(os.path.abspath(mcp.__file__))))
    except Exception as exc:
        print("  ECHEC import SDK : %s" % exc)
        return 1
    try:
        from mcp.server.mcpserver import MCPServer  # noqa: F401
        from mcp import ClientSession  # noqa: F401
        from mcp.client.stdio import stdio_client  # noqa: F401
        print("  API serveur (MCPServer) + client (stdio) : OK")
    except Exception as exc:
        print("  ECHEC API : %s" % exc)
        return 1
    print("  outils declares : %d" % len(TOOLS))
    for t in TOOLS:
        print("    - %s" % t["name"])
    st = call_local("localai_status", {})
    print("  appel direct localai_status : %s"
          % ("OK (%d service(s))" % len(st.get("services", {})) if "services" in st else st))
    vr = call_local("localai_vram_status", {})
    print("  appel direct localai_vram_status : %s"
          % ("OK (%s Mo libres)" % vr.get("free_mb") if "free_mb" in vr else vr))
    res = asyncio.run(client_list("localai"))
    stat = {k: v.get("status") for k, v in res.items()}
    print("  client stdio sur 'localai' : %s" % json.dumps(stat))
    tools = []
    for v in res.values():
        tools.extend(t["name"] for t in v.get("tools", []))
    print("  outils vus par le client : %d %s" % (len(tools), sorted(tools)))
    ok = stat.get("localai") == "up" and len(tools) == len(TOOLS)
    print("  VERDICT : %s" % ("VERT" if ok else "A REVOIR"))
    _log("selftest MCP : %s (%d outils vus)" % ("VERT" if ok else "A REVOIR", len(tools)))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Passerelle MCP LocalAI (spec %s)" % SPEC_VERSION)
    ap.add_argument("mode", choices=["list", "call", "serve", "selftest", "tools", "settings"])
    ap.add_argument("--server", default="localai")
    ap.add_argument("--tool")
    ap.add_argument("--args", nargs="?", const="{}", default="{}")
    ap.add_argument("--args-file", dest="args_file",
                    help="fichier JSON contenant les arguments (evite les problemes de quoting shell)")
    a = ap.parse_args()
    if a.mode == "settings":
        print(json.dumps(load_settings(), ensure_ascii=False, indent=2))
        return 0
    if a.mode == "tools":
        print(json.dumps(TOOLS, ensure_ascii=False, indent=2))
        return 0
    if a.mode == "serve":
        build_server().run(transport="stdio")
        return 0
    if a.mode == "list":
        res = asyncio.run(client_list())
        total = sum(len(v.get("tools", [])) for v in res.values())
        print("Passerelle MCP LocalAI - spec %s" % SPEC_VERSION)
        print("Serveurs declares : %d | outils visibles : %d" % (len(res), total))
        for name, v in res.items():
            print("  - %-12s [%s] %d outil(s)" % (name, v.get("status"), len(v.get("tools", []))))
            for t in v.get("tools", []):
                print("      * %-24s %s" % (t["name"], t["description"]))
            if v.get("error"):
                print("      ! %s" % v["error"])
        return 0
    if a.mode == "call":
        if not a.tool:
            print("usage : call --server <nom> --tool <outil> [--args '<json>']")
            return 2
        raw = a.args
        if a.args_file:
            try:
                with open(a.args_file, encoding="utf-8-sig") as fh:
                    raw = fh.read()
            except Exception as exc:
                print("lecture des arguments impossible : %s" % exc)
                return 2
        try:
            payload = json.loads(raw or "{}")
        except Exception as exc:
            print("arguments JSON invalides : %s" % exc)
            return 2
        print(json.dumps(asyncio.run(client_call(a.server, a.tool, payload)),
                         ensure_ascii=False, indent=2))
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
"""

VRAM_STATUS_PS1 = r"""# vram_status.ps1 - etat VRAM + seuils + watchdog (v1.4.1)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$stPath = Join-Path $root 'data\vram-status.json'
$actPath = Join-Path $root 'data\vram-action.json'

$total = 0; $used = 0; $free = 0; $src = 'n/a'
try {
  $o = & nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader,nounits 2>$null | Select-Object -First 1
  if ($o) {
    $p = $o -split ','
    $total = [int]$p[0].Trim(); $used = [int]$p[1].Trim(); $free = [int]$p[2].Trim(); $src = 'nvidia-smi'
  }
} catch {}
if ($total -le 0) {
  try {
    $v = Get-CimInstance Win32_VideoController | Where-Object { $_.AdapterRAM -gt 0 } | Select-Object -First 1
    if ($v) { $total = [int]([math]::Round($v.AdapterRAM/1MB,0)); $used = 0; $free = $total; $src = 'wmi' }
  } catch {}
}

$alert = 15.0; $crit = 5.0; $recover = 20.0
if (Test-Path $stPath) {
  try {
    $j = Get-Content $stPath -Raw | ConvertFrom-Json
    if ($j.alert_pct) { $alert = [double]$j.alert_pct }
    if ($j.crit_pct) { $crit = [double]$j.crit_pct }
    if ($j.recover_pct) { $recover = [double]$j.recover_pct }
  } catch {}
}

Write-Host "=== Etat VRAM LocalAI (__VERSION__) ==="
if ($total -gt 0) {
  $freePct = [math]::Round(100.0 * $free / $total, 2)
  $state = 'ok'
  if ($freePct -lt $crit) { $state = 'CRITIQUE' } elseif ($freePct -lt $alert) { $state = 'ALERTE' }
  Write-Host ("  Source   : {0}" -f $src)
  Write-Host ("  Total    : {0} Mo" -f $total)
  Write-Host ("  Utilisee : {0} Mo" -f $used)
  Write-Host ("  Libre    : {0} Mo ({1} %)" -f $free, $freePct)
  Write-Host ("  Etat     : {0}" -f $state)
} else {
  Write-Host "  VRAM non detectee (GPU absent ou pilote manquant)"
}
Write-Host ("  Seuils   : alerte < {0} % ; critique < {1} % ; reprise > {2} %" -f $alert, $crit, $recover)
if (Test-Path $stPath) {
  try {
    $j = Get-Content $stPath -Raw | ConvertFrom-Json
    Write-Host ("  Watchdog : {0} (etat={1}, maj={2})" -f $j.watchdog, $j.state, $j.at)
  } catch {}
} else {
  Write-Host "  Watchdog : inactif (aucun statut : demarrez avec Run-LocalAI.bat start)"
}
if (Test-Path $actPath) {
  try {
    $a = Get-Content $actPath -Raw | ConvertFrom-Json
    Write-Host ("  Derniere action : {0} (applied={1}) - {2}" -f $a.action, $a.applied, $a.detail)
  } catch {}
}
exit 0
"""

ENGINE_SELECT_PS1 = r"""# engine_select.ps1 - bascule la variante active de llama.cpp (v1.3.0)
param(
  [Parameter(Mandatory=$true)][ValidateSet('cpu','vulkan','cuda','hip')][string]$Variant,
  [switch]$Quiet
)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$lc = Join-Path $root 'backends\llama-cpp'
$varDir = Join-Path $lc ('variants\' + $Variant)
if (-not (Test-Path $varDir)) { Write-Host ("[engine] variante '{0}' introuvable : {1}" -f $Variant, $varDir); exit 2 }
$keep = @('cloud-proxy.exe')
foreach ($pat in @('llama*.exe','llama*.dll','ggml*.dll','libomp.dll','mtmd.dll','cudart*.dll','cublas*.dll','nvrtc*.dll','LICENSE-LLVM-OpenMP','readme.txt')) {
  Get-ChildItem -Path $lc -Filter $pat -File -ErrorAction SilentlyContinue |
    Where-Object { $keep -notcontains $_.Name } | Remove-Item -Force -ErrorAction SilentlyContinue
}
Copy-Item -Path (Join-Path $varDir '*') -Destination $lc -Recurse -Force -ErrorAction SilentlyContinue
[IO.File]::WriteAllText((Join-Path $lc 'active.json'), (([ordered]@{ variant=$Variant; selected_at=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') } | ConvertTo-Json) + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
if (-not $Quiet) { Write-Host ("[engine] variante active -> {0}" -f $Variant) }
exit 0
"""

BENCH_PS1 = r"""# bench.ps1 - benchmark tokens/s du moteur actif (v1.3.0)
param([switch]$Cpu, [int]$Tokens = 128)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$lc = Join-Path $root 'backends\llama-cpp'
$exe = Join-Path $lc 'llama-server.exe'
$model = Join-Path $root 'models\Llama-3.2-1B-Instruct-Q4_K_M.gguf'
$profilePath = Join-Path $root 'config\hardware-profile.json'
$ngl = 0; $threads = 8; $ctx = 4096
if (Test-Path $profilePath) {
  try { $p = Get-Content $profilePath -Raw | ConvertFrom-Json; $ngl=[int]$p.params.ngl; $threads=[int]$p.params.threads; $ctx=[int]$p.params.ctx } catch {}
}
$label = 'gpu'
if ($Cpu) { $ngl = 0; $label = 'cpu' }
$port = 8097
try { $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $port); $l.Start(); $l.Stop() } catch { $port = 8096 }
$out = Join-Path $root 'logs\bench.out.log'; $err = Join-Path $root 'logs\bench.err.log'
$argLine = '-m "{0}" -ngl {1} --threads {2} -c {3} --host 127.0.0.1 --port {4}' -f $model, $ngl, $threads, $ctx, $port
$proc = Start-Process -FilePath $exe -ArgumentList $argLine -WorkingDirectory $lc -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
$ready = $false
for ($i=0; $i -lt 80; $i++) { Start-Sleep -Milliseconds 500; try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 ("http://127.0.0.1:{0}/health" -f $port); if ($r.StatusCode -eq 200) { $ready=$true; break } } catch {} }
if (-not $ready) {
  Write-Host "[bench] moteur non pret (voir logs\bench.err.log)"
  try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
  exit 1
}
$body = '{"messages":[{"role":"user","content":"Write a detailed paragraph about the history of computing."}],"max_tokens":' + $Tokens + ',"temperature":0.1}'
$t0 = Get-Date
try {
  $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 300 -Method Post -Uri ("http://127.0.0.1:{0}/v1/chat/completions" -f $port) -ContentType 'application/json' -Body $body
} catch { Write-Host ("[bench] echec inference : " + $_.Exception.Message); try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}; exit 1 }
$dt = ((Get-Date) - $t0).TotalSeconds
try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
$j = $resp.Content | ConvertFrom-Json
$t = $j.timings
$ntok = $j.usage.completion_tokens
$tps = $(if ($t -and $t.predicted_per_second) { [math]::Round($t.predicted_per_second,2) } else { [math]::Round($ntok / [math]::Max($dt,0.001), 2) })
Write-Host ("[bench] {0} : ngl={1} threads={2} ctx={3} -> {4} tok/s  (n={5}, {6:N2} s)" -f $label, $ngl, $threads, $ctx, $tps, $ntok, $dt)
$hist = Join-Path $root 'config\bench-history.jsonl'
$rec = [ordered]@{ at=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); label=$label; ngl=$ngl; threads=$threads; ctx=$ctx; tokens=$ntok; seconds=[math]::Round($dt,2); tok_per_s=$tps }
($rec | ConvertTo-Json -Compress) | Add-Content -Path $hist -Encoding UTF8
exit 0
"""

HW_PROFILE_PS1 = r"""# hw_profile.ps1 - detection materielle + calcul des parametres optimaux (v1.3.0)
param(
  [ValidateSet('soft','normal','hard','auto','custom')][string]$Profile = 'auto',
  [int]$Threads = 0,
  [int]$Ctx = 0,
  [int]$Ngl = -1,
  [string]$Model = '',
  [switch]$Write,
  [switch]$SelectEngine,
  [switch]$AsJson
)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$cfg  = Join-Path $root 'config'
$profilePath = Join-Path $cfg 'hardware-profile.json'
New-Item -ItemType Directory -Force -Path $cfg | Out-Null
$MB = 1048576

function Get-CpuInfo {
  $c = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $c) { return [pscustomobject]@{ name='unknown'; cores=1; threads=1 } }
  return [pscustomobject]@{ name=($c.Name -replace '\s+',' '); cores=[int]$c.NumberOfCores; threads=[int]$c.NumberOfLogicalProcessors }
}
function Get-RamGb {
  try { return [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1) } catch { return 0 }
}
function Get-NvidiaGpu {
  if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { return $null }
  try {
    $line = (& nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
    if (-not $line) { return $null }
    $p = $line -split ','
    if ($p.Count -lt 3) { return $null }
    return [pscustomobject]@{ vendor='NVIDIA'; name=$p[0].Trim(); vram_total_mb=[int]$p[1].Trim(); vram_free_mb=[int]$p[2].Trim(); detection_method='nvidia-smi' }
  } catch { return $null }
}
function Test-VulkanDll { return (Test-Path (Join-Path $env:SystemRoot 'System32\vulkan-1.dll')) }
function Get-GenericGpu {
  $vc = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch 'Microsoft Basic|Remote|Parsec' } | Select-Object -First 1
  if (-not $vc) { return $null }
  $vendor = 'Unknown'
  if ($vc.Name -match 'NVIDIA') { $vendor='NVIDIA' } elseif ($vc.Name -match 'AMD|Radeon|ATI') { $vendor='AMD' } elseif ($vc.Name -match 'Intel') { $vendor='Intel' }
  $vramMb = 0
  try {
    $key = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000'
    $q = (Get-ItemProperty -Path $key -Name 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue).'HardwareInformation.qwMemorySize'
    if ($q) { $vramMb = [int]([math]::Round(([int64]$q)/1MB,0)) }
  } catch {}
  if ($vramMb -le 0 -and $vc.AdapterRAM -gt 0) { $vramMb = [int]([math]::Round(([int64]$vc.AdapterRAM)/1MB,0)) }
  return [pscustomobject]@{ vendor=$vendor; name=$vc.Name; vram_total_mb=$vramMb; vram_free_mb=[int]($vramMb*0.85); detection_method='wmi/registry' }
}
function Get-ModelInfo([string]$modelPath) {
  $info = [pscustomobject]@{ path=$modelPath; bytes=[int64]0; n_layers=0; n_embd=0; n_vocab=0; n_ctx_train=0; n_kv_heads=0; key_len=0; val_len=0 }
  if (-not (Test-Path $modelPath)) { return $info }
  $info.bytes = (Get-Item $modelPath).Length
  $exe = Join-Path $root 'local-ai.exe'
  if (Test-Path $exe) {
    try {
      $out = (& $exe util gguf-info $modelPath 2>&1 | Out-String)
      $clean = $out -replace "\x1b\[[0-9;]*m", ''
      if ($clean -match 'BlockCount:(\d+)')            { $info.n_layers = [int]$matches[1] }
      if ($clean -match 'EmbeddingLength:(\d+)')       { $info.n_embd = [int]$matches[1] }
      if ($clean -match 'VocabularyLength:(\d+)')      { $info.n_vocab = [int]$matches[1] }
      if ($clean -match 'MaximumContextLength:(\d+)')  { $info.n_ctx_train = [int]$matches[1] }
      if ($clean -match 'AttentionHeadCountKV:(\d+)')  { $info.n_kv_heads = [int]$matches[1] }
      if ($clean -match 'AttentionKeyLength:(\d+)')    { $info.key_len = [int]$matches[1] }
      if ($clean -match 'AttentionValueLength:(\d+)')  { $info.val_len = [int]$matches[1] }
    } catch {}
  }
  return $info
}
function Get-EstimateNgl($gpu, $model, [int]$ctx, [int]$marginMb) {
  if (-not $gpu -or $gpu.vram_free_mb -le 0) { return 0 }
  $nLayers = [int]$model.n_layers
  if ($nLayers -le 0) { return 99 }
  $budget = ([int64]$gpu.vram_free_mb - [int64]$marginMb) * $MB
  if ($budget -le 0) { return 0 }
  $kv = [int64]0
  if ($model.n_kv_heads -gt 0 -and ($model.key_len + $model.val_len) -gt 0) {
    $kv = [int64]$nLayers * [int64]$model.n_kv_heads * [int64]($model.key_len + $model.val_len) * 2 * [int64]$ctx
  }
  $kvPerLayer = [int64]($kv / $nLayers)
  $layerBytes = [int64]($model.bytes / ($nLayers + 1))
  $perLayer = [int64](([double]$layerBytes + [double]$kvPerLayer) * 1.10)
  if ($perLayer -le 0) { return 0 }
  $nv = [math]::Max([int64]$model.n_vocab, [int64]32000)
  $compute = [int64]($nv * 8) + [int64]([int64]$ctx * [math]::Max([int64]$model.n_embd, 1) * 4)
  $fit = [int64](($budget - $compute) / $perLayer)
  if ($fit -ge $nLayers) { return 99 }
  if ($fit -lt 0) { return 0 }
  return [int]$fit
}

function Get-ProfileParams([string]$prof, $cpu, $gpu, $model, [int]$uThreads, [int]$uCtx, [int]$uNgl) {
  $threads = $cpu.threads; $ctx = 4096; $margin = 1024; $ngl = 0
  $hasGpu = ($null -ne $gpu -and $gpu.vram_free_mb -gt 0)
  $auto = 'soft'
  if ($hasGpu) { if ($gpu.vram_free_mb -ge 12000) { $auto='hard' } else { $auto='normal' } }
  if ($prof -eq 'auto') { $prof = $auto }
  switch ($prof) {
    'soft'   { $margin=1536; $ctx=4096; $threads=$cpu.cores;   $ngl = 0 }
    'normal' { $margin=1024; $ctx=4096; $threads=$cpu.threads; $ngl = Get-EstimateNgl $gpu $model 4096 1024 }
    'hard'   { $margin=768;  $ctx=4096; $threads=$cpu.threads; if ($hasGpu -and $gpu.vram_free_mb -ge 8192) { $ctx=8192 }; $ngl = Get-EstimateNgl $gpu $model $ctx 768 }
    'custom' { $margin=1024; if ($uThreads -gt 0) { $threads=$uThreads }; if ($uCtx -gt 0) { $ctx=$uCtx }
               if ($uNgl -ge 0) { $ngl=$uNgl } else { $ngl = Get-EstimateNgl $gpu $model $ctx 1024 } }
  }
  if (-not $hasGpu) { $ngl = 0 }
  if ($model.n_ctx_train -gt 0 -and $ctx -gt $model.n_ctx_train) { $ctx = [int]$model.n_ctx_train }
  $ctx = [int]([math]::Floor($ctx / 4096) * 4096)
  if ($ctx -lt 4096) { $ctx = 4096 }
  return [pscustomobject]@{ profile=$prof; auto_profile=$auto; margin_mb=$margin; threads=$threads; ctx=$ctx; ngl=$ngl }
}

# --- Detection ---
$cpu = Get-CpuInfo
$ramGb = Get-RamGb
$gpu = Get-NvidiaGpu
if (-not $gpu) { $gpu = Get-GenericGpu }
$vulkan = Test-VulkanDll

$cudaCustom = Test-Path (Join-Path $root 'backends\llama-cpp\variants\cuda\custom-build.txt')
$backend = 'cpu'
if ($gpu) {
  if ($gpu.vendor -eq 'NVIDIA') {
    if ($cudaCustom) { $backend = 'cuda' }
    elseif ($vulkan) { $backend = 'vulkan' }
    else { $backend = 'cuda' }
  }
  elseif ($gpu.vendor -eq 'AMD') { $backend = 'hip' }
  elseif ($vulkan) { $backend = 'vulkan' }
}

if (-not $Model) { $Model = Join-Path (Join-Path $root 'models') 'Llama-3.2-1B-Instruct-Q4_K_M.gguf' }
$mdl = Get-ModelInfo $Model
$params = Get-ProfileParams $Profile $cpu $gpu $mdl $Threads $Ctx $Ngl

$variantsDir = Join-Path $root 'backends\llama-cpp\variants'
$available = @()
foreach ($v in @('cpu','vulkan','cuda','hip')) { if (Test-Path (Join-Path $variantsDir $v)) { $available += $v } }
$selected = 'cpu'; $reason = 'repli CPU'
if ($available -contains $backend) { $selected = $backend; $reason = ("{0} via {1}" -f $gpu.vendor, $backend) }
elseif ($backend -ne 'cpu') { $reason = ("backend {0} indisponible (variante non installee) -> repli CPU" -f $backend) }
if ($selected -eq 'cuda' -and $cudaCustom) { $reason = "NVIDIA via cuda (build personnalise sm_52+ detecte)" }

# --- Securite VRAM ---
$needed = 0; $ratio = 1.0; $safety = 'n/a'
if ($params.ngl -gt 0 -and $mdl.n_layers -gt 0) {
  $per = [int64](([double]($mdl.bytes / ($mdl.n_layers + 1))) * 1.10)
  $needed = [int]([math]::Round(($per * [math]::Min([int]$params.ngl, [int]$mdl.n_layers)) / $MB, 0))
}
if ($needed -gt 0 -and $gpu) {
  $ratio = [math]::Round([double]$gpu.vram_free_mb / [double]$needed, 2)
  if ($ratio -ge 1.05) { $safety='optimal' } elseif ($ratio -ge 0.75) { $safety='possible' } else { $safety='experimental' }
  if ($ratio -lt 0.75) { $params.ngl = 0; $needed = 0; $safety = 'cpu-fallback' }
}

$gpuObj = $null
if ($gpu) { $gpuObj = [ordered]@{ vendor=$gpu.vendor; name=$gpu.name; vram_total_mb=$gpu.vram_total_mb; vram_free_mb=$gpu.vram_free_mb; backend=$backend; detection_method=$gpu.detection_method } }
$obj = [ordered]@{
  profile_version     = '1.3.0'
  detected_at         = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  cpu                 = [ordered]@{ name=$cpu.name; cores=$cpu.cores; threads=$cpu.threads }
  ram_gb              = $ramGb
  gpu                 = $gpuObj
  vulkan_dll_present  = $vulkan
  cuda_custom_build   = $cudaCustom
  recommended_profile = $params.auto_profile
  profile             = $params.profile
  params              = [ordered]@{ ngl=$params.ngl; threads=$params.threads; ctx=$params.ctx; margin_mb=$params.margin_mb }
  active_variant      = $selected
  variant_reason      = $reason
  variants_available  = $available
  model               = [ordered]@{ file=(Split-Path -Leaf $Model); bytes=$mdl.bytes; n_layers=$mdl.n_layers; n_embd=$mdl.n_embd; n_vocab=$mdl.n_vocab; n_ctx_train=$mdl.n_ctx_train }
  vram_needed_mb      = $needed
  vram_safety         = $safety
  vram_ratio          = $ratio
}
if ($Write) { [IO.File]::WriteAllText($profilePath, (($obj | ConvertTo-Json -Depth 8) + "`r`n"), (New-Object System.Text.UTF8Encoding($false))) }
if ($SelectEngine) {
  $sel = Join-Path $root 'scripts\engine_select.ps1'
  if (Test-Path $sel) { & $sel -Variant $selected -Quiet | Out-Null }
}
if ($AsJson) { $obj | ConvertTo-Json -Depth 8; exit 0 }
Write-Host "=== Profil materiel LocalAI (__VERSION__) ==="
Write-Host ("  CPU    : {0} ({1}c/{2}t)" -f $cpu.name, $cpu.cores, $cpu.threads)
if ($gpu) { Write-Host ("  GPU    : {0} {1} - {2} Mo libres - backend={3} [{4}]" -f $gpu.vendor, $gpu.name, $gpu.vram_free_mb, $backend, $gpu.detection_method) }
else { Write-Host "  GPU    : aucun detecte" }
Write-Host ("  Profil : {0} (recommande: {1})" -f $params.profile, $params.auto_profile)
Write-Host ("  Params : ngl={0} threads={1} ctx={2} marge={3} Mo" -f $params.ngl, $params.threads, $params.ctx, $params.margin_mb)
Write-Host ("  Variante active : {0}  ({1})" -f $selected, $reason)
Write-Host ("  Variantes dispo : {0}" -f ($(if ($available.Count) { $available -join ', ' } else { 'aucune' })))
if ($needed -gt 0) { Write-Host ("  VRAM   : besoin ~{0} Mo / libre {1} Mo (ratio {2}) -> {3}" -f $needed, $gpu.vram_free_mb, $ratio, $safety) }
exit 0
"""

AITRON_STATUS_PS1 = r"""# localai_status.ps1 - etat des services LocalAI (v1.3.0)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$pidFile = Join-Path $root 'data\pids.txt'
$envFile = Join-Path $root 'data\runtime.env'
$ports = @{ localai = 8080; llama = 8090; whisper = 8091; sd = 8092; tts = 8093; litellm = 4000; vision = 8095; failover = 8081 }
if (Test-Path $envFile) {
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^(LOCALAI|LLAMA|WHISPER|SD|TTS|VISION|FAILOVER|LITELLM)_PORT=(\d+)') {
      $k = $matches[1].ToLower()
      if     ($k -eq 'localai') { $ports.localai = [int]$matches[2] }
      elseif ($k -eq 'llama')   { $ports.llama   = [int]$matches[2] }
      elseif ($k -eq 'whisper') { $ports.whisper = [int]$matches[2] }
      elseif ($k -eq 'sd')      { $ports.sd      = [int]$matches[2] }
      elseif ($k -eq 'tts')     { $ports.tts     = [int]$matches[2] }
      elseif ($k -eq 'vision')  { $ports.vision  = [int]$matches[2] }
      elseif ($k -eq 'failover'){ $ports.failover = [int]$matches[2] }
      elseif ($k -eq 'litellm') { $ports.litellm = [int]$matches[2] }
    }
  }
}
Write-Host "=== Etat des services LocalAI __VERSION__ ==="
$tracked = @{}
if (Test-Path $pidFile) {
  foreach ($line in Get-Content $pidFile) {
    $parts = $line -split '\s+'
    if ($parts.Length -ge 2) { $tracked[$parts[0]] = [int]$parts[1] }
  }
}
foreach ($n in @('llama','whisper','sd','tts','vision','failover','local-ai','litellm')) {
  $procId = $tracked[$n]
  $alive = $false
  if ($procId) { $alive = [bool](Get-Process -Id $procId -ErrorAction SilentlyContinue) }
  $state = $(if ($alive) { "RUNNING (PID $procId)" } else { "stopped" })
  Write-Host ("  {0,-10} {1}" -f $n, $state)
}
Write-Host ""
Write-Host "Disponibilite des endpoints :"
$tests = @(
  @('LocalAI', "http://127.0.0.1:$($ports.localai)/v1/models"),
  @('LiteLLM', "http://127.0.0.1:$($ports.litellm)/health/liveliness"),
  @('Whisper', "http://127.0.0.1:$($ports.whisper)/"),
  @('Images',  "http://127.0.0.1:$($ports.sd)/"),
  @('TTS',     "http://127.0.0.1:$($ports.tts)/health"),
  @('Vision',  "http://127.0.0.1:$($ports.vision)/health"),
  @('Failover',"http://127.0.0.1:$($ports.failover)/health")
)
foreach ($t in $tests) {
  $ok = 'DOWN'
  try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $t[1]; if ($r.StatusCode -lt 500) { $ok = 'UP' } } catch {}
  Write-Host ("  {0,-10} {1}  ({2})" -f $t[0], $ok, $t[1])
}
Write-Host ""
Write-Host ("Ports resolus : localai={0} llama={1} whisper={2} sd={3} tts={4} litellm={5}" -f $ports.localai, $ports.llama, $ports.whisper, $ports.sd, $ports.tts, $ports.litellm)
Write-Host ""
$prof = Join-Path $root 'config\hardware-profile.json'
if (Test-Path $prof) {
  try {
    $hp = Get-Content $prof -Raw | ConvertFrom-Json
    $g = $(if ($hp.gpu) { "$($hp.gpu.vendor) $($hp.gpu.name)" } else { 'aucun (CPU)' })
    Write-Host ("Profil materiel : {0} (recommande {1}) - variante {2}" -f $hp.profile, $hp.recommended_profile, $hp.active_variant)
    Write-Host ("  -> {0} | ngl={1} threads={2} ctx={3} | VRAM {4}" -f $g, $hp.params.ngl, $hp.params.threads, $hp.params.ctx, $hp.vram_safety)
  } catch {}
}
Write-Host ("Fichier runtime : " + $envFile)
exit 0
"""

AITRON_UP_PS1 = r"""# localai_up.ps1 - demarre tous les services LocalAI (ports auto, PIDs traces)
param([switch]$NoLitellm, [switch]$NoEngines, [switch]$NoWatchdog, [switch]$NoPeers)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$logs = Join-Path $root 'logs'
$data = Join-Path $root 'data'
New-Item -ItemType Directory -Force -Path $logs, $data | Out-Null
$pidFile  = Join-Path $data 'pids.txt'
$envFile  = Join-Path $data 'runtime.env'

# Idempotence : arreter une instance deja en cours AVANT tout (y compris les
# services Python TTS/LiteLLM, identifies via data\pids.txt par stop.bat).
$stopBat = Join-Path $root 'stop.bat'
if (Test-Path $stopBat) {
  Write-Host "[Run-LocalAI] Arret d'une instance eventuelle avant demarrage ..."
  & cmd /c "`"$stopBat`" silent" | Out-Null
  Start-Sleep -Milliseconds 800
}
if (Test-Path $pidFile) { Remove-Item $pidFile -Force }

function Write-Step($m) { Write-Host ("[Run-LocalAI] " + $m) }
function Get-FreePort([int]$Start) {
  $p = $Start
  while ($p -lt ($Start + 200)) {
    try { $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $p); $l.Start(); $l.Stop(); return $p } catch { $p++ }
  }
  return $Start
}
function Start-Tracked($name, $exe, $argLine, $outLog) {
  $wd = Split-Path -Parent $exe
  if ($argLine -and $argLine.Trim().Length -gt 0) {
    $p = Start-Process -FilePath $exe -ArgumentList $argLine -WorkingDirectory $wd -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError ($outLog + '.err')
  } else {
    $p = Start-Process -FilePath $exe -WorkingDirectory $wd -WindowStyle Hidden -PassThru
  }
  Add-Content -Path $pidFile -Value ("{0} {1}" -f $name, $p.Id)
  return $p.Id
}
function Wait-Http($url, [int]$timeoutSec) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $url; if ($r.StatusCode -ge 200) { return $true } } catch {}
    Start-Sleep -Milliseconds 500
  }
  return $false
}

$P = @{}
$P.localai = Get-FreePort 8080
$P.llama   = Get-FreePort 8090
$P.whisper = Get-FreePort 8091
$P.sd      = Get-FreePort 8092
$P.tts     = Get-FreePort 8093
$P.litellm = Get-FreePort 4000
$P.vision  = Get-FreePort 8095
$P.failover = Get-FreePort 8081
Write-Step ("ports -> localai={0} llama={1} whisper={2} sd={3} tts={4} litellm={5} vision={6} failover={7}" -f $P.localai, $P.llama, $P.whisper, $P.sd, $P.tts, $P.litellm, $P.vision, $P.failover)

# Cles cloud (BYOK) : lues depuis config\cloud-keys.env
$env:AITRON_API_BASE = "http://127.0.0.1:$($P.localai)/v1"
$env:AITRON_LOCAL_KEY = "sk-local"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:AITRON_PORT     = "$($P.localai)"
$env:LLAMA_PORT       = "$($P.llama)"
$env:WHISPER_PORT     = "$($P.whisper)"
$env:SD_PORT          = "$($P.sd)"
$env:TTS_PORT         = "$($P.tts)"
$env:VISION_PORT      = "$($P.vision)"
$env:LITELLM_PORT     = "$($P.litellm)"
$keys = Join-Path $root 'config\cloud-keys.env'
$script:loaded = 0
foreach ($kf in @('config\cloud-keys.env', 'config\keys.env')) {
  $kp = Join-Path $root $kf
  if (Test-Path $kp) {
    Get-Content $kp | ForEach-Object {
      if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$') {
        Set-Item -Path ("env:" + $matches[1]) -Value $matches[2]
        $script:loaded++
      }
    }
  }
}
if ($script:loaded -gt 0) { Write-Step ("{0} cle(s) cloud chargee(s) (cloud-keys.env / keys.env)" -f $script:loaded) }
$env:AITRON_ROUTING_LOG = Join-Path $root 'logs\routing.jsonl'
$env:AITRON_ROUTE_LOCAL = 'local-llama'
$env:AITRON_ROUTE_WORDS = '3'
$env:AITRON_ROUTE_CONTEXT = '6000'
$models = Join-Path $root 'models'
$py = Join-Path $root 'runtime\python\python.exe'

# 0. Profil materiel (v1.3.0) : detection + variante + parametres optimaux
$profilePath = Join-Path $root 'config\hardware-profile.json'
$hwScript = Join-Path $root 'scripts\hw_profile.ps1'
if ((-not (Test-Path $profilePath)) -and (Test-Path $hwScript)) {
  Write-Step "Profil materiel absent : detection initiale ..."
  & $hwScript -Write -SelectEngine | Out-Null
}
$ngl = 0; $thr = [Environment]::ProcessorCount; $ctx = 4096; $variant = 'cpu'
if (Test-Path $profilePath) {
  try {
    $hp = Get-Content $profilePath -Raw | ConvertFrom-Json
    $ngl = [int]$hp.params.ngl
    if ([int]$hp.params.threads -gt 0) { $thr = [int]$hp.params.threads }
    if ([int]$hp.params.ctx -gt 0) { $ctx = [int]$hp.params.ctx }
    if ($hp.active_variant) { $variant = [string]$hp.active_variant }
    Write-Step ("profil={0} variante={1} ngl={2} threads={3} ctx={4}" -f $hp.profile, $variant, $ngl, $thr, $ctx)
  } catch { Write-Step "profil materiel illisible -> valeurs par defaut" }
}
$sel = Join-Path $root 'scripts\engine_select.ps1'
if ((Test-Path $sel) -and $variant) { & $sel -Variant $variant -Quiet | Out-Null }

# 1. Moteurs natifs (texte, audio, image)
if (-not $NoEngines) {
  $llamaExe = Join-Path $root 'backends\llama-cpp\llama-server.exe'
  $gguf = Join-Path $models 'Llama-3.2-1B-Instruct-Q4_K_M.gguf'
  # Speculative Decoding (v1.9.0) : si la paire texte+draft est presente, elle devient le
  # moteur principal -- le draft DOIT partager le tokenizer du principal (meme famille).
  $specMain = Join-Path $models 'qwen2.5-1.5b-instruct-q4_k_m.gguf'
  $specDraft = Join-Path $models 'qwen2.5-0.5b-instruct-q4_k_m.gguf'
  if ((Test-Path $specMain) -and (Test-Path $specDraft)) { $gguf = $specMain }
  if ((Test-Path $llamaExe) -and (Test-Path $gguf)) {
    $llamaArgs = @('-m', $gguf, '-ngl', "$ngl", '--threads', "$thr", '-c', "$ctx",
                   '--host', '127.0.0.1', '--port', "$($P.llama)")
    # Speculative Decoding TEXT-ONLY (v1.9.0) : paire principal/draft, garde VRAM comprise.
    # JAMAIS avec un projecteur multimodal (--mmproj) : limitation upstream de llama.cpp.
    $specScript = Join-Path $root 'scripts\spec_decoding.py'
    if ((Test-Path $specScript) -and (Test-Path $specDraft) -and (Test-Path $py)) {
      $sArgs = @($specScript, 'save', '--model', $gguf, '--draft', $specDraft)
      if ($env:AITRON_SPEC -eq '0') { $sArgs += '--off' }
      try {
        $specDec = & $py @sArgs | ConvertFrom-Json
        if ($specDec.enabled) {
          $llamaArgs += @('--model-draft', $specDraft, '--spec-draft-n-max', '8', '--spec-draft-n-min', '2')
          Write-Step ("decoding speculatif ACTIF (draft={0}, n-max=8 n-min=2)" -f (Split-Path -Leaf $specDraft))
        } else {
          Write-Step ("decoding speculatif inactif : {0}" -f $specDec.reason)
        }
      } catch { Write-Step "decoding speculatif : decision indisponible -> decoding standard" }
    }
    $jsonCmd = ([ordered]@{ exe = $llamaExe; args = $llamaArgs; workdir = (Split-Path -Parent $llamaExe) } |
      ConvertTo-Json -Depth 4)
    [IO.File]::WriteAllText((Join-Path $data 'llama-cmd.json'), $jsonCmd, (New-Object System.Text.UTF8Encoding($false)))
    $a = ($llamaArgs | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }) -join ' '
    $id = Start-Tracked 'llama' $llamaExe $a (Join-Path $logs 'llama-server.log')
    Write-Step ("llama-server PID={0} (:{1})" -f $id, $P.llama)
  } else { Write-Step "llama-server indisponible (binaire/modele absent) -> texte local indisponible" }

  $whisperExe = Join-Path $root 'backends\whisper-cpp\whisper-server.exe'
  $whisperModel = Join-Path $models 'ggml-base.bin'
  if ((Test-Path $whisperExe) -and (Test-Path $whisperModel)) {
    $a = '-m "{0}" --host 127.0.0.1 --port {1} --inference-path /v1/audio/transcriptions' -f $whisperModel, $P.whisper
    $id = Start-Tracked 'whisper' $whisperExe $a (Join-Path $logs 'whisper-server.log')
    Write-Step ("whisper-server PID={0} (:{1})" -f $id, $P.whisper)
  } else { Write-Step "whisper indisponible (binaire/modele absent)" }

  $sdExe = Join-Path $root 'backends\stable-diffusion\sd-server.exe'
  $sdModel = Join-Path $models 'sd_turbo-f16-q8_0.gguf'
  if (-not (Test-Path $sdModel)) { $sdModel = Join-Path $models 'sd-turbo.safetensors' }
  if ((Test-Path $sdExe) -and (Test-Path $sdModel)) {
    $sdExtra = ''
    if ((Split-Path -Leaf $sdModel) -match 'turbo') { $sdExtra = ' --steps 4' }
    $a = '-m "{0}" --listen-ip 127.0.0.1 --listen-port {1}{2}' -f $sdModel, $P.sd, $sdExtra
    $id = Start-Tracked 'sd' $sdExe $a (Join-Path $logs 'sd-server.log')
    Write-Step ("sd-server PID={0} (:{1}) modele={2}" -f $id, $P.sd, (Split-Path -Leaf $sdModel))
  } elseif (Test-Path $sdExe) { Write-Step "sd-server present, modele SD absent -> Run-LocalAI.bat pull sd-turbo-light" }

  # Moteur VISION (v1.5.0) : llama-server --mmproj <projecteur dedie> --------
  # Le fichier mmproj est indissociable du modele : les deux sont verifies ici.
  $vlm = $null
  foreach ($cand in @(@('qwen2-vl-2b', 'Qwen2-VL-2B-Instruct-Q4_K_M.gguf', 'mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf'),
                      @('smolvlm-500m', 'SmolVLM-500M-Instruct-Q8_0.gguf', 'mmproj-SmolVLM-500M-Instruct-Q8_0.gguf'))) {
    $mp = Join-Path $models $cand[1]
    $pp = Join-Path $models $cand[2]
    if ((Test-Path $mp) -and (Test-Path $pp)) { $vlm = $cand; break }
  }
  if ((Test-Path $llamaExe) -and $vlm) {
    $visModel = Join-Path $models $vlm[1]
    $visProj  = Join-Path $models $vlm[2]
    # Le chemin multimodal (mtmd) provoque un 'Vulkan device lost' sur Maxwell :
    # le moteur vision tourne donc en CPU par defaut (surchargeable par AITRON_VISION_NGL).
    $vngl = 0
    if ($env:AITRON_VISION_NGL) { try { $vngl = [int]$env:AITRON_VISION_NGL } catch { $vngl = 0 } }
    $visArgs = @('-m', $visModel, '--mmproj', $visProj, '-ngl', "$vngl", '--threads', "$thr",
                 '-c', '2048', '--host', '127.0.0.1', '--port', "$($P.vision)")
    $jsonV = ([ordered]@{ exe = $llamaExe; args = $visArgs; workdir = (Split-Path -Parent $llamaExe) } |
      ConvertTo-Json -Depth 4)
    [IO.File]::WriteAllText((Join-Path $data 'vision-cmd.json'), $jsonV, (New-Object System.Text.UTF8Encoding($false)))
    $av = ($visArgs | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }) -join ' '
    $id = Start-Tracked 'vision' $llamaExe $av (Join-Path $logs 'vision-server.log')
    Write-Step ("moteur VISION PID={0} (:{1}) modele={2} + mmproj={3} (ngl={4})" -f $id, $P.vision, $vlm[1], $vlm[2], $vngl)
  } else {
    Write-Step "moteur vision inactif (Run-LocalAI.bat pull qwen2-vl-2b pour l'activer)"
  }

  # Proxy FAILOVER SSE (v1.6.0) : bufferisation + bascule locale/cloud --------------
  $fov = Join-Path $root 'scripts\failover_proxy.py'
  if ((Test-Path $fov) -and (Test-Path $py)) {
    $env:AITRON_FAILOVER_PORT = "$($P.failover)"
    $id = Start-Tracked 'failover' $py ("`"{0}`"" -f $fov) (Join-Path $logs 'failover-proxy.log')
    Write-Step ("proxy FAILOVER SSE PID={0} (:{1}) - bufferisation + bascule locale/cloud" -f $id, $P.failover)
  }
}

# 2. TTS (kokoro via Python embarque)
$py = Join-Path $root 'runtime\python\python.exe'
$ttsServer = Join-Path $root 'backends\tts\tts_server.py'
$ttsModel  = Join-Path $models 'kokoro-v1.1-zh.onnx'
$ttsVoices = Join-Path $models 'voices-v1.1-zh.bin'
if ((Test-Path $py) -and (Test-Path $ttsServer) -and (Test-Path $ttsModel) -and (Test-Path $ttsVoices)) {
  $a = '"{0}" --port {1} --model "{2}" --voices "{3}"' -f $ttsServer, $P.tts, $ttsModel, $ttsVoices
  $id = Start-Tracked 'tts' $py $a (Join-Path $logs 'tts-server.log')
  Write-Step ("tts-server PID={0} (:{1})" -f $id, $P.tts)
}

# 3. Coeur LocalAI
$core = Join-Path $root 'local-ai.exe'
$bridge = Join-Path $root 'backends\llama-cpp\cloud-proxy.exe'
if (Test-Path $core) {
  $env:AITRON_EXTERNAL_GRPC_BACKENDS = "cloud-proxy:$bridge"
  $a = 'run --address 127.0.0.1:{0} --models-path "{1}" --backends-path "{2}" --external-grpc-backends "cloud-proxy:{3}"' -f $P.localai, $models, (Join-Path $root 'backends'), $bridge
  $id = Start-Tracked 'local-ai' $core $a (Join-Path $logs 'local-ai.out.log')
  Write-Step ("local-ai PID={0} (:{1})" -f $id, $P.localai)
  $ok = Wait-Http ("http://127.0.0.1:{0}/v1/models" -f $P.localai) 60
  Write-Step ("coeur LocalAI pret : {0}" -f $ok)
}

# 4. Gateway LiteLLM (routage local/externe)
if ((-not $NoLitellm) -and (Test-Path $py)) {
  $litellmCfg = Join-Path $root 'config\litellm-config.yaml'
  if (Test-Path $litellmCfg) {
    $env:PYTHONPATH = Join-Path $root 'config'
    $launcher = Join-Path $root 'config\litellm_launch.py'
    $a = '"{0}" --config "{1}" --host 127.0.0.1 --port {2}' -f $launcher, $litellmCfg, $P.litellm
    $id = Start-Tracked 'litellm' $py $a (Join-Path $logs 'litellm.log')
    Write-Step ("litellm PID={0} (:{1})" -f $id, $P.litellm)
    $ok2 = Wait-Http ("http://127.0.0.1:{0}/health/liveliness" -f $P.litellm) 90
    Write-Step ("gateway LiteLLM pret : {0}" -f $ok2)
  } else { Write-Step "config LiteLLM absente -> gateway non demarree" }
}

# 6. Watchdog VRAM (v1.4.1)
if (-not $NoWatchdog) {
  $wd = Join-Path $root 'scripts\vram_watchdog.py'
  if ((Test-Path $wd) -and (Test-Path $py)) {
    $wdArgs = '"{0}" --interval 2' -f $wd
    $id = Start-Tracked 'vram-watchdog' $py $wdArgs (Join-Path $logs 'vram-watchdog.log')
    Write-Step ("watchdog VRAM PID={0} (alerte<15%, critique<5%, reprise>20%)" -f $id)
  }
} else {
  Write-Step "watchdog VRAM desactive (--no-watchdog)"
}

# 7. Decouverte reseau des noeuds RPC federes (v2.1.0a)
if (-not $NoPeers) {
  $pd = Join-Path $root 'scripts\peer_discovery.py'
  if ((Test-Path $pd) -and (Test-Path $py)) {
    $pdArgs = '"{0}" announce --interval 20' -f $pd
    $idp = Start-Tracked 'peer-discovery' $py $pdArgs (Join-Path $logs 'peer-discovery.log')
    Write-Step ("decouverte RPC PID={0} (annonce UDP non invasive, port 47653)" -f $idp)
  }
} else {
  Write-Step "decouverte RPC desactivee (--no-peers)"
}

# 5. Fichier runtime.env + resume
@(
  "AITRON_PORT=$($P.localai)",
  "LLAMA_PORT=$($P.llama)",
  "WHISPER_PORT=$($P.whisper)",
  "SD_PORT=$($P.sd)",
  "TTS_PORT=$($P.tts)",
  "VISION_PORT=$($P.vision)",
  "FAILOVER_PORT=$($P.failover)",
  "LITELLM_PORT=$($P.litellm)",
  "PROFILE=$variant",
  "NGL=$ngl",
  "THREADS=$thr",
  "CTX=$ctx"
) | Set-Content -Path $envFile -Encoding ASCII

Write-Host ""
# Banniere internationalisee (v2.1.1) : config\lang.json puis i18n\<lang>.json (couche 2).
$lg = 'fr'
$lj = Join-Path $root 'config\lang.json'
if (Test-Path $lj) { try { $t = (Get-Content $lj -Raw | ConvertFrom-Json).lang; if ($t) { $lg = $t } } catch { } }
$env:AITRON_LANG = $lg
$btitle = 'AiTron - portage Windows natif'
$ij = Join-Path $root ('i18n\{0}.json' -f $lg)
if (Test-Path $ij) { try { $t = (Get-Content $ij -Raw | ConvertFrom-Json).banner_title; if ($t) { $btitle = $t } } catch { } }
Write-Host ("=== {0} (__VERSION__) ===" -f $btitle)
Write-Host ("  API AiTron    : http://127.0.0.1:{0}/v1" -f $P.localai)
Write-Host ("  Gateway LiteLLM: http://127.0.0.1:{0}/v1" -f $P.litellm)
Write-Host ("  Whisper (STT)  : http://127.0.0.1:{0}/v1/audio/transcriptions" -f $P.whisper)
Write-Host ("  Images         : http://127.0.0.1:{0}/v1/images/generations" -f $P.sd)
Write-Host ("  TTS            : http://127.0.0.1:{0}/v1/audio/speech" -f $P.tts)
if ($vlm) { Write-Host ("  Vision (VLM)   : http://127.0.0.1:{0}/v1/chat/completions  [{1} + mmproj]" -f $P.vision, $vlm[0]) }
Write-Host ("  Arret          : Run-LocalAI.bat stop")
exit 0
"""

RUN_AITRON_BAT = r"""@echo off
rem Alignment de la page de code Windows : evite la corruption des accents (v2.1.1)
chcp 65001 >nul 2>&1
rem Run-LocalAI.bat - CLI wrapper principal (v1.2.0)
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "SCRIPTS=%ROOT%\scripts"
set "PS=-NoProfile -ExecutionPolicy Bypass -File"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

rem -- i18n (v2.1.1) : chargement DYNAMIQUE des messages selon la langue active ---------
rem Priorite : AITRON_LANG -> config\lang.json -> "fr" (implemente dans i18n.py).
set "LG="
rem v3.1.0 (D1) : AUCUN fichier temporaire partage. Mesure : %%RANDOM%% renvoie la MEME valeur a
rem des lancements simultanes (1 valeur distincte sur 8), donc un nom "unique" par RANDOM ne
rem suffit pas ; l'ancien data\lang.tmp unique provoquait "fichier utilise par un autre processus".
rem 'for /f usebackq' + 'cmd /d /c ""exe" "arg""' (double guillemetage) lit la sortie directement.
if exist "%SCRIPTS%\i18n.py" if exist "%ROOT%\runtime\python\python.exe" (
  for /f "usebackq delims=" %%L in (`cmd /d /c ""%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" get" 2^>nul`) do set "LG=%%L"
)
if not defined LG set "LG=fr"
if exist "%ROOT%\i18n\_!LG!.bat" call "%ROOT%\i18n\_!LG!.bat"
rem Repli de securite si les fichiers de messages sont absents (aucun plantage).
if not defined MSG_HELP_COUNT (
  set "MSG_HELP_COUNT=01"
  set "MSG_HELP_01=  (messages indisponibles : lancez Run-LocalAI.bat i18n-test)"
)
if not defined MSG_MSG_UNKNOWN set "MSG_MSG_UNKNOWN=[Run-LocalAI] Commande inconnue :"
if not defined MSG_MSG_HELP_TIP set "MSG_MSG_HELP_TIP="
set "AITRON_LANG=!LG!"

set "CMD=%~1"
if "%CMD%"=="" set "CMD=help"

if /I "%CMD%"=="start"    goto do_start
if /I "%CMD%"=="stop"     goto do_stop
if /I "%CMD%"=="status"   goto do_status
if /I "%CMD%"=="pull"     goto do_pull
if /I "%CMD%"=="list"     goto do_list
if /I "%CMD%"=="backends" goto do_backends
if /I "%CMD%"=="profile"     goto do_profile
if /I "%CMD%"=="optimize"    goto do_optimize
if /I "%CMD%"=="benchmark"   goto do_benchmark
if /I "%CMD%"=="set-profile" goto do_setprofile
if /I "%CMD%"=="index"      goto do_index
if /I "%CMD%"=="rag-query"  goto do_ragquery
if /I "%CMD%"=="proxy-logs" goto do_proxylogs
if /I "%CMD%"=="key-set"    goto do_keyset
if /I "%CMD%"=="vram-status" goto do_vramstatus
if /I "%CMD%"=="mcp-list"  goto do_mcplist
if /I "%CMD%"=="mcp-call"  goto do_mcpcall
if /I "%CMD%"=="mcp-test"  goto do_mcptest
if /I "%CMD%"=="graph-index" goto do_graphindex
if /I "%CMD%"=="graph-show"  goto do_graphshow
if /I "%CMD%"=="quantize"  goto do_quantize
if /I "%CMD%"=="privacy-test"   goto do_privacytest
if /I "%CMD%"=="privacy-levels" goto do_privacylevels
if /I "%CMD%"=="hardware-status" goto do_hwstatus
if /I "%CMD%"=="npu-probe"  goto do_npuprobe
if /I "%CMD%"=="spec-status" goto do_specstatus
if /I "%CMD%"=="spec-test"   goto do_spectest
if /I "%CMD%"=="vault-status" goto do_vaultstatus
if /I "%CMD%"=="vault-seal"   goto do_vaultseal
if /I "%CMD%"=="vault-unseal" goto do_vaultunseal
if /I "%CMD%"=="vault-test"   goto do_vaulttest
if /I "%CMD%"=="learn-profile"  goto do_learnprofile
if /I "%CMD%"=="profile-status" goto do_profilestatus
if /I "%CMD%"=="profile-observe" goto do_profileobserve
if /I "%CMD%"=="reset-profile" goto do_resetprofile
if /I "%CMD%"=="peer-status"  goto do_peerstatus
if /I "%CMD%"=="peer-scan"    goto do_peerscan
if /I "%CMD%"=="peer-test"    goto do_peertest
if /I "%CMD%"=="peer-rpc-arg" goto do_peerrpcarg
if /I "%CMD%"=="lang"        goto do_lang
if /I "%CMD%"=="i18n-status" goto do_i18nstatus
if /I "%CMD%"=="i18n-test"   goto do_i18ntest
if /I "%CMD%"=="help"     goto do_help
if /I "%CMD%"=="-h"       goto do_help
if /I "%CMD%"=="--help"   goto do_help

echo !MSG_MSG_UNKNOWN! %CMD%
echo.
goto do_help

:do_start
set "NW="
set "NP="
for %%A in (%*) do (
  if /I "%%A"=="--no-watchdog" set "NW=-NoWatchdog"
  if /I "%%A"=="--no-pii-filter" set "NP=1"
)
if defined NP (
  echo [Run-LocalAI] filtre de confidentialite PII desactive pour cette session.
  set "AITRON_PII_FILTER=0"
)
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run powershell %PS% "%SCRIPTS%\localai_up.ps1" !NW!
exit /b %ERRORLEVEL%

:do_privacytest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%ROOT%\config\pii_filter.py" test %2 %3
exit /b %ERRORLEVEL%

:do_privacylevels
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%ROOT%\config\pii_filter.py" levels
exit /b %ERRORLEVEL%

:do_hwstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\onnx_provider.py" hardware
exit /b %ERRORLEVEL%

:do_npuprobe
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\onnx_provider.py" probe %2 %3
exit /b %ERRORLEVEL%

:do_specstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\spec_decoding.py" status
exit /b %ERRORLEVEL%

:do_spectest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\spec_decoding.py" check %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:do_vaultstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\vault.py" status
exit /b %ERRORLEVEL%

:do_vaultseal
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\vault.py" seal
exit /b %ERRORLEVEL%

:do_vaultunseal
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\vault.py" unseal
exit /b %ERRORLEVEL%

:do_vaulttest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\vault.py" selftest
exit /b %ERRORLEVEL%

:do_learnprofile
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\learn_profile.py" analyze %2 %3
exit /b %ERRORLEVEL%

:do_profilestatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\learn_profile.py" status
exit /b %ERRORLEVEL%

:do_profileobserve
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\learn_profile.py" observe
exit /b %ERRORLEVEL%

:do_resetprofile
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\learn_profile.py" reset %2 %3
exit /b %ERRORLEVEL%

:do_peerstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\peer_discovery.py" status
exit /b %ERRORLEVEL%

:do_peerscan
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\peer_discovery.py" scan %2 %3
exit /b %ERRORLEVEL%

:do_peertest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\peer_discovery.py" selftest
exit /b %ERRORLEVEL%

:do_peerrpcarg
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\peer_discovery.py" rpc-arg
exit /b %ERRORLEVEL%

:do_lang
if /I "%~2"=="list" (
  "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" list
  exit /b %ERRORLEVEL%
)
if "%~2"=="" (
  "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" status
  exit /b %ERRORLEVEL%
)
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" set %~2
exit /b %ERRORLEVEL%

:do_i18nstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" status
exit /b %ERRORLEVEL%

:do_i18ntest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" selftest
exit /b %ERRORLEVEL%

:do_vramstatus
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run powershell %PS% "%SCRIPTS%\vram_status.ps1"
exit /b %ERRORLEVEL%

:do_mcplist
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\mcp_gateway.py" list
exit /b %ERRORLEVEL%

:do_mcpcall
if "%~4"=="" (
  "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\mcp_gateway.py" call --server %2 --tool %3
) else (
  "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\mcp_gateway.py" call --server %2 --tool %3 --args %4 %5 %6 %7 %8 %9
)
exit /b %ERRORLEVEL%

:do_mcptest
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\mcp_gateway.py" selftest
exit /b %ERRORLEVEL%

:do_graphindex
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat graph-index ^<dossier^>
  exit /b 2
)
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\graph_rag.py" build --input "%~2" %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:do_graphshow
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\graph_rag.py" show
exit /b %ERRORLEVEL%

:do_quantize
if /I "%~2"=="list" (
  "%ROOT%\runtime\python\python.exe" "%SCRIPTS%\quantize_model.py" list
  exit /b %ERRORLEVEL%
)
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat quantize ^<modele_f16.gguf^> ^<type^>  [--out chemin] [--async]
  echo [Run-LocalAI] exemples : quantize models\modele-f16.gguf Q4_K_M
  echo [Run-LocalAI]            quantize list   (types supportes + sources detectees)
  exit /b 2
)
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\quantize_model.py" run "%~2" %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%

:do_stop
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run cmd /d /c ""%ROOT%\stop.bat""
exit /b %ERRORLEVEL%

:do_status
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run powershell %PS% "%SCRIPTS%\localai_status.ps1"
exit /b %ERRORLEVEL%

:do_pull
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat pull ^<model-id^>
  echo [Run-LocalAI] ids disponibles : Run-LocalAI.bat list
  exit /b 2
)
powershell %PS% "%SCRIPTS%\model_manager.ps1" pull "%~2"
exit /b %ERRORLEVEL%

:do_list
powershell %PS% "%SCRIPTS%\model_manager.ps1" list
exit /b %ERRORLEVEL%

:do_backends
echo !MSG_MSG_BACKENDS_HDR! %ROOT%\backends :
for /d %%D in ("%ROOT%\backends\*") do (
  set "HASEXE="
  for %%F in ("%%D\*.exe") do set "HASEXE=1"
  for %%F in ("%%D\*.py") do set "HASEXE=1"
  if defined HASEXE (echo   [OK] %%~nxD) else (echo   [--] %%~nxD)
)
echo.
echo !MSG_MSG_BACKENDS_N1!
echo !MSG_MSG_BACKENDS_N2!
exit /b 0

:do_profile
"%ROOT%\runtime\python\python.exe" "%SCRIPTS%\i18n.py" run powershell %PS% "%SCRIPTS%\hw_profile.ps1"
exit /b %ERRORLEVEL%

:do_optimize
echo [Run-LocalAI] Recalcul du profil materiel et des parametres optimaux ...
powershell %PS% "%SCRIPTS%\hw_profile.ps1" -Write -SelectEngine
exit /b %ERRORLEVEL%

:do_benchmark
if /I "%~2"=="cpu" goto do_bench_cpu
powershell %PS% "%SCRIPTS%\bench.ps1"
exit /b %ERRORLEVEL%

:do_bench_cpu
powershell %PS% "%SCRIPTS%\bench.ps1" -Cpu
exit /b %ERRORLEVEL%

:do_setprofile
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat set-profile ^<soft^|normal^|hard^|auto^|custom^>
  exit /b 2
)
powershell %PS% "%SCRIPTS%\hw_profile.ps1" -Profile "%~2" -Write -SelectEngine
exit /b %ERRORLEVEL%

:do_index
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat index ^<dossier^> [collection]
  exit /b 2
)
set "COL=%~3"
if "%COL%"=="" set "COL=default"
if not exist "%ROOT%\runtime\python\python.exe" (
  echo [Run-LocalAI] Python embarque absent : relancez install_localai_win.py
  exit /b 3
)
echo [Run-LocalAI] indexation de "%~2" (collection %COL%) ...
"%ROOT%\runtime\python\python.exe" "%ROOT%\scripts\rag_ingest.py" --input "%~2" --collection "%COL%"
exit /b %ERRORLEVEL%

:do_ragquery
if "%~2"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat rag-query ^<texte de recherche^>
  exit /b 2
)
rem v3.1.0 (D10) : requete entre guillemets ou en mots separes (shift + %%~1, sans for /f).
set "QRY="
shift
:rq_loop
if "%~1"=="" goto rq_go
set "QRY=!QRY! %~1"
shift
goto rq_loop
:rq_go
set "QRY=!QRY:~1!"
set "QRY=!QRY:"=!"
"%ROOT%\runtime\python\python.exe" "%ROOT%\scripts\rag_ingest.py" --query "!QRY!"
exit /b %ERRORLEVEL%

:do_proxylogs
powershell %PS% "%SCRIPTS%\proxy_logs.ps1"
exit /b %ERRORLEVEL%

:do_keyset
if "%~3"=="" (
  echo [Run-LocalAI] usage : Run-LocalAI.bat key-set ^<provider^> ^<valeur^>
  echo               provider : openrouter ^| openai ^| anthropic ^| deepseek
  exit /b 2
)
powershell %PS% "%SCRIPTS%\key_set.ps1" -Provider "%~2" -Value "%~3%"
exit /b %ERRORLEVEL%

:do_help
echo ===============================================================================
echo  !MSG_MSG_HELP_HEADER! (__VERSION__)
echo ===============================================================================
echo.
rem Aide internationalisee : les lignes viennent de i18n\_<lang>.bat (v2.1.1).
set /a HI=1
:loop_help
set "HK=0!HI!"
set "HK=!HK:~-2!"
if not defined MSG_HELP_!HK! goto end_help
call set "HL=%%MSG_HELP_!HK!%%"
echo(!HL!
set /a HI+=1
goto loop_help
:end_help
echo.
echo  !MSG_MSG_HELP_TIP!
exit /b 0
"""

DOWNLOAD_BAT = r"""@echo off
rem download_model.bat - Telecharge un modele du catalogue (Model Manager).
rem Usage : download_model.bat [id]     (defaut : llama-3.2-1b-instruct)
setlocal
cd /d "%~dp0"
set "ID=%~1"
if "%ID%"=="" set "ID=llama-3.2-1b-instruct"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\model_manager.ps1" pull "%ID%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo [LocalAI] Echec (code %RC%). Voir "Run-LocalAI.bat list".
endlocal
exit /b %RC%
"""

def _sha256(path):
    h = _hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def _ensure_tree(root):
    parts = ["", "backends", _os.path.join("backends", "llama-cpp"), "models",
             "config", "configuration", "logs", "data", "backends-system"]
    for sub in parts:
        _os.makedirs(_os.path.join(root, sub), exist_ok=True)


def _write_text(path, content, log=None):
    _os.makedirs(_os.path.dirname(path), exist_ok=True)
    data = content.replace("__VERSION__", "v" + __VERSION__).replace("\r\n", "\n").replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(data)
    if log:
        log.info("  + ecrit %s (%d octets)" % (path, len(data)))


def _download(url, dest, expected_sha, log):
    _os.makedirs(_os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    req = _urlreq.Request(url, headers={"User-Agent": "AiTron V3-Installer/1.1"})
    with _urlreq.urlopen(req, timeout=180) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        last = 0.0
        while True:
            buf = resp.read(1048576)
            if not buf:
                break
            out.write(buf)
            got += len(buf)
            now = _time.time()
            if log and (now - last) >= 3.0:
                last = now
                if total:
                    log.info("  ... %d/%d Mo (%.0f%%)" % (got // 1048576, total // 1048576, 100.0 * got / total))
                else:
                    log.info("  ... %d Mo" % (got // 1048576))
    if expected_sha:
        actual = _sha256(tmp)
        if actual.lower() != expected_sha.lower():
            try:
                _os.remove(tmp)
            except OSError:
                pass
            raise RuntimeError("SHA-256 invalide pour %s : attendu %s, obtenu %s" % (url, expected_sha, actual))
    _os.replace(tmp, dest)
    if log:
        log.ok("  telecharge %s (%d octets, SHA-256 verifie)" % (dest, _os.path.getsize(dest)))
    return dest


def _extract_zip(zip_path, dest, log):
    _os.makedirs(dest, exist_ok=True)
    with _zipfile.ZipFile(zip_path) as zf:
        broken = zf.testzip()
        if broken is not None:
            raise RuntimeError("Archive ZIP corrompue (entree fautive : %s)" % broken)
        for member in zf.namelist():
            zf.extract(member, dest)
    if log:
        log.info("  extrait %s -> %s" % (zip_path, dest))


def _copy_engine(src_dir, dst_dir, log):
    count = 0
    for name in _os.listdir(src_dir):
        src = _os.path.join(src_dir, name)
        if _os.path.isfile(src):
            _shutil.copy2(src, _os.path.join(dst_dir, name))
            count += 1
    if log:
        log.info("  moteur llama.cpp : %d fichiers copies depuis %s" % (count, src_dir))
    return count


def _enable_packages_pth(dst, log=None):
    # Ajoute '..\\packages' au chemin d'import du Python embarque (mode isole ._pth)
    pth = _os.path.join(dst, "python311._pth")
    lines = [
        "python311.zip",
        ".",
        "Lib\\site-packages",
        "..\\packages",
        "import site",
    ]
    try:
        with open(pth, "w", encoding="ascii") as fh:
            fh.write("\n".join(lines) + "\n")
        if log:
            log.info("  python311._pth mis a jour (..\\packages)")
    except Exception as exc:
        if log:
            log.warn("  python311._pth : %s" % exc)


def _copy_tree(src, dst, log):
    if _os.path.isdir(dst):
        _shutil.rmtree(dst, ignore_errors=True)
    _os.makedirs(_os.path.dirname(dst), exist_ok=True)
    _shutil.copytree(src, dst)
    if log:
        log.info("  arborescence copiee : %s -> %s" % (src, dst))


def _flatten_release(dst):
    rel = _os.path.join(dst, "Release")
    if _os.path.isdir(rel):
        for name in _os.listdir(rel):
            _shutil.move(_os.path.join(rel, name), _os.path.join(dst, name))
        _shutil.rmtree(rel, ignore_errors=True)


def deploy_python(root, sources, opts, log):
    """Python embarque (runtime\\python) -- unique usage : LiteLLM + TTS."""
    dst = _os.path.join(root, "runtime", "python")
    src = sources.get("python_runtime")
    if src and _os.path.isfile(_os.path.join(src, "python.exe")):
        _copy_tree(src, dst, log)
        _enable_packages_pth(dst, log)
        log.ok("Runtime Python embarque copie depuis %s" % src)
        return dst
    if opts.get("skip_python"):
        log.warn("Python embarque ignore (--skip-python).")
        return None
    _os.makedirs(dst, exist_ok=True)
    zp = _os.path.join(opts["cache"], PYTHON_EMBED_FILE)
    if not _os.path.isfile(zp):
        _download(PYTHON_EMBED_URL.format(version="3.11.9"), zp, PYTHON_EMBED_SHA256, log)
    _extract_zip(zp, dst, log)
    with open(_os.path.join(dst, "python311._pth"), "w", encoding="ascii") as fh:
        fh.write("python311.zip\n.\nLib\\site-packages\nimport site\n")
    _os.makedirs(_os.path.join(dst, "Lib", "site-packages"), exist_ok=True)
    gp = _os.path.join(opts["cache"], GET_PIP_FILE)
    if not _os.path.isfile(gp):
        _download(GET_PIP_URL, gp, None, log)
    py = _os.path.join(dst, "python.exe")
    log.info("  bootstrap pip + litellm (peut prendre plusieurs minutes) ...")
    _subprocess.run([py, gp, "--no-warn-script-location"], check=False)
    _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                     "litellm[proxy]==%s" % LITELLM_VERSION], check=False)
    _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                     "kokoro-onnx", "soundfile"], check=False)
    log.ok("Runtime Python embarque installe (LiteLLM + kokoro).")
    return dst


def _rmtree(path):
    if _os.path.isdir(path):
        _shutil.rmtree(path, ignore_errors=True)



def deploy_whisper(root, sources, opts, log):
    dst = _os.path.join(root, "backends", "whisper-cpp")
    _os.makedirs(dst, exist_ok=True)
    src = sources.get("whisper_dir")
    if src and _os.path.isdir(src):
        _copy_engine(src, dst, log)
    if src and _os.path.isdir(src):
        _flatten_release(dst)
    if not _os.path.isfile(_os.path.join(dst, "whisper-server.exe")):
        zp = _os.path.join(opts["cache"], WHISPER_CPP_FILE)
        if not _os.path.isfile(zp):
            _download(WHISPER_CPP_URL, zp, WHISPER_CPP_SHA256, log)
        _extract_zip(zp, dst, log)
        _flatten_release(dst)
    model = _os.path.join(root, "models", WHISPER_MODEL_FILE)
    if not _os.path.isfile(model):
        msrc = sources.get("whisper_model")
        if msrc and _os.path.isfile(msrc):
            _shutil.copy2(msrc, model)
        elif not opts.get("skip_models"):
            _download(WHISPER_MODEL_URL, model, WHISPER_MODEL_SHA256, log)
    _write_text(_os.path.join(dst, "README.txt"), WHISPER_README, log)
    log.ok("Backend whisper.cpp (STT) pret : %s" % dst)
    return dst


def deploy_sd(root, sources, opts, log):
    dst = _os.path.join(root, "backends", "stable-diffusion")
    _os.makedirs(dst, exist_ok=True)
    src = sources.get("sd_dir")
    if src and _os.path.isdir(src):
        _copy_engine(src, dst, log)
    if not _os.path.isfile(_os.path.join(dst, "sd-server.exe")):
        zp = _os.path.join(opts["cache"], SD_CPP_FILE)
        if not _os.path.isfile(zp):
            _download(SD_CPP_URL, zp, SD_CPP_SHA256, log)
        _extract_zip(zp, dst, log)
    # Variante GPU (CUDA) optionnelle : installee pour substitution ulterieure.
    cu = sources.get("sd_cuda_dir")
    if cu and _os.path.isdir(cu):
        vd = _os.path.join(dst, "variants", "cuda")
        if not _os.path.isfile(_os.path.join(vd, "sd-server.exe")):
            _os.makedirs(vd, exist_ok=True)
            _copy_engine(cu, vd, log)
            log.ok("  variante SD 'cuda' installee (non verifiee en runtime : modele SD absent)")
    _write_text(_os.path.join(dst, "README.txt"), SD_README, log)
    log.ok("Backend stable-diffusion.cpp (image) pret : %s" % dst)
    return dst


def deploy_tts(root, sources, opts, log):
    dst = _os.path.join(root, "backends", "tts")
    _os.makedirs(dst, exist_ok=True)
    _write_text(_os.path.join(dst, "tts_server.py"), TTS_SERVER_PY, log)
    pairs = (
        (KOKORO_MODEL_FILE, KOKORO_BASE_URL + KOKORO_MODEL_FILE, KOKORO_MODEL_SHA256, "kokoro_model"),
        (KOKORO_VOICES_FILE, KOKORO_BASE_URL + KOKORO_VOICES_FILE, KOKORO_VOICES_SHA256, "kokoro_voices"),
    )
    for fname, url, sha, key in pairs:
        dest = _os.path.join(root, "models", fname)
        if _os.path.isfile(dest):
            continue
        s = sources.get(key)
        if s and _os.path.isfile(s):
            _shutil.copy2(s, dest)
        elif not opts.get("skip_models"):
            _download(url, dest, sha, log)
    _write_text(_os.path.join(dst, "README.txt"), TTS_README, log)
    log.ok("Backend TTS (kokoro) pret : %s" % dst)
    return dst


def write_catalog(root, log):
    """Model Manager : catalogue JSON multi-modal (Section 6)."""
    models = [
        {"id": "llama-3.2-1b-instruct", "name": "Llama 3.2 1B Instruct", "modality": "text",
         "format": "gguf", "filename": MODEL_FILE, "source": MODEL_URL,
         "size_mb": 770, "sha256": MODEL_SHA256, "recommended": True},
        # --- Phase 9 (v1.9.0) : paire TEXT-ONLY pour le Speculative Decoding ---
        {"id": "qwen2.5-1.5b-instruct",
         "name": "Qwen2.5 1.5B Instruct (texte + draft speculatif)", "modality": "text",
         "format": "gguf", "filename": SPEC_MODEL_FILE, "source": SPEC_MODEL_URL,
         "size_mb": SPEC_MODEL_MB, "sha256": SPEC_MODEL_SHA256, "recommended": True,
         "draft": {"filename": SPEC_DRAFT_FILE, "source": SPEC_DRAFT_URL,
                   "size_mb": SPEC_DRAFT_MB, "sha256": SPEC_DRAFT_SHA256}},
        {"id": "whisper-base", "name": "Whisper Base", "modality": "audio",
         "format": "ggml", "filename": WHISPER_MODEL_FILE, "source": WHISPER_MODEL_URL,
         "size_mb": 142, "sha256": WHISPER_MODEL_SHA256, "recommended": True},
        {"id": "sd-turbo", "name": "SD Turbo (image)", "modality": "image",
         "format": "safetensors", "filename": SD_TURBO_FILE, "source": SD_TURBO_URL,
         "size_mb": 5200, "sha256": "", "recommended": False},
        {"id": "sd-turbo-light", "name": "SD Turbo Q8_0 (image legere)", "modality": "image",
         "format": "gguf", "filename": SD_TURBO_LIGHT_FILE, "source": SD_TURBO_LIGHT_URL,
         "size_mb": SD_TURBO_LIGHT_MB, "sha256": SD_TURBO_LIGHT_SHA256, "recommended": True},
        # --- Phase 5 (v1.5.0) : modeles VISION (modele + projecteur mmproj) ---
        {"id": "qwen2-vl-2b", "name": "Qwen2-VL 2B (vision + texte)", "modality": "vision",
         "format": "gguf", "filename": VLM_QWEN_FILE, "source": VLM_QWEN_BASE + VLM_QWEN_FILE,
         "size_mb": VLM_QWEN_MB, "sha256": VLM_QWEN_SHA256, "recommended": True,
         "multimodal": True,
         "mmproj": {"filename": VLM_QWEN_MMPROJ, "source": VLM_QWEN_BASE + VLM_QWEN_MMPROJ,
                    "size_mb": VLM_QWEN_MMPROJ_MB, "sha256": VLM_QWEN_MMPROJ_SHA256}},
        {"id": "smolvlm-500m", "name": "SmolVLM 500M (vision legere, secours CPU)",
         "modality": "vision", "format": "gguf", "filename": VLM_SMOL_FILE,
         "source": VLM_SMOL_BASE + VLM_SMOL_FILE, "size_mb": VLM_SMOL_MB,
         "sha256": VLM_SMOL_SHA256, "recommended": True, "multimodal": True,
         "mmproj": {"filename": VLM_SMOL_MMPROJ, "source": VLM_SMOL_BASE + VLM_SMOL_MMPROJ,
                    "size_mb": VLM_SMOL_MMPROJ_MB, "sha256": VLM_SMOL_MMPROJ_SHA256}},
        {"id": "kokoro-v1.1", "name": "Kokoro v1.1 (TTS)", "modality": "tts",
         "format": "onnx", "filename": KOKORO_MODEL_FILE,
         "source": KOKORO_BASE_URL + KOKORO_MODEL_FILE,
         "size_mb": 310, "sha256": KOKORO_MODEL_SHA256, "recommended": True},
    ]
    cat = {"version": "1.0", "generated": _time.strftime("%Y-%m-%dT%H:%M:%S"), "models": models}
    out = _os.path.join(root, "models", "models-catalog.json")
    with open(out, "w", encoding="utf-8") as fh:
        _json.dump(cat, fh, indent=2, ensure_ascii=False)
    if log:
        log.ok("catalogue de modeles ecrit : %d entrees (%s)" % (len(models), out))
    return cat


def ensure_onnx_directml(root, log):
    """Garantit le provider d'acceleration universelle DirectML (Windows) + le modele sonde.

    DirectML adresse les NPU Intel et AMD XDNA2 sans SDK constructeur. Si le binaire ou les
    pilotes ne permettent pas l'initialisation, la passerelle bascule sur le CPU (repli QA)
    et l'avertissement est consigne (categorie GPU_DETECT).
    """
    py = _os.path.join(root, "runtime", "python", "python.exe")
    if not _os.path.isfile(py):
        return False
    sp = _os.path.join(root, "runtime", "python", "Lib", "site-packages")
    onnx_dir = _os.path.join(root, "runtime", "onnx")
    _os.makedirs(onnx_dir, exist_ok=True)
    # 1. Modele sonde (inference reelle pour valider le provider).
    probe_model = _os.path.join(onnx_dir, ONNX_MODEL_FILE)
    if not _os.path.isfile(probe_model):
        try:
            _download(ONNX_MODEL_URL, probe_model, ONNX_MODEL_SHA256, log)
        except Exception as exc:
            if log:
                log.warn("  modele sonde ONNX non telecharge : %s" % exc)
    # 2. Provider DirectML (installation isolee dans le Python embarque, comme prescrit).
    check = [py, "-c",
             "import onnxruntime as o; p=o.get_available_providers(); "
             "print('DML' if 'DmlExecutionProvider' in p else 'CPU')"]
    try:
        r = _subprocess.run(check, capture_output=True, timeout=120)
        out = (r.stdout or b"").decode("utf-8", "replace").strip()
        if r.returncode == 0 and out == "DML":
            if log:
                log.ok("  provider DirectML disponible (acceleration NPU/GPU universelle)")
            return True
        if r.returncode == 0:
            if log:
                log.info("  onnxruntime present mais sans DirectML -> installation du provider ...")
    except Exception:
        pass
    if log:
        log.warn("  installation de onnxruntime-directml (peut prendre plusieurs minutes) ...")
    ok = False
    try:
        _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                         "--target", sp, "onnxruntime-directml"], check=False, timeout=2400)
        r = _subprocess.run(check, capture_output=True, timeout=180)
        out = (r.stdout or b"").decode("utf-8", "replace").strip()
        ok = (r.returncode == 0 and out == "DML")
    except Exception as exc:
        if log:
            log.warn("  installation onnxruntime-directml impossible : %s" % exc)
    if log:
        if ok:
            log.ok("  provider DirectML installe (DmlExecutionProvider actif).")
        else:
            log.warn("  DirectML indisponible (pilote/materiel) -> repli CPU automatique "
                     "(voir dev\\crash.log, categorie GPU_DETECT).")
    return ok


def ensure_mcp_sdk(root, log):
    """Garantit la presence du SDK MCP officiel sur le Python embarque.

    Constat mesure : 'litellm[proxy]' 1.103.2 fournit deja 'mcp' 2.3.0 dans le
    site-packages embarque, et l'ensemble (starlette 1.7.0, fastapi 0.142.2,
    typing-extensions 4.16.0) reste importable par LiteLLM : la passerelle consomme
    donc ce SDK sans rien installer.

    Le prefixe isole runtime\\mcp\\packages n'est qu'un REPLI defensif : si une
    version future de LiteLLM cessait de fournir 'mcp', l'installeur le poserait la,
    sans jamais toucher au site-packages qui heberge le proxy d'authentification.
    (Motif d'isolation deja retenu pour les paquets RAG : runtime\\packages.)
    """
    py = _os.path.join(root, "runtime", "python", "python.exe")
    if not _os.path.isfile(py):
        return False
    pkg = _os.path.join(root, "runtime", "mcp", "packages")
    probe = [py, "-c",
             "import sys; sys.path.insert(0, r'%s'); import mcp; print(getattr(mcp, '__version__', 'ok'))" % pkg]
    try:
        r = _subprocess.run(probe, capture_output=True, timeout=120)
        if r.returncode == 0:
            if log:
                log.ok("  SDK MCP present (isole : runtime\\mcp\\packages)")
            return True
    except Exception:
        pass
    if log:
        log.warn("  SDK MCP absent -> installation isolee (pip --target runtime\\mcp\\packages) ...")
    ok = False
    try:
        _os.makedirs(pkg, exist_ok=True)
        _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                         "--target", pkg, "mcp==%s" % MCP_VERSION], check=False, timeout=1800)
        r = _subprocess.run(probe, capture_output=True, timeout=120)
        ok = r.returncode == 0
    except Exception as exc:
        if log:
            log.warn("  installation SDK MCP impossible : %s" % exc)
    if log:
        if ok:
            log.ok("  SDK MCP %s installe (isole)." % MCP_VERSION)
        else:
            log.warn("  SDK MCP TOUJOURS ABSENT (la passerelle MCP sera indisponible).")
    return ok


def ensure_proxy_deps(root, log):
    """Repare les dependances optionnelles du proxy LiteLLM.

    'litellm[proxy]' est installe avec check=False : si la resolution echoue
    partiellement, 'prisma' peut manquer. Or le handler d'erreur d'authentification
    de LiteLLM fait 'import prisma' : sans lui, toute requete non authentifiee
    renvoie HTTP 500 (ModuleNotFoundError) au lieu du 401 attendu.
    """
    py = _os.path.join(root, "runtime", "python", "python.exe")
    if not _os.path.isfile(py):
        return False
    sp = _os.path.join(root, "runtime", "python", "Lib", "site-packages")
    try:
        probe = _subprocess.run([py, "-c", "import prisma"], capture_output=True, timeout=90)
        if probe.returncode == 0:
            if log:
                log.ok("  dependance proxy LiteLLM 'prisma' presente (401 propre garanti)")
            return True
    except Exception:
        pass
    if log:
        log.warn("  'prisma' absent -> installation (handler d'auth LiteLLM) ...")
    ok = False
    try:
        _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                         "--target", sp, "prisma"], check=False, timeout=900)
        probe = _subprocess.run([py, "-c", "import prisma"], capture_output=True, timeout=90)
        ok = probe.returncode == 0
    except Exception as exc:
        if log:
            log.warn("  installation 'prisma' impossible : %s" % exc)
    if log:
        if ok:
            log.ok("  dependance proxy LiteLLM 'prisma' installee.")
        else:
            log.warn("  dependance proxy LiteLLM 'prisma' TOUJOURS ABSENTE "
                     "(401 degrade en 500 sur requete non authentifiee).")
    return ok


def deploy_rag(root, sources, opts, log):
    """Phase 4 : pipeline RAG local (NumPy seul) + packages isoles."""
    rag_dir = _os.path.join(root, "runtime", "rag")
    pkg_dir = _os.path.join(root, "runtime", "packages")
    _os.makedirs(rag_dir, exist_ok=True)
    _os.makedirs(pkg_dir, exist_ok=True)
    _write_text(_os.path.join(root, "scripts", "rag_ingest.py"), RAG_INGEST_PY, log)
    src = sources.get("rag_packages")
    if src and _os.path.isdir(src) and _os.listdir(src):
        count = 0
        for name in _os.listdir(src):
            s = _os.path.join(src, name)
            d = _os.path.join(pkg_dir, name)
            try:
                if _os.path.isdir(s):
                    if _os.path.isdir(d):
                        _shutil.rmtree(d, ignore_errors=True)
                    _shutil.copytree(s, d)
                else:
                    _shutil.copy2(s, d)
                count += 1
            except Exception as exc:
                log.warn("  package %s : %s" % (name, exc))
        log.ok("  packages RAG copies (%d entrees) -> runtime\\packages" % count)
    else:
        py = _os.path.join(root, "runtime", "python", "python.exe")
        if _os.path.isfile(py):
            log.info("  installation des packages RAG (pip --target, isole) ...")
            _subprocess.run([py, "-m", "pip", "install", "--no-warn-script-location",
                             "--target", pkg_dir, "numpy>=1.24.0", "pypdf>=4.0.0",
                             "python-docx", "openpyxl"], check=False)
    log.ok("Pipeline RAG pret : scripts\\rag_ingest.py + index dans runtime\\rag\\")
    return rag_dir


def deploy_llama_variants(root, sources, opts, log):
    """Phase 3 : installe les variantes llama.cpp (cpu/vulkan/cuda) dans variants\\."""
    lc = _os.path.join(root, "backends", "llama-cpp")
    vdir = _os.path.join(lc, "variants")
    _os.makedirs(vdir, exist_ok=True)

    def _place(variant, src_dir=None, zip_name=None, url=None, sha=None, extra=None):
        dst = _os.path.join(vdir, variant)
        if _os.path.isfile(_os.path.join(dst, "llama-server.exe")):
            return True
        _os.makedirs(dst, exist_ok=True)
        if src_dir and _os.path.isdir(src_dir) and _os.listdir(src_dir):
            _copy_engine(src_dir, dst, log)
        elif zip_name:
            zp = _os.path.join(opts["cache"], zip_name)
            if not _os.path.isfile(zp):
                if not url:
                    return False
                _download(url, zp, sha, log)
            _extract_zip(zp, dst, log)
        if extra:
            extra(dst)
        ok = _os.path.isfile(_os.path.join(dst, "llama-server.exe"))
        if log:
            log.ok("  variante llama.cpp '%s' %s" % (variant, "installee" if ok else "INDISPONIBLE"))
        return ok

    def _add_cudart(dst):
        cd = sources.get("cudart_dir")
        if cd and _os.path.isdir(cd):
            _copy_engine(cd, dst, log)

    _place("cpu", src_dir=sources.get("engine_dir"),
           zip_name=LLAMA_VARIANT_FILES["cpu"], url=LLAMA_VARIANT_URLS["cpu"])
    _place("vulkan", src_dir=sources.get("engine_vulkan"),
           zip_name=LLAMA_VARIANT_FILES["vulkan"], url=LLAMA_VARIANT_URLS["vulkan"],
           sha=LLAMA_VARIANT_SHA256["vulkan"])
    if sources.get("engine_cuda") or opts.get("want_cuda"):
        _place("cuda", src_dir=sources.get("engine_cuda"),
               zip_name=LLAMA_VARIANT_FILES["cuda"], url=LLAMA_VARIANT_URLS["cuda"],
               sha=LLAMA_VARIANT_SHA256["cuda"], extra=_add_cudart)
    return vdir


def deploy_hw_scripts(root, log):
    sc = _os.path.join(root, "scripts")
    _os.makedirs(sc, exist_ok=True)
    _write_text(_os.path.join(sc, "hw_profile.ps1"), HW_PROFILE_PS1, log)
    _write_text(_os.path.join(sc, "engine_select.ps1"), ENGINE_SELECT_PS1, log)
    _write_text(_os.path.join(sc, "bench.ps1"), BENCH_PS1, log)
    _write_text(_os.path.join(sc, "vram_status.ps1"), VRAM_STATUS_PS1, log)
    log.ok("  scripts GPU/materiel deployes (hw_profile, engine_select, bench, vram_status)")
    return sc


def generate_hw_profile(root, log):
    """Execute hw_profile.ps1 (detection + selection de variante) sur le produit."""
    script = _os.path.join(root, "scripts", "hw_profile.ps1")
    out_path = _os.path.join(root, "config", "hardware-profile.json")
    if not _os.path.isfile(script):
        return None
    try:
        r = _subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", script, "-Write", "-SelectEngine"],
            capture_output=True, text=True, timeout=240)
        text = (r.stdout or "") + (r.stderr or "")
        for line in text.splitlines():
            if line.strip():
                log.info("  [hw] " + line.strip())
    except Exception as exc:
        log.warn("  profil materiel non genere : %s" % exc)
        return None
    if _os.path.isfile(out_path):
        log.ok("  profil materiel ecrit : %s" % out_path)
        return out_path
    log.warn("  profil materiel absent apres execution.")
    return None


def gen_lang_bat(lang):
    """Genere le contenu de i18n\\_<lang>.bat (messages CLI, UTF-8 sans BOM)."""
    help_lines = I18N_HELP.get(lang) or []
    labels = I18N_LABELS.get(lang) or {}
    out = ["@echo off",
           "rem i18n\\_%s.bat - messages du CLI (%s) - v%s - UTF-8 sans BOM"
           % (lang, lang.upper(), __VERSION__),
           "rem Charge dynamiquement par Run-LocalAI.bat selon la langue active (config\\lang.json).",
           "rem Variables : MSG_HELP_nn (aide), MSG_HELP_COUNT, MSG_<cle> (libelles et messages).",
           ""]
    for i, txt in enumerate(help_lines, 1):
        out.append('set "MSG_HELP_%02d=%s"' % (i, txt.replace("@VER@", __VERSION__)))
    out.append('set "MSG_HELP_COUNT=%02d"' % len(help_lines))
    for k, v in sorted(labels.items()):
        out.append('set "MSG_%s=%s"' % (k.upper(), v))
    out.append("")
    return "\r\n".join(out)


def deploy_i18n_bat(root, log):
    """Ecrit i18n\\_fr.bat et i18n\\_en.bat (couche messages du CLI)."""
    d = _os.path.join(root, "i18n")
    _os.makedirs(d, exist_ok=True)
    n = 0
    for lg in ("fr", "en"):
        try:
            with open(_os.path.join(d, "_%s.bat" % lg), "w", encoding="utf-8", newline="") as fh:
                fh.write(gen_lang_bat(lg))
            n += 1
        except Exception as exc:
            log.warn("  ecriture i18n\\_%s.bat impossible : %s" % (lg, exc))
    log.ok("  messages CLI i18n deployes : %d fichier(s) (%s)" % (n, "i18n\\_fr.bat, i18n\\_en.bat"))
    return n


def generate_i18n(root, log):
    """Genere i18n\\fr.json et i18n\\en.json depuis le dictionnaire embarque (couche 2, v2.1.1)."""
    import json as _j  # import local : independant du namespace du code de deploiement
    ns = {"__file__": _os.path.join(root, "scripts", "i18n.py"), "__name__": "i18n_template"}
    try:
        exec(compile(I18N_PY, "<i18n>", "exec"), ns)
    except Exception as exc:
        log.warn("  dictionnaire i18n embarque illisible : %s" % exc)
        return None
    trans = ns.get("TRANSLATIONS") or {}
    rev = str(ns.get("I18N_REV", "1"))
    if not trans:
        log.warn("  aucun dictionnaire i18n embarque")
        return None
    out_dir = _os.path.join(root, "i18n")
    _os.makedirs(out_dir, exist_ok=True)
    n, kept = 0, 0
    for lg in sorted(trans):
        p = _os.path.join(out_dir, "%s.json" % lg)
        # AUTO-REPARATION : un fichier absent, VIDE ou JSON invalide est regenere ;
        # seule une personnalisation VALIDE est conservee.
        keep = False
        if _os.path.isfile(p) and _os.path.getsize(p) > 0:
            try:
                with open(p, encoding="utf-8-sig") as fh:
                    keep = isinstance(_j.load(fh), dict)
            except Exception:
                keep = False
        if keep:
            kept += 1
            continue
        data = {"_i18n_rev": rev,
                "_comment": "Surcharge utilisateur (couche 2) ; les cles help_*/tip_* sont "
                            "rafraichies automatiquement si _i18n_rev change."}
        data.update(trans[lg])
        try:
            with open(p, "w", encoding="utf-8") as fh:
                _j.dump(data, fh, indent=2, ensure_ascii=False)
            n += 1
        except Exception as exc:
            log.warn("  ecriture %s impossible : %s" % (p, exc))
    log.ok("  fichiers i18n generes : %d (couche 2) ; %d conserve(s) (personnalisation utilisateur)"
           % (n, kept))
    return n


def _looks_like_engine(path):
    return _os.path.isfile(_os.path.join(path, "llama-server.exe"))


def _guard_running_services(root, log):
    """Refuse la reconstruction si la pile tourne encore.

    Des fichiers verrouilles par un service actif (surtout runtime\\python) font echouer la
    bascule ; l'incident du 2026-10-03 a montre qu'il faut l'interdire en amont.
    """
    pidfile = _os.path.join(root, "data", "pids.txt")
    alive = []
    try:
        import ctypes
        with open(pidfile, encoding="utf-8-sig") as fh:
            for line in fh:
                p = line.split()
                if len(p) >= 2 and p[1].isdigit():
                    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(p[1]))
                    if h:
                        ctypes.windll.kernel32.CloseHandle(h)
                        alive.append("%s(%s)" % (p[0], p[1]))
    except Exception:
        pass
    if alive:
        raise RuntimeError("Reinstallation refusee : services encore actifs -> %s\n"
                           "  Lancez d'abord 'Run-LocalAI.bat stop' (zero zombie), "
                           "puis relancez l'installation." % ", ".join(alive))
    if log:
        log.ok("  controle prealable : aucun service actif (aucun fichier verrouille)")


def deploy_product(root, sources, opts, log):
    """Reconstruit l'arborescence du produit dans <root>."""
    log.info("=" * 74)
    log.info("DEPLOIEMENT DU PRODUIT -> %s" % root)
    log.info("=" * 74)
    _guard_running_services(root, log)
    _rmtree(root)
    _ensure_tree(root)

    # Regle d'or de l'heritage : preserver les donnees utilisateur entre reinstalls
    prev = opts.get("prev_product")
    # MIGRATION v2.1.1 -> v3.0.0 : le produit s'appelait "LocalAI", il devient "AiTron".
    # Si aucun produit "AiTron" n'existe encore, on herite depuis le repertoire historique.
    if not (prev and _os.path.isdir(prev)):
        legacy = _os.path.join(SANDBOX, "LocalAI")
        if _os.path.isdir(legacy):
            prev = legacy
            if log:
                log.info("  MIGRATION v3 : heritage repris depuis le repertoire historique %s" % legacy)
    if prev and _os.path.isdir(prev):
        for parts in (("config", "cloud-keys.env"), ("config", "keys.env"),
                      ("config", "bench-history.jsonl"), ("config", "mcp-settings.json"),
                      ("config", "failover.json"),
                      ("config", "profile.json"),
                      ("config", "lang.json"),
                      ("i18n", "fr.json"), ("i18n", "en.json"),
                      ("logs", "history.jsonl"),
                      ("runtime", "rag"), ("runtime", "storage"), ("runtime", "onnx"),
                      ("models", SD_TURBO_FILE),
                      ("models", SD_TURBO_LIGHT_FILE),
                      ("models", VLM_QWEN_FILE),
                      ("models", VLM_QWEN_MMPROJ),
                      ("models", VLM_SMOL_FILE),
                      ("models", VLM_SMOL_MMPROJ),
                      ("models", SPEC_MODEL_FILE),
                      ("models", SPEC_DRAFT_FILE)):
            srcp = _os.path.join(prev, *parts)
            dstp = _os.path.join(root, *parts)
            if not _os.path.exists(srcp) or _os.path.exists(dstp):
                continue
            _os.makedirs(_os.path.dirname(dstp), exist_ok=True)
            if _os.path.isdir(srcp):
                _shutil.copytree(srcp, dstp)
            else:
                _shutil.copy2(srcp, dstp)
            if log:
                log.info("  heritage conserve : %s" % dstp)

    # 1. Coeur LocalAI -------------------------------------------------------
    core_dst = _os.path.join(root, "local-ai.exe")
    core_src = sources.get("core")
    if core_src and _os.path.isfile(core_src):
        _shutil.copy2(core_src, core_dst)
        log.ok("Coeur deploye  : %s  (%d octets)" % (core_dst, _os.path.getsize(core_dst)))
    else:
        raise RuntimeError("Coeur local-ai.exe introuvable : placez-le dans "
                           "build\\out\\local-ai.exe, ou verifiez FALLBACK_LOCAL_AI_URL "
                           "(GitHub Releases) et son SHA-256 (voir INSTALLATION.md).")

    # 2. Bridge gRPC natif ---------------------------------------------------
    bridge_dst = _os.path.join(root, "backends", "llama-cpp", "cloud-proxy.exe")
    bridge_src = sources.get("bridge")
    if bridge_src and _os.path.isfile(bridge_src):
        _shutil.copy2(bridge_src, bridge_dst)
        log.ok("Bridge deploye : %s  (%d octets)" % (bridge_dst, _os.path.getsize(bridge_dst)))
    else:
        raise RuntimeError("Bridge cloud-proxy.exe introuvable : placez-le dans "
                           "build\\out\\cloud-proxy.exe ou verifiez FALLBACK_CLOUD_PROXY_URL "
                           "(GitHub Releases) et son SHA-256.")

    # 3. Moteur d'inference llama.cpp ---------------------------------------
    engine_dst = _os.path.join(root, "backends", "llama-cpp")
    engine_src = sources.get("engine_dir")
    if engine_src and _os.path.isdir(engine_src) and _os.listdir(engine_src):
        _copy_engine(engine_src, engine_dst, log)
    if not _looks_like_engine(engine_dst):
        zip_cache = _os.path.join(opts["cache"], LLAMACPP_ZIP)
        if not _os.path.isfile(zip_cache):
            log.info("Moteur absent localement : telechargement ggml-org %s" % LLAMACPP_TAG)
            _download(LLAMACPP_URL, zip_cache, LLAMACPP_SHA256, log)
        _extract_zip(zip_cache, engine_dst, log)
    if not _looks_like_engine(engine_dst):
        raise RuntimeError("Le moteur llama-server.exe est introuvable apres deploiement.")
    log.ok("Moteur llama.cpp operationnel dans %s" % engine_dst)

    # 4. Modele de test ------------------------------------------------------
    model_dst = _os.path.join(root, "models", MODEL_FILE)
    if not _os.path.isfile(model_dst):
        model_src = sources.get("model")
        if model_src and _os.path.isfile(model_src):
            _shutil.copy2(model_src, model_dst)
            log.ok("Modele copie depuis le cache local (%d octets)" % _os.path.getsize(model_dst))
        elif not opts.get("skip_model"):
            log.info("Modele absent localement : telechargement depuis HuggingFace")
            _download(MODEL_URL, model_dst, MODEL_SHA256, log)
        else:
            log.warn("Modele absent et --skip-model actif : l'inference sera indisponible.")
    if _os.path.isfile(model_dst):
        log.ok("Modele de test en place : %s" % model_dst)

    # 5. Fichiers texte (config, lanceurs, documentation) --------------------
    _write_text(_os.path.join(root, "launcher.bat"), LAUNCHER_BAT, log)
    _write_text(_os.path.join(root, "Run-LocalAI.bat"), RUN_AITRON_BAT, log)
    _write_text(_os.path.join(root, "stop.bat"), STOP_BAT, log)
    _write_text(_os.path.join(root, "download_model.bat"), DOWNLOAD_BAT, log)
    _write_text(_os.path.join(root, "models", "llama-3.2-1b-instruct.yaml"), MODEL_YAML, log)
    _write_text(_os.path.join(root, "backends", "llama-cpp", "README.txt"), BACKEND_README, log)

    # 6. Scripts d'orchestration (PowerShell) --------------------------------
    sc = _os.path.join(root, "scripts")
    _os.makedirs(sc, exist_ok=True)
    _write_text(_os.path.join(sc, "freeport.ps1"), FREEPORT_PS1, log)
    _write_text(_os.path.join(sc, "spawn.ps1"), SPAWN_PS1, log)
    _write_text(_os.path.join(sc, "model_manager.ps1"), MODEL_MANAGER_PS1, log)
    _write_text(_os.path.join(sc, "localai_up.ps1"), AITRON_UP_PS1, log)
    _write_text(_os.path.join(sc, "localai_status.ps1"), AITRON_STATUS_PS1, log)

    # 7. Configuration (LiteLLM + cles cloud BYOK) ---------------------------
    _write_text(_os.path.join(root, "config", "litellm-config.yaml"), LITELLM_CONFIG_YAML, log)
    _write_text(_os.path.join(root, "config", "complexity_router.py"), COMPLEXITY_ROUTER_PY, log)
    _write_text(_os.path.join(root, "config", "pii_filter.py"), PII_FILTER_PY, log)
    _write_text(_os.path.join(root, "config", "litellm_launch.py"), LITELLM_LAUNCH_PY, log)
    ck = _os.path.join(root, "config", "cloud-keys.env")
    if not _os.path.isfile(ck):
        _write_text(ck, CLOUD_KEYS_ENV, log)
    else:
        log.info("  cloud-keys.env existant conserve (regle d'or de l'heritage)")

    # 8. Backends multi-modaux ----------------------------------------------
    deploy_whisper(root, sources, opts, log)
    deploy_sd(root, sources, opts, log)
    deploy_tts(root, sources, opts, log)

    # 9. Python embarque (LiteLLM) ------------------------------------------
    deploy_python(root, sources, opts, log)
    ensure_proxy_deps(root, log)

    # 9b. Variantes GPU llama.cpp + scripts + profil materiel (v1.3.0) -------
    deploy_llama_variants(root, sources, opts, log)
    deploy_hw_scripts(root, log)
    generate_hw_profile(root, log)
    generate_i18n(root, log)
    deploy_i18n_bat(root, log)

    # 9c. Pipeline RAG local + Agent Hub (v1.4.0) ---------------------------
    deploy_rag(root, sources, opts, log)
    ensure_mcp_sdk(root, log)
    ensure_onnx_directml(root, log)
    _write_text(_os.path.join(root, "scripts", "key_set.ps1"), KEY_SET_PS1, log)
    _write_text(_os.path.join(root, "scripts", "proxy_logs.ps1"), PROXY_LOGS_PS1, log)
    ke = _os.path.join(root, "config", "keys.env")
    if not _os.path.isfile(ke):
        _write_text(ke, KEYS_ENV, log)
    else:
        log.info("  config\\keys.env existant conserve (regle d'or de l'heritage)")
    _write_text(_os.path.join(root, "scripts", "vram_watchdog.py"), VRAM_WATCHDOG_PY, log)
    # Passerelle MCP (v1.5.0) : scripts + declaration des outils/serveurs.
    _write_text(_os.path.join(root, "scripts", "mcp_gateway.py"), MCP_GATEWAY_PY, log)
    mcp_cfg = _os.path.join(root, "config", "mcp-settings.json")
    if not _os.path.isfile(mcp_cfg):
        _write_text(mcp_cfg, MCP_SETTINGS_JSON, log)
    else:
        log.info("  config\\mcp-settings.json existant conserve (regle d'or de l'heritage)")
    # GraphRAG (v1.6.0) : extraction entites/relations par le LLM local.
    _write_text(_os.path.join(root, "scripts", "graph_rag.py"), GRAPH_RAG_PY, log)
    # Proxy failover SSE (v1.6.0) : bufferisation + bascule locale/cloud.
    _write_text(_os.path.join(root, "scripts", "failover_proxy.py"), FAILOVER_PROXY_PY, log)
    fov_cfg = _os.path.join(root, "config", "failover.json")
    if not _os.path.isfile(fov_cfg):
        _write_text(fov_cfg, FAILOVER_SETTINGS_JSON, log)
    else:
        log.info("  config\\failover.json existant conserve (regle d'or de l'heritage)")
    # Quantization locale (v1.7.0) : compression de modeles via llama-quantize.exe.
    _write_text(_os.path.join(root, "scripts", "quantize_model.py"), QUANTIZE_MODEL_PY, log)
    # Acceleration universelle NPU/DirectML (v1.8.0) + repli CPU.
    _write_text(_os.path.join(root, "scripts", "onnx_provider.py"), ONNX_PROVIDER_PY, log)
    # Speculative Decoding TEXT-ONLY (v1.9.0) : garde VRAM + injection d'arguments.
    _write_text(_os.path.join(root, "scripts", "spec_decoding.py"), SPEC_DECODING_PY, log)
    # Espace hermetique AES-256 au repos (v2.0.0a).
    _write_text(_os.path.join(root, "scripts", "vault.py"), VAULT_PY, log)
    # Profil apprenant continu : seuils VRAM et -ngl ajustes depuis l'historique (v2.0.0b).
    _write_text(_os.path.join(root, "scripts", "learn_profile.py"), LEARN_PROFILE_PY, log)
    # Decouverte reseau des noeuds RPC federes (v2.1.0a).
    _write_text(_os.path.join(root, "scripts", "peer_discovery.py"), PEER_DISCOVERY_PY, log)
    # Internationalisation FR/EN a trois couches (v2.1.1).
    _write_text(_os.path.join(root, "scripts", "i18n.py"), I18N_PY, log)

    # 10. Model Manager (catalogue multi-modal) -----------------------------
    write_catalog(root, log)

    log.ok("Fichiers de configuration, lanceurs et documentation ecrits.")
    return True


def swap_product(new_root, final_root, log):
    """Bascule transactionnelle SURE : permutation par renommage, jamais par suppression prealable.

    Incident du 2026-10-03 (v1.8.0) : l'ancienne implementation supprimait l'arbre de production
    AVANT d'installer le nouveau (_rmtree puis _os.replace). Un fichier verrouille a fait echouer
    la suppression a mi-chemin, APRES que l'essentiel ait ete efface : le produit a ete perdu.
    Desormais : (1) l'ancien arbre est ecarte par RENOMMAGE, (2) le nouveau est mis en place par
    renommage, (3) l'ancien est supprime en best-effort. Si (2) echoue, l'ancien est restaure :
    aucune perte possible, et le nouveau reste disponible pour reessai.
    """
    retired = final_root + ".old"
    _rmtree(retired)                              # residu eventuel d'une bascule precedente
    had_old = _os.path.isdir(final_root)
    if had_old:
        try:
            _os.replace(final_root, retired)
        except Exception as exc:
            raise RuntimeError("Bascule annulee : ancien produit non escamotable (%s). "
                               "Arret de la pile requis avant toute reinstallation." % exc)
    try:
        _os.replace(new_root, final_root)
    except Exception as exc:
        # Rollback : l'ancien produit est remis en place ; le nouveau est CONSERVE.
        if had_old and not _os.path.isdir(final_root) and _os.path.isdir(retired):
            try:
                _os.replace(retired, final_root)
                if log:
                    log.warn("  rollback : ancien produit restaure a %s" % final_root)
            except Exception:
                if log:
                    log.error("  rollback PARTIEL : ancien produit conserve sous %s" % retired)
        raise RuntimeError("Bascule impossible (%s) ; arborescence de staging conservee : %s"
                           % (exc, new_root))
    if log:
        log.ok("Produit bascule de facon transactionnelle vers %s" % final_root)
    if had_old and _os.path.isdir(retired):
        _rmtree(retired)
        if _os.path.isdir(retired) and log:
            log.warn("  ancien produit partiellement conserve (fichiers verrouilles) : %s" % retired)


def build_manifest(root, log, logical_root=None):
    """Section 3.3 : inventaire complet + hash SHA-256 de chaque composant.

    logical_root : chemin final du produit (Section 12.1) ; le manifest est
    construit dans le staging mais doit pointer vers le dossier LocalAI final
    apres la bascule.
    """
    if logical_root is None:
        logical_root = root
    items = []

    def add(rel, role, version, source, replaceable):
        path = _os.path.join(root, rel.replace("/", _os.sep))
        if not _os.path.isfile(path):
            return
        items.append({
            "path": rel.replace("\\", "/"),
            "role": role,
            "version": version,
            "sha256": _sha256(path),
            "size_bytes": _os.path.getsize(path),
            "source": source,
            "replaceable": replaceable,
        })

    add("local-ai.exe", "moteur LocalAI (coeur, API OpenAI-compatible)",
        LOCALAI_VERSION,
        "compile localement (sources officielles LocalAI %s, Go, CGO_ENABLED=0)" % LOCALAI_TAG, True)
    add("backends/llama-cpp/cloud-proxy.exe", "backend gRPC natif (bridge cloud-proxy)",
        LOCALAI_VERSION, "compile localement (backend/go/cloud-proxy)", True)
    add("backends/llama-cpp/llama-server.exe", "moteur d'inference llama.cpp (ggml-org)",
        LLAMACPP_TAG, LLAMACPP_URL, True)
    add("models/" + MODEL_FILE, "modele de test GGUF (Llama-3.2-1B-Instruct)", "Q4_K_M",
        MODEL_URL, True)
    add("models/llama-3.2-1b-instruct.yaml", "configuration du modele", __VERSION__,
        "genere par l'installeur", True)
    add("launcher.bat", "lanceur (moteur + coeur)", __VERSION__, "genere par l'installeur", True)
    add("stop.bat", "arret propre (zero zombie)", __VERSION__, "genere par l'installeur", True)
    add("download_model.bat", "telechargement du modele (helper)", __VERSION__, "genere par l'installeur", True)
    add("backends/llama-cpp/README.txt", "documentation du backend", __VERSION__,
        "genere par l'installeur", True)
    # --- Phase 2 (v1.2.0) ---
    add("Run-LocalAI.bat", "CLI wrapper principal (start/stop/status/pull/list/backends)", __VERSION__,
        "genere par l'installeur", True)
    add("models/models-catalog.json", "catalogue multi-modal (Model Manager)", __VERSION__,
        "genere par l'installeur", True)
    add("config/litellm-config.yaml", "configuration de la gateway LiteLLM", __VERSION__,
        "genere par l'installeur", True)
    add("config/complexity_router.py", "callback LiteLLM (routage par complexite)", __VERSION__,
        "genere par l'installeur", True)
    add("config/litellm_launch.py", "lanceur LiteLLM (UTF-8 + callbacks)", __VERSION__,
        "genere par l'installeur", True)
    add("backends/whisper-cpp/whisper-server.exe", "moteur speech-to-text (whisper.cpp)",
        WHISPER_CPP_TAG, WHISPER_CPP_URL, True)
    add("models/" + WHISPER_MODEL_FILE, "modele Whisper Base (ggml)", "base", WHISPER_MODEL_URL, True)
    add("backends/stable-diffusion/sd-server.exe", "moteur image (stable-diffusion.cpp)",
        SD_CPP_TAG, SD_CPP_URL, True)
    add("backends/stable-diffusion/variants/cuda/sd-server.exe",
        "variante image GPU (stable-diffusion.cpp cuda)", SD_CPP_TAG, SD_CPP_CUDA_URL, True)
    add("backends/tts/tts_server.py", "service TTS (kokoro-onnx)", __VERSION__,
        "genere par l'installeur", True)
    add("models/" + KOKORO_MODEL_FILE, "modele TTS Kokoro (ONNX)", KOKORO_TAG,
        KOKORO_BASE_URL + KOKORO_MODEL_FILE, True)
    add("runtime/python/python.exe", "Python embarque (LiteLLM + TTS)", "3.11.9",
        PYTHON_EMBED_URL.format(version="3.11.9"), True)
    for sname in ("localai_up.ps1", "localai_status.ps1", "model_manager.ps1",
                  "freeport.ps1", "spawn.ps1"):
        add("scripts/" + sname, "script d'orchestration", __VERSION__,
            "genere par l'installeur", True)
    # --- Phase 3 (v1.3.0) ---
    add("config/hardware-profile.json", "profil materiel detecte (GPU/CPU, params)", __VERSION__,
        "genere par l'installeur", True)
    for sname in ("hw_profile.ps1", "engine_select.ps1", "bench.ps1"):
        add("scripts/" + sname, "script GPU/materiel", __VERSION__, "genere par l'installeur", True)
    for v in ("cpu", "vulkan", "cuda"):
        add("backends/llama-cpp/variants/" + v + "/llama-server.exe",
            "variante moteur llama.cpp (" + v + ")", LLAMACPP_TAG,
            LLAMA_VARIANT_URLS.get(v, ""), True)
    add("backends/llama-cpp/active.json", "variante moteur active", __VERSION__,
        "genere par l'installeur", True)
    # --- Phase 4 (v1.4.0) ---
    add("scripts/rag_ingest.py", "pipeline RAG local (NumPy seul, sans faiss)", __VERSION__,
        "genere par l'installeur", True)
    add("scripts/key_set.ps1", "injection de cle API (BYOK)", __VERSION__,
        "genere par l'installeur", True)
    add("scripts/proxy_logs.ps1", "logs de routage (Token Saver)", __VERSION__,
        "genere par l'installeur", True)
    add("config/keys.env", "cles API externes (BYOK)", __VERSION__,
        "genere par l'installeur", True)
    add("runtime/packages/numpy/__init__.py", "packages RAG isoles (numpy/pypdf/docx/openpyxl)",
        "numpy>=1.24.0", "https://pypi.org/", True)
    add("runtime/python/Lib/site-packages/prisma/__init__.py",
        "dependance proxy LiteLLM (handler d'authentification)",
        "prisma>=0.11", "https://pypi.org/", True)
    # --- Phase 4.1 (v1.4.1) ---
    add("scripts/vram_watchdog.py", "watchdog VRAM (surveillance continue + action preventive)",
        __VERSION__, "genere par l'installeur", True)
    add("scripts/vram_status.ps1", "etat VRAM (vram-status)", __VERSION__,
        "genere par l'installeur", True)
    # --- Phase 5 (v1.5.0) : vision + MCP ---
    add("scripts/mcp_gateway.py", "passerelle MCP (SDK officiel, spec " + MCP_SPEC + ")",
        __VERSION__, "genere par l'installeur", True)
    add("config/mcp-settings.json", "declaration des serveurs et outils MCP",
        __VERSION__, "genere par l'installeur", True)
    add("runtime/mcp/packages/mcp/__init__.py", "SDK MCP officiel (installation isolee)",
        "mcp>=" + MCP_VERSION, "https://pypi.org/", True)
    # --- Phase 6 (v1.6.0) : GraphRAG + failover ---
    add("scripts/graph_rag.py", "GraphRAG local (extraction NER/RE par LLM local)",
        __VERSION__, "genere par l'installeur", True)
    add("scripts/failover_proxy.py", "proxy SSE : bufferisation + failover local/cloud",
        __VERSION__, "genere par l'installeur", True)
    add("config/failover.json", "politique de bufferisation et de failover",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 7 (v1.7.0) : quantization + filtre PII ---
    add("scripts/quantize_model.py", "quantization locale (llama-quantize.exe)",
        __VERSION__, "genere par l'installeur", True)
    add("config/pii_filter.py", "filtre de confidentialite PII hybride (BEST-EFFORT)",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 8 (v1.8.0) : acceleration NPU/DirectML ---
    add("scripts/onnx_provider.py", "accelerateur semantique DirectML/NPU (repli CPU)",
        __VERSION__, "genere par l'installeur", True)
    add("runtime/onnx/" + ONNX_MODEL_FILE, "modele sonde ONNX (validation du provider)",
        __VERSION__, ONNX_MODEL_URL, True)
    # --- Phase 9 (v1.9.0) : speculative decoding ---
    add("scripts/spec_decoding.py", "speculative decoding TEXT-ONLY (garde VRAM)",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 10 (v2.0.0a) : espace hermetique ---
    add("scripts/vault.py", "espace hermetique AES-256-GCM au repos (cle derivee, non stockee)",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 11 (v2.0.0b) : profil apprenant continu ---
    add("scripts/learn_profile.py", "profil apprenant (seuils VRAM + -ngl adaptatifs, reset d'usine)",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 12 (v2.1.0a) : decouverte reseau des noeuds RPC ---
    add("scripts/peer_discovery.py", "decouverte UDP des noeuds RPC federes (aucune dependance)",
        __VERSION__, "genere par l'installeur", True)
    # --- Phase 13 (v2.1.1) : internationalisation FR/EN ---
    add("scripts/i18n.py", "i18n FR/EN a 3 couches (embarque, JSON externe, revision)",
        __VERSION__, "genere par l'installeur", True)
    add("i18n/fr.json", "messages francais (couche 2, personnalisable)", __VERSION__,
        "genere par l'installeur", False)
    add("i18n/en.json", "messages anglais (couche 2, personnalisable)", __VERSION__,
        "genere par l'installeur", False)

    engine = _os.path.join(root, "backends", "llama-cpp")
    if _os.path.isdir(engine):
        for name in sorted(_os.listdir(engine)):
            if name.lower().endswith(".dll"):
                add("backends/llama-cpp/" + name, "bibliotheque du moteur llama.cpp",
                    LLAMACPP_TAG, LLAMACPP_URL, True)

    manifest = {
        "product": "AiTron V3 (portage natif, sans Docker/WSL)",
        "fork_of": "LocalAI (https://github.com/mudler/LocalAI)",
        "license": "MIT",
        "installer_version": "v" + __VERSION__,
        "localai_version": LOCALAI_VERSION,
        "llama_cpp_tag": LLAMACPP_TAG,
        "generated_at": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        "root": logical_root,
        "components": items,
        "component_count": len(items),
    }
    out = _os.path.join(root, "manifest.json")
    with open(out, "w", encoding="utf-8") as fh:
        _json.dump(manifest, fh, indent=2, ensure_ascii=False)
    if log:
        log.ok("manifest.json ecrit : %d composants inventories (%s)" % (len(items), out))
    return manifest

'''

# ---------------------------------------------------------------------------
# Constantes injectees dans le namespace de AITRON_DEPLOY_CODE
# ---------------------------------------------------------------------------
def _deploy_namespace():
    return {
        # v3.1.0 (D4) : SANDBOX etait lu par la migration d'heritage (deploy_product) sans etre
        # injecte -> NameError sur toute 1re installation (aucun produit existant).
        "SANDBOX": SANDBOX,
        "LOCALAI_VERSION": LOCALAI_VERSION,
        "LOCALAI_TAG": LOCALAI_TAG,
        "LLAMACPP_TAG": LLAMACPP_TAG,
        "LLAMACPP_ZIP": LLAMACPP_ZIP,
        "LLAMACPP_URL": LLAMACPP_URL,
        "LLAMACPP_SHA256": LLAMACPP_SHA256,
        "MODEL_FILE": MODEL_FILE,
        "MODEL_URL": MODEL_URL,
        "MODEL_SHA256": MODEL_SHA256,
        "__VERSION__": __version__,
        # Phase 2 (v1.2.0)
        "PYTHON_EMBED_FILE": PYTHON_EMBED_FILE,
        "PYTHON_EMBED_URL": PYTHON_EMBED_URL,
        "PYTHON_EMBED_SHA256": PYTHON_EMBED_SHA256,
        "GET_PIP_URL": GET_PIP_URL,
        "GET_PIP_FILE": GET_PIP_FILE,
        "LITELLM_VERSION": LITELLM_VERSION,
        "WHISPER_CPP_RELEASES": WHISPER_CPP_RELEASES,
        "WHISPER_CPP_TAG": WHISPER_CPP_TAG,
        "WHISPER_CPP_URL": WHISPER_CPP_URL,
        "WHISPER_CPP_FILE": WHISPER_CPP_FILE,
        "WHISPER_CPP_SHA256": WHISPER_CPP_SHA256,
        "WHISPER_MODEL_FILE": WHISPER_MODEL_FILE,
        "WHISPER_MODEL_URL": WHISPER_MODEL_URL,
        "WHISPER_MODEL_SHA256": WHISPER_MODEL_SHA256,
        "SD_CPP_RELEASES": SD_CPP_RELEASES,
        "SD_CPP_TAG": SD_CPP_TAG,
        "SD_CPP_URL": SD_CPP_URL,
        "SD_CPP_FILE": SD_CPP_FILE,
        "SD_CPP_SHA256": SD_CPP_SHA256,
        "SD_TURBO_FILE": SD_TURBO_FILE,
        "SD_TURBO_URL": SD_TURBO_URL,
        "SD_TURBO_LIGHT_FILE": SD_TURBO_LIGHT_FILE,
        "SD_TURBO_LIGHT_URL": SD_TURBO_LIGHT_URL,
        "SD_TURBO_LIGHT_SHA256": SD_TURBO_LIGHT_SHA256,
        "SD_TURBO_LIGHT_MB": SD_TURBO_LIGHT_MB,
        # Phase 5 (v1.5.0) : vision
        "VLM_QWEN_FILE": VLM_QWEN_FILE,
        "VLM_QWEN_MMPROJ": VLM_QWEN_MMPROJ,
        "VLM_QWEN_BASE": VLM_QWEN_BASE,
        "VLM_QWEN_SHA256": VLM_QWEN_SHA256,
        "VLM_QWEN_MMPROJ_SHA256": VLM_QWEN_MMPROJ_SHA256,
        "VLM_QWEN_MB": VLM_QWEN_MB,
        "VLM_QWEN_MMPROJ_MB": VLM_QWEN_MMPROJ_MB,
        "VLM_SMOL_FILE": VLM_SMOL_FILE,
        "VLM_SMOL_MMPROJ": VLM_SMOL_MMPROJ,
        "VLM_SMOL_BASE": VLM_SMOL_BASE,
        "VLM_SMOL_SHA256": VLM_SMOL_SHA256,
        "VLM_SMOL_MMPROJ_SHA256": VLM_SMOL_MMPROJ_SHA256,
        "VLM_SMOL_MB": VLM_SMOL_MB,
        "VLM_SMOL_MMPROJ_MB": VLM_SMOL_MMPROJ_MB,
        "VLM_PORT": VLM_PORT,
        "MCP_VERSION": MCP_VERSION,
        "MCP_SPEC": MCP_SPEC,
        "ONNX_MODEL_FILE": ONNX_MODEL_FILE,
        "ONNX_MODEL_URL": ONNX_MODEL_URL,
        "ONNX_MODEL_SHA256": ONNX_MODEL_SHA256,
        # Phase 9 (v1.9.0) : speculative decoding
        "SPEC_MODEL_FILE": SPEC_MODEL_FILE,
        "SPEC_MODEL_URL": SPEC_MODEL_URL,
        "SPEC_MODEL_SHA256": SPEC_MODEL_SHA256,
        "SPEC_MODEL_MB": SPEC_MODEL_MB,
        "SPEC_DRAFT_FILE": SPEC_DRAFT_FILE,
        "SPEC_DRAFT_URL": SPEC_DRAFT_URL,
        "SPEC_DRAFT_SHA256": SPEC_DRAFT_SHA256,
        "SPEC_DRAFT_MB": SPEC_DRAFT_MB,
        "KOKORO_RELEASES": KOKORO_RELEASES,
        "KOKORO_TAG": KOKORO_TAG,
        "KOKORO_BASE_URL": KOKORO_BASE_URL,
        "KOKORO_MODEL_FILE": KOKORO_MODEL_FILE,
        "KOKORO_VOICES_FILE": KOKORO_VOICES_FILE,
        "KOKORO_MODEL_SHA256": KOKORO_MODEL_SHA256,
        "KOKORO_VOICES_SHA256": KOKORO_VOICES_SHA256,
        "DEFAULT_PORTS": DEFAULT_PORTS,
        # Phase 3 (v1.3.0)
        "LLAMACPP_BASE_URL": LLAMACPP_BASE_URL,
        "LLAMA_VARIANT_URLS": LLAMA_VARIANT_URLS,
        "LLAMA_VARIANT_FILES": LLAMA_VARIANT_FILES,
        "LLAMA_VARIANT_SHA256": LLAMA_VARIANT_SHA256,
        "CUDART_URL": CUDART_URL,
        "CUDART_FILE": CUDART_FILE,
        "CUDART_SHA256": CUDART_SHA256,
        "SD_CPP_CUDA_URL": SD_CPP_CUDA_URL,
        "SD_CPP_CUDA_FILE": SD_CPP_CUDA_FILE,
        "SD_CPP_CUDA_SHA256": SD_CPP_CUDA_SHA256,
        "PROFILE_NAMES": PROFILE_NAMES,
    }


def _fallback_sha256(path):
    """SHA-256 d'un fichier (module installeur, hors code embarque)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def _fallback_download(url, dest, expected_sha, log, label, pe=False):
    """Telecharge <url> -> <dest> (.part atomique) et verifie le SHA-256.

    SHA attendu vide -> la somme reelle est calculee et consignee (tracabilite).
    SHA attendu fourni et different -> rejet (fichier supprime, source ecartee).
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "AiTron V3-Installer/1.1"})
    with urllib.request.urlopen(req, timeout=180) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        last = 0.0
        while True:
            buf = resp.read(1048576)
            if not buf:
                break
            out.write(buf)
            got += len(buf)
            now = time.time()
            if log and (now - last) >= 3.0:
                last = now
                if total:
                    log.info("  ... %d/%d Mo (%.0f%%)" % (got // 1048576, total // 1048576,
                                                          100.0 * got / total))
                else:
                    log.info("  ... %d Mo" % (got // 1048576))
    actual = _fallback_sha256(tmp)
    # v3.1.2 -- garde-fou d'integrite PE "MZ" CONSERVE et applique a TOUT .exe
    # telecharge (GitHub Releases comprise), avec ou sans somme attendue : un
    # binaire Windows valide commence par l'en-tete DOS "MZ".
    if pe:
        with open(tmp, "rb") as fh:
            magic = fh.read(2)
        if magic != b"MZ":
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise RuntimeError("contenu telecharge non executable pour %s "
                               "(magic=%r != b'MZ') : source rejetee"
                               % (url, magic))
    if expected_sha:
        if actual.lower() != expected_sha.lower():
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise RuntimeError("SHA-256 invalide pour %s : attendu %s, obtenu %s"
                               % (url, expected_sha, actual))
        os.replace(tmp, dest)
        log.ok("Fallback %-6s : telecharge %s (%d octets)" % (label, dest, os.path.getsize(dest)))
        log.ok("Fallback %-6s : garde-fou PE MZ OK + SHA-256 verifie (%s)" % (label, actual))
    else:
        os.replace(tmp, dest)
        log.ok("Fallback %-6s : telecharge %s (%d octets)" % (label, dest, os.path.getsize(dest)))
        log.ok("Fallback %-6s : garde-fou PE MZ OK ; SHA-256 calcule (%s) -- aucune somme attendue"
               % (label, actual))
    return dest


def _resolve_binary(key, exe, primary, staging, url, sha, log):
    """v3.1.1 (Section 2.3) -- resolution portable d'un binaire du coeur.

    Cascade : 1. build\\out\\ (local) 2. staging archive 3. produit deploye
    4. telechargement (+ SHA-256). Jamais d'echec sec : si tout echoue, on renvoie
    le chemin local primaire (le deploiement levera une erreur explicite).
    """
    if primary and os.path.isfile(primary):
        return primary
    if staging and os.path.isfile(staging):
        log.info("Fallback %-6s : staging archive %s" % (key, staging))
        return staging
    cand = os.path.join(PRODUCT, exe)
    if os.path.isfile(cand):
        log.info("Fallback %-6s : produit deja deploye %s" % (key, cand))
        return cand
    log.info("Fallback %-6s : telechargement depuis %s" % (key, url))
    try:
        dest = os.path.join(BUILD, "downloads", exe)
        return _fallback_download(url, dest, sha, log, key, pe=exe.lower().endswith(".exe"))
    except Exception as exc:
        log.error("Fallback %-6s : echec du telechargement (%s)" % (key, exc))
        log.error("Fallback %-6s : toutes les sources ont echoue -> placez %s dans "
                  "build\\out\\ ou dev\\old\\test_dynamique\\AiTron\\, ou corrigez l'URL "
                  "GitHub et son SHA-256 (FALLBACK_%s_URL)."
                  % (key, exe, "LOCAL_AI" if key == "core" else "CLOUD_PROXY"))
        return primary


def _locate_sources(log):
    """Localise les artefacts locaux (compilation) et les caches (telechargement)."""
    bmodels = os.path.join(BUILD, "models")
    bt = os.path.join(BUILD, "tools")
    sources = {
        "core": os.path.join(BUILD, "out", CORE_EXE),
        "bridge": os.path.join(BUILD, "out", BRIDGE_EXE),
        "engine_dir": os.path.join(bt, "llama"),
        "model": os.path.join(bmodels, MODEL_FILE),
        "cache": os.path.join(BUILD, "downloads"),
        # --- Phase 2 (v1.2.0) ---
        "python_runtime": os.path.join(bt, "python"),
        "whisper_dir": os.path.join(bt, "whisper", "Release"),
        "sd_dir": os.path.join(bt, "sd"),
        "whisper_model": os.path.join(bmodels, WHISPER_MODEL_FILE),
        "kokoro_model": os.path.join(bmodels, KOKORO_MODEL_FILE),
        "kokoro_voices": os.path.join(bmodels, KOKORO_VOICES_FILE),
        # --- Phase 3 (v1.3.0) ---
        "engine_vulkan": os.path.join(bt, "llama-vulkan"),
        "engine_cuda": os.path.join(bt, "llama-cuda"),
        "cudart_dir": os.path.join(bt, "cudart"),
        "sd_cuda_dir": os.path.join(bt, "sd-cuda"),
        # --- Phase 4 (v1.4.0) ---
        "rag_packages": os.path.join(bt, "ragpackages"),
    }
    for key in ("core", "bridge", "model", "whisper_model", "kokoro_model", "kokoro_voices"):
        state = "trouve" if os.path.isfile(sources[key]) else "ABSENT"
        log.info("Source %-14s : %-8s %s" % (key, state, sources[key]))
    for key in ("engine_dir", "python_runtime", "whisper_dir", "sd_dir",
                "engine_vulkan", "engine_cuda", "cudart_dir", "sd_cuda_dir"):
        d = sources[key]
        state = "trouve" if os.path.isdir(d) else "ABSENT"
        log.info("Source %-14s : %-8s %s" % (key, state, d))
    # v3.1.1 (Section 2) -- resolution PORTABLE des binaires du coeur, en cascade :
    #   1. build\out\<exe> (compilation locale)
    #   2. dev\old\test_dynamique\AiTron\... (staging archive, herite)
    #   3. produit deja deploye (AiTron\<exe>)
    #   4. telechargement du fallback (transfert) + verification SHA-256
    _staging = os.path.join(QUARANTINE, "test_dynamique", "AiTron")
    sources["core"] = _resolve_binary(
        "core", CORE_EXE,
        os.path.join(BUILD, "out", CORE_EXE),
        os.path.join(_staging, CORE_EXE),
        FALLBACK_LOCAL_AI_URL, FALLBACK_LOCAL_AI_SHA256, log)
    sources["bridge"] = _resolve_binary(
        "bridge", BRIDGE_EXE,
        os.path.join(BUILD, "out", BRIDGE_EXE),
        os.path.join(_staging, "backends", "llama-cpp", BRIDGE_EXE),
        FALLBACK_CLOUD_PROXY_URL, FALLBACK_CLOUD_PROXY_SHA256, log)
    return sources


def _stop_existing(log):
    """Arrete une instance eventuellement en cours AVANT la bascule (anti-verrou).

    Sans cela, des services encore actifs (ou un lanceur qui retient ses fichiers
    de log) empechent le remplacement transactionnel du produit.
    """
    stop_bat = os.path.join(PRODUCT, "stop.bat")
    if os.path.isfile(stop_bat):
        try:
            subprocess.run(["cmd", "/c", stop_bat, "silent"], check=False, timeout=30)
            log.info("Instance precedente : stop.bat execute.")
        except Exception as exc:
            log.warn("stop.bat : %s" % exc)
    # v3.1.0 : en staging isole, JAMAIS de taskkill par nom d'image (il tuerait aussi les
    # processus du produit stable de la racine). Seuls les processus du dossier de staging
    # sont arretes, par chemin d'executable (bloc suivant).
    for img in (() if STAGE else ("local-ai.exe", "llama-server.exe", "cloud-proxy.exe",
                                  "whisper-server.exe", "sd-server.exe")):
        subprocess.run(["taskkill", "/IM", img, "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    # Tout processus dont l'executable vit dans le produit (python embarque, etc.)
    try:
        ps = ("Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '%s*' } "
              "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps % (PRODUCT + os.sep)],
                       check=False, timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        log.warn("Arret des processus du produit : %s" % exc)
    time.sleep(1)
    log.info("Produit verrouille ? verification...")
    return True


def _check_ports(log):
    """Section 12.2 : verifie que les ports par defaut sont libres au demarrage."""
    import socket
    occupied = 0
    for name, port in sorted(DEFAULT_PORTS.items(), key=lambda kv: kv[1]):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            log.ok("Port %-8s %5d : libre" % (name, port))
        except OSError:
            occupied += 1
            log.warn("Port %-8s %5d : OCCUPE -> Run-LocalAI.bat basculera sur un port alternatif"
                     % (name, port))
        finally:
            s.close()
    return occupied


def main(argv=None):
    # >>> SECTION 1.1 : archive_installer() est la TOUTE PREMIERE instruction. <<<
    archived = archive_installer()
    # v3.1.1 (Section 1.3) : garantir l'arborescence de la sandbox avant tout.
    _ensure_sandbox_tree()

    argv = list(sys.argv[1:] if argv is None else argv)
    skip_model = ("--skip-model" in argv) or ("--skip-models" in argv)
    opts = {
        "skip_model": skip_model,
        "skip_models": skip_model,
        "skip_python": "--skip-python" in argv,
        "cache": os.path.join(BUILD, "downloads"),
        "prev_product": PRODUCT,
    }
    # Audit d'autonomie mono-bloc (v3.0.0) : permettre d'expliciter la source de l'heritage,
    # ce qui autorise une reconstruction complete du produit a partir d'une sauvegarde.
    if "--prev" in argv:
        _i = argv.index("--prev")
        if _i + 1 < len(argv):
            opts["prev_product"] = argv[_i + 1]

    for d in (BLACKBOX, DEV_DIR, QUARANTINE, LOGDIR, BUILD):
        os.makedirs(d, exist_ok=True)

    log = Log(os.path.join(LOGDIR, "install_%s.log" % _ts()))
    log.info("=" * 74)
    log.info("%s v%s  --  AiTron V3 natif" % (INSTALLER_NAME, __version__))
    log.info("Sandbox : %s" % SANDBOX)
    if STAGE:
        log.info("MODE STAGING ISOLE : produit -> %s" % PRODUCT)
        log.info("                     le produit stable %s n'est PAS touche."
                 % os.path.join(SANDBOX, "AiTron"))
    log.info("=" * 74)
    for kind, path in archived:
        log.ok("Boite noire : sauvegarde %-9s -> %s" % (kind, path))

    # Section 1.4 : triple validation AST du code embarque
    try:
        n = validate_deploy_code(AITRON_DEPLOY_CODE)
        log.ok("Validation AST du code embarque : OK (parse + compile + py_compile, %d noeuds)" % n)
    except Exception as exc:
        log.error("Validation AST ECHOUEE : %s" % exc)
        log.error("Rollback : aucun fichier produit n'a ete ecrit.")
        log.close()
        return 2

    sources = _locate_sources(log)
    log.info("-" * 74)
    _check_ports(log)
    _stop_existing(log)
    log.info("-" * 74)

    # Execution du code de deploiement (namespace isole + constantes injectees)
    ns = {}
    ns.update(_deploy_namespace())
    try:
        exec(compile(AITRON_DEPLOY_CODE, "<AITRON_DEPLOY_CODE>", "exec"), ns)
        deploy_product = ns["deploy_product"]
        build_manifest = ns["build_manifest"]
        swap_product = ns["swap_product"]
    except Exception as exc:
        log.error("Chargement du code de deploiement impossible : %s" % exc)
        log.close()
        return 2

    staging = PRODUCT + ".new"
    try:
        deploy_product(staging, sources, opts, log)
        manifest = build_manifest(staging, log, logical_root=PRODUCT)
        swap_product(staging, PRODUCT, log)
    except Exception as exc:
        # Section 1.5 : rollback transactionnel, jamais d'etat intermediaire casse.
        log.error("ECHEC critique du deploiement : %s" % exc)
        log.warn("Rollback : suppression de l'arborescence de staging %s" % staging)
        try:
            shutil.rmtree(staging, ignore_errors=True)
        except Exception:
            pass
        log.close()
        return 3

    log.info("-" * 74)
    log.ok("DEploiement termine. Composants inventories : %d" % manifest["component_count"])
    log.info("Produit   : %s" % PRODUCT)
    log.info("Lanceur   : %s" % os.path.join(PRODUCT, "launcher.bat"))
    log.info("Arret     : %s" % os.path.join(PRODUCT, "stop.bat"))
    log.info("API       : http://127.0.0.1:8080/v1/models")
    log.info("-" * 74)
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

