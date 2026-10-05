# Changelog — AiTron V3

> Resume. Voir dev\CHANGELOG.md pour l'historique complet.

## v3.1.3 — 2026-10-05 (Release GitHub v3.1.2)
- Release GitHub v3.1.2 creee (gh CLI) : binaires local-ai.exe + cloud-proxy.exe
- URLs de fallback basculees sur download/v3.1.2/ (SHA-256 inchanges)
- Garde-fou PE "MZ" conserve

## v3.1.2 — 2026-10-05 (Binaires GitHub Releases)
- Fallbacks de telechargement vers GitHub Releases (URLs perennes, binaires directs)
- SHA-256 integres pour local-ai.exe et cloud-proxy.exe (verifies au telechargement)
- Garde-fou PE "MZ" conserve et renforce (applique a tout .exe telecharge)

## v3.1.1 — 2026-10-05 (Portabilite totale de l'installeur)
- Detection dynamique du repertoire de la sandbox (plus aucun chemin en dur ; option --root)
- Creation automatique de l'arborescence au premier lancement (cle USB, dossier neuf)
- Fallbacks de telechargement en cascade + garde-fou d'integrite PE "MZ"

## v3.1.0 — 2026-10-04 (CERTIFICATION VALIDEE AU VERT)
- Traduction IHM complete (1 597 / 1 597 cles, 100,0 %)
- 13 defauts corriges (D1-D13)
- Certification validee par audit externe

## v3.0.0 — 2026-10-03 (Identite AiTron V3 + audit d'autonomie)
- Renommage : install_localai_win.py -> install_AiTron_v3.py
- Renommage : LocalAI\ -> AiTron\
- Audit d'autonomie mono-bloc (reconstruction verifiee)

## v2.1.1 — 2026-10-03 (i18n FR/EN)
- Support bilingue a trois couches
- Bascule a chaud via CLI

## v2.1.0 — 2026-10-03 (Federation RPC)
- Decouverte reseau UDP broadcast
- Routage federe RPC
- Repli CPU automatique

## v2.0.0 — 2026-10-03 (Espace hermetique + Profil apprenant)
- Chiffrement AES-256-GCM au repos
- Profil apprenant continu

## v1.9.0 — 2026-10-03 (Speculative Decoding TEXT-ONLY)
- Decodage speculatif (OPT-IN)

## v1.8.0 — 2026-10-03 (NPU/DirectML)
- Acceleration universelle NPU
- Repli CPU obligatoire

## v1.7.0 — 2026-10-03 (Quantization + PII)
- Quantization locale
- Filtre PII hybride 3 niveaux

## v1.6.0 — 2026-10-03 (GraphRAG + Failover SSE)
- GraphRAG par LLM local
- Failover SSE transparent

## v1.5.0 — 2026-10-03 (Vision + MCP)
- Vision locale
- Protocole MCP

## v1.4.0 — 2026-10-03 (RAG + Agent Hub)
- Pipeline RAG multi-format
- Agent Hub LiteLLM

## v1.3.0 — 2026-10-03 (GPU)
- Detection GPU multi-constructeur
- Variantes llama.cpp

## v1.2.0 — 2026-10-03 (Python + LiteLLM + Multi-modal)
- Python embarque
- Gateway LiteLLM
- Backends multi-modaux

## v1.1.0 — 2026-10-03 (Portage Windows natif)
- Coeur LocalAI compile
- Bridge gRPC natif
- Moteur llama.cpp

## v1.0.0 — 2026-10-03 (Ouverture du chantier)

Historique complet : dev\CHANGELOG.md
