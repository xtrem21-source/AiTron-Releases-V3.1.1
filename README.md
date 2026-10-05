# AiTron V3

> **Plateforme d'IA locale souveraine pour Windows — sans Docker, sans WSL.**

AiTron V3 est un **fork independant de LocalAI** (licence MIT),
enrichi d'une couche d'orchestration souveraine pour Windows : installeur unique,
arborescence ouverte, doctrine transactionnelle, portabilite cle USB.

**Version actuelle :** v3.1.2 (binaires GitHub Releases) — voir VERSION.

## Points cles
- Installeur unique auto-suffisant (~330 Ko)
- Doctrine transactionnelle (sauvegarde, AST, rollback)
- Arborescence ouverte (moteur + backends + configs separes)
- Portabilite (detection dynamique, fallbacks)
- Multi-modal (texte, vision, image, audio, TTS)
- RAG multi-format (PDF, Word, Excel, code, images)
- GraphRAG par LLM local
- MCP (6 outils, spec 2024-11-05)
- Failover SSE (bufferisation + bascule)
- Filtre PII hybride (3 niveaux)
- Espace hermetique AES-256-GCM
- Profil apprenant continu
- Federation RPC
- i18n FR/EN

## Installation rapide
    cd G:\V1\LocalAI-Projet
    python install_AiTron_v3.py

## Utilisation rapide
    cd AiTron
    Run-LocalAI.bat start
    Run-LocalAI.bat status

## Documentation
Voir QUICKSTART.md, INSTALLATION.md, ARCHITECTURE.md, SECURITY.md, CHANGELOG.md.

## Licence
MIT — voir LICENSE.
AiTron V3 est un fork independant de LocalAI. Non affilie au projet officiel.
