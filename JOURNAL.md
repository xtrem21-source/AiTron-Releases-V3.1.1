# Journal de bord — AiTron V3 (portage Windows natif)

## 2026-10-05 — v3.1.2 : les binaires arrivent par GitHub Releases

**Fin des URLs temporaires.** v3.1.1 avait rendu l'installeur portable et pose un garde-fou PE "MZ" qui
avait denonce les URLs `transfert.free.fr` (pages HTML). v3.1.2 branche le produit sur une **release
GitHub perenne** (`xtrem21-source/AiTron-Releases-V3.1.1@v3.1.1`) et **integre les SHA-256** des deux
binaires (`0F55C483...` / `BFCB2804...`). Le **garde-fou MZ est conserve ET renforce** : il s'applique
desormais a *tout* `.exe` telecharge, meme quand une somme est fournie (defense en profondeur).
**Preuve de bout en bout** : depuis une racine "vierge" (`C:\TestGitHub`), l'installeur a **telecharge**
`local-ai.exe` et `cloud-proxy.exe` depuis GitHub, **verifie le SHA-256**, valide le magic `MZ`, puis
**deploye 87 composants** en v3.1.2. Tests : SHA errone (rejet + `.part` nettoye), cascade (URL invalide),
et coherence v3.1.1 (0 BOM, CLI bilingue, failover SSE, vault, **0 zombie**). **v3.1.2 livree.**

## 2026-10-05 — v3.1.1 : l'installeur apprend a s'installer n'importe ou

**Portabilite totale + fallbacks de telechargement.** L'installeur etait **cable en dur** sur
`G:\V1\LocalAI-Projet\` : il ne savait s'installer que la. Desormais il **se deduit lui-meme** :
`SANDBOX` = dossier du script, ou `--root <chemin>` explicite, avec **creation automatique** de
l'arborescence au premier lancement. **Deux passes chirurgicales** (patch transactionnel, sauvegarde
boite noire a chaque fois, AST triple au vert, zero SyntaxWarning) : D-049 (detection dynamique)
puis D-050 (cascade `build\out\` -> staging -> produit -> telechargement + garde MZ).
**Lecon de terrain** : les URLs de fallback du mandat servent une **page HTML**, pas un binaire —
le SHA etant **vide**, il **fallait** un garde-fou (`MZ`) pour **refuser** cette source trompeuse ;
sans lui, l'installeur aurait deploye un faux `local-ai.exe`. **Le test a revele le defaut ; la
doctrine exigeait de le corriger.** **Preuves** : 5 installations reelles (`G:\`, `C:\AiTron-Test`,
`--root D:\`, USB `E:\`), 87 composants, inférence reelle, **15/15** controles unitaires,
**0 BOM**, **0 zombie, 0 port**. **v3.1.1 livree.**

## 2026-10-03 — v2.1.0, v2.1.1 & v3.0.0 : fédération, bilinguisme, identité

**v2.1.0 — Inférence fédérée (JALON 6 & 7).** Le mandat était catégorique : **ne pas réinventer le
transport**. Nous avons donc écrit une découverte **UDP broadcast en pur Python** (`peer_discovery.py`)
qui ne transporte **aucune donnée d'inférence** et ne sert qu'à **identifier les adresses IP**, puis
délégué **100 % du calcul** au **cœur RPC natif de llama.cpp** via l'argument réel `--rpc <IP>:<Port>`.
Le watchdog applique une **escalade** : routage fédéré d'abord, **repli CPU pur** ensuite.

*Anomalie de nommage (famille A24/A26)* : le mandat cite `rpc-server.exe` ; l'amont libre livre
**`ggml-rpc-server.exe`** (port 50052). **Leçon** : toujours vérifier les noms réels de la distribution
avant de coder dessus.

*Preuve de rupture* : un vrai `ggml-rpc-server.exe` a été lancé, déclaré comme pair (joignable, 1 cible,
`--rpc 192.168.1.84:50052` généré), puis **tué en pleine simulation** → joignable NON, cibles = 0,
`federated_relaunch` → **applied=False, « aucun nœud RPC distant joignable (calcul local conservé) »**.
**Aucun `--rpc` n'est injecté vers un nœud mort** : l'inférence locale n'est jamais cassée. Après arrêt :
**0 port TCP, 0 port UDP, zéro zombie**.

**v2.1.1 — i18n FR/EN (PHASE 2.20).** Trois couches : **embarqué** (vérité ultime), **JSON externe**
(personnalisable, jamais écrasé), **`I18N_REV`** (rafraîchit uniquement les clés de documentation).
`Run-LocalAI.bat` charge **dynamiquement** `i18n\_fr.bat` ou `i18n\_en.bat` — **bascule sans
redémarrage**, bannière comprise.

*Quatre bugs de déploiement, tous silencieux.* `gen_lang_bat()` utilisait `__version__` là où le
namespace de déploiement exige **`__VERSION__`** ; `I18N_PY` était exécuté sans `__file__` ; `json`
n'était pas importé dans ce namespace ; et les fichiers **vides** laissés par ces échecs étaient ensuite
**préservés par la règle d'or de l'heritage**. Enfin `Run-LocalAI.bat` résolvait la langue par `for /f`
avec un chemin d'exécutable entre guillemets — **qui ne s'exécute jamais** : l'interface restait en
français malgré `lang=en`. Chaque bug a été isolé, corrigé, et le générateur rendu **auto-réparant**.
**Leçon retenue et écrite dans la doctrine : un échec d'étape ne fait PAS échouer l'installation — il
faut lire le journal ligne à ligne.**

**v3.0.0 — Identité AiTron V3 (PHASE V3).** Renommage chirurgical : `install_localai_win.py` ➔
**`install_AiTron_v3.py`**, `LocalAI\` ➔ **`AiTron\`**, staging `AiTron.new`, `LOCALAI_DEPLOY_CODE` ➔
**`AITRON_DEPLOY_CODE`**, variables d'environnement `AITRON_*`, manifeste enrichi
(`"product": "AiTron V3"`, `"fork_of": "LocalAI (https://github.com/mudler/LocalAI)"`, `"license":
"MIT"`), `CHARTE.md` actée. Le moteur **`local-ai.exe` conserve son nom** : c'est la technologie, le
produit s'appelle AiTron V3. Une **migration d'héritage** reprend automatiquement les données de
l'ancien répertoire pour ne rien perdre.

**Audit d'autonomie mono-bloc.** Le produit a été **mis en sécurité puis physiquement supprimé**, et
reconstruit par le seul installeur (`--prev` pointant sur la sauvegarde). Le portage renaît de ses
cendres : code, backends GPU, runtimes, configurations, catalogue, documentation.

**Bilan.** **v2.1.0**, **v2.1.1** et **v3.0.0** livrées, validées en conditions physiques réelles et
**gelées**. Le portage sait désormais **fédérer son calcul**, **parler deux langues** et **porter son
propre nom**.


# Journal de bord — portage LocalAI Windows natif

## 2026-10-03 — v1.9.0 & v2.0.0 : décodage spéculatif, espace hermétique, profil apprenant

**v1.9.0 — Décodage spéculatif (JALON 2 & 3).** Implémenté, correct… et **désactivé par défaut**.

Deux pièges réels ont été découverts dans le moteur llama.cpp : **(A24)** les options
`--draft-max/--draft-min` **n'existent plus** en amont — les vrais drapeaux sont
`--spec-draft-n-max/--spec-draft-n-min` ; **(A25)** le modèle brouillon doit **partager son
tokenizer** avec le modèle principal. Une fois ces points corrigés, la mesure a tranché :
**21,39 tok/s contre 21,76 sans** — le portage est **limité par le GPU**, pas par le CPU, donc le
décodage spéculatif **n'apporte rien** ici. Décision **D-039** : il reste livré, mais **à la demande**
(`LOCALAI_SPEC=1`). Livrer une fonction qui ne sert pas aurait été une faute ; la livrer **mesurée et
documentée** en est une information.

**v2.0.0 — Espace hermétique et profil apprenant (JALON 4 & 5).**

*Espace hermétique (v2.0.0a).* `scripts\vault.py` chiffre la zone sémantique
(`runtime\rag\`, `runtime\storage\`) en **AES-256-GCM**. La clé **n'est jamais écrite sur disque** :
elle est dérivée à la volée d'un mot de passe saisi en console, par **PBKDF2-HMAC-SHA256 à 390 000
itérations** avec sel aléatoire. Le scellement **vérifie immédiatement la réversibilité** avant de
supprimer le clair : une perte est **structurellement impossible**. Sur un index RAG réel, le cycle
scellé/ouvert a rendu **4/4 empreintes SHA-256 identiques → zéro corruption**, et `rag-query` a
fonctionné normalement après le cycle. La clause de transparence est écrite noir sur blanc
(INSTALLATION §45, D-040) : protection **au repos**, effacement RAM **non garanti**, mot de passe
oublié **= données perdues**.

*Profil apprenant (v2.0.0b).* `scripts\learn_profile.py` lit la **télémétrie réelle** du poste et
ajuste les seuils du watchdog VRAM. Le seuil d'alerte est **ancré sur le minimum de VRAM libre
réellement observé**, les trois seuils sont **bornés**, et `-ngl` n'est réduit que si des **évictions
critiques** ont été réellement enregistrées. Le watchdog **relit le profil toutes les 5 secondes** :
le réglage s'applique **à chaud**, sans redémarrage.

La preuve la plus parlante est la suivante, relevée sur le poste de référence (GTX 970M, 6144 Mo) :
watchdog démarré en `15/5/20` → **`25/12/35` appliqués à chaud** après apprentissage → puis
`reset-profile soft` → **`20/10/30` appliqués à chaud en quelques secondes**. Les deux faces de la
bascule sont tracées (`GPU_VRAM` côté watchdog, `PROFILE_LEARN` côté apprentissage), et
`config\profile.json` comme `logs\history.jsonl` entrent dans la **règle d'or de l'héritage** :
l'apprentissage **survit aux réinstallations**.

**Trois anomalies corrigées en cours de route (JALON 5).** **(A1)** `reset-profile soft` était
refusé par le parseur d'arguments ; **(A2)** — plus grave — le reset *se contentait de supprimer* le
profil : le watchdog retombait alors sur **sa propre base de démarrage** au lieu du profil d'usine
demandé ; le reset **écrit** désormais les valeurs d'usine, ce qui rend le retour **réellement
instantané** ; **(A3)** une trace annonçait « profil appris » pour un profil d'usine — corrigé, parce
qu'une trace de diagnostic **doit être exacte**.

**Bilan.** **v1.9.0** et **v2.0.0** livrées, validées en conditions physiques réelles (AST VERT,
83 composants, zéro zombie, zéro port) et **gelées**. Le portage sait désormais **sceller sa mémoire
sémantique** et **s'auto-régler d'après ses propres mesures**, tout en conservant un **chemin de
retour déterministe** à chaque étape.


# JOURNAL.md — Journal Narratif du Chantier

> Journal du raisonnement de l'agent : ce qui a ete fait, pourquoi, ce qui a reussi, ce qui a echoue,
> ce qui a ete decide ensuite.

---

## Entree 01 — 2026-10-03 — Ouverture du chantier et reconnaissance de l'environnement

**Fait.**
- Lecture et acceptation de la charte. Copie de la charte en CHARTE.md a la racine de la sandbox
  (acte d'acceptation, conformement a Section 0.6).
- Creation de la structure initiale : `Installeur\`, `dev\`, `dev\old\`, `log\`, plus une zone de
  chantier `build\` (outils, telechargements, sources).
- Reconnaissance du poste : AMD64, Windows 10.0.29639, 34 Go RAM.
- Verification reseau : GitHub, go.dev, huggingface, api.github.com -> HTTP 200.

**Pourquoi.**
- Sans etat des lieux fiable, tout plan serait une hypothese. La reconnaissance est prealable a toute
  action (Section 9).

**Constat materiel.**
- Disque G: disponible (331 Go libres) -> suffisant pour toolchain + sources + modele.
- Python 3.12.10 (defaut) et 3.14.7 presents. Git 2.55.0 present.
- **Go ABSENT** du poste -> a installer dans la sandbox.
- **Aucun compilateur C** (gcc/clang/cl absents), **pas de Visual Studio** -> point critique pour CGO.

**Decouverte majeure (etat de l'art LocalAI).**
- Derniere version officielle : **v4.11.0**.
- Assets officiels : `local-ai-v4.11.0-linux-amd64`, `-linux-arm64`, `-darwin-arm64`, source,
  launcher Linux, DMG macOS. **AUCUN binaire Windows officiel.** LocalAI ne distribue pas de build
  Windows natif : la documentation officielle renvoie a WSL2/Docker.
- `go.mod` (master) exige **Go 1.26.0**. Go 1.27.1 disponible sur go.dev.
- Dependances sensibles : `gorm.io/driver/sqlite` + `github.com/mattn/go-sqlite3` (indirect) ->
  **CGO requis** pour compiler le binaire de base.

**Decision.**
- Appliquer l'ordre strict de la Section 4.2 : (1) compiler depuis les sources Go. Cela impose
  l'installation de Go 1.27.1 **et** d'une chaine C (MinGW-w64) pour satisfaire CGO. WSL2 reste un
  dernier recours documente (non retenu a ce stade).

**Suite.**
- Telecharger Go 1.27.1 (verifie SHA-256), extraire dans `build\tools\go`.
- Telecharger la source LocalAI v4.11.0 (verifie SHA-256) et tenter le build.

## Entree 02 — 2026-10-03 — Toolchain Go

**Fait.**
- Telechargement de `go1.27.1.windows-amd64.zip` (78 931 360 octets).
- Verification SHA-256 OK : `a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d`
  (identique a la valeur publiee par go.dev).
- Extraction via `tar.exe` (bsdtar) dans `build\tools\go` (Expand-Archive s'est revele trop lent /
  timeout). `go version` -> `go1.27.1 windows/amd64`.

**Decision.**
## Entree 03 — 2026-10-03 — Codegen protobuf (protogen-go)

**Fait.**
- Analyse du `Makefile` LocalAI : la cible `build` = `protogen-go` + `generate` + `install-go-tools`
  + `core/http/react-ui/dist`. Deux prerequis externes apparaissent : `protoc` et Node.js.
- Constat : la release source `LocalAI-v4.11.0-source.tar.gz` ne contient **ni** `*.pb.go`, **ni**
  `core/http/react-ui/dist`. Or `core/http/*.go` fait `//go:embed react-ui/dist/*` -> le build
  echouerait sans ces artefacts.
- Telechargement de `protoc-31.1-win64.zip` (3,4 Mo) -> `build\tools\protoc` (`libprotoc 31.1` OK).
- `go install protoc-gen-go@v1.34.2` + `protoc-gen-go-grpc@1958fcbe…` -> `build\gopath\bin`.
- Generation : `pkg/grpc/proto/backend.pb.go` (546 Ko) + `backend_grpc.pb.go` (95 Ko). EXIT=0.

**Pourquoi.**
- Le cœur gRPC est le langage natif des backends LocalAI ; sans codegen, aucun backend n'est joignable.

## Entree 04 — 2026-10-03 — UI React embarquee (npm/vite)

**Fait.**
- Telechargement de Node.js 24.21.0 LTS (37,6 Mo) -> `build\tools\node` (v24.21.0 / npm 11.19.0).
- `npm install` (561 paquets) puis `npm run build` dans `core/http/react-ui` -> `dist\` (index.html +
  bundles). EXIT=0. Cache npm confine via `npm_config_cache` dans la sandbox.

**Pourquoi.**
- `//go:embed react-ui/dist/*` exige un dossier non vide a la compilation.

## Entree 05 — 2026-10-03 — Compilation du coeur LocalAI (le pivot du projet)

**Fait.**
- Environnement Go entierement confine (`GOROOT/GOPATH/GOCACHE/GOENV/GOTMPDIR` sous `build\`).
- Decouverte decisive : le `.goreleaser.yaml` officiel compile le binaire avec **`CGO_ENABLED=0`** et
  `main: ./cmd/local-ai`. Aucun compilateur C n'est donc requis (piste MinGW devenue inutile).
- Premiere compilation `go build -o build\out\local-ai.exe ./cmd/local-ai` -> **EXIT=0** (245 Mo).
- `local-ai.exe --version` : binaire **fonctionnel** sous Windows. Rebuild avec ldflags de version
  -> `Version: v4.11.0-win.1` (186 Mo, `-s -w`).
- Compilation du backend `./backend/go/cloud-proxy` -> `cloud-proxy.exe` (19 Mo). EXIT=0.

**Pourquoi.**
- LocalAI ne publie aucun binaire Windows : la compilation depuis les sources (Section 4.2, etape 1)
  est le seul chemin conforme a la charte.

**Ecueil rencontre.**
- Un premier rebuild avec `-trimpath` a invalide tout le cache de compilation (recompilation complete).
  Correction : rebuilds sans `-trimpath` (cache chaud) -> quasi instantanes.

## Entree 06 — 2026-10-03 — Le backend : comment rendre llama.cpp fonctionnel sous Windows

**Probleme.** Le backend llama.cpp officiel de LocalAI (`backend/cpp/llama-cpp`) est un serveur
C++/gRPC compile sous Linux/Docker. Le porter sous Windows exigerait gRPC C++ + MSVC/MinGW + protoc
C++ : disproportionne et fragile.

**Decouverte.** Lecture de `docs/content/reference/architecture.md` : « It is possible to specify
external gRPC server and/or binaries that LocalAI will manage internally. » Et le backend
`backend/go/cloud-proxy` est **un serveur gRPC ecrit en Go** qui relaie le trafic vers un fournisseur
HTTP OpenAI-compatible. Et `core/backend/options.go` construit `pb.ProxyOptions` depuis un bloc YAML
`proxy:` quand `backend: cloud-proxy`.

**Decision.** Composer l'ecosysteme :
`local-ai.exe --gRPC--> cloud-proxy.exe (compile localement) --HTTP--> llama-server.exe (ggml-org b11375)`.
Enregistrement du bridge via `--external-grpc-backends "cloud-proxy:<chemin>"`.

**Pourquoi.** Inférence réelle, robuste, 100 % Windows natif, sans Docker ni WSL, tout en gardant
`backends\llama-cpp\` comme dossier ouvert et remplaçable.

## Entree 07 — 2026-10-03 — Assemblage et validation de bout en bout

**Fait.** Depot du moteur llama.cpp b11375 (SHA-256 verifie), copie du modele
`Llama-3.2-1B-Instruct-Q4_K_M.gguf` (770 Mo, SHA-256 verifie), ecriture du YAML modele et des lanceurs.

**Tests reels (conditions physiques).**
- `llama-server.exe` : `/health` OK en 2 s ; `/v1/chat/completions` -> « Hello. ».
- `local-ai.exe` + bridge : `GET :8080/v1/models` -> `["llama-3.2-1b-instruct"]` ;
  `POST :8080/v1/chat/completions` -> « Hello, how can I assist you? » ; streaming SSE OK.
- Arret : `taskkill /T /F` -> **zero zombie**, ports liberes.

## Entree 08 — 2026-10-03 — Installeur maitre et Definition of Done

**Fait.**
- Ecriture de `install_localai_win.py` v1.1.0 : mono-bloc, `LOCALAI_DEPLOY_CODE = r'''…'''`
  (18 014 caracteres, **zero** `'''` interne), `archive_installer()` en **toute premiere** instruction
  de `main()`, triple validation AST, deploiement **transactionnel** (`LocalAI.new` -> `LocalAI`),
  `manifest.json` (SHA-256), rollback en cas d'echec.
- Test ultime : **suppression complete de `LocalAI\`** puis `python install_localai_win.py` :
  le produit est integralement reconstruit (38 composants) et **refonctionne** (`/v1/models` + chat).
- Documentation complete produite : `INSTALLATION.md`, `PERIMETRE.md`, `JOURNAL.md`, `dev\CHANGELOG.md`,
  `dev\DECISIONS.md`, `dev\patch_integrity.log` ; boite noire `Installeur\` remplie.

## Entree 09 — 2026-10-03 — PHASE 2 (v1.2.0) : ouverture et reconnaissance

**Fait.**
- Lecture et acceptation du mandat d'evolution Phase 2 (fichier fourni `PHASE 2.rtf`). Objectif :
  incrementer la v1.1.0 vers la v1.2.0 (Python embarque, LiteLLM, backends multi-modaux, Model
  Manager, CLI wrapper, cloud offload BYOK) sans jamais casser l'acquis.
- Reconnaissance des sources : LocalAI v4.11.0 (inchange), whisper.cpp (v1.9.2 = cible du mandat,
  assets Windows `whisper-bin-Win32.zip`), stable-diffusion.cpp (`sd-...-bin-win-cpu-x64.zip`),
  kokoro-onnx (`model-files-v1.1`), Python 3.11.9 embed, LiteLLM (1.103.2).

**Decision.** Respecter l'ordre du mandat : Python embarque UNIQUEMENT pour LiteLLM/TTS ; le coeur
Go reste compile (interdiction de le passer en Python) ; backends multi-modaux en services HTTP separes.

## Entree 10 — 2026-10-03 — Telechargements et setup Python/LiteLLM

**Fait.** Telechargement de Python 3.11.9 embed, get-pip, whisper.cpp v1.9.2, stable-diffusion.cpp,
ggml-base.bin, kokoro-v1.1-zh.onnx + voices, avec verifications SHA-256. Extraction du Python embarque,
activation de `site`, bootstrap pip + `litellm[proxy]==1.103.2` + `kokoro-onnx` + `soundfile`.
Verifications : Python 3.11.9, litellm 1.103.2, kokoro-onnx 0.6.1, onnxruntime 1.30.0.

## Entree 11 — 2026-10-03 — Increment de l'installeur v1.2.0

**Fait.** Greffe de nouveaux templates (Run-LocalAI.bat, helpers PowerShell, model_manager.ps1,
tts_server.py, litellm_launch.py, complexity_router.py, litellm-config.yaml, cloud-keys.env, READMEs)
et de nouvelles fonctions (deploy_python/whisper/sd/tts, write_catalog, _check_ports, _stop_existing).
Corrections Section 12 : manifest `root` = chemin final, detection de ports, version 1.2.0.

## Entree 12 — 2026-10-03 — Bugs reels et auto-healing

**Anomalies corrigees (detail dans `dev\crash.log`) :** encodage Unicode LiteLLM, wrapper
`litellm.exe` pointant vers le mauvais Python, PYTHONPATH ignore (mode isole), nom de modele
upstream, 401 du coeur (LOCALAI_API_KEY), voix kokoro (liste), route whisper (--inference-path),
verrou de bascule (`_stop_existing`), doublons au `start`, orphelins Python, detection `.py`.

**Enseignement.** Le rollback transactionnel a reellement servi : lors d'un echec de verrou, le
produit existant est reste intact et le staging a ete supprime automatiquement.

## Entree 13 — 2026-10-03 — Validation finale Phase 2

**Tests reels.** Ports 8080/4000/8091/8093 UP ; chat coeur ; `local-llama` ; alias `smart` (routage) ;
STT whisper (discours de JFK) ; TTS kokoro (WAV ~140 Ko) ; CLI (start/stop/status/pull/list/backends/help) ;
`start` idempotent (aucun doublon) ; `stop` -> zero zombie, ports liberes.

**Bilan.** Phase 2 / v1.2.0 livree : ecosysteme d'inference local Windows multi-modal et route,
arborescence ouverte, traçabilite complete (`dev\crash.log`, `dev\BETA_TEST_REPORT.md`).

## Entree 14 — 2026-10-03 — PHASE 3 (v1.3.0) : ouverture et reconnaissance materielle

**Fait.** Lecture et acceptation du mandat Phase 3 (fichier fourni `PHASE 3.rtf`). Reconnaissance
materielle decisive : **NVIDIA GTX 970M (Maxwell, 6144 Mo, driver 527.41)**, Intel i7-6700HQ (4c/8t),
31,9 Go de RAM ; `nvidia-smi` present ; `vulkan-1.dll` present ; `rocm-smi` absent ; `cudart64_12.dll` absent.

**Decision.** Implementer la detection multi-constructeur, la selection de variante llama.cpp et le
calcul automatique des parametres, avec repli systematique (GPU -> Vulkan -> CPU).

## Entree 15 — 2026-10-03 — Test decisif CUDA et bascule Vulkan

**Fait.** Telechargement et test des variantes b11375 : cpu, vulkan, cuda (+ cudart). Le binaire CUDA
s'execute mais echoue a l'inference : `CUDA error: invalid device function` -> les prebuilds ne
contiennent pas `sm_52` (Maxwell).

**Resultat.** Bascule sur **Vulkan** : inference reussie, **GPU 85-99 %**, **70,5 tok/s** contre
**10,7 tok/s** en CPU (mesure initiale). Le chantier GPU est donc viable via Vulkan.

**Pourquoi.** Conformement a la Section 15.4 du mandat (blocage -> documenter + contournement + poursuivre).

## Entree 16 — 2026-10-03 — Implementation GPU, auto-healing et validation

**Fait.** Greffe dans l'installeur : `hw_profile.ps1` (detection + calcul + JSON), `engine_select.ps1`
(bascule de variante), `bench.ps1` (tokens/s), variantes dans `backends\llama-cpp\variants\`,
commandes CLI `profile/optimize/benchmark/set-profile`, securite VRAM, et selection de provider ONNX
pour le TTS.

**Anomalies corrigees (detail dans `dev\crash.log`) :** collision `$Model`/`$model` (PowerShell
insensible a la casse), DirectML inutilisable (`ConvTranspose`), variante CUDA inexploitable sur Maxwell.

**Tests reels.** `profile`, `set-profile soft/hard`, `optimize` ; benchmark CPU **14,91 tok/s** vs GPU
**71,41 tok/s** (≈4,8x) ; usage GPU verifie par `nvidia-smi` ; VRAM liberee a l'arret (1245 -> 652 Mo) ;
QA multi-modale sans regression ; `stop` -> zero zombie.

**Bilan.** Phase 3 / v1.3.0 livree : portage Windows natif **optimise GPU**, arborescence ouverte,
replis automatiques documentes, traçabilite complete.

## Entree 17 — 2026-10-03 — PHASE 4 (v1.4.0) : RAG local et Agent Hub

**Fait.** Lecture du mandat (`PHASE 4.rtf`). Choix technique structurant valide par l'experience :
le moteur llama.cpp expose **`/v1/embeddings`** (avec `--pooling mean`), ce qui fournit de **vrais
embeddings neuronaux sans modele supplementaire**. Decision : instance d'embeddings dediee (port 8094)
demarree a la demande par le pipeline RAG.

**Implemente.** Extraction multi-format (texte/code/PDF/Word/Excel), chunking 2048 car. a 10 % de
recouvrement, index **a plat** (`.npy` + `.jsonl` + manifest), recherche **cosinus NumPy pure**
(faiss proscrit), packages isoles (`pip --target`) dans `runtime\packages`, modele virtuel unique
`localai` + Token Saver (saturation de contexte, preference cloud, journal `logs\routing.jsonl`),
CLI `index` / `rag-query` / `proxy-logs` / `key-set`.

**Anomalies corrigees (detail dans `dev\crash.log`, categories RAG_INGEST/VECTOR_DB/PROXY_GATEWAY) :**
pooling manquant, ABI lxml cp311, quoting de `rag-query`, deux en-tetes de templates avales par des
patchs mal ancres, en-tete de gabarit `keys.env`.

**Verification reelle.** Corpus 5 formats -> 5 chunks x 2048 dims ; recherche top-5 coherente ;
routage virtuel (court/complexe/contexte sature) ; bascule cloud sur cle presente ; arret zero zombie
et VRAM liberee (442 Mo).

**Bilan.** Phase 4 / v1.4.0 livree : ecosysteme local Windows **avec memoire documentaire** (RAG) et
**gateway intelligente** (Agent Hub), toujours 100 % natif, sans Docker ni WSL.

---

## v1.4.1 — micro-increment de finition (2026-10-03)

**Mandat.** Garde-fous operationnels (watchdog VRAM), modele image leger (< 2 Go), documentation
CUDA Maxwell (sm_52+), QA bout-en-bout. Doctrine transactionnelle inchangee.

**Livre.**
- `scripts\vram_watchdog.py` : daemon VRAM (2 s), seuils **alerte < 15 %** / **critique < 5 %** /
  **reprise > 20 %**, alerte -> `logs\vram.log` + `dev\crash.log` (categorie `GPU_VRAM`),
  action preventive -> relance du moteur en **CPU pur `-ngl 0`** (`data\vram-action.json`).
- `scripts\vram_status.ps1` + `Run-LocalAI.bat vram-status` ; `start --no-watchdog`.
- Catalogue : **`sd-turbo-light`** (SD-Turbo Q8_0, **1,88 Go**, SHA-256 verifie, GGUF chargeable par
  `sd-server`) ; le lanceur le prefere au safetensors de 5,21 Go.
- `INSTALLATION.md` sections 30-32 : watchdog, CUDA Maxwell (`invalid device function`, CMake
  `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release`), integration via
  `variants\cuda\custom-build.txt` + `optimize` (detection `cuda_custom_build`), modele leger.

**Anomalie trouvee et corrigee (auto-healing).** `data\llama-cmd.json` etait ecrit avec un **BOM UTF-8**
par `Set-Content -Encoding UTF8` ; `json.load` refusait le BOM et l'action preventive se degradait
proprement (`applied:false`). Correctif double : lecture `utf-8-sig` cote Python **et** ecriture via
`[IO.File]::WriteAllText(..., UTF8Encoding($false))` cote PowerShell. Re-test : `applied:true`.

**Verification reelle.** `vram-status` (6144 Mo, 90,5 % libre, seuils) ; alerte + critique simules et
journalises ; action preventive executee (relance `-ngl 0`, chat HTTP 200 « Bonjour ») ;
`pull sd-turbo-light` (1930 Mo, `HASH OK`) ; image generee par le modele leger ; zero zombie a l'arret.

**Bilan.** Phase 4.1 / v1.4.1 au vert : le portage sait desormais **surveiller sa VRAM**, **s'auto-proteger**
et **produire des images avec un modele leger**, avec la voie **CUDA Maxwell documentee**.

---

## v1.5.0 & v1.6.0 — grande campagne a jalons etanches (2026-10-03)

**Protocole.** JALON 0 (sauvegarde ante-execution) -> JALON 1 (beta-test de rupture de l'existant)
-> JALON 2 (implementation v1.5.0) -> JALON 3 (beta-test v1.5.0) -> JALON 4 (implementation v1.6.0)
-> JALON 5 (beta-test final et gel). Auto-regulation activee pour subdiviser le JALON 2 en
**v1.5.0a (Vision)** et **v1.5.0b (MCP)**, chaque sous-etape deployee et validee avant la suivante.

**JALON 1 -- stabilisation prealable.** Beta-test de rupture de la v1.4.1 : **7/7 OK** apres correction
d'un **bug residuel reel** -- le gateway LiteLLM renvoyait **HTTP 500** (`ModuleNotFoundError: prisma`,
handler d'authentification) au lieu de **401** sur requete non authentifiee. Correctif : dependance
officielle `prisma` + routine `ensure_proxy_deps()` **verifiee** au deploiement (D-028).

**JALON 2/3 -- v1.5.0 : vision locale et protocole MCP.**
- Catalogue a **deux URLs par modele multimodal** (GGUF + projecteur `mmproj` dedie), acquisition
  **atomique** « les deux fichiers ou rien », injection `--mmproj` dans `llama-server`.
- Nouveau **moteur VISION** (8095) ; **CPU par defaut** car le chemin `mtmd` provoque un
  `Vulkan device lost` sur Maxwell (D-029). Legende d'image reelle obtenue.
- **Images integrees aux metadonnees de l'index RAG** (dimensions/format/octets, sans dependance
  externe).
- **Passerelle MCP** batie sur le **SDK officiel** (spec 2024-11-05, JSON-RPC 2.0 stdio), serveur local
  `localai` a **5 outils**, declaration centralisee dans `config\mcp-settings.json` (D-030).
  `mcp-list`, `mcp-call`, `mcp-test` (VERDICT VERT).
- Aucune reimplementation du protocole : le SDK est **consomme** (fourni par `litellm[proxy]`, repli
  isole `runtime\mcp\packages`).

**JALON 4/5 -- v1.6.0 : GraphRAG par LLM et failover SSE.**
- **GraphRAG** : extraction NER/RE **deleguee au LLM local** (prompts structures, `T=0`), **aucune
  heuristique regex** ; parsing tolerant (recuperation des objets complets si sortie tronquee) ;
  **interdependances structurelles** du code (imports) en aretes deterministes ; serialisation a plat
  dans `runtime\storage\graph_db.json`. Mesure : **22 noeuds / 50 aretes** (42 LLM + 8 structurelles).
- **Failover SSE** (proxy 8081) : **bufferisation complete avant envoi** pour les requetes
  sensibles/agent (rejeu silencieux, **aucune coupure** visible) et **failover sur erreur avant le
  premier token** pour le streaming de routine ; chaine deterministe `core-local` -> `vision-cpu` ->
  `cloud`. **Panne reelle testee** (kill du llama-server primaire) : decision en **162-367 ms**,
  client en HTTP 200 avec flux complet.
- CLI `graph-index` / `graph-show` ; configuration `config\failover.json` preservee (D-034).

**Bilan.** Versions **v1.5.0** et **v1.6.0** livrees, validees en conditions physiques reelles et
**gelees**. Le portage est desormais multi-modal (texte, vision, image, audio), outille (MCP), memoire
(RAG + graphe de connaissances) et **resilient** (watchdog VRAM + failover SSE). 100 % natif Windows,
sans Docker ni WSL.

---

## v1.7.0 & v1.8.0 — quantization, confidentialite, acceleration NPU (2026-10-03)

**Protocole.** JALON 0 -> JALON 1 (rupture de la v1.6.0 : **7/7 OK**, aucune anomalie) -> JALON 2
(v1.7.0, subdivise en **v1.7.0a Quantize** / **v1.7.0b Privacy**) -> JALON 3 -> JALON 4 (v1.8.0)
-> JALON 5 (validation finale et gel).

**v1.7.0 -- quantization et confidentialite.**
- **Quantization locale** : `llama-quantize.exe` integre a l'orchestrateur, 24 types, mode
  **asynchrone**, historique SHA-256 auditable. Mesure : **782 Mo (F16) -> 417 Mo (Q8_0)** en 2,4 s.
- **Filtre PII hybride (BEST-EFFORT)** : regex deterministes + **entropie de Shannon** + **NER local**.
  Masquage **reversible** (`[PII-TYPE-n]`), integre au **Token Saver** : masquage **avant tout
  debordement cloud**, demasquage de la reponse cote utilisateur. Drapeau `--no-pii-filter`,
  **audit** dans `dev\crash.log` (categorie `PRIVACY_FILTER`). Documente comme protection
  **non garantie a 100 %**.
- Verifie : debordement cloud simule -> **aucun secret original transmis**, reponse restauree.

**v1.8.0 -- acceleration universelle NPU.**
- **DirectML** (`onnxruntime-directml`) installe de maniere isolee : adresse **NPU Intel** et
  **NPU AMD XDNA2** sans SDK constructeur.
- **Repli CPU obligatoire** : si le pilote/materiel ne permet pas DirectML, bascule **automatique et
  transparente** sur CPU, **session preservee**, **avertissement console dans `dev\crash.log`
  (categorie `GPU_DETECT`)**. Scenario **verifie en conditions reelles** (machine sans NPU).
- **Sonde reelle** : modele ONNX authentique (`mnist-8.onnx`) -> inference effective sur le provider
  retenu. CLI `hardware-status` (repartition des charges) et `npu-probe`. Outil MCP deporte
  `localai_semantic_probe`.

**INCIDENT MAJEUR (D-037) -- la doctrine mise a l'epreuve.** Lors d'un deploiement, la bascule
transactionnelle a **detruit l'arbre de production** : elle **supprimait** l'ancien arbre **avant**
d'installer le nouveau, et un fichier verrouille (service encore actif) a fait echouer la suppression
a mi-chemin. Le rollback a de plus supprime le staging **neuf et complet**. Deux correctifs :
**(1) permutation par renommage** (`ecarter -> installer -> purger`, avec restauration de l'ancien en
cas d'echec) ; **(2) garde prealable** refusant toute reconstruction si un service est actif.
La garantie "aucune perte" est desormais assuree **par construction**. Le produit a ete reconstruit ;
seuls les modeles telecharges par l'utilisateur ont du etre re-acquis.

**Bilan.** **v1.7.0** et **v1.8.0** livrees, validees en conditions physiques reelles et **gelees**.
Le portage sait desormais **compresser ses propres modeles**, **proteger la confidentialite** de ses
requetes cloud et **adresser une couche d'acceleration materielle universelle** — avec un repli CPU
toujours disponible.




