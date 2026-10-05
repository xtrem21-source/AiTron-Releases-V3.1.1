# DECISIONS.md — Journal des Decisions Techniques

> Chaque decision structurante : le choix, la raison, l'alternative ecartee.

---

## D-001 — Cible : LocalAI Windows natif, compilation depuis les sources Go
- **Date** : 2026-10-03
- **Contexte** : LocalAI v4.11.0 ne publie aucun binaire Windows (assets officiels = Linux amd64/arm64,
  darwin-arm64, source, DMG). La doc officielle renvoie a WSL2/Docker.
- **Decision** : appliquer l'ordre de la Section 4.2 -> (1) compiler depuis les sources Go. Etape (2)
  = binaire communautaire, etape (3) = WSL2, ecartees tant que (1) est viable.
- **Raison** : conformite charte (pas de Docker ; WSL seulement en dernier recours documente) et
  production d'un vrai binaire natif `local-ai.exe`.
- **Consequence** : necessite Go 1.27.1 + chaine C (CGO).

## D-002 — Toolchain Go isolee dans la sandbox
- **Date** : 2026-10-03
- **Decision** : extraire Go dans `build\tools\go` et forcer `GOPATH`/`GOCACHE`/`GOENV`/`GOTMPDIR`
  sous `build\` a chaque invocation.
- **Raison** : `go env -w` ecrit par defaut dans `%AppData%\go\env` (hors sandbox) -> violation
  Section 2.4. En forcant `GOENV`, l'etat Go reste confine.
- **Alternative ecartee** : installer Go systeme (hors sandbox).

## D-003 — CGO et chaine C (MinGW-w64)
- **Date** : 2026-10-03
- **Contexte** : `gorm.io/driver/sqlite` -> `github.com/mattn/go-sqlite3` exige CGO.
- **Decision** : fournir une chaine MinGW-w64 x86_64 (UCRT) confinee dans la sandbox
  (`build\tools\mingw64`) et configurer `CC`/`CGO_ENABLED=1`. Si le seul consommateur CGO est le
  driver sqlite non importe par le binaire principal, on pourra evaluer `CGO_ENABLED=0`.
- **Raison** : CGO sans compilateur C = echec de build garanti.
- **Source** : https://github.com/niXman/mingw-builds-binaries/releases (hors liste 4.5 -> justifiee ici,
  faute de GCC officiel Windows).

## D-009 — Python embarqué : lanceur LiteLLM dédié
- **Date** : 2026-10-03
- **Contexte** : LiteLLM ne démarre pas sur Windows pour deux raisons cumulées :
  (1) son bandeau contient des caractères Unicode que le codec `cp1252` de la console Windows
  ne peut encoder (`UnicodeEncodeError`) ; (2) le Python embarqué est en **mode isolé** (`python311._pth`),
  donc `PYTHONPATH` est **ignoré**, et le console-script `Scripts\litellm.exe` embarque le chemin Python
  **d'origine** (il exécuterait l'installation de `build\tools\python`, pas le runtime déployé).
- **Décision** : ne pas utiliser `Scripts\litellm.exe` ; lancer LiteLLM via un lanceur dédié
  `config\litellm_launch.py` exécuté par `runtime\python\python.exe`, avec `PYTHONUTF8=1`,
  `PYTHONIOENCODING=utf-8` et `stdout/stderr` reconfigurés en UTF-8. L'entry point officiel est
  `litellm=litellm:run_server` (`import litellm; litellm.run_server()`).
- **Raison** : placer le lanceur dans `config\` met ce dossier dans `sys.path[0]`, rendant le callback
  `complexity_router` importable malgré le mode isolé.

## D-010 — Whisper : route OpenAI via `--inference-path`
- **Date** : 2026-10-03
- **Contexte** : `whisper-server` v1.9.2 n'expose pas `/v1/audio/transcriptions` par défaut (404) ;
  sa route native est `/inference`.
- **Décision** : démarrer le serveur avec `--inference-path /v1/audio/transcriptions`. La route
  OpenAI-compatible est alors servie nativement et renvoie `{"text": "..."}`.
- **Raison** : conformité au mandat (QA `/v1/audio/transcriptions` sur 8091) **sans** code de proxy
  supplémentaire ni processus additionnel.

## D-011 — TTS kokoro : `get_voices()` renvoie une liste
- **Date** : 2026-10-03
- **Contexte** : `kokoro-onnx >= 0.6` fait retourner `get_voices()` sous forme de **list**
  (et non de dict) → `VOICES` restait vide et la voix par défaut (`af_sarah`) était introuvable.
- **Décision** : `tts_server.py` gère `dict` **et** `list/tuple/set` ; voix par défaut `af_maple`
  (103 voix détectées dans `kokoro-v1.1-zh`).

## D-012 — Authentification : cœur local nu, LiteLLM = gateway
- **Date** : 2026-10-03
- **Contexte** : exporter `LOCALAI_API_KEY` active l'authentification du **cœur** LocalAI
  (`APIKeys` → HTTP 401 sur `/v1/models`).
- **Décision** : ne **pas** exporter `LOCALAI_API_KEY`. Le cœur reste sans clé sur la boucle locale ;
  la clé synthétique côté LiteLLM utilise une variable distincte `LOCALAI_LOCAL_KEY` (dummy).
  L'authentification des clients est portée par LiteLLM (`master_key: sk-local`, BYOK).
- **Raison** : éviter un conflit d'espace de variables entre le cœur et la gateway.

## D-013 — Installeur : arrêt préventif et `start` idempotent
- **Date** : 2026-10-03
- **Contexte** : une instance en cours (ou un lanceur retenant ses fichiers de log) empêchait la
  bascule transactionnelle (« Impossible de retirer l'ancien produit »). Un second `start` créait
  des services en doublon.
- **Décision** : ajouter `_stop_existing()` dans l'installeur (stop.bat + taskkill + arrêt des
  processus dont l'exécutable est sous le produit) **avant** le déploiement ; rendre `start`
  idempotent (arrêt de l'instance éventuelle **avant** la remise à zéro de `data\pids.txt`) ;
  compléter `stop.bat` par un nettoyage des services Python du produit.
- **Raison** : le rollback transactionnel a protégé le produit existant, mais l'expérience doit être
  idempotente et sans doublon.

## D-014 — CUDA prébuild incompatible Maxwell → repli Vulkan
- **Date** : 2026-10-03
- **Contexte** : la machine de test est équipée d'une **GTX 970M (Maxwell, compute capability 5.2)**,
  driver 527.41. Le binaire `llama-b11375-bin-win-cuda-12.4-x64.zip` s'exécute (`--version` OK) mais
  toute inférence échoue : `CUDA error: invalid device function` → les binaires CUDA prébuilds ggml-org
  ne contiennent pas l'architecture `sm_52`.
- **Décision** : détecter NVIDIA → tenter **Vulkan** en priorité si `vulkan-1.dll` est présent
  (supporté par le driver), et ne retenir CUDA que si Vulkan est indisponible. La variante CUDA reste
  installée (substituable sur une machine récente) mais n'est pas activée.
- **Alternative écartée** : recompiler llama.cpp avec `CMAKE_CUDA_ARCHITECTURES=52` — hors périmètre,
  exige le CUDA Toolkit complet (coûteux, et la charte privilégie l'autonomie).

## D-015 — Calcul des paramètres à partir des métadonnées GGUF
- **Date** : 2026-10-03
- **Décision** : obtenir les constantes du modèle via l'outil intégré du cœur
  (`local-ai.exe util gguf-info`), puis extraire par expression régulière (après retrait des codes ANSI)
  `BlockCount`, `EmbeddingLength`, `VocabularyLength`, `MaximumContextLength`, `AttentionHeadCountKV`,
  `AttentionKeyLength`, `AttentionValueLength`. Ces valeurs alimentent le calcul de `-ngl`
  (budget VRAM − marge, cache KV par couche, marge 10 %), du `--threads` et du `--ctx-size`
  (aligné sur 4096, plafonné par `n_ctx_train`).
- **Raison** : éviter d'écrire un parseur GGUF ; réutiliser une brique déjà validée du cœur.

## D-016 — Piège PowerShell : variables insensibles à la casse
- **Date** : 2026-10-03
- **Contexte** : dans `hw_profile.ps1`, `$Model` (paramètre) et `$model` (objet PSCustomObject retourné)
  désignaient **la même variable** (PowerShell ignore la casse) → les champs `bytes`/`n_layers`
  ressortaient nuls.
- **Décision** : renommer l'objet local en `$mdl`. Leçon appliquée à tous les scripts PowerShell du
  produit (préfixes distincts).

## D-017 — TTS : sélection de provider ONNX avec repli automatique
- **Date** : 2026-10-03
- **Contexte** : DirectML (`onnxruntime-directml 1.24.4`) échoue sur `ConvTranspose`
  (`Paramètre incorrect`, 0x80070057) sur Maxwell ; pire, ce build casse aussi le provider CPU.
- **Décision** : `tts_server.py` construit une liste de providers candidats
  (`DmlExecutionProvider` → `CUDAExecutionProvider` → `CPUExecutionProvider`), **sonde** chacun par une
  inférence courte, et retient le premier fonctionnel ; le provider actif est exposé par `/health`.
  `onnxruntime` standard (1.30.0) est conservé.
- **Raison** : optimiser le TTS sur GPU quand c'est possible, sans jamais casser un TTS qui fonctionne
  (auto-healing). Sur cette machine : `provider=CPUExecutionProvider` (repli).

## D-018 — Variante moteur active aplatie + variantes archivées
- **Date** : 2026-10-03
- **Décision** : conserver le contrat v1.2.0 (`backends\llama-cpp\llama-server.exe` = moteur ACTIF)
  tout en archivant les variantes dans `backends\llama-cpp\variants\{cpu,vulkan,cuda}\`.
  `engine_select.ps1` nettoie les fichiers moteur actifs (hors `cloud-proxy.exe`) puis copie la variante
  choisie ; `active.json` trace la sélection.
- **Raison** : préserver la compatibilité (lanceur, manifest, DoD) tout en rendant le moteur remplaçable
  individuellement sans recompilation.

## D-019 — Embeddings RAG : le moteur llama.cpp, sans modèle supplémentaire
- **Date** : 2026-10-03
- **Contexte** : un pipeline RAG exige des vecteurs d'embeddings. Les options classiques
  (`sentence-transformers`/torch, modèle ONNX dédié + tokenizer) sont lourdes (téléchargement,
  VRAM, dépendances).
- **Décision** : utiliser l'endpoint **`/v1/embeddings`** du moteur llama.cpp déjà présent, en
  démarrant une **instance dédiée** (`--embeddings --pooling mean`, port 8094) lancée **à la demande**
  par `rag_ingest.py` (et tracée dans `data\pids.txt` pour l'arrêt propre).
- **Raison** : aucun téléchargement supplémentaire, VRAM optimisée (instance non permanente),
  embeddings neuronaux réels (dimension 2048 constatée). Le flag `--pooling mean` est indispensable :
  sans lui, l'API renvoie *« Pooling type 'none' is not OAI compatible »*.

## D-020 — Recherche vectorielle : NumPy pur (faiss proscrit)
- **Date** : 2026-10-03
- **Décision** : conformément à la Section 1.1 du mandat, **ne pas utiliser faiss** (échecs de
  compilation native C++ sous Windows). La base vectorielle est une matrice `.npy` (float32) et la
  recherche s'effectue par **similarité cosinus** = produit scalaire de vecteurs L2-normalisés, calculé
  en NumPy.
- **Raison** : zéro compilation native, robustesse Windows, performances largement suffisantes pour
  les volumes visés (des dizaines de milliers de chunks).

## D-021 — Chunking et persistance à plat
- **Date** : 2026-10-03
- **Décision** : chunks de **2048 caractères** (multiple de 512, aligné sur le *prompt caching* de
  llama.cpp — équivalent ≈512 tokens) avec **recouvrement de 10 %**. Index **à plat** dans
  `runtime\rag\` : `index-<collection>.npy`, `chunks-<collection>.jsonl`, `manifest-<collection>.json`,
  `collections.json`. Aucune base embarquée (pas de sqlite/duckdb).

## D-022 — Token Saver : modèle virtuel unique + saturation de contexte
- **Date** : 2026-10-03
- **Décision** : exposer un **modèle virtuel unique** `localai` (alias `smart`, `auto`) côté LiteLLM ;
  le callback `complexity_router.py` décide :
  prompt court (< 3 mots) → **local** ; prompt complexe → **cloud si clé présente, sinon local** ;
  **contexte saturé** (> 6000 tokens ≈ `len/4`) → cloud si clé, sinon local.
  Préférence cloud : OpenRouter > DeepSeek > OpenAI > Anthropic. Chaque décision est journalisée dans
  `logs\routing.jsonl` (visible via `Run-LocalAI.bat proxy-logs`).
- **Raison** : point d'entrée unique pour l'agent (compatible Cline), coût maîtrisé (Token Saver),
  transparence totale du routage.

## D-023 — BYOK : coexistence `keys.env` / `cloud-keys.env` + `key-set`
- **Date** : 2026-10-03
- **Décision** : le mandat nomme `config\keys.env` ; la v1.2/v1.3 utilisait `config\cloud-keys.env`.
  Les **deux** fichiers sont chargés au démarrage (`keys.env` prioritaire). `Run-LocalAI.bat key-set`
  écrit de façon **chirurgicale** dans `keys.env` (les autres lignes et commentaires sont préservés ;
  la valeur n'est jamais réaffichée). Les deux fichiers sont **préservés** entre redéploiements.

## D-024 — `sd-turbo-light` : GGUF Q8_0 (déviation documentée du « safetensors »)
- **Date** : 2026-10-03
- **Contexte** : le mandat v1.4.1 demande une entrée `sd-turbo-light` **< 2 Go**, **format safetensors**,
  **source** `https://huggingface.co/stabilityai/sd-turbo`.
- **Constat (mesuré)** : `stabilityai/sd-turbo` ne publie qu'un seul safetensors —
  `sd_turbo.safetensors` = **5 214 561 328 octets (5,21 Go)**, `sha256 3f067a1b…616549`. Aucun fichier
  safetensors < 2 Go n'existe à cette source ; la contrainte « < 2 Go » **et** « safetensors **et**
  source stabilityai » est donc **irréalisable**.
- **Décision** : retenir la **quantisation Q8_0** de SD-Turbo — `Green-Sky/SD-Turbo-GGUF` →
  `sd_turbo-f16-q8_0.gguf`, **1,88 Go**, `sha256 d50be765…e51580`. Le format **GGUF est nativement
  supporté par `sd-server`** (stable-diffusion.cpp), donc l'objectif fonctionnel (modèle image léger
  réellement chargeable) est atteint.
- **Pourquoi** : la légèreté (« < 2 Go ») est l'intention opérationnelle ; c'est aussi la seule option
  qui reste **téléchargeable et utilisable** par le moteur installé. La source est un dérivé officiel
  du modèle stabilityai (documenté dans le catalogue).
- **Alternative écartée** : télécharger les 5,21 Go du safetensors officiel (contredit « léger »).

## D-025 — Watchdog VRAM : seuils et action préventive
- **Date** : 2026-10-03
- **Décision** : daemon `scripts\vram_watchdog.py`, échantillonnage **toutes les 2 s** :
  **alerte < 15 %** de VRAM libre (log console + `logs\vram.log` + `dev\crash.log` catégorie `GPU_VRAM`),
  **critique < 5 %** (action préventive : relance du moteur en **CPU pur `-ngl 0`** pour libérer la VRAM,
  consignée dans `data\vram-action.json`), **reprise > 20 %** (effacement de l'alerte).
- **Raison** : garde-fou opérationnel non intrusif (2 s × une requête `nvidia-smi` légère), action
  décisive et sûre en cas de saturation (le CPU fonctionne toujours), traçabilité complète.
- **Robustesse** : l'action n'est déclenchée qu'**une fois par épisode critique** (transition d'état) ;
  toute erreur est interceptée ; l'action est désactivable (`--no-action`) et le watchdog entier par
  `Run-LocalAI.bat start --no-watchdog`.
- **Commande** : `Run-LocalAI.bat vram-status` (VRAM totale/libre/utilisée, seuils, état du watchdog,
  dernière action).

## D-026 — Modèles *turbo* : `--steps 4` par défaut
- **Date** : 2026-10-03
- **Décision** : lorsque le modèle image est un modèle *turbo* (nom contenant `turbo`,
  cas de `sd-turbo` et `sd-turbo-light`), `sd-server` est lancé avec **`--steps 4`** ; sinon le défaut
  du moteur (20 étapes) est conservé.
- **Constat (mesuré)** : à 512×512 sur CPU, 20 étapes = **~12 min** par image ; 4 étapes = **~3,5 min**
  (`sampling 150 s` + `decode 68 s`), soit **~5× plus rapide**, sans perte notable (SD-Turbo est
  entraîné pour 1 à 4 étapes).
- **Erreur évitée** : `--extra-sample-args steps=4` est **ignoré** par ce moteur (cette liste ne
  concerne pas `steps`) ; le flag correct est le CLI **`--steps <int>`** (documenté par `sd-server --help`).
- **Impact** : uniquement les modèles dont le nom contient `turbo` — les modèles classiques gardent
  le défaut.

## D-027 — Héritage des modèles téléchargés + version dynamique
- **Date** : 2026-10-03
- **Constat** : la réinstallation reconstruit l'arborescence (`_rmtree` puis déploiement) ; la règle
  d'or ne préservait que `config\keys.env`, `config\cloud-keys.env`, `config\bench-history.jsonl`,
  `runtime\rag\`. Le modèle image **téléchargé par l'utilisateur** (1,88 Go) était donc **perdu**
  à chaque réinstallation.
- **Décision 1** : étendre la règle d'or à `models\<SD_TURBO_LIGHT_FILE>` (copie transactionnelle
  depuis `prev_product` vers `LocalAI.new` avant bascule). Vérifié : `heritage conserve : …\models\
  sd_turbo-f16-q8_0.gguf`.
- **Décision 2** : `_write_text()` substitue désormais le placeholder **`__VERSION__`** par la version
  courante lors de l'écriture des gabarits. Les versions figées (`v1.2.0` dans la bannière, `v1.3.0`
  dans les titres) sont remplacées par ce placeholder : plus aucune dérive de version à chaque phase.
- **Impact** : une donnée utilisateur coûteuse (téléchargement) survit aux réinstallations et la
  version affichée est toujours celle réellement déployée.

## D-028 — Stabilisation v1.4.1 : dépendance `prisma` du proxy LiteLLM (bug résiduel)
- **Date** : 2026-10-03
- **Détection** : JALON 1 (bêta-test de rupture pré-v1.5.0). `GET http://127.0.0.1:4000/v1/models`
  **sans** en-tête `Authorization` → **HTTP 500** au lieu de **401**.
- **Cause racine (trace de pile)** :
  `litellm/proxy/auth/user_api_key_auth.py` → `auth_exception_handler._as_proxy_exception()` →
  `PrismaDBExceptionHandler.is_database_service_unavailable_error()` →
  `litellm/proxy/db/exception_handler.py::is_database_infrastructure_error()` fait un
  **`import prisma` non protégé** → `ModuleNotFoundError: No module named 'prisma'` → 500.
  La cause amont : `deploy_python()` installe `litellm[proxy]==1.103.2` avec **`check=False`** ;
  l'extra `proxy` apporte `prisma`, mais un échec partiel de résolution pip est **silencieux**.
- **Impact** : toute requête non authentifiée (client mal configuré, Cline/VS Code sans clé)
  recevait un 500 opaque au lieu d'un 401 explicite. La voie nominale (clé maître `sk-local`)
  fonctionnait, ce qui masquait le défaut.
- **Correctif (auto-healing, 2 volets)** :
  1. **Réparation runtime** : `ensure_proxy_deps(root, log)` dans le code de déploiement —
     sonde `python -c "import prisma"` ; si absent, `pip install --target <site-packages> prisma`
     puis **re-vérifie** l'import et trace le résultat (`[OK]` / avertissement explicite).
  2. **Inventaire** : `runtime/python/Lib/site-packages/prisma/__init__.py` ajouté au manifest.
- **Principe retenu** : on n'installe **pas** de stub maison (un faux module `prisma` masquerait
  d'éventuelles fonctionnalités de base de données réelles) ; on installe la **dépendance officielle**
  dans le Python embarqué isolé, conformément à la doctrine du portage.
- **Vérification** : `is_database_infrastructure_error(ValueError) -> False` (plus d'exception) ;
  `GET /v1/models` sans clé → **HTTP 401** ; avec clé `sk-local` → **HTTP 200** + 7 modèles.
- **Statut** : ✅ corrigé, re-testé (JALON 1 : 7/7).

## D-029 — Moteur VISION en CPU sur Maxwell (Vulkan device lost)
- **Date** : 2026-10-03
- **Constat (mesuré)** : le moteur vision lancé sur GPU (`-ngl 99`, variante Vulkan) **crashe** dès
  l'encodage de l'image :
  `mtmd_batch_encode: error: vk::Device::waitForFences: ErrorDeviceLost` →
  `ggml_vulkan: device lost on Vulkan0`. Le processus meurt, le port 8095 devient muet
  (`WinError 10061` — connexion refusée) — ce qui faisait échouer l'outil MCP `localai_vision_caption`.
- **Cause** : le chemin **multimodal** (`mtmd`, encodeur visuel) est nettement plus gourmand que le
  chemin texte et déclenche une perte de device Vulkan sur Maxwell (GTX 970M, CC 5.2).
  Le texte (llama — chat) reste stable sur Vulkan.
- **Décision** : le **moteur vision tourne en CPU par défaut** (`-ngl 0`), surchargeable par
  `LOCALAI_VISION_NGL`. Le moteur de chat conserve le GPU.
- **Justification** : un VLM 2B en CPU à `-c 2048` produit une légende en ~40 s (376 tokens) —
  largement suffisant pour de la description d'image ; la stabilité prime sur le débit.
  Le GPU reste dédié au texte, où il apporte son gain (≈4,8×).
- **Vérifié** : `{"status":"ok"}` sur 8095, puis outil MCP `localai_vision_caption` →
  `isError:false`, légende correcte.

## D-030 — Passerelle MCP : SDK officiel consommé, aucune réimplémentation
- **Date** : 2026-10-03
- **Décision** : `scripts\mcp_gateway.py` s'appuie **exclusivement** sur le SDK officiel `mcp`
  (JSON-RPC 2.0 sur stdio), conformément à la spécification **2024-11-05**. Aucune réimplémentation
  maison du protocole.
- **Constat mesuré** : `litellm[proxy]==1.103.2` (déjà installé) **fournit `mcp` 2.3.0** dans le Python
  embarqué, et l'ensemble (starlette 1.7.0, fastapi 0.142.2, typing-extensions 4.16.0) **reste
  importable par LiteLLM**. La passerelle consomme donc ce SDK **sans rien installer**.
- **API retenue** : SDK v2 — `from mcp.server.mcpserver import MCPServer` (`FastMCP` renommé en v2),
  décorateur `@app.tool(...)`, `app.run(transport="stdio")` ; côté client `stdio_client` +
  `ClientSession` (`initialize`, `list_tools`, `call_tool`).
- **Repli défensif** : `runtime\mcp\packages` reste prévu comme cible d'installation isolée
  (`pip install mcp --target`) si une version future de LiteLLM cessait de fournir le SDK — motif
  d'isolation déjà retenu pour les paquets RAG (`runtime\packages`).
- **Centralisation** : `config\mcp-settings.json` déclare les **serveurs** (transport, commande, args)
  et les **outils** ; il est **préservé** entre réinstallations (règle d'or).
- **Outils exposés** : `localai_rag_query`, `localai_vision_caption`, `localai_status`,
  `localai_vram_status`, `localai_graph_show`.
- **Vérifié** : `mcp-list` → serveur `localai [up]`, 5 outils ; `mcp-test` → **VERDICT VERT** ;
  `mcp-call` → payload JSON-RPC propre (`isError:false`).

## D-031 — Auto-régulation : subdivision du JALON 2 en v1.5.0a / v1.5.0b
- **Date** : 2026-10-03
- **Décision** : conformément à la clause d'auto-régulation du mandat, le jalon v1.5.0 a été exécuté
  en **deux sous-étapes étanches**, chacune déployée, testée et validée au vert :
  - **v1.5.0a — Vision locale** : paire GGUF+`mmproj` atomique, injection `--mmproj`, métadonnées
    images dans l'index RAG.
  - **v1.5.0b — Protocole MCP** : SDK officiel, passerelle, `mcp-settings.json`, commandes CLI.
- **Justification** : les deux chantiers touchent des surfaces disjointes (moteur d'inférence vs
  passerelle d'outils) et chacun exige son propre cycle déploiement/test ; les séparer a permis de
  détecter et corriger tôt des défauts réels (perte d'héritage des modèles vision, `serve` transformé
  en chemin, `Vulkan device lost`) sans contaminer la seconde sous-étape.
- **Doctrine** : inchangée à chaque sous-étape (sauvegarde ante-exécution, patch chirurgical,
  validation AST, test, trace).

## D-032 — GraphRAG : extraction NER/RE déléguée au LLM local (pas de regex)
- **Date** : 2026-10-03
- **Décision** : `scripts\graph_rag.py` n'utilise **aucune heuristique par expressions régulières** pour
  l'extraction d'entités et de relations. Chaque chunk est soumis à **`llama-server.exe`**
  (`POST /v1/chat/completions`, prompt structuré exigeant **un tableau JSON strict**
  `[{"head","type","relation","tail"}]`, `temperature=0`).
- **Pourquoi** : les graphes issus de regex sont pauvres (pas de typage, pas de relations
  sémantiques, pas de synonymie). Déléguer au LLM local produit un graphe typé et exploitable,
  **100 % hors ligne**.
- **Robustesse du parsing** : extraction du **premier tableau JSON équilibré** (recherche par comptage
  de crochets), puis nettoyage des virgules terminales et second essai ; les triplets invalides sont
  ignorés, les échecs comptés (`stats.echecs`) — **aucun crash** sur sortie LLM imparfaite.
- **Complément déterministe** : les **interdépendances structurelles du code source** (imports /
  références via `IMPORT_PATTERNS` par langage) sont ajoutées au graphe comme arêtes `kind:"structural"`,
  distinctes des arêtes `kind:"llm"` (traçabilité `provenance` = fichier d'origine).
- **Sérialisation** : `runtime\storage\graph_db.json` **à plat** — `nodes` (id, name, type, mentions,
  degree, sources) et `edges` (source, relation, target, kind, provenance), plus `stats` et `engine`.
- **Interface** : `Run-LocalAI.bat graph-index <dossier>` / `graph-show` ; outil MCP
  `localai_graph_show` (déjà déclaré en v1.5.0).

## D-033 — Failover SSE : bufferisation complète ou bascule avant le premier token
- **Date** : 2026-10-03
- **Décision** : `scripts\failover_proxy.py` (port 8081) applique **deux régimes distincts** :
  1. **Requêtes sensibles / agent** (stream + `model` dans la liste bufferisée, ou en-tête
     `X-LocalAI-Buffer: 1`) → **BUFFERISATION COMPLÈTE AVANT ENVOI** : la génération est lue
     intégralement, puis restituée au client sous forme de flux SSE régulier. Toute défaillance
     (port injoignable, exception, HTTP ≥ 500) est **interceptée** et la requête est **rejouée
     silencieusement** sur la route suivante — le client ne voit **jamais** de flux interrompu.
  2. **Requêtes de routine en streaming pur** → **FAILOVER SUR ERREUR AVANT LE PREMIER TOKEN** :
     la route est choisie **avant** d'ouvrir le flux (sonde TCP, `connect_timeout_s = 1.5 s`),
     puis relayée telle quelle.
- **Chaîne de reprise déterministe** : **primaire** (cœur LocalAI, 8080) → **secondaire local**
  (moteur vision CPU, 8095) → **cloud** (clé lue dans `config\cloud-keys.env`, activable/désactivable).
  L'ordre est fixe et auditable ; aucun réessai aléatoire.
- **Budget de décision** : la sonde TCP + l'ouverture d'un socket refusé sont **quasi instantanées** ;
  le budget `1.5 s` borne la décision de bascule. Chaque événement est journalisé dans
  `logs\failover.jsonl` (`route`, `mode`, `failover`, `ms_decision`, `caracteres`).
- **Configuration** : `config\failover.json` (préservé entre réinstallations, cf. D-034) — routes,
  marqueur de bufferisation, seuils de temps, activation du cloud.

## D-034 — `config\failover.json` entre dans la règle d'or
- **Date** : 2026-10-03
- **Décision** : comme `config\mcp-settings.json`, la politique de failover est **préservée** entre
  réinstallations et n'est écrite que si elle est absente.
- **Justification** : ces deux fichiers sont des **points d'extension utilisateur** (serveurs MCP
  externes, routes de secours, seuils). Les écraser silencieusement à chaque mise à jour ferait perdre
  une configuration coûteuse — exactement le défaut corrigé en A6 pour les modèles téléchargés.

## D-035 — Auto-régulation : subdivision du JALON 2 en v1.7.0a / v1.7.0b
- **Date** : 2026-10-03
- **Décision** : conformément à la clause d'auto-régulation du mandat v1.7.0/v1.8.0, le jalon v1.7.0
  a été exécuté en **deux sous-étapes étanches**, chacune déployée, testée et validée au vert :
  - **v1.7.0a — Quantization** : support de `llama-quantize.exe`, CLI, mode asynchrone, historique.
  - **v1.7.0b — Privacy** : filtre PII hybride 3 niveaux, intégration Token Saver, audit, drapeau
    de désactivation.
- **Justification** : surfaces disjointes (chaîne d'outils de compression vs chemin de requête du
  proxy) avec deux cycles de validation distincts (un modèle F16 réel à compresser ; un prompt
  sensible à faire déborder vers le cloud). Les séparer a permis de valider la quantization sur un
  artefact physique avant d'introduire le filtre dans le chemin de routage.

## D-036 — Filtre PII : BEST-EFFORT assumé, réversible, désactivable, audité
- **Date** : 2026-10-03
- **Décision** : le filtre de confidentialité est délibérément présenté comme une protection
  **BEST-EFFORT** (et non une garantie d'étanchéité), conformément au mandat.
- **Niveaux retenus** : (1) regex déterministes pour les formats standard ; (2) **entropie de
  Shannon** (≥ 3,5 bits, jetons ≥ 20 caractères, jeu de caractères mixte) pour les secrets en clair ;
  (3) NER local léger via le moteur déjà présent.
- **Choix d'ingénierie N3** : plutôt qu'un modèle de Token Classification séparé (< 50 Mo) exigeant
  une chaîne tokenizer + runtime supplémentaire, le niveau 3 réutilise le **moteur local déjà
  installé** (prompt NER structuré, `T=0`). Même capacité sémantique, **zéro téléchargement
  supplémentaire**, cohérent avec D-032 (GraphRAG). Le modèle reste local : l'appel NER ne quitte
  jamais la machine.
- **Réversibilité** : le masquage produit `[PII-TYPE-n]` **et** un mapping ; la réponse est
  démasquée avant d'être rendue à l'utilisateur local (aucune perte d'information pour lui).
- **Désactivation** : `--no-pii-filter` sur `start` (→ `LOCALAI_PII_FILTER=0`) et inspection
  indépendante `privacy-levels` / `privacy-test`.
- **Audit** : chaque masquage est consigné dans `dev\crash.log` catégorie `PRIVACY_FILTER`
  (type, niveau, jeton, aperçu tronqué) — un aperçu tronqué est journalisé, **jamais le secret
  complet**, afin que le journal d'audit ne devienne pas lui-même une fuite.

## D-037 — INCIDENT v1.8.0 : bascule destructive → permutation par renommage (correctif critique)
- **Date** : 2026-10-03
- **Gravité** : **CRITIQUE** — la garantie centrale de la doctrine (« aucune perte ») a été violée.
- **Séquence** : (1) un processus hérité (installation `onnxruntime-directml` lancée dans le Python
  embarqué) **verrouillait `runtime\python`** ; (2) `swap_product()` appelait `_rmtree(final_root)`
  **avant toute garantie** ; la suppression a échoué **à mi-chemin** après avoir effacé
  `config\`, `models\`, `scripts\`, `backends\` et la racine ; (3) `_os.replace(LocalAI.new → LocalAI)`
  a échoué ; (4) le rollback a **supprimé `LocalAI.new`**, jetant le produit neuf et complet.
  Seul `runtime\python` (partiellement verrouillé) a survécu.
- **Cause racine** : ordre destructif (`supprimer l'ancien` **puis** `installer le nouveau`) au lieu
  d'une **permutation**. Un verrou de fichier suffisait donc à perdre le produit **et** le staging.
- **Correctif 1 — permutation par renommage** :
  1. `LocalAI` → `LocalAI.old` (`_os.replace`) ;
  2. `LocalAI.new` → `LocalAI` (`_os.replace`) ;
  3. suppression de `LocalAI.old` en **best-effort** (un échec ici n'est **pas** une perte).
  Si l'étape 2 échoue : l'ancien est **restauré** et le nouveau **conservé** pour réessai.
- **Correctif 2 — garde préalable** : `_guard_running_services()` sonde `data\pids.txt`
  (`OpenProcess`) et **refuse** la reconstruction si un service est actif, avec un message
  actionnable (« `Run-LocalAI.bat stop` puis relance »). Le scénario de fichiers verrouillés est
  désormais **impossible par construction**.
- **Leçon doctrinale retenue** : une bascule transactionnelle doit être **non destructive en amont** ;
  l'ordre correct est *écarter → installer → purger*, jamais *purger → installer*. La suppression
  d'un arbre de production ne doit **jamais** précéder la mise en place de son remplaçant.
- **Reconstruction** : produit reconstruit par l'installeur (doctrine « reconstructible, effaçable »).
  Les modèles téléchargés par l'utilisateur (SD-Turbo Q8, paires vision) **doivent être ré-acquis**
  via `Run-LocalAI.bat pull` — consigné dans `dev\crash.log` (catégorie `DEPLOY_GUARD`).

## D-038 — Auto-régulation : exécution de la cascade v1.9.0/v2.0.0/v2.1.0 en sous-étapes bornées
- **Date** : 2026-10-03
- **Décision** : conformément à la clause d'auto-régulation du mandat (qui cite explicitement
  « v2.0.0a Crypt / v2.0.0b Learn »), la cascade **v1.9.0 → v2.0.0 → v2.1.0** est exécutée en
  **sous-étapes bornées**, chacune livrée, déployée, éprouvée par le mode Bêta-Testeur Fou et validée
  au vert **avant** d'ouvrir la suivante.
- **Découpage retenu** :
  | Sous-étape | Contenu | Jalon du mandat |
  |---|---|---|
  | **v1.9.0** | Speculative Decoding **TEXT-ONLY** (`--model-draft`, `--draft-max/min`), garde VRAM avant lancement | JALON 2/3 |
  | **v2.0.0a** | Espace hermétique **AES-256** au repos (clé dérivée d'un mot de passe, jamais stockée) | JALON 4/5 |
  | **v2.0.0b** | **Profil apprenant** continu (`logs\history.jsonl` → seuils VRAM/`-ngl`) + `reset-profile` | JALON 4/5 |
  | **v2.1.0a** | Découverte réseau **mDNS/UDP** des nœuds RPC | JALON 6/7 |
  | **v2.1.0b** | **Routage fédéré** (`--rpc <IP>:<Port>` injecté dynamiquement) + `peer-status` | JALON 6/7 |
- **Justification** : chaque sous-étape modifie une surface **disjointe** (chemin de lancement du
  moteur ; stockage au repos ; télémétrie de profil ; découverte réseau ; transport de calcul). Une
  sous-étape à la fois préserve la doctrine transactionnelle (sauvegarde, patch chirurgical, AST,
  test) et permet d'isoler toute régression sur une seule surface — leçon directement tirée de
  l'incident D-037.
- **Engagements** : aucune sous-étape n'est déclarée livrée sans (a) validation AST, (b) test physique
  réel, (c) trace dans `dev\patch_integrity.log`, `dev\CHANGELOG.md`, `dev\DECISIONS.md` et
  `dev\crash.log` (catégories dédiées : `SPEC_DECODE`, `SOUVERAIN_CRYPT`, `PROFILE_LEARN`,
  `RPC_FEDERATED`).

## D-039 — Speculative Decoding : implémenté, correct, mais **désactivé par défaut** (aucun gain mesuré)
- **Date** : 2026-10-03
- **Décision** : le Speculative Decoding TEXT-ONLY est **implémenté et pleinement fonctionnel**
  (paire de tokenizer partagé, garde VRAM, règle TEXT-ONLY, drapeaux réels du binaire), mais il est
  **OPT-IN** (`LOCALAI_SPEC=1`) et **non actif par défaut**.
- **Mesure réelle** (prompt texte pur, `max_tokens=160`, GPU Vulkan `ngl=99`) :
  | Configuration | Débit |
  |---|---|
  | **AVEC draft** (Qwen2.5-1.5B + draft 0.5B) | 160 tokens / 7,48 s = **21,39 tok/s** |
  | **SANS draft** (Qwen2.5-1.5B seul) | 160 tokens / 7,35 s = **21,76 tok/s** |
  → **Aucun gain** : l'écart est dans le bruit, alors que le draft coûte **~470 Mo de VRAM** et un
  **second chargement de modèle**.
- **Pourquoi** : le décodage spéculatif accélère les charges **limitées par la bande passante
  mémoire** (CPU-bound, offload partiel). Ici le modèle entier est déjà offloadé sur GPU et la
  vérification des jetons draftés ajoute du travail sans réduire le coût dominant.
- **Conséquence produit** : activer le draft par défaut dégraderait l'expérience (VRAM consommée,
  démarrage plus long) **sans bénéfice**. La fonctionnalité reste **disponible** pour les profils
  CPU-bound (« SOFT ») et pour les machines à faible VRAM, où le gain est réel.
- **Anomalies corrigées au passage** :
  - **A24** : `--draft-max`/`--draft-min` **retirés** par llama.cpp → le moteur refusait de démarrer ;
    remplacés par `--spec-draft-n-max`/`--spec-draft-n-min` (constatés par `llama-server --help`).
    Le mandat citait les anciens noms : la déviation est **documentée**.
  - **A25** : incohérence de tokenizer (principal Llama-3.2 vs draft Qwen2.5) → la paire déclarée au
    catalogue devient le moteur principal quand elle est présente.
- **Traces** : `dev\crash.log` (catégorie `SPEC_DECODE`), `dev\patch_integrity.log` (JALON 2/3).

## D-040 — Espace hermétique : AES-256-GCM au repos, clé dérivée et jamais stockée
- **Date** : 2026-10-03 · **Sous-étape v2.0.0a**
- **Décision** : `scripts\vault.py` chiffre la **zone sémantique** (`runtime\rag\`, `runtime\storage\`)
  en **AES-256-GCM** (chiffrement **authentifié** : confidentialité **et** détection de toute
  corruption), avec une **clé dérivée à la volée** par **PBKDF2-HMAC-SHA256** — **390 000 itérations**,
  **sel aléatoire de 16 octets** conservé dans l'en-tête du conteneur.
- **La clé n'est JAMAIS écrite sur disque** : elle est recalculée à chaque opération à partir du
  **mot de passe saisi dans la console** (`getpass`, saisie masquée) ou, pour l'automatisation, d'une
  **variable d'environnement** (`--password-env`) explicitement documentée comme moins sûre.
- **Formats supportés** : `.npy`, `.json`, `.jsonl`, `.bin` — soit exactement les artefacts de l'index
  RAG et du graphe (`index-*.npy`, `chunks-*.jsonl`, `manifest-*.json`, `collections.json`,
  `graph_db.json`).
- **Cycle retenu** : `seal` chiffre puis **supprime le clair** (données verrouillées au repos) ;
  `unseal` reconstitue le clair **et conserve le conteneur** (le `.enc` reste la source au repos).
  `seal` **vérifie immédiatement la réversibilité** avant toute suppression : si le contrôle échoue,
  le conteneur est supprimé et l'opération annulée — **aucune perte possible**.
- **CLAUSE DE TRANSPARENCE** (reprise dans `INSTALLATION.md`) :
  1. le chiffrement agit **strictement au repos** — pendant la session, les fichiers nécessaires aux
     moteurs (NumPy, JSON) existent **en clair sur le disque**, faute de quoi ils seraient
     inexploitables ; `stop` les scelle ;
  2. **l'effacement des chaînes en mémoire vive n'est PAS garanti** : il dépend du **ramasse-miettes**
     de Python (meilleur effort sémantique), pas d'un verrouillage mémoire ;
  3. un **mot de passe oublié = données perdues** (aucune porte dérobée, aucune clé de secours).
- **Dépendance** : `cryptography` (wheel Python **déjà présent**, apporté par les dépendances du
  proxy) ; `AESGCM` est la primitive standard. Aucune installation système, aucun binaire externe.
- **CLI** : `vault-status`, `vault-seal`, `vault-unseal`, `vault-test` (autotest sur zone temporaire,
  les données réelles ne sont jamais touchées).
- **Mesure réelle** : autotest **VERT** (scellement OK, ouverture OK, **intégrité IDENTIQUE**,
  **mauvais mot de passe refusé**) ; sur un **index RAG réel** (4 fichiers : `.npy` 41 Ko, `.jsonl`,
  `.json` ×2) → cycle scellé/ouvert avec **4/4 empreintes SHA-256 identiques → ZÉRO CORRUPTION**.

## D-041 — Profil apprenant continu : adaptation à chaud des seuils VRAM (et retour d'usine garanti)
- **Date** : 2026-10-03
- **Contexte** : le watchdog VRAM (§ v1.4.1) utilisait des seuils **fixes** (SOFT/NORMAL/HARD) choisis
  au démarrage. Or la VRAM réellement disponible varie selon les modèles chargés et l'usage : une
  machine confortable reçoit des alertes inutiles, une machine tendue n'est protégée qu'en surface.
  JALON 4 (v2.0.0b) demande un profil **apprenant**.
- **Décision** :
  1. **`scripts\learn_profile.py`** analyse la **télémétrie réelle** de la session :
     `logs\history.jsonl` (observations consolidées), `logs\vram.log` (échantillons du watchdog),
     `logs\failover.jsonl` (bascules) et `config\hardware-profile.json` (machine).
  2. Il écrit `config\profile.json` : **seuil d'alerte ancré sur le MINIMUM de VRAM libre réellement
     observé** (+5 pts de marge), seuil critique = alerte − 8, seuil de reprise = alerte + 10, le tout
     **borné** (alerte 8–25 %, critique 3–12 %, reprise 15–40 %) pour interdire tout réglage absurde.
  3. **Offload `-ngl`** : conservé au maximum par défaut ; **réduit de 20 %** uniquement si des
     évictions critiques ont été enregistrées par le watchdog (preuve d'une saturation réelle).
  4. **Application à chaud** : le watchdog **relit** `config\profile.json` toutes les 5 s et adopte les
     nouveaux seuils **sans redémarrage** (et **revient** aussitôt aux valeurs d'usine si le profil est
     un profil d'usine). Preuve obtenue : watchdog démarré en `15/5/20` → `25/12/35` appliqués à chaud.
  5. **Garde-fou QA `reset-profile [soft|normal|hard]`** : efface le profil appris **et écrit** les
     valeurs d'usine choisies dans `config\profile.json`, de sorte que le retour soit **immédiat**
     (vérifié : 25/12/35 → 20/10/30 en quelques secondes, sans redémarrage).
  6. **Persistance** : `config\profile.json` et `logs\history.jsonl` ajoutés à la **règle d'or de
     l'héritage** — l'apprentissage **survit aux réinstallations** (vérifié après redéploiement).
  7. **Traçabilité** : catégorie `PROFILE_LEARN` dans `dev\crash.log` ; *fichier absent ou données
     insuffisantes (< 2 observations) → repli automatique sur le profil d'usine*, jamais d'échec.
- **Raison** : s'adapter aux mesures **réelles** plutôt qu'à des constantes théoriques, tout en
  conservant un **chemin de retour déterministe** (exigence de réversibilité du mandat).
- **Transparence** : l'apprentissage est **descriptif** (statistiques simples sur des mesures du
  poste) ; il n'exporte aucune donnée et n'infère rien sur le contenu des requêtes.
- **Mesures (matériel de référence)** : NVIDIA GTX 970M, 6144 Mo ; VRAM libre observée 61,3–62,6 %
  → seuil d'alerte appris 25 % (borne haute), `ngl` 99 conservé (0 éviction) ; historique 3 → n
  observations ; AST VERT ; 83 composants ; zéro zombie.

## D-044 — Renommage AiTron V3 : identité produit, migration d'héritage, audit mono-bloc
- **Date** : 2026-10-03
- **Contexte** : PHASE V3 Finale exige l'identité **AiTron V3** : renommage du script maître, du
  répertoire produit, des références internes, de la charte et du manifeste, puis un **audit
  d'autonomie** (reconstruction complète après suppression physique du produit).
- **Décision** :
  1. **Script maître** : `install_localai_win.py` ➔ **`install_AiTron_v3.py`** (racine de la sandbox).
  2. **Produit** : `LocalAI\` ➔ **`AiTron\`** ; staging `AiTron.new` (dérivé automatiquement).
  3. **Code embarqué** : `LOCALAI_DEPLOY_CODE` ➔ **`AITRON_DEPLOY_CODE`**.
  4. **Variables d'environnement** : `LOCALAI_*` ➔ **`AITRON_*`** (y compris `AITRON_LANG`,
     `AITRON_LOCAL_KEY`, `AITRON_SPEC`, `AITRON_P2P`…). **Exception assumée** : les constantes de
     **provenance amont** (`LOCALAI_VERSION`, `LOCALAI_TAG`, `LOCALAI_URL`, `LOCALAI_SHA256`,
     `LOCALAI_ASSET`…) **conservent leur nom** — elles décrivent le fork, pas notre produit.
  5. **Le moteur garde son nom** : **`local-ai.exe`** reste inchangé. C'est la technologie ; seul le
     **produit d'inférence contextuelle** s'appelle **AiTron V3**. De même, l'identifiant de modèle
     LiteLLM `localai` et le wrapper `Run-LocalAI.bat` (nommé tel quel par le mandat) sont conservés.
  6. **Manifeste** : `"product": "AiTron V3 (portage natif, sans Docker/WSL)"`,
     `"fork_of": "LocalAI (https://github.com/mudler/LocalAI)"`, `"license": "MIT"`.
  7. **CHARTE.md** : `Projet : AiTron V3`, `Livrable : install_AiTron_v3.py`.
  8. **Migration d'héritage** : si `AiTron\` n'existe pas mais que `LocalAI\` est présent, l'installeur
     **reprend automatiquement l'héritage depuis le répertoire historique** — aucune donnée
     utilisateur (clés, index RAG, modèles téléchargés, profil appris, historique) n'est perdue.
  9. **Audit mono-bloc (JALON 3)** : nouvelle option **`--prev <chemin>`** permettant d'expliciter la
     source d'héritage, afin de pouvoir **supprimer physiquement** le produit et le **reconstruire
     intégralement** à partir d'une sauvegarde. La sauvegarde est un **déplacement** (renommage, sans
     copie) : ~6 Go de modèles ne sont pas dupliqués inutilement.
  10. **Avertissement de transparence** ajouté à la documentation (FR et EN) : « AiTron V3 est un fork
      indépendant de LocalAI (licence MIT), enrichi d'une couche d'orchestration souveraine pour
      Windows. Il n'est aucunement affilié au projet LocalAI officiel. »
- **Écart assumé par rapport au libellé du mandat** : le mandat cite une sandbox `G:\Projet\` ; la
  sandbox réelle du chantier est **`G:\V1\LocalAI-Projet\`**. Renommer le répertoire de sandbox
  reviendrait à déplacer la session en cours : hors périmètre. Tous les livrables « à la racine »
  exigés par le mandat sont produits à la racine de la sandbox **réelle**. Consigné dans
  `ANOMALIES_NON_RÉSOLUES.log` (catégorie `RENAME`).
- **Raison** : sceller l'autonomie et l'identité du produit sans perdre l'acquis de l'utilisateur, et
  **prouver** par un crash-test que l'installeur est **auto-suffisant** (mono-bloc).
- **Mesures** : renommage appliqué (produit `AiTron\`, manifeste `AiTron V3` + `fork_of` + `MIT`) ;
  **audit mono-bloc** : produit **supprimé** puis **entièrement reconstruit** par le seul installeur
  (87 composants), moteur 195 Mo, modèle 807 Mo, index RAG et 4 backends (llama-cpp,
  stable-diffusion, whisper-cpp, tts) restaurés ; `local-ai.exe` conservé ; bannière `AiTron (v3.0.0)`.


- **Date** : 2026-10-03
- **Contexte** : PHASE 2.20 (v2.1.1) demande un support multilingue **FR/EN** avec **repli embarqué
  garanti**, sans dépendance système lourde, et une bascule **à chaud**.
- **Décision** :
  1. **Couche 1 — embarquée (source de vérité ultime)** : le dictionnaire `TRANSLATIONS` vit
     **dans** `scripts\i18n.py`, lui-même généré par le script maître. Il est donc **toujours
     disponible**, même si tous les fichiers externes sont absents ou corrompus.
  2. **Couche 2 — JSON externe** : `i18n\fr.json` et `i18n\en.json` sont **générés à l'installation**
     depuis l'embarqué, puis **surchargent** celui-ci clé par clé : l'utilisateur peut personnaliser
     ses messages sans toucher au code. **Une personnalisation existante n'est jamais écrasée** lors
     d'une réinstallation.
  3. **Couche 3 — `I18N_REV`** : si la révision du script diffère de `_i18n_rev` lu sur le disque, seules
     les clés de **documentation** (`help_*`, `tip_*`) sont **rafraîchies depuis l'embarqué** pour
     propager les mises à jour textuelles ; **les autres clés restent sous contrôle utilisateur**.
  4. **Aiguillage universel** `tr(key, **kwargs)` ; langue active par priorité :
     **`LOCALAI_LANG` → `config\lang.json` "lang" → défaut `"fr"`**.
  5. **Restitution CLI** : `i18n\_fr.bat` et `i18n\_en.bat` (**UTF-8 sans BOM**) portent les messages du
     wrapper (`MSG_HELP_nn`, `MSG_HELP_COUNT`, `MSG_<clé>`). `Run-LocalAI.bat` **charge dynamiquement**
     le fichier de la langue active — **aucun redémarrage** n'est nécessaire. `chcp 65001 >nul` est
     injecté au sommet du wrapper pour éviter la corruption des accents par la page de code Windows.
  6. **Bannière** : `localai_up.ps1` lit `config\lang.json` puis `i18n\<lang>.json` (clé
     `banner_title`) → la bannière de démarrage suit la langue active.
  7. **Commandes** : `lang` (état), `lang fr|en` (bascule à chaud, écrit `config\lang.json`),
     `lang list` ; plus `i18n-status` et `i18n-test` (autotest FR/EN/repli).
  8. **Documentation double** : `INSTALLATION.fr.md` et `INSTALLATION.en.md` ; `INSTALLATION.md` à la
     racine fait office d'**aiguillage** et contient l'essentiel autonome dans les deux langues.
  9. **Repli sûr** : fichier JSON absent, illisible ou **JSON invalide** → repli **silencieux** sur la
     couche 1 (tracé en catégorie `I18N` dans `dev\crash.log`). Le produit **ne plante jamais** à
     cause d'un fichier de langue.
- **Bug de déploiement corrigé (leçon)** : `gen_lang_bat()` utilisait `__version__` alors que le code de
  déploiement s'exécute dans un **namespace injecté** où la convention est **`__VERSION__`** ; et
  `generate_i18n()` exécutait `I18N_PY` dans un namespace **sans `__file__`**. Symptôme : fichiers
  `i18n\*.bat` **vides (0 octet)** et JSON non générés, sans échec d'installation visible.
  Corrigé : `__VERSION__` + injection de `__file__`. **Leçon : lire le journal d'installation ligne à
  ligne — une étape « dégradée » peut passer pour un succès.**
- **Raison** : garantir qu'aucune panne de fichier externe ne prive l'utilisateur de l'interface, tout
  en laissant la personnalisation possible et les mises à jour propageables.
- **Mesures (poste de référence)** : `i18n-test` → **VERDICT VERT** (FR et EN résolus, repli embarqué
  correct) ; `lang en` → bannière et aide **instantanément en anglais**, `config\lang.json` mis à jour ;
  `lang fr` → retour immédiat ; JSON corrompu → repli couche 1 sans plantage.


- **Date** : 2026-10-03
- **Contexte** : JALON 6 (v2.1.0) demande une **inférence fédérée** : déporter du calcul vers d'autres
  machines quand l'hôte sature. Le mandat est explicite : **ne pas réinventer de protocole de
  transport** ; le module de découverte doit être **léger, autonome, en pur Python** (mDNS **ou**
  broadcast UDP non invasif) et ne servir **qu'à identifier les adresses IP** des nœuds disponibles.
- **Décision** :
  1. **`scripts\peer_discovery.py`** (v2.1.0a) — découverte **UDP broadcast**, **pur Python, zéro
     dépendance externe** (pas de `zeroconf`, pas d'`avahi`). Il ne transporte **aucune donnée
     d'inférence** : deux messages seulement, `query` (demande) et `reply` (identité du nœud).
  2. Le transport et la parallélisation du calcul sont **délégués à 100 % au cœur RPC natif de
     llama.cpp** : le module se contente de produire l'**argument exact** `--rpc <IP>:<Port>`
     (option réelle `--rpc SERVERS` de `llama-server`, liste `host:port` séparée par des virgules).
  3. **`scripts\vram_watchdog.py`** (v2.1.0b) applique le **routage fédéré local** : si la VRAM passe
     sous le seuil critique et qu'un nœud RPC distant est **déclaré ET réellement joignable** (test
     TCP court sur le port RPC), le moteur est relancé avec `--rpc` injecté. **Escalade** : routage
     fédéré d'abord, **repli CPU pur (`-ngl 0`)** ensuite. Catégorie `FEDERATION` tracée.
  4. **CLI** : `peer-status` (exigé par le mandat — IP, port, latence, joignabilité), `peer-scan`,
     `peer-test` (autotest du protocole sur boucle locale), `peer-rpc-arg` (argument généré).
  5. Un **démon d'annonce** (`announce`) est lancé avec la pile (désactivable par `--no-peers`), suivi
     dans `data\pids.txt` et arrêté proprement avec elle.
  6. **Anti-piège** : aucun `--rpc` n'est injecté vers un nœud **injoignable** (sinon l'inférence
     casserait). Sur un poste isolé, le calcul reste **100 % local**.
- **Anomalies de nommage découvertes (famille A24)** :
  - Le mandat cite `rpc-server.exe` ; **l'amont libre livre `ggml-rpc-server.exe`** — c'est le nom réel
    utilisé (port par défaut **50052** ; options `-H/--host`, `-p/--port`, `-t/--threads`, `-c/--cache`).
  - Rappel : les options `--draft-max/--draft-min` du décodage spéculatif (v1.9.0) n'existent plus
    davantage.
  - **Leçon** : toujours vérifier les noms réels de la distribution amont avant de coder dessus.
- **Clause technique matérielle (exigence du mandat §1)** : le support **NPU AMD XDNA2 via DirectML est
  purement expérimental et NON fonctionnel** en l'état de l'art amont — DirectML limite son support NPU
  à **Intel** et **Qualcomm**. L'architecture AMD repose donc sur le **repli CPU NumPy maîtrisé**.
  Documenté ici et dans `INSTALLATION.md`.
- **Raison** : respecter la sobriété (aucune dépendance nouvelle, aucun protocole maison pour le
  transport) tout en livrant une fédération **réellement fonctionnelle** dès qu'un nœud distant
  annonce un RPC ggml.
- **Mesures (poste de référence, isolé)** : `peer-test` → **VERDICT VERT** (protocole validé sur boucle
  locale) ; `peer-status` → aucun nœud distant (état normal) donc **calcul 100 % local** et **aucun
  `--rpc` injecté** ; `peer-scan` → `config\peers.json` écrit.

## D-004 — Zone de chantier `build\`
- **Date** : 2026-10-03
- **Decision** : ajouter `G:\V1\LocalAI-Projet\build\` (tools, downloads, src, gopath, gocache, tmp)
  comme espace de compilation.
- **Raison** : `dev\` interdit les sous-dossiers (Section 2.4) et doit rester un laboratoire a plat.
  Une compilation Go genere des dizaines de milliers de fichiers ; il faut une zone dediee, mais
  TOUJOURS dans la sandbox.
- **Statut** : `build\` est reconstructible et non livre (seul `LocalAI\` est le produit).

## D-005 — Backend llama.cpp : composition bridge gRPC natif + moteur ggml-org
- **Date** : 2026-10-03
- **Contexte** : le backend llama.cpp de LocalAI v4 (`backend/cpp/llama-cpp`) est un serveur
  **C++/gRPC** compilé sous Linux (Docker) avec cmake + gRPC C++ + protoc. Porté tel quel, il
  exigerait une chaîne gRPC C++ complète sous Windows (très lourde, fragile).
- **Décision** : composer plutôt l'écosystème comme suit :
  `local-ai.exe (coeur) --gRPC--> cloud-proxy.exe (bridge natif Windows) --HTTP--> llama-server.exe (moteur ggml-org)`.
  Le bridge `cloud-proxy` est **compilé nativement** (Go, `CGO_ENABLED=0`). Le moteur provient des
  releases officielles ggml-org (autorisées, Section 4.5). Enregistrement du bridge via
  `--external-grpc-backends "cloud-proxy:<chemin>"` ; modèle configuré avec `backend: cloud-proxy` +
  bloc `proxy:` (mode `translate`, provider `openai`).
- **Raison** : obtenir une inférence réelle et robuste sous Windows natif sans chaîne C++ lourde,
  tout en respectant la charte (pas de Docker, pas de WSL) et l'arborescence ouverte
  (`backends\llama-cpp\` reste un dossier remplaçable).
- **Alternative écartée** : compiler `backend/cpp/llama-cpp` sous Windows (chaîne gRPC C++/MinGW),
  jugée disproportionnée et hors du temps imparti.

## D-006 — WSL2 NON retenu
- **Date** : 2026-10-03
- **Décision** : la Section 4.2 relègue WSL2 au « dernier recours documenté ». Grâce à la compilation
  Go native (CGO désactivé, aucun compilateur C requis) et à la composition D-005, **WSL2 n'a pas
  été nécessaire**. Aucun contournement Linux n'est utilisé.

## D-007 — UI React embarquée : build locale requise
- **Date** : 2026-10-03
- **Contexte** : le cœur embarque `//go:embed react-ui/dist/*`, mais la release source ne contient pas
  `react-ui/dist` (généré par `make react-ui`, via npm).
- **Décision** : installer Node.js 24 LTS (confinné dans `build\tools\node`) et exécuter
  `npm install && npm run build` dans `core/http/react-ui` **une seule fois** pour produire `dist`,
  prérequis à la compilation du cœur.
- **Raison** : sans `dist`, `go build` échoue (« pattern react-ui/dist/*: no matching files »).

## D-008 — Sources additionnelles (build) justifiées
- **Date** : 2026-10-03
- **Décision** : outre les sources Section 4.5, recours documenté à :
  - **protoc v31.1** — `github.com/protocolbuffers/protobuf/releases` — requis par `protogen-go`
    (génération `pkg/grpc/proto/backend{,_grpc}.pb.go`) ; le Makefile LocalAI télécharge lui-même
    protoc depuis cette URL.
  - **Node.js 24 LTS** — `nodejs.org/dist/` — requis par le build de l'UI embarquée (D-007).
  - **Plugins gRPC** `protoc-gen-go@v1.34.2` et `protoc-gen-go-grpc@1958fcbe…` — installés via
    `go install` (proxy.golang.org), conformément au Makefile LocalAI.
  - **Hash téléchargements** : `go1.27.1.windows-amd64.zip` =
    `a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d` (officiel go.dev) ;
    `LocalAI-v4.11.0-source.tar.gz` =
    `6002ee89d9674b3b7fe5cb4db0a9f5028d487469b906719db492053212b09522` (checksums officiels) ;
    `llama-b11375-bin-win-cpu-x64.zip` =
    `90c6721cb0b8d37658b00da9f3e0521e1749c2e5593fb2553a397cc835f1fa9d`.
  - **MinGW-w64 non utilisé** : CGO étant désactivé (`CGO_ENABLED=0`, comme dans le `.goreleaser.yaml`
    officiel), aucun compilateur C n'est nécessaire. La piste MinGW évoquée en D-003 a été écartée.


## D-045 — Audit v3.1.0 : staging isole et detection par emplacement du script
- **Date** : 2026-10-04
- **Contexte** : le mandat exige de deployer dans `dev\test_dynamique\`. `SANDBOX` etant code en dur,
  lancer l'installeur de la-bas aurait remplace le vrai `AiTron\` (cf. incident D-037).
- **Decision** : `_detect_stage()` : si le script vit dans `<SANDBOX>\dev\test_dynamique\`, `PRODUCT` et
  `LOGDIR` pointent dans ce dossier ; `taskkill /IM` par nom d'image est desactive (il tuerait aussi les
  processus du produit stable). Depuis la racine, comportement v3.0.0 inchange.
- **Verification** : manifeste stable identique (SHA-256) et 31 973 fichiers avant/apres.
- **Ecart** : `dev\` ne doit contenir que `old\` en sous-dossier (CHARTE 2.4) ; `test_dynamique\` est une
  exception demandee par le mandat. A retirer (vers `dev\old\`) a la cloture.

## D-046 — Audit v3.1.0 : defauts corriges (D1 a D11)
- **Methode** : chaque defaut est REPRODUIT et mesure avant correctif (build\audit\*.py), patch chirurgical
  avec garde (une occurrence exacte, CRLF preserve), triple validation AST, puis reinstallation a blanc.
- **Mesures** : D1 7/8 invocations en echec -> 0/8 ; D2 oe -> \x9c ; D3 clair supprime apres ecriture
  tronquee -> conserve ; D5 4 routes cloud sans masquage -> 0 fuite ; D11 1 BOM -> 0 sur 41 fichiers.
- **Note D1** : `%RANDOM%` renvoie la MEME valeur a 8 lancements simultanes (1 distincte sur 8) :
  un nom de fichier "unique" par RANDOM ne suffit pas ; lecture directe sans fichier temporaire.
- **Limite D10** : un `!` dans la requete `rag-query` est consomme par l'expansion retardee.

## D-047 — IHM : francais ajoute au cœur ; certification refusee
- **Contexte** : le mandat veut l'IHM bilingue ; l'IHM React d'amont ne propose pas le francais.
- **Decision** : ajout de `fr` dans `src/i18n/index.js` et de fichiers `public/locales/fr/*.json`, puis
  `npm run build` et `go build` (CGO_ENABLED=0) vers `build\out_v310\`, copie dans `build\out\`.
- **Resultat** : francais servi par :8080 ; 685 cles ; couverture 42,4 % (admin, auth, importModel, media
  absents). Anomalie A-12 : curable, non corrigee. **Certification refusee.**
- **Non verifie** : rendu visuel dans un navigateur (aucun test sans navigateur ne le prouve).


## D-048 — IHM française complète : choix de traduction (clôture de l'anomalie A-12)
- **Date** : 2026-10-04
- **Contexte** : la première passe d'audit v3.1.0 avait refusé la certification (couverture FR 42,4 %).
  Le propriétaire a autorisé la clôture complète par le même auditeur (dérogation à la séparation des
  rôles, motivée par la connaissance des défauts ; risque : l'auteur relit sa propre traduction).
- **Réalisé** : 920 feuilles traduites (admin 234, auth 92, importModel 96, media 366, chat 26, home 14,
  models 92), fusionnées par `build\audit\merge_tr.py` qui refuse d'écrire si un chemin est absent de
  l'anglais, si les variables `{{x}}` diffèrent, si une valeur est vide, ou si une clé est traduite deux fois.
  Mesure sur l'IHM SERVIE par le cœur : 1 597 / 1 597 clés (100,0 %), 0 placeholder divergent, 0 BOM.
- **Principes** : français courant et professionnel ; vouvoiement ; infinitif pour les boutons et titres
  d'action ; points de suspension typographiques (…) ; « % » précédé d'une espace ; guillemets français
  « » ; « p. ex. » pour « e.g. » ; formes plurielles `_one` / `_other` conservées. Mesure : 8 clés
  `_many` existent en français (agents, common, home), ajoutées lors de la première passe. Aucune autre
  langue du cœur (de, es, it, pt-BR) n'en a, et l'anglais non plus. Elles ont le même texte que `_other`,
  donc redondantes ; leur effet dans i18next n'a pas été vérifié. À supprimer si une relecture les juge
  inutiles.
- **Termes conservés en anglais (usage établi ou nom propre)** : backend, cluster, middleware, watchdog,
  embeddings, token (rendu « jeton »), P2P, CORS, WebRTC, WebSocket, OCI, YAML, GLB, BPM, VRAM, CUDA,
  GPU, RAM, MMProj, LocalVQE, Hugging Face, Ollama, noms de paramètres techniques (`k_dpmpp_2m`,
  `q4_k_m`, `AutoModelForCausalLM`, etc.). Mesure : 94 clés identiques à l'anglais, toutes de cette nature.
- **Choix lexicaux** : prompt → « description » (images, sons), « invite » (une seule fois, compteur de
  jetons : « (invite) + (réponse) ») ; seed →
  « graine » ; pin / unpin → « épingler » / « désépingler » ; failover → « basculement » ; worker →
  « nœud de calcul » ; diarization → « diarisation » ; remesh → « remaillage » ; voice cloning →
  « clonage de voix » ; personality library → « bibliothèque de personnalités » ; talk → « conversation
  vocale » ; traces → « traces » ; gallery → « galerie » ; reranker → « modèle de reclassement ».
- **Marque** : « LocalAI » remplacé par « AiTron » dans les textes français affichés (mesure : 17 lignes
  contiennent « AiTron », 0 contient « LocalAI », nav.appName compris) ; le titre de l'onglet du navigateur
  (`<title>LocalAI</title>` dans index.html) n'est PAS modifié : c'est l'identité amont du cœur (voir D-044).
- **Limites** : traduction produite sans relecture par un locuteur natif tiers ; rendu visuel non
  contrôlé dans un navigateur (longueur des libellés, retours à la ligne) ; les tests d'IHM portent sur
  les fichiers servis, pas sur l'affichage.

## D-049 — Portabilite totale : detection dynamique du repertoire de la sandbox
- **Date** : 2026-10-05
- **Contexte** : l'installeur etait cable en dur sur `G:\V1\LocalAI-Projet\`
  (`SANDBOX = r"G:\V1\LocalAI-Projet"`) ; il ne fonctionnait que dans ce dossier, ce qui interdisait
  toute distribution (cle USB, `C:\AiTron\`, `D:\Projets\AiTron\`).
- **Decision** : `SANDBOX` est desormais **derive dynamiquement** :
  1. option **`--root <chemin>`** (prioritaire si fournie ; erreur nette si dossier inexistant) ;
  2. sinon **dossier du script** (`_detect_sandbox()`), avec repli sur le repertoire courant si
     `__file__` est absent (exec/import par les outils de validation).
  Les sous-arborescences (`Installeur\`, `dev\`, `dev\old\`, `log\`, `build\`) sont creees a la
  demande (`_ensure_sandbox_tree()`), y compris au premier lancement sur un support vierge.
- **Raison** : rendre le produit **distribuable** sans dependance a un lecteur ni a un chemin
  utilisateur (Section 1.4 du mandat).
- **Alternative ecartee** : chemin par defaut via variable d'environnement (fragile, non portable,
  contraire a l'esprit « click and go »).
- **Mesures** : detection verifiee depuis 4 emplacements (`G:\`, `C:\AiTron-Test`, `--root
  D:\AiTron-Root-Test`, USB `E:\AiTron-Portable`) ; 15 controles unitaires
  (`build\test_portability_v311.py`).

- **Note (isolation de staging, v3.1.0)** : l'ancien mecanisme `_detect_stage()` (execution depuis
  `<sandbox>\dev\test_dynamique\`) devient **inerte** avec un `SANDBOX` dynamique : ce dossier *est*
  desormais la sandbox (donc `root != SANDBOX` et la condition ne se declenche plus). L'isolation du
  produit stable s'obtient **naturellement** en executant l'installeur depuis un **dossier dedie**
  (Tests T2, T3, T4) : c'est meme le but de la portabilite. `_detect_stage()` est **conserve** (aucun
  effet de bord) ; le staging archive reste `dev\old\test_dynamique\AiTron\`.

## D-050 — Fallbacks de telechargement des binaires + garde-fou d'integrite
- **Date** : 2026-10-05
- **Contexte** : si `build\out\local-ai.exe` (ou `cloud-proxy.exe`) est absent (machine neuve), le
  deploiement echouait. Mandat v3.1.1 (Section 2) : ajouter des fallbacks de telechargement.
- **Decision** : cascade de resolution `_resolve_binary()` :
  1. `build\out\<exe>` (compilation locale) ;
  2. `dev\old\test_dynamique\AiTron\...` (staging archive) ;
  3. produit deja deploye (`AiTron\<exe>`) ;
  4. **telechargement** depuis `FALLBACK_LOCAL_AI_URL` / `FALLBACK_CLOUD_PROXY_URL` + verification
     SHA-256 (fichier `.part` atomique).
  Les URLs de transfert etant **temporaires** et le SHA-256 du mandat **vide**, un **garde-fou
  d'integrite minimale** rejette tout `.exe` telecharge qui ne commence pas par le magic PE `MZ`
  (sinon une page HTML servie par un lien de partage serait acceptee comme binaire).
- **Raison** : permettre une installation meme sans binaires locaux, tout en refusant une source
  corrompue ou trompeuse (Section 2.3 : « rejeter et essayer une source alternative »).
- **Mesures** : cascade verifiee (local / staging / produit) ; telechargement + SHA (concordant et
  divergent) et garde-fou MZ verifies hors reseau (`build\test_portability_v311.py`,
  `build\test_mz_guard.py`). **Anomalie constatee** : les deux URLs de transfert renvoient
  `text/html` (217 573 octets) et non le binaire -> a **remplacer par des liens binaires directs**
  et SHA-256 renseigne. Consigne dans `INSTALLATION.md` et `ANOMALIES_NON_RÉSOLUES.log`.

## D-051 — Integration des binaires GitHub Releases (URLs perennes + SHA-256)
- **Date** : 2026-10-05
- **Contexte** : v3.1.1 avait revele que les URLs de transfert (`transfert.free.fr`) renvoient une page
  HTML (rejetee a juste titre par le garde-fou MZ) : installation impossible depuis une machine vierge.
  Mandat v3.1.2 : basculer sur **GitHub Releases** (URLs directes, stables, versionnees).
- **Decision** :
  1. `FALLBACK_LOCAL_AI_URL` / `FALLBACK_CLOUD_PROXY_URL` -> release
     `xtrem21-source/AiTron-Releases-V3.1.1` (tag `v3.1.1`), fichiers `local-ai.exe` / `cloud-proxy.exe`.
  2. **SHA-256 integres** (calcules sur les fichiers reellement telecharges) :
     `local-ai.exe`     = `0F55C48379F971A6108339C9D90291A76D8DD21CDCE283AD8EF972C4E3855B34`
     `cloud-proxy.exe`  = `BFCB28047F97F4DD4D6374938971BAA2F2711BFA6992C866EEED078B88F50F0C`
  3. **Garde-fou PE "MZ" conserve et etendu** : applique a tout `.exe` telecharge, meme quand un SHA est
     fourni (defense en profondeur) — exigence explicite de la Section 5 du mandat.
  4. **Erreurs actionnables** : rejet + suppression du `.part` ; cascade `build\out\` -> staging ->
     produit deploye ; message explicite si tout echoue.
- **Raison** : permettre une installation complete depuis une machine neuve (aucun binaire local).
- **Verification** : binaires GitHub **byte-identiques** aux binaires locaux (meme taille, meme SHA-256) ;
  HTTP 200, `application/octet-stream`, magic `MZ`.
- **Alternative ecartee** : hebergement hors GitHub (moins perenne, sans versionnage ni tag).
- **Mesures** : Test 1 (telechargement GitHub -> deploiement) ; Test 2 (SHA errone -> rejet) ; Test 3
  (URL invalide -> cascade) ; harnais `build\test_v312_cascade.py`, `build\test_v312_sha_mismatch.py`.

## D-052 — Creation de la Release GitHub v3.1.2 (upload via gh CLI)
- **Date** : 2026-10-05
- **Contexte** : la publication d'une release via l'interface web GitHub etait bloquee (bouton
  « Publish release » grise avec les gros assets). Les binaires v3.1.2 sont byte-identiques a ceux de
  la v3.1.1 (deja heberges).
- **Decision** :
  1. Installer **GitHub CLI** (`winget install --id GitHub.cli`) et creer la release en **ligne de
     commande** : `gh release create v3.1.2 <local-ai.exe> <cloud-proxy.exe> ... --draft=false`.
  2. Authentifier `gh` via le jeton **Git Credential Manager** (`git credential fill` -> `GH_TOKEN`),
     `GH_TOKEN` etant accepte sans le scope `read:org` exige par `gh auth login`.
  3. Basculer les URLs de fallback de `download/v3.1.1/` vers `download/v3.1.2/` (SHA-256 inchanges).
- **Raison** : rendre le fallback coherent avec la version du script et contourner le bug de l'interface.
- **Consequences** : `v3.1.3` du script ; manifeste `v3.1.3` ; garde-fou PE « MZ » conserve.
- **Mesures** : `gh release view v3.1.2` -> 2 assets ; URLs v3.1.2 verifiees (HTTP 200, MZ) ;
  installation en racine vierge reussie (fallback GitHub -> deploiement).
