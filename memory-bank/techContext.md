# Tech Context — Technologies d'AiTron V3

## Langages
- **Go** : cœur LocalAI (`local-ai.exe`), bridge gRPC (`cloud-proxy.exe`)
- **Python** : orchestrateur, scripts, gateway LiteLLM, backends TTS
- **PowerShell** : scripts d'orchestration Windows
- **Batch** : lanceurs (`Run-LocalAI.bat`, `launcher.bat`, `stop.bat`)
- **C++** : moteur llama.cpp (`llama-server.exe`), whisper.cpp, stable-diffusion.cpp
- **JavaScript/React** : IHM embarquée dans le cœur

## Versions clés
- **LocalAI** : v4.11.0 (compilé localement, `CGO_ENABLED=0`)
- **Go** : 1.27.1
- **Python embarqué** : 3.11.9
- **LiteLLM** : 1.103.2
- **llama.cpp** : b11375 (ggml-org)
- **whisper.cpp** : v1.9.2
- **stable-diffusion.cpp** : master-929-3f8527a
- **kokoro-onnx** : model-files-v1.1
- **MCP SDK** : 2.3.0 (spec 2024-11-05)
- **cryptography** : AES-256-GCM
- **numpy** : >=1.24.0
- **pypdf** : >=4.0.0
- **python-docx**, **openpyxl** : pour RAG multi-format

## Dépendances principales
- **Go** : gRPC, HTTP, SQLite (CGO_ENABLED=0)
- **Python** : litellm, kokoro-onnx, soundfile, numpy, pypdf, python-docx, openpyxl, cryptography, mcp, prisma
- **PowerShell** : natif Windows
- **Windows** : DirectML (pour NPU)

## Matériel supporté
- **CPU** : x86_64, ARM64 (Linux)
- **GPU NVIDIA** : CUDA 12.4, 13.1 (Pascal+), Vulkan
- **GPU AMD** : ROCm/HIP, Vulkan
- **GPU Intel** : Vulkan
- **NPU Intel** : DirectML/OpenVINO
- **NPU AMD XDNA2** : **EXPÉRIMENTAL ET NON FONCTIONNEL** via DirectML → repli CPU

## Prérequis système
- **OS** : Windows 10/11 64 bits
- **RAM** : 8 Go minimum, 16+ recommandé
- **Disque** : ~12 Go (avec modèles)
- **Python** : 3.10+ (pour lancer l'installeur ; runtime embarqué dans le produit)
- **GPU** : optionnel

## Interdictions techniques
- **Pas de Docker**
- **Pas de WSL** (sauf dernier recours documenté)
- **Pas de packaging monolithique** (PyInstaller, `go build -ldflags "-s -w"` en un seul binaire)
- **Pas de chemin en dur** (détection dynamique)
- **Pas de faiss** (NumPy pur pour la similarité cosinus)

## Endpoints
- **LocalAI** : `http://127.0.0.1:8080/v1` (API directe)
- **LiteLLM** : `http://127.0.0.1:4000` (gateway, authentifié `Bearer sk-local`)
- **Whisper** : `http://127.0.0.1:8091/v1/audio/transcriptions`
- **SD** : `http://127.0.0.1:8092/v1/images/generations`
- **TTS** : `http://127.0.0.1:8093/v1/audio/speech`
- **Vision** : `http://127.0.0.1:8095/v1/chat/completions`
- **Failover** : `http://127.0.0.1:8081`
- **IHM web** : `http://127.0.0.1:8080/app`
