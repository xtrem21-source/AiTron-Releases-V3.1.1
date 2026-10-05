# INSTALLATION.md — LocalAI Windows (portage natif, sans Docker / sans WSL)

> Produit : **LocalAI** porté nativement sous Windows 64 bits.
> Livrable maître : `install_localai_win.py` (racine de la sandbox `G:\V1\LocalAI-Projet\`).
> Version : **v1.1.0** — cœur LocalAI **v4.11.0-win.1** — moteur llama.cpp **b11375**.

---

## 1. En bref

Ce portage fournit un écosystème d'inférence locale **100 % Windows natif** :

```
client OpenAI  --HTTP-->  local-ai.exe (:8080)  --gRPC-->  cloud-proxy.exe  --HTTP-->  llama-server.exe (:8090)  -->  *.gguf
                          (coeur LocalAI)                    (bridge natif)                (moteur llama.cpp)
```

* `local-ai.exe` — cœur LocalAI compilé depuis les sources officielles (Go, `CGO_ENABLED=0`).
* `cloud-proxy.exe` — backend gRPC natif Windows (compilé depuis `backend/go/cloud-proxy`),
  qui relaie vers le moteur d'inférence via une API OpenAI-compatible.
* `llama-server.exe` — moteur d'inférence llama.cpp officiel (release ggml-org, build Windows CPU x64).

Aucun conteneur, aucune machine virtuelle, aucune couche Linux.

## 2. Prérequis système

| Élément | Exigence |
|---|---|
| Système | Windows 10 / 11, 64 bits (x86_64) |
| Python | 3.9+ (pour lancer l'installeur `install_localai_win.py`) |
| Espace disque | ~ 3 Go libres (cœur 195 Mo + moteur 48 Mo + modèle 770 Mo + marge) |
| RAM | 4 Go minimum (8 Go conseillés) |
| Outils natifs utilisés | `curl.exe`, `tar.exe`, `powershell.exe`, `taskkill.exe`, `cmd.exe` (tous fournis par Windows) |
| Réseau | Accès HTTPS à GitHub, go.dev, huggingface.co/npm/Node (uniquement si reconstruction/téléchargement) |

Aucune installation de Go, Node, Docker ou WSL n'est nécessaire **pour utiliser** le produit déployé.

## 3. Arborescence déployée (`G:\V1\LocalAI-Projet\LocalAI\`)

```
LocalAI\
├── local-ai.exe                  Cœur LocalAI (API OpenAI-compatible)  — NE PAS MODIFIER
├── launcher.bat                  Lanceur : démarre le moteur + le coeur
├── stop.bat                      Arrêt propre (taskkill /T /F, zéro zombie)
├── download_model.bat            Téléchargement du modèle GGUF (helper)
├── manifest.json                 Inventaire + hash SHA-256 de chaque composant
├── backends\
│   └── llama-cpp\                Backend « llama.cpp » (remplaçable individuellement)
│       ├── llama-server.exe      Moteur d'inférence llama.cpp (ggml-org)
│       ├── cloud-proxy.exe       Bridge gRPC natif Windows
│       ├── *.dll                 Bibliothèques ggml/llama (+ libomp, mtmd)
│       └── README.txt            Rôle et procédure de remplacement
├── models\
│   ├── Llama-3.2-1B-Instruct-Q4_K_M.gguf   Modèle de test (GGUF)
│   └── llama-3.2-1b-instruct.yaml          Configuration du modèle
├── config\                       (réservé aux configurations additionnelles)
├── configuration\                (api_keys.json / external_backends.json dynamiques)
├── data\                         Données persistantes (généré au 1er lancement)
├── backends-system\              Backends système (réservé)
└── logs\                         Journaux d'exécution (append-only)
```

## 4. Procédure d'installation (ordre des étapes)

### Étape 1 — Reconstruire le produit (obligatoire la première fois)
Depuis la racine de la sandbox :

```bat
cd /d G:\V1\LocalAI-Projet
python install_localai_win.py
```

L'installeur, dans l'ordre :

1. **Sauvegarde ante-exécution** (Section 1.1) : archive le script maître et la charte dans
   `Installeur\` au format `install_localai_win_AAAAMMJJ_HHMMSS.py.txt` / `CHARTE_*.md`.
2. **Validation AST** du code embarqué (`ast.parse` + `compile` + `py_compile`) — échec = rollback.
3. **Déploiement transactionnel** dans `LocalAI.new\`, puis bascule vers `LocalAI\`
   (jamais d'état intermédiaire cassé).
4. **Écriture de `manifest.json`** (role + version + SHA-256 + source de chaque composant).

Options : `python install_localai_win.py --skip-model` (ne pas télécharger le modèle).

### Étape 2 — Vérifier / fournir le modèle
Le modèle `models\Llama-3.2-1B-Instruct-Q4_K_M.gguf` (≈ 770 Mo) est copié depuis le cache local
ou téléchargé automatiquement. Pour le (re)télécharger manuellement :

```bat
cd /d G:\V1\LocalAI-Projet\LocalAI
download_model.bat
```

Rôle du `.bat` de téléchargement : récupérer le modèle GGUF depuis HuggingFace via `curl.exe`,
avec reprise sur erreur, et rappeler l'empreinte SHA-256 attendue.

### Étape 3 — Lancer
```bat
cd /d G:\V1\LocalAI-Projet\LocalAI
launcher.bat
```

`launcher.bat` : (1) définit les variables d'environnement (`LOCALAI_MODELS_PATH`,
`LOCALAI_BACKENDS_PATH`, `LOCALAI_CONFIG_PATH`, `LOCALAI_EXTERNAL_GRPC_BACKENDS`…),
(2) vérifie la présence des composants critiques, (3) démarre le moteur llama.cpp puis le cœur
LocalAI sur `http://127.0.0.1:8080`.

### Étape 4 — Arrêter
```bat
stop.bat
```
`stop.bat` termine `local-ai.exe`, `cloud-proxy.exe`, `llama-server.exe` (`taskkill /T /F`) et
vérifie l'absence de processus résiduel (zéro zombie).

## 5. Utilisation de l'API (compatible OpenAI)

Une fois `launcher.bat` en marche :

```bat
curl http://127.0.0.1:8080/v1/models
```

```bat
curl -X POST http://127.0.0.1:8080/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"llama-3.2-1b-instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"Bonjour\"}]}"
```

Exemple Python :

```python
from openai import OpenAI
c = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="localai")
r = c.chat.completions.create(
    model="llama-3.2-1b-instruct",
    messages=[{"role": "user", "content": "Bonjour en une phrase."}],
)
print(r.choices[0].message.content)
```

Le streaming (`"stream": true`) est pris en charge (SSE).

## 6. URLs de téléchargement (sources officielles)

| Composant | Source |
|---|---|
| Cœur LocalAI (sources Go) | https://github.com/mudler/LocalAI/releases (v4.11.0) |
| Documentation LocalAI | https://localai.io/ |
| Compilateur Go | https://go.dev/dl/ |
| Git pour Windows | https://git-scm.com/download/win |
| Moteur llama.cpp (backend) | https://github.com/ggml-org/llama.cpp/releases (`b11375`, `llama-b11375-bin-win-cpu-x64.zip`) |
| Modèle de test GGUF | https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF |
| Node.js (build UI, reconstruction) | https://nodejs.org/dist/ |
| protoc (codegen gRPC, reconstruction) | https://github.com/protocolbuffers/protobuf/releases (v31.1) |

Empreintes de référence (SHA-256) :

* moteur llama.cpp `llama-b11375-bin-win-cpu-x64.zip` :
  `90c6721cb0b8d37658b00da9f3e0521e1749c2e5593fb2553a397cc835f1fa9d`
* modèle `Llama-3.2-1B-Instruct-Q4_K_M.gguf` :
  `6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83`

## 7. Reconstruction complète depuis les sources (optionnel)

Le cœur `local-ai.exe` et le bridge `cloud-proxy.exe` sont **compilés localement** (aucun binaire
Windows officiel n'existe pour LocalAI). Pour les reconstruire :

```powershell
# 1. Toolchain (confinee dans la sandbox)
#    - Go 1.27.1   -> build\tools\go
#    - Node 24 LTS -> build\tools\node  (pour l'UI embarquee)
#    - protoc 31.1 -> build\tools\protoc
# 2. Sources LocalAI v4.11.0 -> build\src
# 3. Codegen gRPC + UI, puis :
. G:\V1\LocalAI-Projet\build\go-env.ps1
cd G:\V1\LocalAI-Projet\build\src
go build -ldflags "-s -w -X github.com/mudler/LocalAI/internal.Version=v4.11.0-win.1" -o ..\out\local-ai.exe ./cmd/local-ai
go build -o ..\out\cloud-proxy.exe ./backend/go/cloud-proxy
```

Les étapes détaillées (codegen protoc, build React) sont décrites dans `dev/DECISIONS.md`
(entrées D-003, D-008). Les scripts opérationnels sont conservés dans `build\` (`do-build3.ps1`,
`do-codegen.ps1`, `do-ui.ps1`, `go-env.ps1`).

## 8. Dépannage

| Symptôme | Cause probable | Remède |
|---|---|---|
| `/v1/models` ne répond pas | Le cœur n'est pas lancé, ou port 8080 occupé | Vérifier `logs\local-ai.out.log`; libérer le port (`stop.bat`) |
| Erreur `Composant manquant` au lancement | Produit incomplet | Relancer `python install_localai_win.py` |
| `502`/timeout sur `/v1/chat/completions` | Moteur llama.cpp non démarré ou modèle absent | Vérifier `logs\llama-server.log`; lancer `download_model.bat` |
| Modèle introuvable | Téléchargement incomplet | `download_model.bat`, vérifier le SHA-256 |
| Port 8090 occupé | Instance llama-server résiduelle | `stop.bat` |
| Erreur DLL au lancement du moteur | DLL déplacées hors du dossier | Garder tous les fichiers de `backends\llama-cpp\` ensemble |

## 9. Limites documentées

* **Backends Python non inclus** (`diffusers`, `transformers`, TTS) : non distribués en mode binaire
  — voir `dev/DECISIONS.md`.
* Le backend llama.cpp historique de LocalAI (C++/gRPC) n'est pas compilable sur Windows sans chaîne
  gRPC C++ complète ; ce portage compose à la place un bridge gRPC natif + le moteur llama.cpp
  officiel (voir `dev/DECISIONS.md` D-005).
* Seul le moteur CPU x64 est fourni par défaut ; des variantes CUDA/Vulkan peuvent être substituées
  dans `backends\llama-cpp\`.

## 10. Cycle de vie et traçabilité

* `Installeur\` — boîte noire : versions antérieures du script maître et de la charte.
* `log\install_AAAAMMJJ_HHMMSS.log` — journaux d'exécution de l'installeur (append-only).
* `dev\CHANGELOG.md` — historique des versions.
* `dev\DECISIONS.md` — décisions techniques.
* `dev\patch_integrity.log` — validation de chaque patch (AST, tests, résultats).
* `JOURNAL.md` — journal narratif du chantier.
* `LocalAI\manifest.json` — inventaire + SHA-256 des composants déployés.

---

# PHASE 2 (v1.2.0) — MULTI-MODAL & ROUTAGE

## 11. Architecture v1.2.0

```
 client (OpenAI SDK)  ->  LiteLLM gateway (:4000)   [routage, auth, cloud offload]
                                |
                                v
                        Coeur LocalAI (:8080)  [gRPC cloud-proxy -> llama.cpp]

   llama-server     whisper-server      sd-server          python tts_server.py
   :8090 texte      :8091 speech-to-text :8092 images      :8093 TTS (kokoro)
```

| Service | Port | Rôle | Remplaçable |
|---|---|---|---|
| LiteLLM gateway | 4000 | routage, auth, cloud offload | `config\litellm-config.yaml` |
| Coeur LocalAI | 8080 | API OpenAI, orchestration | `local-ai.exe` |
| llama.cpp | 8090 | inférence texte | `backends\llama-cpp\` |
| whisper.cpp | 8091 | speech-to-text | `backends\whisper-cpp\` |
| stable-diffusion.cpp | 8092 | images | `backends\stable-diffusion\` |
| Kokoro TTS | 8093 | synthèse vocale | `backends\tts\` |
| Python embarqué | — | LiteLLM + TTS uniquement | `runtime\python\` |

Les ports sont **résolus automatiquement** : si un port par défaut est occupé, `Run-LocalAI.bat start`
bascule sur le premier port libre suivant et l'annonce au démarrage.

## 12. Commandes (CLI wrapper)

```bat
cd /d G:\V1\LocalAI-Projet\LocalAI
Run-LocalAI.bat start              :: démarre TOUS les services (idempotent)
Run-LocalAI.bat stop               :: arrête tous les services (zéro zombie)
Run-LocalAI.bat status             :: état des services (PID, ports, UP/DOWN)
Run-LocalAI.bat list               :: liste le catalogue de modèles
Run-LocalAI.bat pull <model-id>    :: télécharge un modèle (SHA-256 vérifié)
Run-LocalAI.bat backends           :: liste les backends installés
Run-LocalAI.bat help               :: aide
```

## 13. Modèles (Model Manager)

Catalogue : `LocalAI\models\models-catalog.json` (id, name, modality, format, filename, source, size_mb, sha256, recommended).

| id | modalité | format | taille | recommandé |
|---|---|---|---|---|
| `llama-3.2-1b-instruct` | text | gguf | 770 Mo | oui |
| `whisper-base` | audio | ggml | 142 Mo | oui |
| `sd-turbo` | image | safetensors | ~5200 Mo | non (volumineux) |
| `kokoro-v1.1` | tts | onnx | 310 Mo | oui |

Tous les modèles vont dans `LocalAI\models\`. Suppression : effacer le fichier. Ajout : éditer
`models-catalog.json` (champs ci-dessus + `filename`).

## 14. Routage local / externe (BYOK)

1. Créer/éditer `LocalAI\config\cloud-keys.env` (non versionné) :

```
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

2. Relancer `Run-LocalAI.bat start`. Les clés sont lues par LiteLLM au démarrage (aucune clé en dur).

3. Modèles exposés par la gateway :

| model (client) | destination |
|---|---|
| `local-llama` | coeur LocalAI (local) |
| `gpt-4o` | OpenAI (si `OPENAI_API_KEY`) |
| `claude-sonnet` | Anthropic (si `ANTHROPIC_API_KEY`) |
| `openrouter-claude` | OpenRouter (si `OPENROUTER_API_KEY`) |
| `smart` | **routage par complexité** : prompt court (< 4 mots) → local ; sinon → externe si clé, sinon local |

Authentification de la gateway : `master_key: sk-local` (`Authorization: Bearer sk-local`).

```bat
curl -X POST http://127.0.0.1:4000/v1/chat/completions ^
  -H "Authorization: Bearer sk-local" -H "Content-Type: application/json" ^
  -d "{\"model\":\"smart\",\"messages\":[{\"role\":\"user\",\"content\":\"Bonjour\"}]}"
```

Variables de bascule : `LOCALAI_ROUTE_LOCAL`, `LOCALAI_ROUTE_CLOUD`, `LOCALAI_ROUTE_WORDS`.

## 15. Multi-modal — exemples

```bat
:: Speech-to-text (whisper.cpp, 8091)
curl -X POST http://127.0.0.1:8091/v1/audio/transcriptions ^
  -F "file=@G:\V1\LocalAI-Projet\build\jfk.wav" -F "model=whisper-1"

:: Text-to-speech (kokoro, 8093) -> WAV
curl -X POST http://127.0.0.1:8093/v1/audio/speech ^
  -H "Content-Type: application/json" ^
  -o sortie.wav -d "{\"input\":\"Bonjour, ceci est un test.\",\"voice\":\"af_maple\"}"

:: Images (stable-diffusion.cpp, 8092) -- apres "Run-LocalAI.bat pull sd-turbo" puis restart
curl -X POST http://127.0.0.1:8092/v1/images/generations ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"a cat\",\"size\":\"512x512\"}"
```

## 16. Dépannage Phase 2

| Symptôme | Cause probable | Remède |
|---|---|---|
| LiteLLM ne démarre pas | encodage / PYTHONPATH | corrigé (UTF-8 + `litellm_launch.py`) ; voir `logs\litellm.log.err` |
| 401 sur `:8080/v1/models` | `LOCALAI_API_KEY` exportée | ne pas exporter cette variable |
| 404 sur `/v1/audio/transcriptions` | `--inference-path` absent | déjà géré par `scripts\localai_up.ps1` |
| TTS 500 « voice not found » | voix inexistante | utiliser une voix de `voices-v1.1-zh.bin` (`af_maple`, `zf_001`…) |
| `:8092` DOWN | modèle SD non téléchargé | `Run-LocalAI.bat pull sd-turbo` puis `stop` + `start` |
| Port occupé au démarrage | autre application | bascule automatique (voir `status`) |
| Services en double | ancienne instance | `start` est idempotent ; sinon `stop` puis `start` |

## 17. Réinstallation / reconstruction

```bat
cd /d G:\V1\LocalAI-Projet
python install_localai_win.py                  :: reconstruit tout (transactionnel)
python install_localai_win.py --skip-models    :: sans les gros modèles
python install_localai_win.py --skip-python    :: sans le runtime Python/LiteLLM
```

L'installeur arrête automatiquement toute instance en cours avant la bascule, valide l'AST, déploie
dans `LocalAI.new` puis bascule vers `LocalAI` (rollback si échec), et régénère `manifest.json`.

## 18. Limites & notes
- Backend image : le binaire est installé et vérifié, mais le modèle SD-Turbo (~5 Go) n'est **pas**
  téléchargé par défaut (consigne « pas de téléchargement massif »). Activer via `pull sd-turbo`.
- L'authentification des clients est portée par **LiteLLM** (gateway) ; le coeur LocalAI reste nu sur
  la boucle locale.
- Le runtime Python embarqué ne sert qu'à LiteLLM et au TTS ; le coeur Go reste autonome.

---

# PHASE 3 (v1.3.0) — OPTIMISATION GPU

## 19. Détection matérielle et sélection du moteur

Ordre de détection (Section 3 du mandat) :

| Priorité | Constructeur | Méthode |
|---|---|---|
| 1 | NVIDIA | `nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits` |
| 2 | AMD | présence de `amdhip64.dll` / `rocm-smi` |
| 3 | Vulkan | présence de `%SystemRoot%\System32\vulkan-1.dll` |
| 4 | CPU | repli si aucun GPU |

Méthode de secours VRAM (AMD/Intel) : `Win32_VideoController` + registre
`HardwareInformation.qwMemorySize` (fiable au-delà de 4 Go), avec **marge de sécurité de 85 %**
(estimation, pas mesure).

Sélection de la variante llama.cpp (b11375) : `cuda` (NVIDIA sans Vulkan) · `hip` (AMD) ·
`vulkan` (support Vulkan) · `cpu` (repli). Les variantes sont stockées dans
`backends\llama-cpp\variants\{cpu,vulkan,cuda}\` ; la **variante active** est copiée à la racine de
`backends\llama-cpp\` (à côté de `cloud-proxy.exe`) et tracée dans `backends\llama-cpp\active.json`.

> **Note importante (vérifiée)** : les binaires **CUDA prébuilds** de ggml-org ne contiennent pas
> l'architecture **Maxwell (sm_52)** ; sur une GTX 970M, CUDA échoue (`invalid device function`) et le
> portage bascule **automatiquement sur Vulkan** (supporté par le pilote). Voir `dev/DECISIONS.md` D-014.

## 20. Profils de performance et calcul des paramètres

Les paramètres (`-ngl`, `--threads`, `--ctx-size`) sont calculés à partir des métadonnées GGUF du modèle
actif (`local-ai util gguf-info` : `BlockCount`, `EmbeddingLength`, `VocabularyLength`,
`MaximumContextLength`, `AttentionHeadCountKV`, …) :

* budget VRAM = VRAM libre − marge du profil ; `-ngl` dérivé du coût par couche (+ cache KV, marge 10 %) ;
* `--ctx-size` aligné sur un multiple de 4096, plafonné par `n_ctx_train` ;
* `--threads` = cœurs (SOFT) ou threads logiques (NORMAL/HARD/AUTO).

| Profil | Marge VRAM | Contexte | Threads | `-ngl` |
|---|---|---|---|---|
| `soft` | 1536 Mo | 4096 | cœurs | 0 (CPU) |
| `normal` | 1024 Mo | 4096 | threads | auto |
| `hard` | 768 Mo | 8192 si VRAM ≥ 8 Go | threads | auto |
| `auto` | dynamique | idem selon VRAM | threads | auto |
| `custom` | manuel | manuel | manuel | manuel |

**Sécurité VRAM** : `ratio = VRAM libre / VRAM requise`. `≥ 1.05` → *optimal* ; `≥ 0.75` → *possible* ;
sinon **bascule automatique en CPU** (`-ngl 0`) avec journalisation.

## 21. Commandes GPU

```bat
cd /d G:\V1\LocalAI-Projet\LocalAI
Run-LocalAI.bat profile                 :: affiche le profil matériel détecté
Run-LocalAI.bat optimize                :: recalcule le profil + sélectionne la variante
Run-LocalAI.bat benchmark               :: mesure les tok/s (moteur actif, GPU)
Run-LocalAI.bat benchmark cpu           :: mesure les tok/s en CPU (référence)
Run-LocalAI.bat set-profile hard        :: change le profil (soft|normal|hard|auto|custom)
Run-LocalAI.bat status                  :: état + profil + variante active
```

Exemple de sortie :

```
=== Profil materiel LocalAI (v1.3.0) ===
  CPU    : Intel(R) Core(TM) i7-6700HQ CPU @ 2.60GHz (4c/8t)
  GPU    : NVIDIA NVIDIA GeForce GTX 970M - 5577 Mo libres - backend=vulkan [nvidia-smi]
  Profil : normal (recommande: normal)
  Params : ngl=99 threads=8 ctx=4096 marge=1024 Mo
  Variante active : vulkan  (NVIDIA via vulkan)
  Variantes dispo : cpu, vulkan, cuda
  VRAM   : besoin ~797 Mo / libre 5577 Mo (ratio 7) -> optimal
```

## 22. Profil matériel persistant

`LocalAI\config\hardware-profile.json` est écrit à l'installation et à chaque `optimize`/`set-profile`.
Il est **relu au démarrage** pour éviter de recalculer. Champs principaux : `cpu`, `ram_gb`, `gpu`
(vendor, name, vram_total_mb, vram_free_mb, backend, detection_method), `recommended_profile`,
`profile`, `params` (ngl, threads, ctx, margin_mb), `active_variant`, `variants_available`,
`vram_needed_mb`, `vram_safety`, `vram_ratio`.

L'historique des benchmarks est conservé dans `config\bench-history.jsonl` (une ligne JSON par mesure).

## 23. Dépannage GPU

| Symptôme | Cause probable | Remède |
|---|---|---|
| `CUDA error: invalid device function` | GPU Maxwell (sm_52) absent des binaires prébuilds | normal : bascule **Vulkan** automatique (D-014) |
| `backend=vulkan` mais `-ngl` nul | profil `soft` | `Run-LocalAI.bat set-profile normal` |
| `VRAM possible/experimental` | VRAM insuffisante | réduire le contexte ou le profil ; bascule CPU automatique si ratio < 0.75 |
| `nvidia-smi` absent | pilote NVIDIA absent/ancien | installer le pilote ; sinon détection WMI/registre |
| Variante GPU absente | téléchargement manquant | `Run-LocalAI.bat optimize` (re-télécharge) |
| TTS `provider=CPUExecutionProvider` | DirectML/CUDA indisponible sur ce GPU | comportement attendu (repli, D-017) |
| `hw_profile.ps1` valeurs nulles | conflit de variables PowerShell | corrigé (D-016) |

## 24. Notes multi-modales GPU
- **Texte (llama.cpp)** : accéléré GPU (Vulkan vérifié ; CUDA sur GPU ≥ Pascal).
- **TTS (kokoro/ONNX)** : providers essayés **DML → CUDA → CPU** avec sonde automatique ; le provider
  retenu est visible via `GET :8093/health`.
- **Image (stable-diffusion.cpp)** : variante CUDA disponible dans
  `backends\stable-diffusion\variants\cuda\` (substitution manuelle ; modèle SD requis).
- **Audio (whisper.cpp)** : la release Windows ne fournit pas de build GPU x64 → CPU.

---

# PHASE 4 (v1.4.0) — RAG LOCAL & AGENT HUB

## 25. Pipeline RAG local (texte, code, PDF, Office)

```bat
cd /d G:\V1\LocalAI-Projet\LocalAI
Run-LocalAI.bat index "C:\mes\documents"          :: indexe un dossier (collection "default")
Run-LocalAI.bat index "C:\projets\src" monprojet  :: collection nommée
Run-LocalAI.bat rag-query "comment fonctionne le routage ?"
```

Chaîne de traitement :
1. **Extraction** — `.txt .md .json .py .js .ts .go .rs .c/.cpp/.h .java .cs .sh .bat .ps1 .yaml .ini
   .csv .xml .html .css .sql …` + **`.pdf`** (pypdf) + **`.docx`** (python-docx) + **`.xlsx`** (openpyxl).
2. **Chunking** — blocs de **2048 caractères** (multiple de 512, aligné *prompt caching*), **recouvrement 10 %**.
3. **Embeddings** — instance dédiée du moteur llama.cpp (`--embeddings --pooling mean`, port 8094),
   démarrée à la demande et arrêtée avec le produit. **Aucun modèle supplémentaire.**
4. **Persistance à plat** — `runtime\rag\` :
   `index-<collection>.npy` (matrice float32), `chunks-<collection>.jsonl` (texte + source + index),
   `manifest-<collection>.json` (métadonnées, dimensions, erreurs), `collections.json` (registre).
5. **Recherche** — **similarité cosinus NumPy** (produit scalaire normalisé). **faiss est proscrit**
   (pas de compilation native sous Windows).

Packages RAG isolés (`pip --target`) dans `runtime\packages\` : `numpy`, `pypdf`, `python-docx`,
`openpyxl` ; le fichier `python311._pth` du runtime contient `..\packages` et `import site`.

## 26. Agent Hub — modèle virtuel & Token Saver

LiteLLM (port 4000) expose un **modèle virtuel unique** `localai` (alias `smart`, `auto`). Le callback
`config\complexity_router.py` décide de la destination :

| Condition | Destination |
|---|---|
| prompt court (< 3 mots) | **local** (cœur LocalAI) |
| prompt complexe **et** clé cloud présente | **cloud** (OpenRouter/DeepSeek/OpenAI/Anthropic) |
| prompt complexe **sans** clé cloud | **local** (repli) |
| contexte saturé (> 6000 tokens ≈ `len/4`) | cloud si clé, sinon local |

Préférence cloud : **OpenRouter > DeepSeek > OpenAI > Anthropic** (première clé présente).
Chaque décision est journalisée dans `logs\routing.jsonl` :

```bat
Run-LocalAI.bat proxy-logs
```

## 27. Clés API (BYOK)

```bat
Run-LocalAI.bat key-set deepseek sk-xxxxxxxx
Run-LocalAI.bat key-set openrouter sk-or-xxxxxxxx
Run-LocalAI.bat key-set openai sk-xxxxxxxx
Run-LocalAI.bat key-set anthropic sk-ant-xxxxxxxx
```

L'écriture est **chirurgicale** dans `config\keys.env` (les autres lignes et commentaires sont
préservés ; la valeur n'est jamais réaffichée). `config\cloud-keys.env` reste supporté
(**les deux fichiers sont chargés**, `keys.env` prioritaire) et **conservés entre redéploiements**.
Variables du routeur : `LOCALAI_ROUTE_LOCAL`, `LOCALAI_ROUTE_WORDS`, `LOCALAI_ROUTE_CONTEXT`.

## 28. Dépannage Phase 4

| Symptôme | Cause probable | Remède |
|---|---|---|
| `400 Pooling type 'none' is not OAI compatible` | `--pooling` manquant | le script `rag_ingest.py` le passe déjà ; vérifier `logs\embed-server.log` |
| `ModuleNotFoundError: No module named 'numpy'/'pypdf'` | `..\packages` absent du `._pth` | relancer `install_localai_win.py` |
| Aucun résultat `rag-query` | index absent | `Run-LocalAI.bat index <dossier>` d'abord |
| Extraction PDF vide | PDF scanné (image) | OCR non inclus (documenté) |
| Routage toujours local | aucune clé cloud | `Run-LocalAI.bat key-set <provider> <clé>` |
| `key-set` sans effet | services non redémarrés | `Run-LocalAI.bat start` (recharge `keys.env`) |

## 29. Limites Phase 4
- **Pas d'OCR** : les PDF purement images ne sont pas extraits (aucun moteur OCR embarqué).
- Embeddings produits par le **modèle de chat** (qualité correcte, non spécialisée) — l'architecture
  permet de brancher un modèle d'embeddings dédié plus tard.
- Index **plein** (pas encore incrémental) : chaque `index` reconstruit la collection.
- La recherche demande l'instance d'embeddings (démarrée à la demande, ~10 s au premier appel).

---

# PHASE 4.1 (v1.4.1) — WATCHDOG VRAM, IMAGE LÉGÈRE, CUDA MAXWELL

## 30. Watchdog VRAM (surveillance continue)

Un **daemon** (`scripts\vram_watchdog.py`, thread léger) échantillonne la VRAM **toutes les 2 secondes**
sans impacter le débit de tokens, et applique une machine à états :

| Seuil | Valeur par défaut | Action |
|---|---|---|
| **Alerte** | VRAM libre < **15 %** | alerte console + `logs\vram.log` + `dev\crash.log` (catégorie `GPU_VRAM`) |
| **Critique** | VRAM libre < **5 %** | **action préventive** : relance du moteur en **CPU pur (`-ngl 0`)** pour libérer la VRAM (proposition/état consigné dans `data\vram-action.json`) |
| **Reprise** | VRAM libre > **20 %** | effacement de l'état d'alerte |

```bat
Run-LocalAI.bat vram-status                 :: VRAM totale/libre/utilisée + seuils + état watchdog
Run-LocalAI.bat start --no-watchdog         :: démarre sans le watchdog (désactivation silencieuse)
Run-LocalAI.bat status                      :: inclut la ligne de profil (ngl/threads/ctx)
```

État temps réel : `data\vram-status.json`. Journal : `logs\vram.log`.
Seuils ajustables par variables d'environnement :
`LOCALAI_VRAM_ALERT_PCT`, `LOCALAI_VRAM_CRIT_PCT`, `LOCALAI_VRAM_RECOVER_PCT`.

## 31. Utiliser CUDA sur les vieux GPU Maxwell (GTX 970M, GTX 980M, etc.)

### Pourquoi les binaires officiels échouent
Les archives **prébuildées** `llama-*-bin-win-cuda-*-x64.zip` publiées par ggml-org sont compilées pour
des architectures **récentes** et **n'embarquent pas `sm_52`** (Maxwell). Sur une GTX 970M/980M, le
binaire se lance mais toute inférence échoue avec :

```
CUDA error: invalid device function
  current device: 0, in function ggml_cuda_kernel_can_use_pdl ... common.cuh
```

Le portage **le détecte** : si Vulkan est disponible, il bascule automatiquement dessus (repli documenté,
cf. `dev/DECISIONS.md` D-014).

### Compiler soi-même llama.cpp pour `sm_52`
Prérequis : **CUDA Toolkit ≥ 12.x**, **CMake ≥ 3.20**, **Git**, un compilateur C++ (MSVC ou MinGW-w64).

```bat
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

Les binaires sont produits dans `build\bin\Release\` (notamment `llama-server.exe` et les DLL
`ggml-cuda.dll`, `ggml.dll`, …).

### Intégration automatique par le portage
1. Copier les binaires compilés dans
   `LocalAI\backends\llama-cpp\variants\cuda\` (écraser les fichiers existants de cette variante).
2. **Créer un marqueur** `LocalAI\backends\llama-cpp\variants\cuda\custom-build.txt`
   (fichier texte, contenu libre : version, arch, date). Sa seule présence signale un build validé.
3. Lancer :

```bat
Run-LocalAI.bat optimize
```

`hw_profile.ps1` détecte le marqueur (`cuda_custom_build = true` dans `config\hardware-profile.json`)
et **préfère alors CUDA à Vulkan** : la variante active devient `cuda`, et `engine_select.ps1` copie ces
binaires à la racine de `backends\llama-cpp\`. `Run-LocalAI.bat status` affiche la variante et la raison
(« build personnalise sm_52+ detecte »).

> Sans le marqueur, le portage reste sur **Vulkan** (qui fonctionne sur Maxwell) — c'est le comportement sûr.

## 32. Modèle image léger (`sd-turbo-light`)

Le catalogue expose désormais **`sd-turbo-light`** : quantisation **Q8_0** de SD-Turbo
(`Green-Sky/SD-Turbo-GGUF` → `sd_turbo-f16-q8_0.gguf`, **1,88 Go**, SHA-256 vérifié), **compatible
`sd-server`** (format GGUF) et **< 2 Go**.

```bat
Run-LocalAI.bat list                       :: sd-turbo-light y figure (recommande)
Run-LocalAI.bat pull sd-turbo-light        :: telechargement + verification SHA-256
Run-LocalAI.bat start                      :: sd-server charge en priorite le modele leger
```

Le lanceur préfère `sd_turbo-f16-q8_0.gguf` s'il est présent, sinon `sd-turbo.safetensors` (5,2 Go).
L'image est ensuite générée sur `POST http://127.0.0.1:8092/v1/images/generations`.

> **Note (déviation documentée)** : le mandat visait un safetensors < 2 Go chez `stabilityai/sd-turbo` ;
> le seul fichier safetensors officiel pèse **5,21 Go**. La quantisation Q8_0 (**1,88 Go**) atteint donc
> l'objectif de légèreté tout en restant chargeable par `sd-server`. Voir `dev/DECISIONS.md` D-024.

---

# PHASE 5 (v1.5.0) — VISION LOCALE & PROTOCOLE MCP

## 33. Vision locale multi-modale (paire modèle + projecteur `mmproj`)

Un modèle multimodal **ne fonctionne pas seul** : il exige son **projecteur** dédié (`mmproj.gguf`).
Le catalogue encapsule donc **deux URLs** par modèle vision, et l'acquisition est **atomique**
(les deux fichiers ou rien).

```bat
Run-LocalAI.bat list                        :: qwen2-vl-2b et smolvlm-500m y figurent
Run-LocalAI.bat pull qwen2-vl-2b            :: modele + projecteur (atomique, SHA-256 verifies)
Run-LocalAI.bat start                       :: demarre le moteur VISION (port 8095)
```

| Modèle vision | GGUF | projecteur | Total |
|---|---|---|---|
| `qwen2-vl-2b` | 942 Mo | 676 Mo | **1,6 Go** |
| `smolvlm-500m` | 420 Mo | 100 Mo | **0,5 Go** |

Le moteur est lancé avec l'argument requis :

```
llama-server.exe -m models\Qwen2-VL-2B-Instruct-Q4_K_M.gguf \
                 --mmproj models\mmproj-Qwen2-VL-2B-Instruct-Q8_0.gguf \
                 -ngl 0 --threads 8 -c 2048 --port 8095
```

> **`-ngl 0` par défaut (voir D-029)** : sur Maxwell, le chemin multimodal (`mtmd`) provoque un
> `Vulkan device lost` — le moteur vision tourne donc en **CPU**, ce qui est stable et suffisant
> (~40 s pour décrire une image 512×512). Surcharge :
> `set LOCALAI_VISION_NGL=99` avant `start` pour tenter le GPU.

Appel direct (format OpenAI, image en base64) :

```bat
curl -sS -X POST http://127.0.0.1:8095/v1/chat/completions -H "Content-Type: application/json" ^
  -d "{\"model\":\"vlm\",\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"Decris l'image\"},{\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,...\"}}]}]}"
```

## 34. Protocole MCP (Model Context Protocol, spécification 2024-11-05)

La passerelle `scripts\mcp_gateway.py` s'appuie **exclusivement** sur le **SDK officiel** `mcp`
(JSON-RPC 2.0 sur stdio) — **aucune réimplémentation** du protocole. Elle expose LocalAI comme
**serveur MCP local** consommable par Cline/VS Code, et sait aussi **agréger** des serveurs externes.

```bat
Run-LocalAI.bat mcp-list                    :: serveurs + outils actifs
Run-LocalAI.bat mcp-call localai localai_status
Run-LocalAI.bat mcp-call localai localai_rag_query --args-file args.json
Run-LocalAI.bat mcp-test                    :: autotest de bout en bout (VERDICT VERT attendu)
```

Outils exposés : `localai_rag_query`, `localai_vision_caption`, `localai_status`,
`localai_vram_status`, `localai_graph_show`.

Tout est déclaré dans **`config\mcp-settings.json`** (préservé entre réinstallations) :

```json
{
  "spec_version": "2024-11-05",
  "servers": {
    "localai": { "enabled": true, "type": "stdio",
                 "command": "runtime\\python\\python.exe",
                 "args": ["scripts\\mcp_gateway.py", "serve"] }
  },
  "tools": [ { "name": "localai_rag_query", "server": "localai", "enabled": true } ]
}
```

Ajouter un serveur externe = ajouter une entrée dans `servers` (transport `stdio`, `command` + `args`) ;
`mcp-list` le fera apparaître avec ses outils.

> **Isolation** : le SDK provient de l'extra `litellm[proxy]` (constaté : `mcp 2.3.0`). Si une version
> future cessait de le fournir, l'installeur le poserait dans le préfixe isolé `runtime\mcp\packages`,
> sans jamais toucher au site-packages qui héberge le proxy d'authentification (voir D-030).

## 35. Images dans l'index contextuel RAG

Le pipeline RAG indexe désormais les **images** (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp`)
avec leurs **métadonnées structurelles**, lues depuis l'en-tête binaire (**aucune dépendance
externe** : ni PIL, ni ImageMagick) :

```json
{"source": "capture_pomme.png", "chunk": 0, "chars": 88,
 "meta": {"kind": "image", "format": "png", "width": 512, "height": 512,
          "bytes": 402991, "megapixels": 0.262},
 "text": "[image png 512x512 px, 402991 octets, 0.262 MP] fichier image indexe : capture_pomme.png"}
```

## 36. GraphRAG local (extraction d'entités et relations par le LLM)

`scripts\graph_rag.py` construit un graphe de connaissances **sans aucune heuristique regex** :
chaque chunk est soumis au **LLM local** (`llama-server /v1/chat/completions`, `temperature=0`)
avec un prompt exigeant un **tableau JSON strict** `[{"head","type","relation","tail"}]`.

```bat
Run-LocalAI.bat graph-index G:\mon\code --max-files 40 --max-chunks 24
Run-LocalAI.bat graph-show
```

- **Parsing robuste** : isole le premier tableau JSON équilibré ; si la sortie est **tronquée**
  (limite de tokens), les **objets complets déjà émis** sont récupérés, les virgules terminales
  nettoyées et les triplets invalides ignorés. Les échecs sont comptés (`stats.echecs`) sans jamais
  interrompre l'indexation.
- **Interdépendances structurelles du code** : les imports/références (Python, Go, JS/TS, PS1, BAT)
  ajoutent des arêtes déterministes `kind:"structural"`, distinctes des arêtes `kind:"llm"`
  (avec `provenance` = fichier d'origine).
- **Sérialisation à plat** dans `runtime\storage\graph_db.json` :

```json
{ "built_at": "...", "source_dir": "...", "engine": "llama-server /v1/chat/completions (NER/RE par LLM local)",
  "stats": {"files": 6, "chunks": 6, "triplets": 18, "echecs": 0},
  "nodes": [{"id": "watchdog", "name": "watchdog", "type": "module", "mentions": 3, "degree": 4, "sources": ["vram_watchdog.py"]}],
  "edges": [{"source": "watchdog", "relation": "surveille", "target": "vram", "kind": "llm", "provenance": "vram_watchdog.py"}] }
```

L'outil MCP `localai_graph_show` expose ces statistiques (nœuds, arêtes, hubs, moteur).

## 37. Failover SSE (proxy port 8081) — bufferisation et bascule

`scripts\failover_proxy.py` est un **proxy OpenAI-compatible** placé devant le cœur LocalAI :

```bat
:: requete bufferisee (agent) : aucune coupure possible
curl -sS -X POST http://127.0.0.1:8081/v1/chat/completions ^
  -H "Content-Type: application/json" -H "X-LocalAI-Buffer: 1" ^
  -d "{\"model\":\"localai-buffered\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"Bonjour\"}]}"
```

| Régime | Déclencheur | Comportement |
|---|---|---|
| **Bufferisé** | `stream:true` **et** (`model` dans `buffered.models` **ou** en-tête `X-LocalAI-Buffer: 1`) | la génération est lue **intégralement** (en JSON, `stream:false` en amont), puis restituée au client en **flux SSE régulier**. Toute défaillance (port mort, exception, **HTTP ≥ 500**) est interceptée et la requête est **rejouée silencieusement** sur la route suivante : **le client ne voit jamais de flux interrompu**. |
| **Routin (flux)** | `stream:true` sans marqueur | la route est choisie **avant** d'ouvrir le flux (sonde TCP, **1.5 s**) : **failover sur erreur avant le premier token**. |

**Chaîne de reprise** (déterministe) : `core-local` (8080) → `vision-cpu` (8095, local CPU) →
`cloud` (clé dans `config\cloud-keys.env`, désactivable). Un **HTTP 4xx** est une erreur de *requête*
(modèle inconnu) : elle est renvoyée telle quelle, **sans** bascule inutile.

**Audit** : `logs\failover.jsonl` — une ligne par décision (`route`, `mode`, `failover`,
`ms_decision`, `caracteres`). **Mesuré** : bascule décidée en **162–367 ms** (< budget 1,5 s).

**Configuration** : `config\failover.json` (routes, marqueur, seuils, `alias_map` des alias de
bufferisation vers le modèle réel du primaire) — **préservé** entre réinstallations.

# PHASE 7 (v1.7.0) — QUANTIZATION LOCALE & FILTRE DE CONFIDENTIALITÉ

## 39. Quantization locale (`llama-quantize.exe`)

L'orchestrateur expose la compression locale de modèles, **sans aucun service externe** :

```bat
Run-LocalAI.bat quantize list                              :: types supportes + sources F16/F32 detectees
Run-LocalAI.bat quantize models\modele-f16.gguf Q4_K_M     :: compression synchrone
Run-LocalAI.bat quantize models\modele-f16.gguf Q8_0 --async   :: compression en arriere-plan
```

- **Prérequis** : la source doit être **non quantifiée** (F16/F32) — `llama-quantize` refuse les
  requantifications ; la commande avertit si le nom du fichier n'indique ni `f16` ni `f32`.
- **Types** : `Q8_0`, `Q6_K`, `Q5_K_M/S`, `Q5_0/1`, `Q4_K_M/S`, `Q4_0/1`, `Q3_K_L/M/S`, `Q2_K`,
  `IQ4_NL`, `IQ4_XS`, `IQ3_S`, `IQ3_XXS`, `IQ2_S`, `IQ2_XS`, `IQ2_XXS`, `F16`, `BF16`, `F32`.
- **Sortie** : par défaut `models\<nom>-<type>.gguf` (surchargeable par `--out`).
- **Asynchrone** : `--async` détache un processus de fond (le CLI rend la main immédiatement) ;
  suivi dans `logs\quantize.log`, historique JSON dans `data\quantize-history.jsonl`
  (source, cible, type, tailles, ratio, SHA-256, durée, code retour).
- **Sécurité** : binaire, source et cible vérifiés avant lancement ; toute erreur est remontée
  proprement (code non nul + message), jamais silencieuse.

> **Mesure réelle** : `SmolVLM-500M-Instruct-f16.gguf` (782 Mo) → Q8_0 = **417 Mo** (8.50 BPW) en
> **2,4 s**, SHA-256 calculé et consigné.

## 40. Filtre de confidentialité PII hybride — **protection BEST-EFFORT**

> ⚠️ **AVERTISSEMENT DE TRANSPARENCE** : ce filtre est une protection **BEST-EFFORT**. Il **ne
> garantit pas** une étanchéité absolue à 100 % : un format de secret inconnu, un encodage exotique
> ou une entité non reconnue par le NER local peuvent passer. Il **réduit** fortement le risque de
> fuite lors d'un débordement vers une API cloud, il ne l'annule pas. Ne l'utilisez pas comme unique
> rempart pour des données classifiées.

Le module `config\pii_filter.py` combine **trois niveaux** :

| Niveau | Principe | Couverture |
|---|---|---|
| **1 — Regex déterministes** | formats standards | e-mails, IPv4/IPv6, clés `sk-…` (OpenAI), `ghp_/gho_/…` (GitHub), `AKIA…` (AWS), `xox…` (Slack), JWT, clés privées PEM, cartes bancaires (**validées par Luhn**) |
| **2 — Entropie de Shannon** | jetons ≥ 20 caractères, entropie ≥ **3,5 bits**, jeu de caractères mixte | mots de passe complexes, clés/chaînes custom en clair |
| **3 — NER local léger** | appel **interne** au moteur local (`llama-server`) | personnes, adresses, organisations (aucun envoi externe) |

**Fonctionnement** : `redact()` renvoie le texte masqué (`[PII-<TYPE>-<n>]`) **et** le mapping
réversible ; `restore()` restitue les valeurs d'origine dans la réponse. Le Token Saver
(`config\complexity_router.py`) masque **uniquement lorsque la requête part vers le cloud**
(une requête servie localement ne quitte pas la machine) et démasque la réponse avant de la rendre.

```bat
Run-LocalAI.bat privacy-test              :: autotest masquage + reversibilite (niveaux 1-2)
Run-LocalAI.bat privacy-test --with-ner   :: autotest incluant le niveau 3 (moteur requis)
Run-LocalAI.bat privacy-levels            :: detail des 3 niveaux
```

**Désactivation explicite** (transparence utilisateur) :

```bat
Run-LocalAI.bat start --no-pii-filter     :: desactive le filtre pour la session (LOCALAI_PII_FILTER=0)
```

Réglages : `LOCALAI_PII_FILTER=0|1`, `LOCALAI_PII_LEVELS=1,2,3`, `LLAMA_PORT` (port du NER local).

**Audit** : chaque masquage est journalisé dans `dev\crash.log`, catégorie **`PRIVACY_FILTER`**
(type, niveau, jeton, aperçu tronqué + rappel de la nature BEST-EFFORT) ; le routage consigne en
outre le nombre de masques dans `logs\routing.jsonl`.

**Mesure réelle** (débordement cloud simulé) : requête virtuelle `localai` routée vers
`openrouter-claude` ; la clé `sk-proj-…`, les IP `192.168.1.42` / `10.0.0.7` et l'adresse e-mail ont
été masquées **avant** l'envoi, puis restituées dans la réponse — **aucun secret original n'a quitté
la machine** dans le corps transmis.

# PHASE 8 (v1.8.0) — ROUTAGE HÉTÉROGÈNE NPU (DIRECTML UNIFIÉ)

## 42. Accélération universelle NPU via DirectML + repli CPU

Windows n'expose pas d'API unique pour les NPU ; **DirectML** sert de couche de virtualisation de
calcul native et adresse **NPU Intel**, **NPU AMD Ryzen AI (XDNA2)** et GPU **sans SDK constructeur**.
Le provider est installé de manière isolée dans le Python embarqué :

```bat
Run-LocalAI.bat npu-probe          :: sonde reelle du provider retenu (inference ONNX effective)
Run-LocalAI.bat hardware-status    :: repartition exacte des charges d'inference
```

`onnxruntime-directml` est posé dans `runtime\python\Lib\site-packages` par la routine
**`ensure_onnx_directml()`** (installation puis **re-contrôle** effectif du provider).

### Répartition des charges
```
MOTEUR PRINCIPAL            llama.cpp  ──►  GPU (variante vulkan/cuda)   : inference de texte
TÂCHES SÉMANTIQUES LÉGÈRES  DirectML   ──►  NPU Intel / NPU AMD XDNA2   : NER du filtre PII,
                                                                            outils MCP légers
                            (repli)    ──►  CPU  : bascule automatique, transparente
```

### Repli CPU obligatoire (sécurité QA)
Si le matériel ou les pilotes ne permettent pas l'initialisation de DirectML, l'accélérateur bascule
**automatiquement et de manière totalement transparente sur le CPU** :

- la **session utilisateur n'est jamais interrompue** ;
- un **avertissement explicite** est consigné dans `dev\crash.log`, catégorie **`GPU_DETECT`** :

```
[20261003_200521] [GPU_DETECT] [WARN] Acceleration DirectML indisponible
(DirectML absent (pilote ou materiel incompatible) -> repli CPU) : bascule automatique
sur CPU pour les taches semantiques legeres. Session utilisateur preservee.
```

### Validation matérielle réelle
Un **modèle ONNX authentique** est déployé pour la sonde : `runtime\onnx\mnist-8.onnx`
(**25 843 octets**, SHA-256 `2f06e72d…c9bf`). `npu-probe` exécute une **inférence effective** sur le
provider retenu (et non un simple test de disponibilité d'API) :

```json
{ "ok": true, "device": "cpu", "selected": "cpu",
  "providers": ["AzureExecutionProvider", "CPUExecutionProvider"],
  "prediction": 9, "model": "mnist-8.onnx" }
```

> Sur la machine de référence (GTX 970M, **sans NPU**, pilotes 2014), DirectML est indisponible :
> le **repli CPU** s'est déclenché et la sonde a tout de même exécuté l'inférence — le scénario
> d'auto-healing exigé par le mandat est donc **vérifié en conditions réelles**.

### Outil MCP déporté
`localai_semantic_probe` (6ᵉ outil du serveur MCP local) exécute la sonde sur l'accélérateur et
renvoie provider, device et latence — démonstration du déport des **outils légers** vers la couche
DirectML.

## 43. Garde-fou de bascule (leçon de l'incident v1.8.0)

⚠️ **Incident majeur corrigé (D-037)** : la bascule transactionnelle supprimait l'arbre de production
**avant** d'installer le nouveau ; un fichier verrouillé (service encore actif) a provoqué la **perte
de l'arbre**. Deux correctifs sont désormais en place :

1. **Permutation par renommage** : `LocalAI` → `LocalAI.old` → mise en place du nouveau → purge
   best-effort de l'ancien. En cas d'échec, l'ancien est **restauré** et le nouveau **conservé**.
2. **Garde préalable** : l'installation **refuse** de s'exécuter si un service est encore actif
   (sonde `OpenProcess` sur `data\pids.txt`) :
   `Reinstallation refusee : services encore actifs -> ... Lancez d'abord 'Run-LocalAI.bat stop'`.

**Règle à retenir : arrêtez toujours la pile (`Run-LocalAI.bat stop`) avant de réinstaller.**

## 44. Chaîne complète v1.8.0
```
                 ┌──────────────────── MOTEUR PRINCIPAL (GPU) ────────────────────┐
Cline ─► 8081 ─► │ 8080 cœur LocalAI ─► 8090 llama-server (vulkan/vulkan+cuda)     │ ─► texte
   failover      │ 8091 whisper  8092 sd  8093 tts  8095 vision (CPU)  4000 LiteLLM│
                 └────────────────────────────────────────────────────────────────┘
# PHASE 10 (v2.0.0a) — ESPACE HERMÉTIQUE SOUVERAIN (AES-256 AU REPOS)

## 45. Chiffrement de la zone sémantique

`scripts\vault.py` chiffre la **base de connaissances locale** (`runtime\rag\` — index, chunks,
manifestes, registre de collections — et `runtime\storage\` — graphe GraphRAG).

```bat
Run-LocalAI.bat vault-status    :: etat : fichiers en clair / scelles, backend, derivation
Run-LocalAI.bat vault-seal      :: chiffre la zone (mot de passe demande, JAMAIS stocke)
Run-LocalAI.bat vault-unseal    :: ouvre la zone pour la session
Run-LocalAI.bat vault-test      :: autotest (scellement, ouverture, integrite, refus)
```

- **Algorithme** : **AES-256-GCM** (chiffrement **authentifié** — toute altération est détectée et
  refusée).
- **Clé** : dérivée à la volée par **PBKDF2-HMAC-SHA256**, **390 000 itérations**, **sel aléatoire
  de 16 octets** stocké dans l'en-tête du conteneur (le sel n'est pas secret ; **la clé ne l'est
  jamais écrite sur le disque**).
- **Mot de passe** : saisi en **console** (`getpass`, saisie masquée) au moment de `seal`/`unseal`.
  Pour l'automatisation, `--password-env <NOM>` lit une variable d'environnement — **moins sûre**
  (elle peut apparaître dans l'environnement du processus).
- **Conteneur** : `MAGIC(8) | version(1) | itérations(4) | sel(16) | nonce(12) | chiffré`, stocké à
  côté de l'original sous `<fichier>.enc`.
- **Anti-perte** : `seal` **vérifie immédiatement** que le conteneur se déchiffre à l'identique
  **avant** de supprimer le clair ; en cas d'échec, le conteneur est retiré et l'opération annulée.

> ⚠️ **CLAUSE DE TRANSPARENCE — portée exacte du chiffrement**
> 1. **Strictement AU REPOS.** Pendant la session, les fichiers de l'index doivent exister en clair
>    sur le disque pour être lus par les moteurs (NumPy, JSON) : c'est inévitable. `stop` (ou
>    `vault-seal`) les scelle ; **après un arrêt propre, la zone ne contient plus que des `.enc`**.
> 2. **L'effacement en mémoire vive n'est PAS garanti.** La clé et les données déchiffrées vivent en
>    RAM pendant la session ; leur disparition dépend du **ramasse-miettes de Python** (meilleur
>    effort sémantique) et non d'un verrouillage mémoire matériel. Ce n'est **pas** une protection
>    contre une attaque en mémoire vive.
> 3. **Un mot de passe oublié = données perdues.** Il n'existe **aucune** porte dérobée, aucun
>    escrow, aucune clé de récupération : c'est le prix de la souveraineté.
> 4. Le chiffrement protège la **zone sémantique** ; il ne chiffre ni les modèles, ni les journaux,
>    ni les fichiers de configuration.

**Mesures réelles**
- Autotest (`vault-test`) : **VERDICT VERT** — scellement OK, ouverture OK, **intégrité IDENTIQUE**,
  **mauvais mot de passe refusé** (authentification GCM), clé jamais écrite.
- Sur un **index RAG réel** (4 fichiers : `index-default.npy` 41 Ko, `chunks-default.jsonl`,
  `manifest-default.json`, `collections.json`) : cycle `seal` → `unseal` avec **4/4 empreintes
  SHA-256 identiques → ZÉRO CORRUPTION**, et **aucun fichier en clair** ne subsiste après scellement.

## 46. Chaîne complète v2.0.0a
```
Run-LocalAI.bat vault-seal ──► mot de passe (console, masque) ──► PBKDF2-HMAC-SHA256 (390 000 iter.)
                                       │                                   │
                                       │                            cle 32 octets (RAM seule)
                                       ▼                                   ▼
                       runtime\rag\index-*.npy ──AES-256-GCM──► index-*.npy.enc  (+ clair supprime)
                       runtime\storage\graph_db.json ──────────► graph_db.json.enc
```












## 47. Profil apprenant continu (adaptation à chaud)
Le poste **s'auto-règle** d'après ses mesures réelles — et le retour aux profils d'usine reste garanti.

```
Run-LocalAI.bat profile-observe    :: enregistre une observation (logs\history.jsonl)
Run-LocalAI.bat learn-profile      :: analyse la telemetrie et ecrit config\profile.json
Run-LocalAI.bat profile-status     :: etat (appris vs usine) + seuils en vigueur
Run-LocalAI.bat reset-profile soft :: GARDE-FOU : retour immediat a un profil d'usine
                                   ::   (soft | normal | hard ; defaut : normal)
```

- **Sources analysées** (jamais de contenu de requête, uniquement des mesures du poste) :
  `logs\history.jsonl`, `logs\vram.log`, `logs\failover.jsonl`, `config\hardware-profile.json`.
- **Ce qui est ajusté** : seuil d'alerte VRAM, seuil critique, seuil de reprise et profondeur
  d'offload `-ngl`. Le seuil d'alerte est **ancré sur le minimum de VRAM libre réellement observé**
  (+5 points de marge), et les trois seuils sont **bornés** (8–25 % / 3–12 % / 15–40 %) : aucun
  réglage absurde n'est possible.
- **`-ngl`** : conservé par défaut ; **réduit de 20 %** uniquement si le watchdog a réellement
  enregistré des **évictions critiques**.
- **Instantanéité** : le watchdog relit `config\profile.json` toutes les **5 secondes** — le profil
  appris s'applique **sans redémarrage**, et `reset-profile` **revient** aux valeurs d'usine tout aussi
  vite.
- **Persistance** : `config\profile.json` et `logs\history.jsonl` sont **conservés à la
  réinstallation** (règle d'or de l'héritage) : l'apprentissage n'est jamais perdu par une mise à jour.
- **Repli sûr** : fichier absent ou **moins de 2 observations** → repli automatique sur le profil
  d'usine. Aucune erreur bloquante.
- **Traçabilité** : `dev\crash.log`, catégorie `PROFILE_LEARN`.
- **Transparence** : statistiques simples sur des mesures du poste ; **aucune donnée n'est exportée**.

## 48. Chaîne complète v2.0.0
```
Run-LocalAI.bat start ──► watchdog VRAM (seuils 15/5/20 au demarrage)
                              │
                              │ toutes les 5 s : relit config\profile.json
                              ▼
   profile-observe ──► logs\history.jsonl ──► learn-profile ──► config\profile.json (25/12/35)
                                                                      │
                                                       applique A CHAUD (0 redemarrage)
                                                                      │
   reset-profile soft ─────────────────────────────────────────────────┘
   ──► config\profile.json = usine soft (20/10/30) ──► applique A CHAUD en quelques secondes
                                                                      │
   Run-LocalAI.bat vault-seal ──► AES-256-GCM de runtime\{rag,storage} ──► .enc (clair supprime)
```
**Mesures sur le poste de référence (GTX 970M 6144 Mo)** : VRAM libre observée **61,3–62,6 %** → seuil
d'alerte appris **25 %**, `ngl` **99** conservé (0 éviction) ; retour d'usine **`25/12/35` → `20/10/30`
en quelques secondes** ; **AST VERT**, **83 composants**, **zéro zombie**.

## 49. Inférence fédérée : découverte réseau et RPC natif (v2.1.0)
Le portage sait **trouver ses pairs sur le réseau local** et leur **déporter du calcul** — sans jamais
réinventer le transport : tout passe par le **cœur RPC natif de llama.cpp**.

```
Run-LocalAI.bat peer-status     :: noeuds RPC distants (IP, port, latence, joignabilité)
Run-LocalAI.bat peer-scan       :: scan reseau (broadcast UDP non invasif) -> config\peers.json
Run-LocalAI.bat peer-test       :: autotest de la decouverte (protocole, boucle locale)
Run-LocalAI.bat peer-rpc-arg    :: affiche l'argument --rpc genere pour le moteur principal
```

- **Découverte** (`scripts\peer_discovery.py`) : **UDP broadcast en pur Python, zéro dépendance**
  (ni `zeroconf`, ni `avahi`). Deux messages seulement (`query` / `reply`) ; la découverte **ne
  transporte aucune donnée d'inférence** — uniquement des adresses IP et des métadonnées de nœud.
- **Péremption** : un pair muet disparaît automatiquement après **90 secondes**.
- **Routage fédéré** (`vram_watchdog.py`) : si la **VRAM passe sous le seuil critique** et qu'un nœud
  RPC distant est **déclaré et réellement joignable**, le moteur est relancé avec l'argument exact
  **`--rpc <IP>:<Port>`** (option réelle de `llama-server`). Sinon, **repli CPU pur (`-ngl 0`)**.
- **Garde-fou** : un nœud **injoignable** n'est **jamais** utilisé. Sur un poste isolé, le calcul reste
  **100 % local** et l'inférence n'est jamais cassée.
- **Côté machine distante** : lancer le serveur RPC fourni par le moteur —
  **`ggml-rpc-server.exe`** (nom réel de la distribution amont, port par défaut **50052**) :
  `ggml-rpc-server.exe -H 0.0.0.0 -p 50052`
- **Démon d'annonce** : lancé avec la pile (désactivable par `Run-LocalAI.bat start --no-peers`),
  il écoute/émet sur le port **UDP 47653** et est arrêté proprement avec la pile.

## 50. Clause matérielle — accélération et NPU
- **GPU NVIDIA** : accélération **Vulkan** (testée et validée, sans CUDA ni DirectML).
- **NPU Intel / Qualcomm** : adressables via **DirectML** ou **OpenVINO** selon disponibilité.
- ⚠️ **NPU AMD XDNA2 via DirectML : EXPÉRIMENTAL ET NON FONCTIONNEL.** DirectML limite son support NPU
  aux plateformes **Intel** et **Qualcomm** ; il n'existe à ce jour **aucun backend NPU AMD
  fonctionnel** dans DirectML pour cette architecture. L'architecture **AMD s'appuie donc sur le
  repli CPU (calcul NumPy natif), maîtrisé et validé**.
- **CPU seul** : chaîne complète fonctionnelle (RAG NumPy, GraphRAG, embeddings, inférence quantifiée).
- Aucun de ces chemins n'est obligatoire : le portage **choisit automatiquement** la couche disponible
  et **retombe toujours** sur un chemin fonctionnel.

## 51. Chaîne complète v2.1.0
```
Run-LocalAI.bat start ──► coeur 8080 · gateway 4000 · VLM 8095 · Whisper/Images/TTS
                     ──► watchdog VRAM (escalade) ──► demon d'annonce UDP 47653
                                                        │
   peer-scan ──► broadcast UDP ──► config\peers.json ◄──┘  (paires declares, TTL 90 s)
                                        │
   VRAM critique ──► _federated_targets() : test TCP de joignabilité
                                        │
              joignable ? ──oui──► relance moteur avec --rpc <IP>:<Port>  (RPC natif llama.cpp)
                          └─non──► repli CPU pur (-ngl 0)   [JAMAIS de --rpc vers un noeud mort]
```
**Mesures sur le poste de référence (GTX 970M, isolé)** : `peer-test` → **VERDICT VERT** (latence
**0,6 ms**) ; découverte réelle d'un nœud en broadcast (latence **17,2 ms**) ; **panne RPC simulée** →
nœud mort refusé, `federated_relaunch` → **applied=False** (calcul local conservé) ; inférence
**6,0 s** (non perturbée) ; arrêt → **0 port TCP, 0 port UDP, zéro zombie, VRAM libérée** ;
**AST VERT**, **84 composants**.

