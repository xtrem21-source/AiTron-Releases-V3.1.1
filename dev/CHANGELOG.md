# CHANGELOG.md — Historique des Versions

Format : `VERSION — DATE — RESUME`

## v3.1.3 — 2026-10-05 (CREATION DE LA RELEASE GITHUB v3.1.2)
**Release GitHub v3.1.2 publiee via `gh` CLI ; fallbacks bascules sur v3.1.2.**
- **Release GitHub v3.1.2** creee par ligne de commande (`gh`) dans `xtrem21-source/AiTron-Releases-V3.1.1`
  (l'interface web etait bloquee pour les gros fichiers) : assets `local-ai.exe` (195 156 992 o) et
  `cloud-proxy.exe` (19 915 776 o), byte-identiques a la v3.1.1 (D-052).
- **URLs de fallback** basculees de `download/v3.1.1/` vers `download/v3.1.2/` (SHA-256 inchanges).
- **Version** : `__version__ = "3.1.3"` ; manifeste `installer_version = v3.1.3`.
- **Tests** : T1 (release verifiee : 2 assets, tailles 186/19 Mo) ; T2 (installation en racine vierge ->
  telechargement GitHub v3.1.2 + SHA-256 + garde-fou MZ -> deploiement) ; T3 (coherence v3.1.2 : 0 BOM,
  CLI bilingue, failover SSE, vault, zero zombie). Voir `dev\BETA_TEST_REPORT.md` §52.
- **Garde-fou PE "MZ"** conserve.

## v3.1.2 — 2026-10-05 (INTEGRATION DES BINAIRES GITHUB RELEASES)
**Les binaires du coeur se telechargent desormais depuis une release GitHub perenne.**
- **URLs GitHub Releases** (D-051) : `FALLBACK_LOCAL_AI_URL` / `FALLBACK_CLOUD_PROXY_URL` pointent vers
  `github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.1/` — remplacent les URLs
  temporaires `transfert.free.fr` qui servaient une page HTML.
- **SHA-256 integres** (calcules sur les binaires telecharges, strictement identiques aux locaux) :
  `local-ai.exe` = `0F55C483...` (195 156 992 o) ; `cloud-proxy.exe` = `BFCB2804...` (19 915 776 o).
- **Garde-fou PE "MZ" CONSERVE ET RENFORCE** : applique a TOUT `.exe` telecharge, avec ou sans SHA
  attendu (un binaire Windows valide commence par `MZ`).
- **Erreurs actionnables** : rejet + nettoyage du `.part` ; cascade `build\out\` -> staging -> produit
  deploye ; message explicite (chemins + URL + SHA) si toutes les sources echouent.
- **Tests** : Test 1 (machine vierge -> telechargement GitHub + SHA + MZ -> deploiement 87 composants) ;
  Test 2 (SHA errone -> rejet + `.part` nettoye) ; Test 3 (URL invalide -> cascade) ; Test 4 (coherence
  v3.1.1 : 0 BOM/41 fichiers, CLI bilingue, failover SSE, vault, zero zombie). Voir
  `dev\BETA_TEST_REPORT.md` §51.
- **Increments** : `__version__ = "3.1.2"` ; manifeste `installer_version = v3.1.2`.
- **Anomalie close** : `FALLBACK_DOWNLOAD` (URLs HTML de v3.1.1) **resolue** par l'usage de GitHub Releases.

## v3.1.1 — 2026-10-05 (PORTABILITE TOTALE de l'installeur + fallbacks de telechargement)
**L'installeur ne depend plus d'aucun chemin en dur : il s'installe la ou il est.**
- **Detection dynamique du repertoire** : `SANDBOX` est derive du dossier du script (ou de
  `--root <chemin>`) ; l'ancien chemin en dur `G:\V1\LocalAI-Projet\` est supprime. Fonctionne sur
  cle USB, `C:\AiTron\`, `D:\...`, partage reseau (D-049).
- **Creation automatique** de l'arborescence (`Installeur\`, `dev\`, `dev\old\`, `log\`, `build\`)
  au premier lancement dans un dossier neuf (`_ensure_sandbox_tree()`).
- **Fallbacks de telechargement** `local-ai.exe` / `cloud-proxy.exe` (D-050) : cascade
  `build\out\` -> `dev\old\test_dynamique\AiTron\` -> produit deploye -> telechargement
  (`FALLBACK_LOCAL_AI_URL`, `FALLBACK_CLOUD_PROXY_URL`, SHA-256 verifie, `.part` atomique).
  URLs TEMPORAIRES ; garde-fou d'integrite PE `MZ` si aucune somme attendue (SHA vide).
- **Tests** : 5 installations reelles (racine courante, `C:\AiTron-Test`, `--root
  D:\AiTron-Root-Test`, USB `E:\AiTron-Portable`, fallback) ; 87 composants ; inference reelle
  (`BONJOUR`) ; 15/15 controles unitaires + garde MZ ; 0 BOM sur 41 fichiers ; arret propre
  (0 processus, 0 port). Voir `dev\BETA_TEST_REPORT.md` §50.
- **Increments** : `__version__ = "3.1.1"` ; manifeste `installer_version = v3.1.1`.
- **Limites** : les URLs de fallback servent actuellement une page HTML -> a remplacer par des liens
  binaires directs ET renseigner le SHA-256 pour une installation croisee de bout en bout.

## v3.1.0 — 2026-10-04 (AUDIT DYNAMIQUE : CERTIFICATION VALIDEE AU VERT apres 2e passe)
**Cloture (2e passe, autorisee par le proprietaire) : anomalie A-12 resolue.**
- 920 cles FR traduites (admin, auth, importModel, media, chat, home, models) -> IHM servie couverte a
  100,0 % (1 597 / 1 597 cles EN), 14 fichiers FR, 1 611 cles ; coeur `local-ai.exe` recompile.
- D12 : derniers libelles francais fixes en mode EN corriges ; table de traduction CLI = 207 entrees.
- Staging redeploye avec `--prev` vers la sauvegarde v3.0.0 (installation #11) : 13/13 controles,
  38 executions CLI sans erreur, arret propre (0 processus, 0 port TCP, 0 UDP 47653).
- `dev\test_dynamique\` deplace dans `dev\old\` (charte 2.4). Certificat refuse archive dans `dev\old\`.
- Limites : rendu navigateur non verifie ; PDF/DOCX/XLSX/images RAG non rejoues ; traduction sans relecture tiers.
- Le produit stable `AiTron\` reste en v3.0.0 jusqu'au prochain lancement de l'installeur depuis la racine.

### Premiere passe (historique, certification refusee a l'epoque)
**Audit physique en staging isole (dev\test_dynamique\) ; 11 defauts corriges, 1 anomalie restante.**
- **Isolation** : l'installeur lance depuis `dev\test_dynamique\` deploie `AiTron\` et `log\` DANS ce
  dossier et n'arrete plus (taskkill) les processus du produit stable de la racine.
- **Corrections** : D1 `lang.tmp` partage (7/8 en echec) ; D2 cp1252 avant latin-1 (RAG) ; D3 vault
  `seal` relit le disque avant de supprimer le clair ; D4 `SANDBOX` non injecte (1re installation) ;
  D5 PII sur toute route cloud ; D6-D8 traduction de la sortie CLI en mode EN (~190 libelles,
  `i18n.py run`) ; D7 `stop.bat` ne tue pas l'enveloppe ; D9/D9b failover en flux avant le 1er evenement
  SSE ; D10 `rag-query` entre guillemets ; D11 plus de BOM (3 scripts PowerShell).
- **IHM** : francais ajoute (selecteur + 10 fichiers, 685 cles) ; `local-ai.exe` recompile avec l'IHM
  embarquee (ancien binaire : `dev\old\local-ai_v3.0.0_pre-fr.exe`).
- **Verdict** : 13 controles sur 13 conformes, mais couverture FR de l'IHM = 42,4 % -> anomalie A-12
  (923 cles) -> **CERTIFICATION REFUSEE**. Voir `CHECK_DE_CONTRÔLE_FINAL.log`.
- Le produit stable `AiTron\` reste en v3.0.0 (non redeploye).


## v3.0.0 — 2026-10-03 (PHASE V3 Finale : identité AiTron V3 + audit d'autonomie)
**Le produit porte désormais son nom — et il prouve qu'il peut renaître de zéro.**
- **Renommage officiel** : `install_localai_win.py` → **`install_AiTron_v3.py`** (racine de la sandbox) ;
  produit `LocalAI\` → **`AiTron\`** ; staging `AiTron.new` ; `LOCALAI_DEPLOY_CODE` →
  **`AITRON_DEPLOY_CODE`** ; variables d'environnement `AITRON_*` (les constantes de **provenance
  amont** `LOCALAI_VERSION`/`LOCALAI_TAG`/`LOCALAI_URL`/`LOCALAI_SHA256` gardent leur nom).
- **Le moteur garde son nom** : **`local-ai.exe`** (195 Mo) reste inchangé — c'est la technologie ; seul
  le **produit** s'appelle **AiTron V3**. `Run-LocalAI.bat` et l'identifiant de modèle `localai` sont
  également conservés.
- **Manifeste enrichi** : `"product": "AiTron V3 (portage natif, sans Docker/WSL)"`,
  **`"fork_of": "LocalAI (https://github.com/mudler/LocalAI)"`**, **`"license": "MIT"`**.
- **`CHARTE.md`** : `Projet : AiTron V3`, `Livrable : install_AiTron_v3.py`.
- **Avertissement de transparence** dans les trois documents d'installation : *AiTron V3 est un fork
  indépendant de LocalAI (licence MIT) ; il n'est aucunement affilié au projet LocalAI officiel.*
- **Migration d'héritage** : si `AiTron\` est absent mais `LocalAI\` présent, l'installeur **reprend
  automatiquement l'héritage historique** — aucune donnée utilisateur perdue.
- **AUDIT D'AUTONOMIE MONO-BLOC** : produit **supprimé physiquement** puis **entièrement reconstruit**
  par le seul installeur (nouvelle option **`--prev <chemin>`**) → moteur, modèle 807 694 464 o, index
  RAG, 4 backends (`llama-cpp`, `stable-diffusion`, `whisper-cpp`, `tts`), configurations et
  documentations **tous restaurés**. **L'installeur est auto-suffisant.**
- **Bannière** : `=== AiTron - portage Windows natif (sans Docker ni WSL) (v3.0.0) ===`.
- **Livrables racine** : `ANOMALIES_NON_RÉSOLUES.log` (format standardisé, 8 entrées — **limites amont /
  caractéristiques documentées**, aucun défaut de notre code non résolu) ; `INSTALLATION.md` (guide
  autonome bilingue) + `INSTALLATION.fr.md` + `INSTALLATION.en.md`.
- **Boîte noire** : les archives suivent le nouveau nom (`install_AiTron_v3_*.py.txt`).
- **Mesures** : **AST VERT**, **87 composants**, **zéro zombie**, 0 port TCP/UDP.

## v2.1.1 — 2026-10-03 (PHASE 2.20 : internationalisation FR/EN)
**Interface bilingue à trois couches, avec repli embarqué garanti et bascule à chaud.**
- **Couche 1 — embarquée** : dictionnaire `TRANSLATIONS` **dans** `scripts\i18n.py` = **source de vérité
  ultime**, toujours disponible même si tous les fichiers externes manquent.
- **Couche 2 — JSON externe** : `i18n\fr.json` / `i18n\en.json`, **générés à l'installation**, qui
  **surchargent** l'embarqué clé par clé. **Une personnalisation utilisateur n'est jamais écrasée.**
- **Couche 3 — `I18N_REV`** : quand la révision change, seules les clés de documentation (`help_*`,
  `tip_*`) sont **rafraîchies** depuis l'embarqué ; les autres restent sous contrôle utilisateur.
- **Aiguillage `tr(key)`** ; langue active : `LOCALAI_LANG` → `config\lang.json` → défaut `fr`.
- **CLI bilingue** : `i18n\_fr.bat` / `i18n\_en.bat` (**UTF-8 sans BOM**) chargés **dynamiquement** par
  `Run-LocalAI.bat` — **bascule sans redémarrage**. `chcp 65001 >nul` ajouté au wrapper pour préserver
  les accents. La **bannière** de démarrage suit aussi la langue active.
- **Commandes** : `lang`, `lang fr|en` (bascule à chaud + écriture de `config\lang.json`), `lang list`,
  `i18n-status`, `i18n-test`.
- **Documentation double** : `INSTALLATION.fr.md`, `INSTALLATION.en.md` ; `INSTALLATION.md` racine =
  **aiguillage** + essentiel autonome bilingue.
- **Repli sûr** : JSON absent/illisible/**invalide** → repli **silencieux** sur la couche 1
  (catégorie `I18N` dans `dev\crash.log`). **Aucun plantage** possible à cause d'un fichier de langue.
- **Anomalies corrigées** : `__version__` → **`__VERSION__`** (convention du namespace de déploiement) ;
  namespace d'exécution de `I18N_PY` doté de `__file__` ; `json` non importé dans le namespace de
  déploiement → **import local**. *Symptôme initial : fichiers `i18n\*.bat` vides (0 octet), sans échec
  d'installation visible — d'où la règle : **lire le journal d'installation ligne à ligne**.*
- **Mesures** : `i18n-test` → **VERDICT VERT** ; `lang en` → aide et bannière **instantanément en
  anglais** ; `lang fr` → retour immédiat ; **AST VERT** ; **88 composants**.

## v2.1.0 — 2026-10-03 (JALON 6&7 : inférence fédérée RPC + découverte réseau)
### v2.1.0a — Découverte réseau des nœuds RPC
**Le portage sait trouver ses pairs — sans jamais réinventer le transport.**
- **`scripts\peer_discovery.py`** : découverte **UDP broadcast en pur Python, zéro dépendance**
  (pas de `zeroconf`). Deux messages seulement (`query` / `reply`) ; **aucune donnée d'inférence
  ne transite** — la découverte ne sert qu'à identifier les adresses IP.
- **Démon d'annonce** lancé avec la pile (désactivable par `--no-peers`), arrêt propre avec elle.
- **CLI** : `peer-status` (IP, port, latence, **joignabilité**), `peer-scan`, `peer-test` (autotest du
  protocole sur boucle locale), `peer-rpc-arg` (argument `--rpc` généré).
- **Péremption** des pairs : 90 s (TTL) — un nœud muet disparaît tout seul.

### v2.1.0b — Routage fédéré RPC
**Quand l'hôte sature, le calcul se déporte — via le RPC natif de llama.cpp.**
- **`vram_watchdog.py`** : sur VRAM critique, **escalade** — (1) **routage fédéré** : relance du moteur
  avec l'argument exact **`--rpc <IP>:<Port>`** (option réelle de `llama-server`) ; (2) à défaut,
  **repli CPU pur** `-ngl 0`.
- **Garde-fou essentiel** : aucun `--rpc` n'est injecté vers un nœud **injoignable** (test TCP court) —
  sur un poste isolé, le calcul reste **100 % local** et l'inférence n'est jamais cassée.
- **Traçabilité** : catégorie `FEDERATION` dans `dev\crash.log` ; `data\vram-action.json` distingue
  `routage-federe (--rpc)` de `relaunch-llama-cpu (ngl=0)`.
- **Anomalie de nommage documentée** : l'amont livre **`ggml-rpc-server.exe`** (et non `rpc-server.exe`
  comme cité au mandat) — port par défaut **50052**. Même famille que l'anomalie A24 du décodage
  spéculatif : toujours vérifier les noms réels de la distribution amont.
- **Clause matérielle** : support **NPU AMD XDNA2 via DirectML = expérimental et non fonctionnel**
  (DirectML limite son NPU à Intel/Qualcomm) → l'architecture AMD s'appuie sur le **repli CPU NumPy**.

## v2.0.0 — 2026-10-03 (JALON 4&5 : espace hermétique + profil apprenant)
### v2.0.0a — Espace hermétique

**Chiffrement AES-256-GCM de la zone sémantique, clé dérivée et jamais stockée.**
- **`scripts\vault.py`** : chiffrement **authentifié** AES-256-GCM de `runtime\rag\` et
  `runtime\storage\` (`.npy`, `.json`, `.jsonl`, `.bin`).
- **Clé jamais écrite sur disque** : dérivée à la volée par **PBKDF2-HMAC-SHA256**
  (**390 000 itérations**, **sel aléatoire 16 o** dans l'en-tête), à partir d'un **mot de passe
  saisi en console** (masqué) — ou `--password-env` pour l'automatisation (documenté comme moins sûr).
- **Cycle sûr** : `seal` chiffre puis **supprime le clair** ; `unseal` restaure en **conservant le
  conteneur**. **Vérification immédiate de réversibilité** avant toute suppression — aucune perte
  possible.
- **CLI** : `vault-status`, `vault-seal`, `vault-unseal`, `vault-test`.
- **Clause de transparence** documentée (INSTALLATION §45, D-040) : portée **strictement au repos**,
  **effacement RAM non garanti** (ramasse-miettes Python, meilleur effort), **mot de passe oublié =
  données perdues** (aucune porte dérobée).
- **Mesures** : autotest **VERT** (intégrité identique, mauvais mot de passe refusé) ; **index RAG
  réel** → cycle scellé/ouvert **4/4 empreintes identiques → ZÉRO CORRUPTION** ; `rag-query`
  fonctionnel après le cycle.

### v2.0.0b — Profil apprenant continu
**Le poste s'auto-règle d'après ses mesures réelles ; le retour aux profils d'usine est garanti.**
- **`scripts\learn_profile.py`** : analyse la **télémétrie réelle** (`logs\history.jsonl`,
  `logs\vram.log`, `logs\failover.jsonl`, `config\hardware-profile.json`) et écrit `config\profile.json`.
- **Seuil d'alerte ancré sur le MINIMUM de VRAM libre réellement observé** (+5 pts), critique = alerte − 8,
  reprise = alerte + 10, **bornés** (8–25 / 3–12 / 15–40 %) : aucun réglage absurde possible.
- **`-ngl`** conservé par défaut, **réduit de 20 %** seulement si des **évictions critiques** ont été
  enregistrées (preuve de saturation réelle).
- **Application À CHAUD** : le watchdog VRAM **relit** `config\profile.json` toutes les 5 s — nouveau
  réglage adopté **sans redémarrage**. *Preuve : watchdog démarré en `15/5/20` → `25/12/35` appliqués à chaud.*
- **`reset-profile [soft|normal|hard]`** (garde-fou QA) : efface le profil appris **et applique
  immédiatement** les valeurs d'usine choisies. *Preuve : `25/12/35` → `20/10/30` en quelques secondes.*
- **Persistance** : `config\profile.json` + `logs\history.jsonl` entrent dans la **règle d'or de
  l'héritage** → l'apprentissage **survit aux réinstallations** (vérifié après redéploiement).
- **CLI** : `learn-profile`, `profile-status`, `profile-observe`, `reset-profile`.
- **Repli sûr** : données insuffisantes (< 2 observations) ou fichier absent → **profil d'usine**.
- **Traçabilité** : catégorie `PROFILE_LEARN` dans `dev\crash.log`.
- **Mesures (GTX 970M 6144 Mo)** : VRAM libre observée 61,3–62,6 % → alerte apprise **25 %**, `ngl` **99**
  conservé (0 éviction) ; **AST VERT**, 83 composants, zéro zombie.

## v1.9.0 — 2026-10-03
**Speculative Decoding TEXT-ONLY (implémenté, fonctionnel, rendu OPT-IN après mesure).**
- **Paire à tokenizer partagé** : `qwen2.5-1.5b-instruct` (1066 Mo, principal) +
  `qwen2.5-0.5b-instruct` (draft, 469 Mo) — acquisition **atomique** (principal + draft, les deux
  ou rien) via le catalogue et le gestionnaire de modèles.
- **Injection des drapeaux** dans `llama-server.exe` : `--model-draft <draft.gguf>` +
  `--spec-draft-n-max 8` + `--spec-draft-n-min 2`.
  ⚠️ **Déviation documentée (A24)** : le mandat citait `--draft-max`/`--draft-min`, **retirés** par
  llama.cpp (le moteur refusait alors de démarrer) ; les noms réellement supportés par le binaire
  installé (b11375) sont `--spec-draft-n-max`/`--spec-draft-n-min`.
- **Règle TEXT-ONLY** : le draft n'est **jamais** injecté avec un projecteur multimodal (`--mmproj`) —
  limitation upstream de llama.cpp.
- **Garde VRAM** : le lancement n'est autorisé que si la VRAM libre couvre *principal + draft +
  cache KV couplé + marge*, sinon **repli silencieux sans draft** (`SPEC_DECODE`).
- **Cohérence de tokenizer** : lorsqu'elle est présente, la paire déclarée au catalogue devient le
  **moteur principal** (A25).
- **Mesure réelle** : 160 tokens / 7,48 s = **21,39 tok/s avec draft** vs 160 tokens / 7,35 s =
  **21,76 tok/s sans** → **aucun gain sur profil GPU-bound**. Décision **D-039** : fonctionnalité
  **OPT-IN** (`LOCALAI_SPEC=1`), la garde VRAM et la règle TEXT-ONLY restant en vigueur.
- **CLI** : `spec-status`, `spec-test`.
- Manifest : version globale **v1.9.0**.

## v1.8.0 — 2026-10-03
**Routage hétérogène NPU (DirectML unifié) + repli CPU obligatoire.**
- **Accélération universelle Windows** : le provider **`onnxruntime-directml`** est installé de manière
  isolée dans le Python embarqué (routine `ensure_onnx_directml()` **vérifiée**, avec re-contrôle).
  DirectML adresse **NPU Intel** et **NPU AMD Ryzen AI (XDNA2)** sans SDK constructeur, via la couche
  de virtualisation de calcul native de Windows.
- **Accélérateur sémantique** (`scripts\onnx_provider.py`) : détection déterministe du provider,
  priorité DirectML puis **repli CPU automatique et transparent** ; les tâches d'extraction
  **légères** (NER du filtre PII, **outils MCP légers**) y sont adressées. Le moteur llama.cpp reste
  le moteur principal (GPU Vulkan).
- **Repli QA consigné** : si DirectML est indisponible (pilote/matériel), bascule CPU **sans
  interruption de session** et **avertissement explicite** dans `dev\crash.log`
  (catégorie **`GPU_DETECT`**).
- **Sonde réelle** : un **modèle ONNX authentique** (`mnist-8.onnx`, 25 Ko, SHA-256 vérifié) est
  déployé dans `runtime\onnx\` ; `npu-probe` exécute une **inférence effective** sur le provider
  retenu (validation matérielle, pas seulement une détection d'API).
- **CLI** : `hardware-status` (répartition exacte des charges : moteur principal GPU vs tâches
  sémantiques NPU/CPU, ports et PID par service), `npu-probe`.
- **Outil MCP déporté** : `localai_semantic_probe` (6ᵉ outil) exécute la sonde sur l'accélérateur.
- ⚠️ **INCIDENT MAJEUR corrigé (D-037)** : la bascule transactionnelle supprimait l'arbre de
  production **avant** d'installer le nouveau ; un fichier verrouillé a provoqué une **perte de
  l'arbre**. Correctifs : **permutation par renommage** (`LocalAI`→`.old`→remplacement→purge
  best-effort, avec restauration de l'ancien en cas d'échec) + **garde préalable**
  (`_guard_running_services()`) qui **refuse** la reconstruction si la pile tourne encore.
- Manifest : version globale **v1.8.0** (80 composants).

## v1.7.0 — 2026-10-03
**Quantization locale + filtre de confidentialité PII hybride (BEST-EFFORT).** Exécuté en deux
sous-étapes étanches (v1.7.0a Quantize, v1.7.0b Privacy — cf. D-035).
- **Quantization adaptative** : `Run-LocalAI.bat quantize <modele_f16.gguf> <type>` s'appuie sur le
  binaire `llama-quantize.exe` du portage. 24 types supportés, sortie par défaut
  `models\<nom>-<type>.gguf`, mode **asynchrone** (`--async`), journal `logs\quantize.log` et
  historique auditable `data\quantize-history.jsonl` (tailles, ratio, SHA-256, durée).
  *Mesure : 782 Mo (F16) → 417 Mo (Q8_0, 8,50 BPW) en 2,4 s.*
- **Filtre PII hybride** (3 niveaux) : **regex déterministes** (e-mails, IPv4/IPv6, `sk-`, `ghp_`,
  `AKIA`, `xox`, JWT, PEM, cartes Luhn) + **entropie de Shannon** (mots de passe/secret custom) +
  **NER local léger** via le moteur local. Masquage réversible `[PII-TYPE-n]` avec **démasquage
  automatique de la réponse**.
- **Intégration Token Saver** : `config\complexity_router.py` masque **avant tout débordement cloud**
  (une requête locale n'est jamais masquée) et restaure la réponse côté utilisateur.
- **Transparence** : documenté comme protection **BEST-EFFORT, non garantie à 100 %** (INSTALLATION
  §40) ; drapeau `start --no-pii-filter` (+ `LOCALAI_PII_FILTER=0`) ; **audit** de chaque masquage
  dans `dev\crash.log` catégorie **`PRIVACY_FILTER`**.
- **CLI** : `quantize`, `quantize list`, `privacy-test [--with-ner]`, `privacy-levels`.
- Manifest : version globale **v1.7.0**.

## v1.6.0 — 2026-10-03
**GraphRAG par LLM local + failover SSE déterministe.**
- **GraphRAG** : `scripts\graph_rag.py` délègue l'**extraction d'entités et de relations au LLM local**
  (`llama-server /v1/chat/completions`, prompt exigeant un **tableau JSON strict**, `temperature=0`) —
  **aucune heuristique regex** (D-032). Parsing tolérant (premier tableau équilibré + nettoyage),
  échecs comptés sans crash. Les **interdépendances structurelles du code** (imports/références par
  langage) complètent le graphe en arêtes déterministes `kind:"structural"`.
  Sérialisation **à plat** dans `runtime\storage\graph_db.json` (nœuds typés + degrés + provenance).
- **CLI** : `graph-index <dossier>`, `graph-show` ; outil MCP `localai_graph_show` opérationnel.
- **Failover SSE** : `scripts\failover_proxy.py` (port 8081) — **bufferisation complète avant envoi**
  pour les requêtes sensibles/agent (aucun flux interrompu possible : rejeu silencieux en cas
  d'erreur) et **failover sur erreur avant le premier token** pour le streaming de routine (D-033).
  Chaîne déterministe **primaire → secondaire local (CPU) → cloud (`config\cloud-keys.env`)**, sonde
  TCP bornée à **1.5 s**, journal d'audit `logs\failover.jsonl` (`route`, `ms_decision`, `failover`).
- **Configuration** : `config\failover.json` (politique de bufferisation, routes, seuils) — préservé
  entre réinstallations comme `config\mcp-settings.json` (D-034).
- Manifest : version globale **v1.6.0**.

## v1.5.0 — 2026-10-03
**Vision locale corrigée + protocole MCP sécurisé.** Exécuté en deux sous-étapes étanches
(v1.5.0a Vision, v1.5.0b MCP — cf. D-031).
- **Vision multi-modale** : le catalogue encapsule désormais **deux URLs** par modèle multimodal
  (GGUF principal + **projecteur `mmproj` dédié**) : `qwen2-vl-2b` (942 Mo + 676 Mo) et
  `smolvlm-500m` (420 Mo + 100 Mo). Le gestionnaire télécharge la paire de manière **atomique**
  (« les deux fichiers ou rien » : `.part`, doubles vérifications SHA-256, publication groupée).
- **Orchestration** : nouveau **moteur VISION** (port 8095) lancé avec
  `llama-server -m … --mmproj models/mmproj_specifique.gguf` ; ligne de commande vérifiée.
  Il tourne **en CPU** par défaut (D-029 : le chemin `mtmd` provoque un `Vulkan device lost` sur
  Maxwell), surchargeable par `LOCALAI_VISION_NGL`.
- **Index contextuel** : les images `.png/.jpg/.jpeg/.bmp/.gif/.webp` sont **indexées avec
  métadonnées** (`kind`, `format`, `width`, `height`, `bytes`, `megapixels`) sans aucune dépendance
  externe (lecture d'en-tête binaire) — vérifié : `capture_pomme.png` → `512x512, 0.262 MP`.
- **Protocole MCP (spec 2024-11-05)** : passerelle `scripts\mcp_gateway.py` bâtie sur le **SDK
  officiel** (JSON-RPC 2.0 stdio, **aucune réimplémentation**), serveur local `localai` exposant
  5 outils ; déclaration centralisée dans `config\mcp-settings.json` (préservé à la réinstallation).
- **CLI** : `mcp-list` (serveurs + outils actifs), `mcp-call <serveur> <outil> [json]`,
  `mcp-test` (autotest **VERT**).
- **Correctifs d'auto-healing** : héritage étendu aux modèles vision (réparation d'une régression),
  résolution d'arguments MCP (le mode `serve` n'est plus traité comme un chemin), `--args-file`
  (JSON robuste hors quoting shell).
- Manifest : version globale **v1.5.0**.

## v1.4.1 (stabilisation JALON 1) — 2026-10-03
Garde-fou de stabilité découvert par le **bêta-test de rupture** précédant la v1.5.0.
- **Bug résiduel corrigé** : le gateway LiteLLM (port 4000) renvoyait **HTTP 500**
  (`ModuleNotFoundError: prisma`) sur toute requête **non authentifiée**, au lieu de **401**.
  Cause : `litellm[proxy]` installé avec `check=False` → extra `prisma` omis silencieusement ;
  le handler d'erreur d'authentification de LiteLLM importe `prisma` sans protection.
- **Correctif** : nouvelle routine de déploiement vérifiée **`ensure_proxy_deps()`** (sonde
  `import prisma`, installation `pip --target`, re-vérification, trace) + entrée manifest.
- **Vérifié** : `GET /v1/models` sans clé → **401** ; avec `sk-local` → **200** (7 modèles) ;
  inférence texte cœur (8080) et gateway (4000) OK ; RAG `index` + `rag-query` OK (5 formats).
- Suite de tests JALON 1 : **7/7 OK**.

## v1.4.1 — 2026-10-03
**Micro-incrément de finition** (v1.4.0 → v1.4.1). Fondations inchangées ; garde-fous opérationnels
et documentation complétée.
- **Watchdog VRAM** : daemon `scripts\vram_watchdog.py` (échantillonnage **2 s**) avec seuils
  **alerte < 15 %** / **critique < 5 %** / **reprise > 20 %** ; alerte journalisée dans `logs\vram.log`
  **et** `dev\crash.log` (catégorie `GPU_VRAM`) ; **action préventive** au seuil critique (relance du
  moteur en **CPU pur `-ngl 0`**), état dans `data\vram-status.json` + `data\vram-action.json`.
- **CLI** : `Run-LocalAI.bat vram-status` (VRAM totale/libre/utilisée + seuils + état) ;
  `Run-LocalAI.bat start --no-watchdog` (désactivation silencieuse).
- **Modèle image léger** : entrée catalogue **`sd-turbo-light`** = SD-Turbo **Q8_0**
  (`sd_turbo-f16-q8_0.gguf`, **1,88 Go**, SHA-256) — `pull sd-turbo-light`, chargé en priorité par
  `sd-server`. Déviation « safetensors » documentée (D-024).
- **Documentation CUDA Maxwell** : nouvelle section `INSTALLATION.md` §31 (pourquoi
  `invalid device function`, compilation
  `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release`, intégration automatique
  via `variants\cuda\custom-build.txt` + `Run-LocalAI.bat optimize`).
- **Image turbo 5× plus rapide** : `--steps 4` appliqué automatiquement aux modèles *turbo*
  (`sd-server … --steps 4`) — génération 512×512 en ~3,5 min au lieu de ~12 min (QA : division par ~5).
- **Héritage élargi** : le modèle image téléchargé (`models\sd_turbo-f16-q8_0.gguf`) est **préservé**
  entre réinstallations (règle d'or), plus besoin de le re-télécharger.
- **Version dynamique** : placeholder `__VERSION__` substitué au déploiement → fin des versions figées
  (bannière de démarrage, en-tête CLI, titres `hw_profile` / `localai_status`).
- **Corrections QA (auto-healing)** : BOM UTF-8 dans `data\llama-cmd.json` (action préventive),
  échappement `%%` dans l'affichage du watchdog, argument `--steps` (au lieu d'`--extra-sample-args`).
- Manifest : **70 composants**, `root` = chemin final. Version globale **v1.4.1**.

## v1.4.0 — 2026-10-03
**Phase 4 (mandat d'évolution).** Incrément de la v1.3.0 — **RAG local + Agent Hub** (cœur Go inchangé).
- **Pipeline RAG local unifié** (texte, code, PDF, Office) :
  - extraction `.txt/.md/.json/.py/.js/.go/.rs/.c/.cpp/…`, **PDF** (`pypdf`), **Word** (`python-docx`),
    **Excel** (`openpyxl`) ;
  - chunking 2048 caractères (multiple de 512, aligné *prompt caching*) avec **recouvrement 10 %** ;
  - **embeddings neuronaux réels** via le moteur llama.cpp (`/v1/embeddings`, `--pooling mean`) —
    **aucun modèle supplémentaire** ;
  - index **à plat** : `runtime\rag\{index-<col>.npy, chunks-<col>.jsonl, manifest-<col>.json, collections.json}` ;
  - **faiss STRICTEMENT proscrit** : similarité cosinus en **NumPy pur** (produit scalaire normalisé).
- **Packages isolés** (`pip --target`) dans `runtime\packages\` (numpy, pypdf, python-docx, openpyxl) ;
  `python311._pth` complété de `..\packages` (mode isolé géré).
- **Agent Hub / LiteLLM avancé** : **modèle virtuel unique** `localai` (+ alias `smart`/`auto`) ;
  **Token Saver** (prompt court → local ; prompt complexe ou **contexte saturé** → cloud si clé, sinon local) ;
  préférence cloud OpenRouter > DeepSeek > OpenAI > Anthropic ; **journal de routage** `logs\routing.jsonl`.
- **CLI enrichi** : `index <dossier> [collection]`, `rag-query <texte>`, `proxy-logs`,
  `key-set <provider> <valeur>` (écriture chirurgicale dans `config\keys.env`).
- **BYOK** : `config\keys.env` + `config\cloud-keys.env` (les deux chargés ; `keys.env` prioritaire),
  **préservés** entre redéploiements.
- Manifest : **68 composants**, `root` = chemin final.
- Validation QA réelle : indexation 5 formats → 5 chunks × 2048 dims ; recherche cosinus ; routage
  virtuel (local + saturation) ; bascule cloud sur clé présente ; arrêt zéro zombie + VRAM libérée.

## v1.3.0 — 2026-10-03
**Phase 3 (mandat d'évolution).** Incrément de la v1.2.0 — **optimisation GPU** (cœur Go inchangé).
- **Détection matérielle multi-constructeur** : NVIDIA (`nvidia-smi`) → AMD (ROCm `amdhip64.dll`) →
  Vulkan (`vulkan-1.dll`) → CPU (repli). Détection VRAM générique via WMI + registre
  (`HardwareInformation.qwMemorySize`), marge 85 %.
- **Profil matériel persistant** : `config\hardware-profile.json` (CPU, RAM, GPU, VRAM, backend,
  profil recommandé, paramètres calculés, sécurité VRAM, variante active).
- **Variantes llama.cpp** téléchargées et déployées dans `backends\llama-cpp\variants\{cpu,vulkan,cuda}\` ;
  bascule automatique de la variante active (`scripts\engine_select.ps1`).
- **Calcul automatique** de `-ngl` (budget VRAM, cache KV, marge 10 %), `--threads`, `--ctx-size`
  (aligné 4096, plafonné par `n_ctx_train`) à partir des métadonnées GGUF (`local-ai util gguf-info`).
- **Profils de performance** `soft | normal | hard | auto | custom` + **sécurité VRAM** (bascule CPU
  automatique si ratio < 0.75).
- **`Run-LocalAI.bat` enrichi** : `profile`, `optimize`, `benchmark [cpu]`, `set-profile <p>`.
- **Benchmark réel** : CPU **14,91 tok/s** vs GPU Vulkan **71,41 tok/s** (**≈4,8×**), GPU 85-99 %,
  VRAM ~1245 Mo, libération confirmée à l'arrêt. Historique : `config\bench-history.jsonl`.
- **Repli CUDA → Vulkan documenté** : les binaires CUDA prébuilds ne supportent pas Maxwell (CC 5.2).
- **Multi-modal GPU** : TTS = sélection de provider ONNX **avec repli automatique** (DML → CUDA → CPU) ;
  DirectML testé et rejeté (incompatibilité `ConvTranspose` sur Maxwell) ; variante SD CUDA installée.
- Manifest : **63 composants** (dont profil, scripts GPU, variantes), `root` = chemin final.
- Nouveaux livrables : `config\hardware-profile.json`, `scripts\{hw_profile,engine_select,bench}.ps1`.

## v1.2.0 — 2026-10-03
**Phase 2 (mandat d'évolution).** Incrément de la v1.1.0 (aucune régression : cœur Go inchangé).
- **Python 3.11.9 embarqué** (`runtime\python`) — usage unique : LiteLLM + TTS.
- **Gateway LiteLLM 1.103.2** sur le port 4000 (routage local/externe, BYOK, règle de complexité).
- **Backends multi-modaux** (services HTTP séparés, remplaçables individuellement) :
  `whisper-cpp` (speech-to-text, 8091), `stable-diffusion` (images, 8092), `tts` (kokoro, 8093).
- **Model Manager** : catalogue JSON multi-modal + `download_model.bat` + `Run-LocalAI.bat pull/list`.
- **CLI wrapper `Run-LocalAI.bat`** : `start | stop | status | pull <model> | list | backends | help`.
- **Cloud offload (BYOK)** : `config\cloud-keys.env` + callback `complexity_router.py`
  (prompts courts → local ; prompts complexes → externe si clé configurée, sinon repli local).
- **Résolution automatique des ports** (bascule en cas de conflit) + vérification au démarrage.
- **Installeur v1.2.0** : `_stop_existing()` (anti-verrou), `start` idempotent,
  manifest `root` = chemin final (correction Section 12.1), 54 composants inventoriés.
- **Corrections Section 12** : manifest root final ; détection de ports occupés ; version v1.2.0.
- **Validation QA réelle** : 8080/4000/8091/8093 UP ; chat local ; routage `smart` ; STT (JFK) ; TTS WAV.
- Nouveaux livrables : `dev\crash.log`, `dev\BETA_TEST_REPORT.md`, `INSTALLATION.md` enrichi.

## v1.1.0 — 2026-10-03
- **Premier livrable fonctionnel.** Cœur LocalAI compilé **nativement sous Windows** (Go 1.27.1,
  `CGO_ENABLED=0`) depuis les sources officielles **v4.11.0**. Aucun binaire Windows officiel
  n'existe : compilation locale (Section 4.2, étape 1).
- Ajout du backend gRPC natif **`cloud-proxy.exe`** (compilé localement depuis `backend/go/cloud-proxy`)
  servant de bridge vers le moteur d'inférence.
- Intégration du moteur d'inférence **llama.cpp officiel** (release ggml-org **b11375**, Windows CPU x64).
- Arborescence ouverte produite dans `LocalAI\` : `local-ai.exe`, `backends\llama-cpp\` (moteur +
  bridge), `models\`, `config\`, `configuration\`, `logs\`, `data\`, `launcher.bat`, `stop.bat`,
  `download_model.bat`, `manifest.json`.
- `install_localai_win.py` (installeur maître mono-bloc **v1.1.0**) : `archive_installer()` en toute
  première instruction de `main()`, validation AST de `LOCALAI_DEPLOY_CODE` (parse + compile +
  py_compile), déploiement **transactionnel** (staging puis bascule), `manifest.json` avec SHA-256.
- Validation QA réelle (Section 5) : `GET /v1/models` OK, `POST /v1/chat/completions` OK
  (Llama-3.2-1B répond), **streaming SSE** OK, arrêt propre `stop.bat` (**zéro zombie**), ports libérés.
- Documentation : `INSTALLATION.md` créé ; `PERIMETRE.md`, `JOURNAL.md`, `DECISIONS.md`,
  `patch_integrity.log` mis à jour.
- Modèle de test : `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (770 Mo, SHA-256 vérifié).

## v1.0.0 — 2026-10-03
- Ouverture du chantier (version de depart du livrable).
- Copie de la charte en `CHARTE.md` (acte d'acceptation).
- Creation de l'arborescence de travail : `Installeur\`, `dev\`, `dev\old\`, `log\`, `build\`.
- Redaction de `PERIMETRE.md` (contrat de confinement).
- Redaction de `JOURNAL.md`, `dev\DECISIONS.md`, `dev\patch_integrity.log`.
- Acquisition de la toolchain Go 1.27.1 (SHA-256 verifie) dans `build\tools\go`.
- Decisions initiales documentees (binaire Windows absent -> compilation depuis les sources).
