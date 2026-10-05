# System Patterns — Architecture d'AiTron V3

## Vue d'ensemble

    Client (OpenAI-compatible)
        ↓ HTTP
    LiteLLM Gateway (:4000) — routage local/externe
        ↓
    LocalAI Core (:8080) — API OpenAI-compatible
        ↓ gRPC
    cloud-proxy.exe — bridge gRPC natif
        ↓ HTTP
    llama-server.exe (:8090) — moteur d'inférence

## Composants

### Moteur principal
- `local-ai.exe` (186 Mo) — cœur LocalAI compilé en Go
- Nom conservé (c'est la technologie)
- Expose `/v1/*` (API OpenAI-compatible)

### Bridge gRPC
- `cloud-proxy.exe` (19 Mo) — backend gRPC natif Windows
- Compilé depuis `backend/go/cloud-proxy`
- Relaie les requêtes vers le moteur llama.cpp

### Moteur d'inférence
- `llama-server.exe` — moteur llama.cpp officiel (ggml-org)
- Variantes : CPU, Vulkan, CUDA (dans `backends\llama-cpp\variants\`)

### Backends multi-modaux (services HTTP séparés)
- `whisper-server.exe` (:8091) — speech-to-text
- `sd-server.exe` (:8092) — génération d'images
- `tts_server.py` (:8093) — text-to-speech (kokoro)

### Moteur vision
- `llama-server.exe` (:8095) avec `--mmproj`
- Modèles : Qwen2-VL, SmolVLM

### Gateway LiteLLM
- Python embarqué (`runtime\python\`)
- Port 4000
- Routage local/externe avec Token Saver

### Proxy failover SSE
- `failover_proxy.py` (:8081)
- Bufferisation complète + bascule locale/cloud

### Scripts d'orchestration
- `scripts\*.ps1` — PowerShell (hw_profile, engine_select, bench, vram_status, localai_up, localai_status, model_manager)
- `scripts\*.py` — Python (rag_ingest, mcp_gateway, graph_rag, failover_proxy, quantize_model, onnx_provider, spec_decoding, vault, learn_profile, peer_discovery)

## Design patterns

### Doctrine transactionnelle
- Sauvegarde ante-exécution (`archive_installer()`)
- Staging (`AiTron.new\`)
- Bascule par renommage (`AiTron\` → `AiTron.old\` → `AiTron.new\` → `AiTron\`)
- Rollback automatique

### Arborescence ouverte
- Moteur + backends + configs séparés
- Chaque composant remplaçable individuellement

### Détection dynamique
- Sandbox détectée (pas de chemin en dur)
- Variantes de moteur sélectionnées automatiquement (GPU/CPU)
- Fallbacks en cascade

### Traçabilité
- `dev\CHANGELOG.md` — versions
- `dev\DECISIONS.md` — décisions
- `dev\patch_integrity.log` — validation
- `dev\crash.log` — anomalies
- `dev\BETA_TEST_REPORT.md` — rapports de test
