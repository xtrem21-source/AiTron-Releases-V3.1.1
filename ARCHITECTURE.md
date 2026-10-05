# Architecture — AiTron V3

## Vue d'ensemble
    Client (OpenAI-compatible)
        | HTTP
        v
    LiteLLM Gateway (:4000)  --- routage local/externe
        |
        v
    LocalAI Core (:8080)     --- API OpenAI-compatible
        | gRPC
        v
    cloud-proxy.exe          --- bridge gRPC natif Windows
        | HTTP
        v
    llama-server.exe (:8090) --- moteur d'inference
        |
        v
    *.gguf                   --- modeles

## Composants
- local-ai.exe (186 Mo) — coeur Go
- cloud-proxy.exe (19 Mo) — bridge gRPC
- llama-server.exe — moteur llama.cpp (variantes CPU/Vulkan/CUDA)
- whisper-server.exe (:8091) — STT
- sd-server.exe (:8092) — images
- tts_server.py (:8093) — TTS
- llama-server.exe (:8095) — vision (--mmproj)
- litellm (Python embarque, :4000) — gateway
- failover_proxy.py (:8081) — failover SSE
- scripts\*.ps1, scripts\*.py — orchestration

## Design patterns
- Doctrine transactionnelle (sauvegarde + AST + rollback)
- Arborescence ouverte (composants remplacables)
- Detection dynamique (sandbox, variantes, fallbacks)
- Traabilite (CHANGELOG, DECISIONS, crash.log)

## Ports
| Port | Service |
|------|---------|
| 4000 | LiteLLM |
| 8080 | LocalAI Core |
| 8081 | Failover proxy |
| 8090 | llama-server |
| 8091 | whisper-server |
| 8092 | sd-server |
| 8093 | tts_server |
| 8094 | embed-server |
| 8095 | vision-server |

## Technologies
- Go : coeur, bridge
- Python : orchestrateur, LiteLLM
- PowerShell : scripts
- C++ : moteurs
- React : IHM embarquee

## Versions cles
- LocalAI : v4.11.0
- Go : 1.27.1
- Python embarque : 3.11.9
- LiteLLM : 1.103.2
- llama.cpp : b11375
- whisper.cpp : v1.9.2
- MCP SDK : 2.3.0

## Decisions
Voir dev\DECISIONS.md (D-001 a D-049).
