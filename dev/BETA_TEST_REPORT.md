# BETA_TEST_REPORT.md — Mode BÊTA-TESTEUR FOU (Phase 2 / v1.2.0)

> Mandat Section 11. Épreuve intensive de l'écosystème en conditions réelles, corrective immédiate,
> puis rapport. Aucun bug connu laissé en vie.

## 1. Scénarios éprouvés (Section 11.1)

| # | Scénario | Méthode | Verdict |
|---|----------|---------|---------|
| 1 | Robustesse des backends | Démarrage individuel de chaque moteur + API testée (`/health`, endpoints) | ✅ OK |
| 2 | Robustesse du routage LiteLLM | `local-llama` (court) → local ; `smart` (long, sans clé) → repli local ; `smart` avec clé | ✅ OK |
| 3 | Robustesse du Model Manager | `list`, `pull` (id inconnu → erreur claire), `pull` (existant → hash vérifié) | ✅ OK |
| 4 | Robustesse du CLI wrapper | `start`, `stop`, `status`, `pull`, `list`, `backends`, `help` + commande inconnue | ✅ OK |
| 5 | Robustesse multi-modale | texte (chat), audio (STT JFK), audio (TTS WAV), image (binaire présent) | ✅ OK |
| 6 | Robustesse de l'arrêt | `stop` → aucun PID survivant, ports libérés | ✅ OK |
| 7 | Robustesse du routage hybride | panne clé cloud simulée (clé absente) → repli local immédiat | ✅ OK |

## 2. Anomalies détectées et CORRIGÉES

| # | Catégorie | Anomalie | Correctif |
|---|-----------|----------|-----------|
| A1 | ROUTING | LiteLLM : `UnicodeEncodeError` (bandeau) sur cp1252 | `PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8` + reconfiguration UTF-8 |
| A2 | ROUTING | `Scripts\litellm.exe` pointe vers le Python **d'origine** | lanceur `config\litellm_launch.py` (entry point `litellm:run_server`) |
| A3 | ROUTING | `PYTHONPATH` ignoré (mode isolé `._pth`) → callback non importable | lanceur dans `config\` → `sys.path[0]` |
| A4 | ROUTING | `openai/local` → `model "local" not found` | `openai/llama-3.2-1b-instruct` |
| A5 | BACKEND | Cœur LocalAI → HTTP 401 (clé d'API activée par erreur) | ne plus exporter `LOCALAI_API_KEY` ; `LOCALAI_LOCAL_KEY` pour LiteLLM |
| A6 | MULTIMODAL | TTS : 0 voix (`get_voices()` renvoie une liste) | gestion dict/list ; défaut `af_maple` |
| A7 | BACKEND | Whisper : `/v1/audio/transcriptions` → 404 | `--inference-path /v1/audio/transcriptions` |
| A8 | MODEL | Whisper « Invalid request » : fichier de test = page HTML (fausse alerte) | retéléchargement depuis `raw.githubusercontent.com` (vérif. RIFF) |
| A9 | SHUTDOWN | Bascule impossible : produit verrouillé par un lanceur précédent | `_stop_existing()` (stop + taskkill + arrêt des binaires du produit) |
| A10 | SHUTDOWN | `start` créait des services en doublon | `start` idempotent (arrêt avant remise à zéro de `pids.txt`) |
| A11 | SHUTDOWN | Services Python (TTS/LiteLLM) orphelins après `stop` | nettoyage Python rattaché au produit dans `stop.bat` |
| A12 | CLI | `backends` n'affichait pas le backend TTS (Python, sans `.exe`) | détection étendue aux `*.py` |

## 3. Scénario de « crash et reprise » (Section 11.1.1)
- `taskkill` ciblé sur un moteur → `status` signale immédiatement `stopped` et met l'endpoint `DOWN`.
- `Run-LocalAI.bat start` relance proprement l'ensemble (idempotent) et l'endpoint repasse `UP`.
- Aucun processus zombie après cycles répétés `start`/`stop`.

## 4. Anomalies restantes (assumées et documentées)
- **Image (SD) : modèle non téléchargé par défaut** (~5 Go). Le binaire `sd-server.exe` est installé et
  vérifié (`--help`) ; l'endpoint 8092 n'est actif qu'après `Run-LocalAI.bat pull sd-turbo`.
  *Raison : respect de la consigne « pas de téléchargement massif » (Section 4.4).*
- **Routage externe non testé bout-en-bout** : aucune clé cloud n'est fournie dans la sandbox (BYOK).
  Le repli local est vérifié ; le chemin externe est validé par construction (LiteLLM + `os.environ/...`).

## 5. Recommandations pour la v1.3.0
1. **Supervision** : healthcheck périodique + redémarrage automatique des moteurs (watchdog).
2. **Images** : intégrer un modèle SD léger (ex. SD-Turbo quantifié) dans le catalogue `recommended`.
3. **Multi-modèle** : plusieurs GGUF simultanés et routage par nom de modèle dans LiteLLM.
4. **GPU** : variantes CUDA/Vulkan des moteurs (substitution dans `backends\llama-cpp\`).
5. **Sécurité** : rotation des clés BYOK, chiffrement de `cloud-keys.env` au repos.
6. **UI** : exposer un tableau de bord de statut (déjà servi par le cœur LocalAI sur `/app`).

## 6. Verdict
Écosystème multi-modal et routé **opérationnel** sous Windows natif (sans Docker, sans WSL).
Toutes les anomalies détectées ont été corrigées et re-testées ; le cœur Go reste inchangé (aucune régression).

---
# PHASE 3 (v1.3.0) — BÊTA-TEST GPU

## 7. Scénarios éprouvés (mandat Section 10.1)

| # | Scénario | Méthode | Verdict |
|---|----------|---------|---------|
| 1 | Détection GPU | `nvidia-smi` (NVIDIA) / absence ROCm / présence Vulkan / repli CPU | ✅ (NVIDIA détecté, Vulkan retenu, CPU en repli) |
| 2 | Téléchargement variantes | cpu + vulkan + cuda + cudart, SHA-256 vérifiés | ✅ |
| 3 | Calcul `-ngl` | budget VRAM vs modèle+cache KV ; cas « modèle trop gros » simulé (marge) | ✅ (ngl=99 ; bascule CPU si ratio<0.75) |
| 4 | Profils | `set-profile soft/normal/hard` puis `optimize` | ✅ persistés dans `hardware-profile.json` |
| 5 | Benchmark CPU vs GPU | `benchmark` et `benchmark cpu` | ✅ voir §8 |
| 6 | Multi-modal GPU | TTS provider ONNX (DML→CUDA→CPU) ; SD CUDA installé ; whisper (pas de build GPU x64) | ⚠️ partiel (documenté) |
| 7 | Arrêt | `stop` → zéro zombie + VRAM libérée | ✅ |

## 8. Benchmark CPU vs GPU (réel, Llama-3.2-1B Q4_K_M)

| Profil / backend | ngl | threads | ctx | tok/s (génération) | GPU util | VRAM |
|---|---|---|---|---|---|---|
| **CPU** (`benchmark cpu`) | 0 | 8 | 4096 | **14,91** | — | — |
| **GPU Vulkan** (`benchmark`) | 99 | 8 | 4096 | **71,41** | 85-99 % | ~1245 Mo |

→ **Accélération GPU ≈ 4,8×**. VRAM libérée à l'arrêt : 1245 → 652 Mo. Aucun zombie.

*Mesures de confirmation (2ᵉ campagne, même matériel) :* GPU **70,19 tok/s** · CPU **16,38 tok/s**
(→ ratio ≈ 4,3×). Valeurs consignées dans `config\bench-history.jsonl`.

## 9. Tableau des profils (calculés pour cette machine)

| Profil | marge VRAM | ngl | threads | ctx | Appliqué |
|---|---|---|---|---|---|
| soft | 1536 Mo | 0 (CPU) | 4 (cœurs) | 4096 | ✅ |
| normal | 1024 Mo | 99 (auto) | 8 | 4096 | ✅ |
| hard | 768 Mo | 99 (auto) | 8 | 4096 (8192 si VRAM ≥ 8 Go) | ✅ |
| auto | dynamique | → normal | 8 | 4096 | ✅ |
| custom | 1024 Mo | manuel | manuel | manuel | mécanisme validé |

Sécurité VRAM : `optimal` (ratio ≥1.05), `possible` (≥0.75), sinon **bascule CPU automatique**.

## 10. Anomalies GPU détectées et corrigées

| # | Catégorie | Anomalie | Correctif |
|---|-----------|----------|-----------|
| G1 | GPU_DOWNLOAD | CUDA prébuild → `invalid device function` (Maxwell CC 5.2) | repli automatique **Vulkan** ; CUDA documenté inutilisable ici |
| G2 | PROFILE | `$Model`/`$model` (PowerShell insensible à la casse) → champs du modèle nuls | objet renommé `$mdl` |
| G3 | MULTIMODAL | DirectML échoue (`ConvTranspose`, 0x80070057) et casse aussi le CPU | sélection de provider **avec repli automatique** ; retour à `onnxruntime` 1.30.0 |
| G4 | GPU_DETECT | `AdapterRAM` WMI tronqué (4293918720) | VRAM de référence via `nvidia-smi` ; repli registre `qwMemorySize` + marge 85 % |
| G5 | MULTIMODAL | Whisper : aucun build GPU x64 dans la release Windows | documenté (whisper reste CPU) |

## 11. Notes multi-modales GPU
- **Texte (llama.cpp)** : GPU via **Vulkan** (vérifié, 4,8×).
- **TTS (kokoro/ONNX)** : sélection DML→CUDA→CPU avec sonde ; sur cette machine repli **CPU**
  (`provider=CPUExecutionProvider` dans `/health`). Sur GPU compatibles, DirectML/CUDA seront retenus
  automatiquement.
- **Image (stable-diffusion.cpp)** : variante **CUDA installée** (`backends\stable-diffusion\variants\cuda\`)
  mais non vérifiée en runtime (modèle SD ~5 Go non téléchargé par défaut).
- **Audio (whisper.cpp)** : pas de binaire GPU x64 fourni → CPU.

## 12. Recommandations pour la v1.4.0
1. **Supervision GPU** : watchdog des moteurs + surveillance VRAM (auto-éviction, `--memory-reclaimer` du cœur).
2. **CUDA custom** : build `sm_52+` documenté (ou binaire alternatif) pour les GPU Maxwell.
3. **Modèle image léger** : intégrer un SD-Turbo quantifié (≤1 Go) dans le catalogue `recommended`.
4. **Compression de contexte** : ajuster `ctx` selon la longueur réelle des prompts (éviter le surdimensionnement).
5. **Multi-GPU** : sélection du GPU (`CUDA_VISIBLE_DEVICES`/`GGML_VK_DEVICE`) et `--tensor-split`.
---
# PHASE 4 (v1.4.0) — BÊTA-TEST RAG & AGENT HUB

## 13. Scénarios éprouvés (mandat Section 4)

| # | Scénario | Méthode | Verdict |
|---|----------|---------|---------|
| 1 | **Pipeline multi-format** | corpus de test `.txt/.py/.pdf/.docx/.xlsx` → `Run-LocalAI.bat index` | ✅ 5 fichiers, 5 chunks, 2048 dims, index à plat, aucune exception |
| 2 | **Recherche vectorielle** | `Run-LocalAI.bat rag-query "<question multi-mots>"` | ✅ top-5 cosinus (voir §14) |
| 3 | **Routage hybride** | modèle virtuel `localai` : prompt court / complexe / contexte saturé / clé présente | ✅ 4 cas validés (voir §15) |
| 4 | **Arrêt & verrou** | `stop` après indexation + services | ✅ zéro zombie, ports libérés, VRAM 442 Mo |
| 5 | **Journalisation des crashs** | catégories `RAG_INGEST`, `VECTOR_DB`, `PROXY_GATEWAY` | ✅ `dev\crash.log` enrichi |

## 14. Résultats d'indexation et de recherche (réels)

```
[rag] 5 fichier(s) candidat(s) dans ...\corpus_test
[rag] serveur d'embeddings pret (pid 5440, port 8094)
[rag] embeddings de 5 chunks ...
[rag] index 'default' : 5 chunks x 2048 dims en 7.8s
```

| Rang | Score cosinus | Source | Type |
|---|---|---|---|
| 1 | 0.7694 | `notes.txt` | texte brut |
| 2 | 0.7693 | `rapport.pdf` | PDF (pypdf) |
| 3 | 0.7586 | `rapport.docx` | Word (python-docx) |
| 4 | 0.6207 | `sample.py` | code source |
| 5 | 0.5864 | `mesures.xlsx` | Excel (openpyxl) |

→ Les **5 formats** sont extraits, chunkés, vectorisés et retrouvés : le pipeline est réellement
multi-format. Rappel : **faiss n'est pas utilisé** (proscrit) — similarité cosinus NumPy pure.

## 15. Routage Token Saver (modèle virtuel `localai`)

| Cas | Entrée | Modèle sélectionné | Raison (journalisée) |
|---|---|---|---|
| prompt court | « Bonjour, qui es-tu ? » | `local-llama` | prompt court / complexe selon seuil |
| prompt complexe, sans clé | question longue | `local-llama` | `prompt complexe, aucune cle cloud -> local` |
| **contexte saturé**, sans clé | ~200 tokens (seuil 100 en test) | `local-llama` | `contexte sature (200 tok > 100)` |
| **clé cloud présente** | clé DeepSeek fournie | **`deepseek`** | bascule cloud effective |

Toutes les décisions sont visibles via `Run-LocalAI.bat proxy-logs` (fichier `logs\routing.jsonl`).

## 16. Anomalies détectées et corrigées (Phase 4)

| # | Catégorie | Anomalie | Correctif |
|---|-----------|----------|-----------|
| R1 | RAG_INGEST | `/v1/embeddings` → 400 « Pooling type 'none' is not OAI compatible » | `--pooling mean` sur l'instance d'embeddings |
| R2 | RAG_INGEST | `lxml` inutilisable hors runtime 3.11 (ABI cp311) | usage exclusif du Python embarqué 3.11 |
| R3 | VECTOR_DB | `rag-query "texte libre"` : le 2ᵉ mot était pris pour la collection | reconstitution de la requête complète (`%*`) |
| R4 | PROXY_GATEWAY | en-têtes de templates avalés par un patch mal ancré (AST rouge) | restauration + règle d'ancrage renforcée |
| R5 | PROXY_GATEWAY | `keys.env` réutilisait l'en-tête de `cloud-keys.env` | gabarit `KEYS_ENV` dédié |

## 17. Recommandations pour la v1.5.0
1. **Recherche hybride** BM25 + vecteurs, et **re-ranking** des top-K par le LLM local.
2. **RAG dans le chat** : injection automatique du contexte RAG dans les requêtes (retrieval-augmented).
3. **Watchdog GPU/VRAM** (reporté de la v1.3.0) : supervision des moteurs et éviction mémoire.
4. **Collections multiples** exposées dans `Run-LocalAI.bat` (`--collection`).
5. **Index incrémental** : n'embarquer que les fichiers nouveaux/modifiés (hash par fichier).
6. **Observabilité** : endpoint `/metrics` agrégé (ports, VRAM, taille d'index, décisions de routage).

---

# PHASE 4.1 — RAPPORT BÊTA-TEST v1.4.1 (micro-incrément de finition)

**Date** : 2026-10-03 · **Version** : v1.4.1 · **Machine** : i7-6700HQ (4c/8t), 32 Go RAM,
NVIDIA GTX 970M 6 Go (Maxwell CC 5.2) · **Verdict** : ✅ **AU VERT**

## 18. Environnement de test
| Élément | Valeur |
|---|---|
| Sandbox | `G:\V1\LocalAI-Projet\` (aucune écriture hors périmètre) |
| Version globale | **v1.4.1** (`manifest.json` → `installer_version`) |
| Composants déployés | **70** |
| Backend GPU retenu | `vulkan` (`ngl=99`, `threads=8`, `ctx=4096`) |
| Python | embarqué 3.11.9 (runtime isolé) |

## 19. Section 1 — Watchdog VRAM
| Test | Résultat |
|---|---|
| `Run-LocalAI.bat vram-status` | **OK** — `6144 Mo` total, `528 Mo` utilisée, `5563 Mo` libre (**90,54 %**), état `ok`, seuils affichés |
| Seuils déclarés | **OK** — alerte `< 15 %`, critique `< 5 %`, reprise `> 20 %` |
| Alerte simulée (`--alert 99`) | **OK** — `[GPU_VRAM] [WARN] VRAM faible : 90.4% libre (< 99%)` → `logs\vram.log` **et** `dev\crash.log` |
| Critique simulé (`--crit 99 --no-action`) | **OK** — `[GPU_VRAM] [CRITICAL]` + `data\vram-action.json` (`applied:false`, action désactivée) |
| **Action préventive réelle** | **OK** — moteur relancé `-ngl 0`, `applied:true` ; ligne de commande vérifiée : `… -ngl 0 --threads 8 -c 4096 …` ; chat `HTTP 200` → « Bonjour » |
| Reprise (`> 20 %`) | **OK** — effacement de l'état d'alerte (retour `ok`) |
| `data\vram-status.json` | **OK** — `watchdog: running`, `free_pct`, seuils, horodatage |
| `Run-LocalAI.bat start --no-watchdog` | **OK** — `watchdog VRAM desactive pour cette session.` + `watchdog VRAM desactive (--no-watchdog)` ; **absent** de `data\pids.txt` |
| Thread activé par `start` | **OK** — `watchdog VRAM PID=604 (alerte<15%, critique<5%, reprise>20%)` |

## 20. Section 2 — Modèle image léger
| Test | Résultat |
|---|---|
| Entrée catalogue | **OK** — `list` affiche `sd-turbo-light  image  gguf  1880 Mo  [recommande]` |
| `pull sd-turbo-light` | **OK** — téléchargement puis `[model-manager] OK : …\sd_turbo-f16-q8_0.gguf` |
| Vérification SHA-256 | **OK** — `d50be7655f0a554cf8041c145d88b210bd5f3c545423119dee62ae08cae51580` = valeur du catalogue → `HASH OK` |
| Taille réelle | **1930 MiB (≈ 1,88 Go)** — conforme à la cible `< 2 Go` |
| Chargement par `sd-server` | **OK** — `sd-server PID=6888 (:8092) modele=sd_turbo-f16-q8_0.gguf` (priorité sur le safetensors 5,21 Go) |
| **Génération d'image d'évaluation** | **OK** — `sampling completed 150,06 s` + `latent decoded 67,80 s` + `generate_image completed in 219,56 s` ; réponse `HTTP 200`, **537 393 octets** |
| Image produite | **OK** — `build\eval_image.png`, signature `\x89PNG\r\n\x1a\n`, **512 × 512**, 393,5 Ko |

> Lancer `--steps 4` sur les modèles *turbo* : temps de génération divisé par **~5** (20 → 4 étapes).

## 21. Section 3 — Documentation & automatisation CUDA Maxwell (sm_52+)
| Test | Résultat |
|---|---|
| Section `INSTALLATION.md` §31 | **OK** — erreur `invalid device function` expliquée + commande exacte<br>`cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release` |
| Détection `variants\cuda\custom-build.txt` | **OK** — marqueur présent → `active_variant = cuda`, `cuda_custom_build = true`,<br>raison « NVIDIA via cuda (build personnalise sm_52+ detecte) » |
| Retour à l'état sûr | **OK** — marqueur retiré → `active_variant = vulkan`, `cuda_custom_build = false` |
| Section `INSTALLATION.md` §32 | **OK** — modèle léger documenté (dont la déviation D-024) |
| Section `INSTALLATION.md` §30 | **OK** — watchdog documenté (seuils, CLI, variables d'environnement) |

## 22. Section 4 — Hygiène d'exécution
| Test | Résultat |
|---|---|
| Arrêt propre | **OK** — `[LocalAI] Tous les processus sont arretes. Zero zombie.` |
| Vérification indépendante | **OK** — aucun `llama-server` / `whisper-server` / `sd-server` / `tts_server` / `local-ai` / `litellm` résiduel |
| Ports libérés | **OK** — 8080, 8090, 8091, 8092, 8093, 4000 : aucune écoute |
| Processus Python résiduels | **OK** — aucun client bloqué |
| Arrêt d'un moteur relancé par le watchdog | **OK** — le nouveau PID (inscrit dans `pids.txt`) est bien arrêté |

## 23. Anomalies rencontrées et auto-healing (traçabilité QA)
| # | Anomalie | Cause racine | Correctif | Statut |
|---|---|---|---|---|
| A1 | Action préventive inopérante (`applied:false`) | `data\llama-cmd.json` écrit avec **BOM UTF-8** (`Set-Content -Encoding UTF8`) → `json.load` refuse | lecture `utf-8-sig` (Python) **et** écriture `[IO.File]::WriteAllText(…, UTF8Encoding($false))` (PS1) | ✅ corrigé, re-testé |
| A2 | `--extra-sample-args steps=4` ignoré | `steps` n'est pas une clé `extra-sample-args` pour ce moteur | usage du flag CLI **`--steps 4`** (documenté par `sd-server --help`) | ✅ corrigé, 4/4 étapes |
| A3 | Bannière affichant `v1.2.0` | version figée dans `localai_up.ps1` (et en-têtes CLI/profil/état) | placeholder **`__VERSION__`** substitué au déploiement (`_write_text`) | ✅ corrigé |
| A4 | `%%` littéral dans l'affichage du watchdog | échappement erroné dans le format PowerShell | format corrigé (`%`) | ✅ corrigé |
| A5 | Insertion d'un gabarit consommant la ligne d'en-tête suivante | édition textuelle des gabarits | **validation AST** après chaque patch (détection + reconstruction) | ✅ maîtrisé |

## 24. Verdict
- **Sections 1, 2, 3 et 4 du mandat : livrées et validées en conditions physiques réelles.**
- **Doctrine transactionnelle respectée** : `archive_installer()` en tête de `main()`, `manifest.json`
  `root` = chemin de production final, triple validation AST, déploiement transactionnel avec rollback.
- **Aucun zombie**, aucune écriture hors sandbox, aucune dépendance Docker/WSL, cœur Go inchangé.
- **PHASE 4.1 / v1.4.1 VALIDÉE ET RATIFIÉE.**

---

# PHASE 5 — RAPPORT BÊTA-TEST v1.5.0 (JALON 3)

**Date** : 2026-10-03 · **Version** : v1.5.0 · **Machine** : i7-6700HQ, 32 Go, GTX 970M 6 Go ·
**Verdict** : ✅ **AU VERT** · Exécution en sous-étapes étanches **v1.5.0a** (vision) / **v1.5.0b** (MCP).

## 25. Vision locale multi-modale
| Test | Résultat |
|---|---|
| Catalogue à deux URLs (+ `mmproj`) | **OK** — `qwen2-vl-2b` (942+676 Mo), `smolvlm-500m` (420+100 Mo) |
| Téléchargement **atomique** | **OK** — `acquisition ATOMIQUE de 2 fichiers (les deux ou rien)` ; aucun fichier publié tant que les deux SHA-256 ne sont pas validés ; `paire modele + projecteur publiee (atomique)` |
| Injection `--mmproj` | **OK** — ligne de commande : `-m Qwen2-VL-2B-Instruct-Q4_K_M.gguf --mmproj mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf` |
| Inférence vision (image locale 512×512) | **OK** — `HTTP 200` → « Un tableau de fruits, avec une **pomme rouge** … sur une **table en bois** » |
| Moteur vision stable | **OK** — `/health` → `{"status":"ok"}` (CPU, `-ngl 0`, cf. D-029) |
| Images dans les métadonnées RAG | **OK** — `{"kind":"image","format":"png","width":512,"height":512,"bytes":402991,"megapixels":0.262}` |

## 26. Protocole MCP (spécification 2024-11-05)
| Test | Résultat |
|---|---|
| SDK officiel, aucune réimplémentation | **OK** — `mcp 2.3.0` (JSON-RPC 2.0 stdio) |
| `mcp-list` | **OK** — `Serveurs declares : 1 | outils visibles : 5` ; serveur `localai [up]` |
| `mcp-test` (list_tools + call_tool) | **OK** — `client stdio sur 'localai' : {"localai":"up"}` ; 5 outils vus ; **VERDICT VERT** |
| `mcp-call` payload propre | **OK** — `isError:false` ; `localai_vram_status` et `localai_vision_caption` renvoient un JSON structuré |
| `call_tool` vision via client MCP | **OK** — `isError:false`, légende correcte (376 tokens / 40,8 s) |
| Déclaration centralisée | **OK** — `config\mcp-settings.json` (serveurs + outils), préservé à la réinstallation |

## 27. Non-régression v1.4.1 (sur la pile v1.5.0)
| Test | Résultat |
|---|---|
| Ports 8080 / 8090 / 8092 / 4000 / **8095** | **OK** |
| Inférence texte (cœur et gateway `sk-local`) | **OK** — `PONG` |
| Sécurité gateway (sans clé) | **OK** — **HTTP 401** |
| Watchdog VRAM | **OK** — `watchdog VRAM PID=… (alerte<15%, critique<5%, reprise>20%)` |
| Suite JALON 1 rejouée sur v1.5.0 | **7/7 OK** |

## 28. Anomalies v1.5.0 et auto-healing
| # | Anomalie | Correctif | Statut |
|---|---|---|---|
| A6 | Modèles vision perdus à chaque réinstallation | Héritage étendu (SD-Turbo + paires vision) | ✅ |
| A7 | Le mode `serve` transformé en chemin → serveur stdio muet | Résolution sélective des arguments | ✅ |
| A8 | Quoting shell consommant le JSON de `mcp-call` | Option `--args-file` + garde `.bat` | ✅ |
| A9 | **`Vulkan device lost`** (mtmd) sur Maxwell → vision HS | Moteur vision en **CPU** par défaut (D-029) | ✅ |
| A10 | `os.kill(pid, 0)` → `WinError 87` sous Windows | Sonde `OpenProcess` (ctypes) portable | ✅ |
| A11 | Titre `vram-status` figé sur v1.4.1 | Placeholder `__VERSION__` | ✅ |

## 29. Verdict JALON 3
- Sections **1 et 2 du mandat v1.5.0 livrées et validées** en conditions réelles (GPU physiques, image
  réelle, appels MCP réels).
- **Doctrine respectée** : `archive_installer()` en tête de `main()`, `manifest.json` `root` = chemin
  final, triple validation AST à chaque patch, déploiement transactionnel, **zéro zombie** à l'arrêt.
- **PHASE 5 / v1.5.0 VALIDÉE ET RATIFIÉE.**

---

# PHASE 6 — RAPPORT FINAL v1.6.0 (JALON 5 : validation combinée et gel)

**Date** : 2026-10-03 · **Version** : **v1.6.0** · **Machine** : i7-6700HQ, 32 Go, GTX 970M 6 Go ·
**Verdict** : ✅ **AU VERT — SYSTÈME GELÉ ET LIVRÉ**

## 30. GraphRAG par LLM local
| Test | Résultat |
|---|---|
| Extraction **déléguée au LLM local** (aucune regex) | **OK** — `llama-server /v1/chat/completions`, `T=0`, prompt exigeant un tableau JSON strict |
| Parsing robuste (sortie tronquée) | **OK** — l'arrêt à `max_tokens` était fatal (0 triplet) ; récupération des **objets complets déjà émis**, `max_tokens=256`, consigne de fermeture → **42 triplets** extraits |
| Interdépendances **structurelles** du code | **OK** — **8 arêtes** `kind:"structural"` (imports Python/Go/JS/PS1/BAT), distinctes des arêtes `kind:"llm"` |
| Sérialisation **à plat** | **OK** — `runtime\storage\graph_db.json` (`nodes` + `edges` + `stats` + `engine` + `provenance`) |
| Volume produit (scripts du portage) | **22 nœuds / 50 arêtes** sur 6 chunks, **0 échec** |
| `Run-LocalAI.bat graph-show` | **OK** — date, source, moteur, fichiers/chunks/échecs, nœuds/arêtes, LLM vs structurelles, top relations, **hubs** (degrés) |
| Outil MCP `localai_graph_show` | **OK** — `isError:false`, payload structuré (`nodes`, `edges`, `engine`, `top_hubs`) |

## 31. Failover SSE transparent (panne matérielle réelle)
Panne simulée : **kill du processus `llama-server` primaire** (PID 8860) — le cœur répond alors HTTP 500.

| Scénario | Résultat |
|---|---|
| **Routine en streaming** (primaire mort) | **OK** — `route=vision-cpu`, `failover=true`, **décision 162 ms** (budget 1,5 s respecté), flux `chunks=5`, `[DONE]` |
| **Requête bufferisée (agent)** pendant la panne | **OK** — `core-local : HTTP 500` **intercepté**, rejeu silencieux sur `vision-cpu`, **décision 334–367 ms**, contenu reçu (`caracteres=4`), client en **HTTP 200** avec **flux SSE complet** (`chunks=3`, `DONE`) |
| Intégrité de la session client | **OK** — **aucune coupure visible** : le client reçoit un flux cohérent de bout en bout |
| Bufferisation en régime nominal | **OK** — amont interrogé en **JSON** (`stream:false`) puis flux SSE reconstruit ; route `core-local` (plus de bascule parasite) |
| HTTP 4xx (modèle inconnu) | **OK** — renvoyé tel quel **sans** bascule (erreur de requête, pas panne moteur) |
| Chaîne de reprise | **OK** — `core-local` → `vision-cpu` (local CPU) → `cloud` (clé `cloud-keys.env`, désactivable) |
| Audit | **OK** — `logs\failover.jsonl` : `route`, `mode`, `failover`, `ms_decision`, `caracteres` |

## 32. Non-régression complète (v1.4.1 → v1.6.0)
| Test | Résultat |
|---|---|
| Suite JALON 1 rejouée (ports, inférence cœur + gateway, **401**) | **7/7 OK** |
| Vision locale (`--mmproj`, image réelle) | **OK** — légende correcte |
| Passerelle MCP (`mcp-test`) | **OK** — `{localai: up}`, 5 outils, **VERDICT VERT** |
| Watchdog VRAM | **OK** — actif, seuils affichés |
| Index RAG multi-format + images | **OK** |

## 33. Hygiène finale (gel)
| Test | Résultat |
|---|---|
| `Run-LocalAI.bat stop` | **OK** — « Tous les processus sont arretes. **Zero zombie.** » |
| Vérification indépendante | **OK** — aucun `llama-server` / `whisper-server` / `sd-server` / `tts_server` / `local-ai` / `litellm` résiduel |
| Ports libérés | **OK** — 8080, **8081**, 8090, 8091, 8092, 8093, **8095**, 4000 : aucune écoute |
| VRAM | **OK** — libérée après arrêt (2276 Mo utilisés pendant le service → relâchés) |
| Registre des PID | **OK** — `data\pids.txt` recense 9 services (llama, whisper, sd, vision, failover, tts, local-ai, litellm, vram-watchdog) et l'arrêt les élimine tous |

## 34. Anomalies v1.6.0 et auto-healing
| # | Anomalie | Correctif | Statut |
|---|---|---|---|
| A12 | Sortie LLM **tronquée** → 0 triplet extrait | Récupération des objets JSON complets + `max_tokens=256` + consigne de fermeture | ✅ |
| A13 | Bufferisation : `stream:true` transmis en amont → contenu illisible | Amont interrogé en **JSON**, flux SSE reconstruit côté client | ✅ |
| A14 | Failover déclenché par un **HTTP 404** (erreur de requête) | 4xx renvoyés tels quels + `alias_map` des modèles | ✅ |
| A15 | Proxy failover non démarré (`$py` utilisé avant sa définition) | Définition en tête de `localai_up.ps1` | ✅ |
| A16 | Titre `vram-status` figé sur v1.4.1 | Placeholder `__VERSION__` | ✅ |

## 35. Verdict final et gel
- **Sections du mandat v1.6.0 livrées et validées** : indexation **GraphRAG sécurisée par LLM local**
  (aucune regex) + **failover SSE déterministe** (bufferisation complète / bascule avant le premier
  token), avec les commandes CLI `graph-show` et `mcp-list`.
- **Doctrine constitutionnelle respectée de bout en bout** : `archive_installer()` en tête de `main()`,
  `manifest.json` `root` = chemin de production final, **triple validation AST** après chaque patch,
  déploiement transactionnel (swap atomique + rollback), **règle d'or de l'héritage** étendue aux
  données utilisateur coûteuses (modèles téléchargés, `mcp-settings.json`, `failover.json`).
- **Périmètre** : 100 % natif Windows, **sans Docker ni WSL** ; cœur Go inchangé ; aucune écriture hors
  sandbox `G:\V1\LocalAI-Projet\`.
- **Versions livrées** : v1.4.1 (stabilisation) → **v1.5.0** (vision + MCP) → **v1.6.0** (GraphRAG +
  failover). Manifest : **version globale v1.6.0**.
- **SYSTÈME GELÉ — v1.6.0 STABILISÉE AU VERT.**

---

# PHASE 7-8 — RAPPORT FINAL v1.7.0 & v1.8.0

**Date** : 2026-10-03 · **Versions** : v1.7.0 puis **v1.8.0** · **Verdict final** : ✅ **AU VERT**
(+ **un incident majeur** détecté, corrigé et documenté — D-037)

## 36. JALON 1 — bêta-test de rupture de la v1.6.0 (avant tout code v1.7.0)
| Épreuve | Résultat |
|---|---|
| Ports 8080/8090/8092/4000/8095/8081 + inférence cœur et gateway + 401 | **7/7 OK** |
| Vision (`--mmproj`, image réelle) | **OK** — légende correcte |
| RAG (`rag-query`) | **OK** — 5 résultats cosinus |
| GraphRAG (`graph-show`) | **OK** — 19 nœuds / 23 arêtes |
| Failover nominal + **bascule sur panne réelle** | **OK** — `HTTP 500` intercepté → `vision-cpu` (513-640 ms) |
| MCP (`mcp-test`) | **OK** — VERDICT VERT, 5 outils |
> **Aucune anomalie** → aucun auto-healing nécessaire.

## 37. v1.7.0 — Quantization locale (v1.7.0a)
| Test | Résultat |
|---|---|
| Support `llama-quantize.exe` dans l'orchestrateur | **OK** |
| `quantize <f16> <type>` (synchrone) et `--async` | **OK** |
| `quantize list` — 24 types + sources non quantifiées | **OK** (exclusion des sources déjà quantifiées) |
| **Mesure réelle** : `SmolVLM-500M-Instruct-f16.gguf` **782 Mo → Q8_0 417 Mo** | **OK** — `8.50 BPW`, **2 447 ms** |
| SHA-256 + historique auditable (`data\quantize-history.jsonl`) | **OK** |

## 38. v1.7.0 — Filtre PII hybride BEST-EFFORT (v1.7.0b)
| Test | Résultat |
|---|---|
| N1 regex (e-mail, IPv4/IPv6, `sk-`, `ghp_`, `AKIA`, `xox`, JWT, PEM, Luhn) | **OK** |
| N2 entropie (mot de passe complexe à symboles) | **OK** (jetons non séparés par espace, ≥ 3,5 bits, jeu mixte) |
| N3 NER local léger via le moteur local | **OK** (aucun envoi externe) |
| Reversibilité masquage/démasquage | **OK** — `IDENTIQUE` |
| `privacy-test` | **OK** — **VERDICT VERT** |
| **Débordement cloud simulé** (clé présente, prompt complexe) | **OK** — routage `localai` → `openrouter-claude` ; **aucun secret original** dans le corps transmis ; réponse **restaurée** → **VERDICT VERT** |
| Audit `dev\crash.log` catégorie `PRIVACY_FILTER` | **OK** — type, niveau, jeton, aperçu tronqué (**jamais le secret complet**) |
| Documentation BEST-EFFORT (non garantie 100 %) + `start --no-pii-filter` | **OK** (INSTALLATION §40) |

## 39. v1.8.0 — Routage NPU via DirectML + repli CPU
| Test | Résultat |
|---|---|
| `onnxruntime-directml` installé isolément (routine vérifiée) | **OK** |
| Détection déterministe du provider | **OK** — priorité DirectML → **repli CPU** |
| **Simulation d'absence de pilote NPU** | **OK** — `DirectML absent (pilote ou materiel incompatible)` |
| **Repli CPU automatique, session non interrompue** | **OK** |
| Avertissement **`GPU_DETECT`** consigné dans `dev\crash.log` | **OK** |
| **Sonde réelle** (`npu-probe`, MNIST authentique 25 843 o, SHA-256 vérifié) | **OK** — inférence effective (`prediction: 9`), pas un simple test d'API |
| `hardware-status` (moteur GPU vs tâches sémantiques NPU/CPU + services/ports) | **OK** |
| Outil MCP déporté `localai_semantic_probe` (6ᵉ outil) | **OK** |

## 40. ⚠️ INCIDENT MAJEUR et correctif (v1.8.0)
| Étape | Constat |
|---|---|
| **Fait** | Lors du déploiement, la bascule transactionnelle a **détruit l'arbre de production** (seul `runtime\python`, verrouillé, a survécu) ; le rollback a de plus supprimé le staging **neuf et complet** |
| **Cause racine** | `swap_product()` **supprimait** `LocalAI` **avant** d'y installer le nouveau ; un fichier verrouillé (service actif) a fait échouer la suppression **à mi-chemin** |
| **Correctif 1** | **Permutation par renommage** : `LocalAI`→`.old` → mise en place du nouveau → purge best-effort ; en cas d'échec l'ancien est **restauré** et le nouveau **conservé** |
| **Correctif 2** | **Garde préalable** `_guard_running_services()` : la réinstallation est **refusée** si un service est encore actif (message actionnable) |
| **Vérification** | `Produit bascule de facon transactionnelle vers …\LocalAI` — la nouvelle bascule a été exercée avec succès lors de la reconstruction |
| **Conséquence** | Les **modèles téléchargés par l'utilisateur** (SD-Turbo Q8, paires vision) ont été perdus : à ré-acquérir via `Run-LocalAI.bat pull`. **Aucun autre actif irremplaçable perdu** (tout le reste est reconstructible par conception) |

**Leçon doctrinale** : une bascule transactionnelle ne doit **jamais** être destructive en amont.
Ordre correct : **écarter → installer → purger**, jamais *purger → installer*.

## 41. Verdict final v1.8.0
- **Sections du mandat v1.7.0 ET v1.8.0 livrées et validées** : quantization locale (+ asynchrone),
  filtre PII hybride 3 niveaux intégré au Token Saver avec audit et drapeau de désactivation,
  routage hétérogène NPU via DirectML avec **repli CPU obligatoire**, commandes CLI `quantize`,
  `privacy-test`, `privacy-levels`, `hardware-status`, `npu-probe`.
- **Manifest** : version globale **v1.8.0** (**80 composants**), `root` = chemin de production final.
- **Doctrine renforcée** : la doctrine transactionnelle a été **mise à l'épreuve** et **réparée** —
  la garantie « aucune perte » est désormais assurée **par construction** (permutation + garde).
- **Traçabilité complète** : `CHANGELOG` (v1.7.0, v1.8.0), `DECISIONS` (**D-035 → D-037**),
  `patch_integrity.log` (JALON 0→5), `crash.log` (`PRIVACY_FILTER`, **`GPU_DETECT`**, **`DEPLOY_GUARD`**),
  `INSTALLATION.md` (§39-44), `JOURNAL.md`, `PERIMETRE.md`.
- **PHASE 7-8 / v1.8.0 VALIDÉE, GELÉE ET LIVRÉE.**





## 42. v1.9.0 — Speculative Decoding TEXT-ONLY (JALON 2 & 3)
- **Périmètre vérifié** : décodage spéculatif **texte uniquement** ; aucune intrusion dans le pipeline
  vision (le couple GGUF + `mmproj` reste scellé au format atomique de la v1.5.0).
- **Garde VRAM** : la décision d'activer le mode est prise **après** lecture de la VRAM libre ; sur le
  poste de référence, le budget disponible autorise le mode **sans risque d'éviction**.
- **Pièges corrigés (A24/A25)** : les options amont `--draft-max/--draft-min` ont **disparu** — les vrais
  drapeaux sont `--spec-draft-n-max/--spec-draft-n-min` ; et le modèle brouillon **doit partager son
  tokenizer** avec le modèle principal, sinon le couple est refusé.
- **Mesure** : `21,39 tok/s` (spéculatif) contre `21,76 tok/s` (normal) → **aucun gain**, le portage
  étant **limité par le GPU**. D'où **D-039** : mode **OPT-IN** (`LOCALAI_SPEC=1`), jamais activé par
  défaut.
- **Verdict** : **V1.9.0 VALIDÉE, GELÉE ET LIVRÉE** (fonction correcte, mesurée, laissée disponible).

## 43. v2.0.0a — Espace hermétique AES-256-GCM (JALON 4 & 5)
- **Autotest `vault-test`** : backend AES-256-GCM ; dérivation PBKDF2-HMAC-SHA256 390 000 itérations,
  sel aléatoire ; scellement OK, ouverture OK, **intégrité IDENTIQUE (4096 octets)** ; **mauvais mot de
  passe REFUSÉ** (authentification GCM) ; **clé jamais sur disque**. → **VERDICT VERT**.
- **Test sur index RAG réel** (produit par `Run-LocalAI.bat index`, 4 fichiers : `.npy` 41 088 o, `.jsonl`,
  `.json` ×2) : scellement → 4 conteneurs `.enc`, **aucun clair résiduel** ; ouverture → 4/4 restaurés ;
  **4/4 empreintes SHA-256 identiques → ZÉRO CORRUPTION**.
- **Fonctionnel après le cycle** : `rag-query` → **5 résultats, scores identiques**.
- **Anti-perte** : la réversibilité est **vérifiée immédiatement** ; en cas d'échec, le conteneur est
  retiré et l'opération annulée — la suppression du clair n'a lieu qu'après preuve.
- **Verdict** : **v2.0.0a VALIDÉE AU VERT.**

## 44. v2.0.0b — Profil apprenant continu (JALON 4 & 5)
- **Télémétrie réelle** : pile démarrée (`local-ai` :8080, LiteLLM :4000, watchdog VRAM), VRAM lue via
  `nvidia-smi` : **6144 Mo** totaux, **3765-3856 Mo libres (61,1-62,6 %)**.
- **Historique** : **5 observations** dans `logs\history.jsonl`, **conservées à travers deux
  réinstallations** (règle d'or de l'héritage).
- **Apprentissage** : min **61,13 %** / moy **61,94 %** / max **62,60 %** → seuils appris
  **alerte < 25,0 % · critique < 12,0 % · reprise > 35,0 %**, `ngl` **99 conservé** (0 éviction) ;
  source = « appris (5 observations réelles) ».
- **Application à chaud (preuve décisive)** : watchdog démarré en **15/5/20** →
  `data\vram-status.json` affiche **25/12/35 SANS redémarrage**, trace
  `[GPU_VRAM] profil appris applique A CHAUD : alerte<25.0% … (ngl=99)`.
- **Garde-fou `reset-profile soft`** : **25/12/35 → 20/10/30 appliqués à chaud en ~8 s**, trace
  `[GPU_VRAM] profil appliqué à chaud`. → **Retour d'usine instantané et vérifié**.
- **`profile-status`** : « USINE (profil 'soft' appliqué à chaud) », seuils 20/10/30, `ngl` 99,
  historique 5 observations.
- **Anomalies corrigées (JALON 5)** : **(A1)** `reset-profile soft` refusé par le parseur d'arguments ;
  **(A2)** le reset *supprimait* le profil au lieu d'appliquer les valeurs d'usine (le watchdog
  retombait sur sa base de démarrage) → le reset **écrit** désormais les valeurs d'usine ;
  **(A3)** trace annonçant « appris » pour un profil d'usine → libellé rendu exact.
- **Traçabilité** : `patch_integrity.log` (JALON 4 & 5), `crash.log` (`PROFILE_LEARN`, `GPU_VRAM`),
  `DECISIONS.md` (**D-041**), `INSTALLATION.md` (§47-48), `CHANGELOG.md` (v2.0.0), `JOURNAL.md`.
- **État global** : master et `manifest.json` en **v2.0.0** ; **AST VERT** ; **83 composants** ;
  **zéro zombie**, **zéro port en écoute**.
- **Verdict** : **V2.0.0 VALIDÉE, GELÉE ET LIVRÉE.**




## 45. v2.1.0 — Inférence fédérée RPC + découverte réseau (JALON 6 & 7)
- **Découverte** (`peer_discovery.py`) : **UDP broadcast, pur Python, zéro dépendance** ; 2 messages
  (`query`/`reply`) ; **aucune donnée d'inférence transmise**. Autotest `peer-test` → **VERDICT VERT**
  (latence **0,6 ms**). Découverte réelle avec la pile démarrée : **1 nœud** en broadcast
  (`DESKTOP-XTREM-21`, rpc_port 50052, latence **17,2 ms**).
- **Routage fédéré** : escalade **fédéré d'abord, repli CPU ensuite**. **PANNE RPC SIMULÉE** : un vrai
  `ggml-rpc-server.exe` déclaré comme pair (joignable, `--rpc 192.168.1.84:50052`, 1 cible) puis
  **tué** → joignable NON, cibles **0**, `federated_relaunch` → **applied=False** (« aucun nœud RPC
  distant joignable : calcul local conservé »). **Aucun `--rpc` vers un nœud mort.** Inférence locale
  **non perturbée** (6,0 s).
- **Arrêt** : 6 ports TCP + UDP 47653 → **0** ; **zéro zombie** ; VRAM libérée ; `data\runtime.env`
  conforme.
- **Anomalie de nommage** : le mandat cite `rpc-server.exe`, l'amont livre **`ggml-rpc-server.exe`**.
- **VERDICT : v2.1.0 VALIDÉE, GELÉE ET LIVRÉE.**

## 46. v2.1.1 — Internationalisation FR/EN (PHASE 2.20)
- **Trois couches** : embarqué (vérité ultime), JSON externe (surcharge personnalisable), `I18N_REV`
  (rafraîchit les clés `help_*`/`tip_*` uniquement).
- **Scénario 1 — initial** : sans configuration → **français**, aucune erreur. **VERT**
- **Scénario 2 — bascule à chaud** : `lang en` → `config\lang.json` (`lang=en`, rev=1) ; **aide ET
  en-tête en anglais instantanément** ; `lang fr` → retour immédiat. **VERT**
- **Scénario 3 — repli** : `config\lang.json` supprimé → repli silencieux sur le défaut `fr`. **VERT**
- **Scénario 4 — corruption** : `i18n\fr.json` rendu **invalide** → exception gérée, repli **couche 1**,
  `i18n-test` → **VERDICT VERT**, **aucun plantage**, trace `[I18N]` dans `dev\crash.log`. **VERT**
- **5 bugs de déploiement corrigés** (B1-B5, tous **silencieux**) — dont un `for /f` batch qui
  **ne s'exécutait jamais** avec un chemin d'exécutable entre guillemets, laissant l'interface en
  français malgré `lang=en`. Générateur rendu **auto-réparant** (fichier vide/invalide → régénéré).
- **VERDICT : v2.1.1 VALIDÉE, GELÉE ET LIVRÉE.**

## 47. v3.0.0 — Identité AiTron V3 + audit d'autonomie (PHASE V3 Finale)
- **JALON 0** : `archive_installer()` première instruction de `main()` (sauvegarde horodatée). **OK**
- **JALON 1** : β-testeur fou pré-code sur la v2.1.1 (RAG, Vision, MCP, GraphRAG, Failover, i18n,
  coffre, profil, fédération) → **aucun bug résiduel**. **VERT**
- **JALON 2 — renommage** : `install_localai_win.py` → **`install_AiTron_v3.py`** ; `LocalAI\` →
  **`AiTron\`** ; staging `AiTron.new` ; `LOCALAI_DEPLOY_CODE` → **`AITRON_DEPLOY_CODE`** ; env
  `AITRON_*` (provenance amont `LOCALAI_*` préservée) ; manifeste `"product": "AiTron V3"`,
  `"fork_of": "LocalAI (https://github.com/mudler/LocalAI)"`, `"license": "MIT"` ; `CHARTE.md` actée ;
  **`local-ai.exe` conserve son nom** (195 Mo). Migration d'héritage automatique `LocalAI\` → `AiTron\`.
  Avertissement de transparence (fork non affilié) dans les 3 documents d'installation.
- **JALON 3 — audit d'autonomie mono-bloc** : produit mis en sécurité **par déplacement**, puis
  **SUPPRIMÉ PHYSIQUEMENT**, puis **reconstruit** par le seul installeur (`--prev` vers la sauvegarde)
  → **renaissance complète** vérifiée : moteur 195 Mo, modèle **807 694 464 o**, index RAG,
  4 backends, configurations, scripts, documentations. **L'installeur est auto-suffisant.** **VERT**
- **JALON 4 — β-testeur fou v3.0.0** : bannière **`=== AiTron - portage Windows natif (sans Docker ni
  WSL) (v3.0.0) ===`** ; inférence texte **6,5 s** ; RAG **3 chunks × 2048 dims en 7,1 s** et requête
  **3 résultats** ; i18n `lang en`/`lang fr` OK ; `I18N_REV` **1→2** → **clés d'aide rafraîchies**
  (l'aide affiche **3.0.0**, plus 2.1.1) ; arrêt → **0 port TCP, 0 port UDP, zéro zombie**. **VERT**
- **JALON 5 — clôture** : `ANOMALIES_NON_RÉSOLUES.log` à la **racine** (8 entrées au format
  standardisé ; **aucun défaut de notre code non résolu**) ; `INSTALLATION.md` à la **racine**
  (autonome, bilingue) + `INSTALLATION.fr.md` / `INSTALLATION.en.md` ; traçabilité complète ;
  **gel à 3.0.0** partout.
- **VERDICT : v3.0.0 LIVRÉE, VALIDÉE AU VERT, GELÉE.**

## 48. v3.1.0 — Audit dynamique en staging isole (certification REFUSEE)
- **Protocole** : copie de `install_AiTron_v3.py` et `Run-LocalAI.bat` dans `dev\test_dynamique\`,
  installation a blanc (`--prev` vers un dossier inexistant), pile reelle demarree (8080, 8081, 4000,
  8090, 8091, 8093), 13 controles dans `build\audit\final_run.py`.
- **Boucle d'auto-reparation** : 10 tentatives d'installation ; chaque defaut reproduit, mesure, corrige,
  valide en AST puis re-teste de zero (D1 a D11, voir DECISIONS D-046).
- **Resultat du dernier parcours** : 13/13 conformes. CLI : 19 commandes x 2 langues, 0 erreur, 0 BOM,
  0 mojibake, 0 ligne francaise non ambigue en EN.
- **Anomalie bloquante A-12** : IHM francaise a 42,4 % (680 / 1 603 cles EN) ; admin, auth, importModel
  et media absents. Curable, non corrigee -> **CERTIFICATION REFUSEE**.
- **Limites** : verification de l'IHM sans navigateur ; pannes simulees par de faux serveurs ; cle cloud
  fictive ; formats PDF/DOCX/XLSX/images non rejoues.
- **Etat** : produit stable `AiTron\` toujours en v3.0.0 ; le staging reste dans `dev\test_dynamique\`.

## 49. v3.1.0 — Cloture de l'audit (2e passe) : CERTIFICATION VALIDEE AU VERT
- **Cause du refus precedent** : IHM francaise a 42,4 % (A-12). **Traitement** : 920 cles traduites,
  fusionnees par un outil qui refuse toute ecriture incoherente ; IHM puis coeur recompiles ; staging
  redeploye avec `--prev` vers la sauvegarde v3.0.0 (installation #11).
- **Mesures sur ce deploiement** : 13/13 controles ; IHM servie 1 597/1 597 cles (100,0 %) ; 38 executions
  CLI sans erreur, BOM ni mojibake ; 0 ligne francaise non ambigue en mode EN (apres D12) ; 0 ERROR/CRITICAL
  non resolue ; arret propre (0 processus, 0 port TCP, 0 UDP 47653).
- **Un defaut de plus trouve a la 2e passe** (D12) : `spec-status` et `graph-show` gardaient 4 lignes
  francaises en mode EN ; corrige, puis TOUT rejoue depuis une installation neuve.
- **Limites** : rendu navigateur non verifie ; PDF/DOCX/XLSX/images RAG non rejoues ; pannes simulees ;
  cle cloud fictive ; traduction produite et validee par le meme auteur (derogation autorisee).
- **Etat** : produit stable `AiTron\` toujours en v3.0.0 ; labo archive dans `dev\old\test_dynamique\`.

## 50. v3.1.1 — Portabilite totale de l'installeur + fallbacks (2026-10-05)
- **Objet** : rendre `install_AiTron_v3.py` portable (plus de chemin en dur) et ajouter des
  fallbacks de telechargement pour `local-ai.exe` / `cloud-proxy.exe`.
- **Methode** : patch transactionnel en 2 passes (D-049, D-050) ; validation AST triple + zero
  SyntaxWarning ; harnais unitaire hors reseau ; installations reelles en cascade.
- **Tests unitaires** : **15/15** (`build\test_portability_v311.py`) : detection auto, `--root`,
  creation d'arborescence, cascade local/staging/produit, telechargement + SHA (concordant/vide) ;
  **garde-fou MZ** (`build\test_mz_guard.py`) : page HTML rejetee, binaire MZ accepte.
- **Installations reelles** :

  | # | Racine | Sandbox detectee | Composants | Version | Etat |
  |---|--------|------------------|-----------|---------|------|
  | T1 | `G:\V1\LocalAI-Projet` (dossier courant) | automatique | 87 | v3.1.1 | OK (`status`/`help`, inférence `BONJOUR`) |
  | T2 | `C:\AiTron-Test` | `C:\AiTron-Test` | 87 | v3.1.1 | OK (`start`, endpoints UP, inférence `BONJOUR`) |
  | T3 | `--root D:\AiTron-Root-Test` (lance depuis G:\) | `D:\AiTron-Root-Test` | 87 | v3.1.1 | OK |
  | T4 | USB `E:\AiTron-Portable` | `E:\AiTron-Portable` | 87 | v3.1.1 | OK |

- **Fallback (T5)** : avec `build\out\local-ai.exe` renomme, la cascade resout le binaire depuis le
  **staging archive** (`dev\old\test_dynamique\AiTron\local-ai.exe`, taille 195 156 992 o) ->
  deploiement reussi ; le chemin de telechargement est couvert par le harnais unitaire.
- **Conformite v3.1.0 preservee (T6)** : **0 BOM sur 41 fichiers** ; CLI bilingue en v3.1.1 ; arret
  propre (**0 processus, 0 port TCP, 0 UDP**) ; manifeste = 87 composants ; produit deja certifie
  (IHM FR 100 %, failover SSE, vault, profil apprenant) non modifie par cet increment.
- **Limites / anomalies** :
  - Les URLs de fallback (`transfert.free.fr`) renvoient une **page HTML** (`text/html`, 217 573 o)
    et non le binaire : le telechargement direct n'est pas exploitable tel quel (garde MZ -> rejet).
    Remede : liens binaires directs + SHA-256 renseigne.
  - Racines alternatives mises en place avec un **junction `build`** vers le cache de la sandbox
    (harnais de test) afin d'eviter un re-telechargement massif (~2 Go) ; le mecanisme d'installation
    est inchange.
  - Rendu navigateur non verifie ; pannes simulees non rejouees.
- **Verdict : v3.1.1 LIVREE — PORTABLE, VALIDEE AU VERT.**

## 51. v3.1.2 — Integration des binaires GitHub Releases (2026-10-05)
- **Objet** : remplacer les URLs temporaires `transfert.free.fr` (HTML) par des URLs GitHub Releases
  perennes, integrer les SHA-256, conserver et renforcer le garde-fou PE "MZ".
- **Methode** : patch transactionnel (D-051) ; validation AST triple + zero SyntaxWarning ; telechargement
  reel des binaires GitHub ; 4 tests ; coherence v3.1.1 reverifiee.
- **Sources GitHub (verifiees a l'instant)** : HTTP 200, `application/octet-stream`, magic `MZ`.
  - `local-ai.exe`    195 156 992 o  SHA-256 `0F55C483...`
  - `cloud-proxy.exe`  19 915 776 o  SHA-256 `BFCB2804...`
  Binaires **byte-identiques** aux binaires locaux (`build\out\`).

| # | Test | Methode | Verdict |
|---|------|---------|---------|
| 1 | Telechargement direct | racine "vierge" `C:\TestGitHub` (build\out neutralise) -> `Fallback core/bridge : telechargement depuis GitHub` puis `garde-fou PE MZ OK + SHA-256 verifie` -> deploiement 87 composants, manifeste v3.1.2 | OK |
| 2 | SHA-256 errone | `_fallback_download(GH cloud-proxy, sha=000...)` -> `RuntimeError` + `.part` nettoye + fichier final absent | OK |
| 3 | Fallback en cascade | URL invalide -> priorite 1 (`build\out\`) sans reseau ; tout absent -> echec reseau + message actionnable + retour local | 3/3 OK |
| 4 | Coherence v3.1.1 | 0 BOM/41 fichiers ; CLI bilingue v3.1.2 ; endpoints UP ; failover SSE `failover-proxy` ; vault AES-256-GCM ; inference `AITRON` ; arret 0 processus / 0 port | OK |

- **Preuve du telechargement (Test 1)** : `Source core : ABSENT` -> `Fallback core : telechargement depuis
  https://github.com/...local-ai.exe` -> `garde-fou PE MZ OK + SHA-256 verifie (0f55c483...)` (idem bridge).
- **Limites** : racines de test montees avec un junction `build` vers le cache local (evite un
  re-telechargement massif de la pile Python/modeles) ; mecanisme d'installation inchange. Rendu
  navigateur non verifie.
- **Verdict : v3.1.2 LIVREE — binaires GitHub Releases integres, VALIDEE AU VERT.**

## 52. v3.1.3 — Creation de la Release GitHub v3.1.2 (2026-10-05)
- **Objet** : publier la Release GitHub v3.1.2 (binaires) et basculer les URLs de fallback sur v3.1.2.
- **Methode** : GitHub CLI (`gh`) installe via `winget`, authentifie par le jeton GCM (`GH_TOKEN`) ;
  release creee en ligne de commande (l'interface web bloquait les gros fichiers). Patch transactionnel
  du script (D-052) : URLs v3.1.1 -> v3.1.2, version 3.1.2 -> 3.1.3 ; AST triple VERT.

| # | Test | Methode | Verdict |
|---|------|---------|---------|
| 1 | Release verifiee | `gh release view v3.1.2` -> assets `local-ai.exe` + `cloud-proxy.exe` ; URLs `.../download/v3.1.2/...` -> HTTP 200, `application/octet-stream`, tailles 195 156 992 / 19 915 776, magic MZ | OK |
| 2 | Telechargement | racine vierge `C:\TestReleaseV312` (build\out neutralise) -> `Fallback core/bridge : telechargement depuis .../v3.1.2/...` + `garde-fou PE MZ OK + SHA-256 verifie` -> deploiement 87 composants | OK |
| 3 | Coherence v3.1.2 | 0 BOM ; CLI bilingue v3.1.3 ; endpoints UP ; failover SSE ; vault AES-256-GCM ; 0 zombie | OK |

- **Release** : https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/tag/v3.1.2
- **Limites** : racine de test montee avec un junction `build` (cache local) ; rendu navigateur non verifie.
- **Verdict : v3.1.3 LIVREE — Release GitHub v3.1.2 publiee, fallbacks a jour, VALIDEE AU VERT.**
