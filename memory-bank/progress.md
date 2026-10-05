# Progress — Ce qui marche, ce qui reste

## Versions livrées

| Version | Contenu | Statut |
|---------|---------|--------|
| v1.0.0 | Ouverture du chantier | ✅ |
| v1.1.0 | Portage Windows natif (CPU) | ✅ |
| v1.2.0 | Python + LiteLLM + multi-modal | ✅ |
| v1.3.0 | GPU (Vulkan/CUDA) + profils | ✅ |
| v1.4.0 | RAG multi-format + Agent Hub | ✅ |
| v1.4.1 | Watchdog VRAM + modèle image léger | ✅ |
| v1.5.0 | Vision + MCP | ✅ |
| v1.6.0 | GraphRAG + Failover SSE | ✅ |
| v1.7.0 | Quantization + Filtre PII | ✅ |
| v1.8.0 | DirectML/NPU + repli CPU | ✅ |
| v1.9.0 | Speculative Decoding | ✅ |
| v2.0.0 | Espace hermétique + Profil apprenant | ✅ |
| v2.1.0 | Fédération RPC | ✅ |
| v2.1.1 | i18n FR/EN | ✅ |
| v3.0.0 | Renommage AiTron V3 + audit | ✅ |
| v3.1.0 | Certification validée | ✅ |
| v3.1.1 | Portabilité installeur (détection dynamique + fallbacks) | ✅ |
| v3.1.2 | Binaires GitHub Releases (URLs pérennes + SHA-256) | ✅ |

## Ce qui marche

### Core
- ✅ Portage Windows natif (sans Docker, sans WSL)
- ✅ API OpenAI-compatible sur :8080
- ✅ Gateway LiteLLM sur :4000
- ✅ Streaming SSE

### Multi-modal
- ✅ Texte (llama.cpp)
- ✅ Vision (Qwen2-VL, SmolVLM)
- ✅ Image (stable-diffusion.cpp)
- ✅ Speech-to-text (whisper.cpp)
- ✅ Text-to-speech (kokoro)

### Intelligence
- ✅ RAG multi-format (PDF, Word, Excel, code, images)
- ✅ GraphRAG (extraction par LLM local)
- ✅ MCP (6 outils)
- ✅ Failover SSE (bufferisation + bascule)

### Sécurité
- ✅ Filtre PII (3 niveaux, best-effort)
- ✅ Espace hermétique AES-256-GCM
- ✅ Chiffrement au repos

### Performance
- ✅ Détection GPU (Vulkan/CUDA/CPU)
- ✅ Profils de performance (SOFT/NORMAL/HARD/AUTO/CUSTOM)
- ✅ Watchdog VRAM
- ✅ Profil apprenant continu
- ✅ Speculative Decoding (TEXT-ONLY, OPT-IN)

### Infrastructure
- ✅ Fédération RPC (découverte mDNS/UDP)
- ✅ i18n FR/EN (bascule à chaud)
- ✅ Installeur auto-suffisant
- ✅ Doctrine transactionnelle
- ✅ Traçabilité complète
- ✅ **Portabilité** : détection dynamique du répertoire (+ `--root`), création automatique de
  l'arborescence, clé USB / dossier neuf
- ✅ **Fallbacks GitHub Releases** : téléchargement des binaires (URLs pérennes) + SHA-256 vérifié
  + garde-fou d'intégrité PE « MZ »

## Ce qui reste à faire

### Court terme
- [ ] Publier le dépôt Git (commit initial + tag `v3.1.2`) — en cours
- [ ] Publier la release GitHub (binaires déjà hébergés)

### Moyen terme
- [ ] Signature numérique (SignPath, gratuit pour open-source)
- [ ] Segmentation des binaires (limite GitHub 25 Mo/fichier)
- [ ] Documentation publique enrichie (wiki)

### Long terme (optionnel)
- [ ] Support Linux/macOS
- [ ] Interface graphique native
- [ ] Marketplace de modèles/recettes
- [ ] Communauté

## Réalisations notables

1. **18 versions majeures** livrées en 3 jours
2. **19 anomalies** détectées et corrigées
3. **Certification** validée au vert par audit externe
4. **Zéro zombie** à chaque arrêt
5. **Coût total** : ~45 $ (construction + certification)
6. **Traçabilité** complète (CHANGELOG, DECISIONS, JOURNAL, etc.)

## Points d'attention

- **Produit stable** en v3.1.2 (G:\ + produit de test C:\TestGitHub)
- **Signature numérique** pas encore en place
- **Binaires** distribués via GitHub Releases
- **NPU AMD XDNA2** non fonctionnel via DirectML
- **Speculative Decoding** sans gain sur GPU-bound (OPT-IN)
