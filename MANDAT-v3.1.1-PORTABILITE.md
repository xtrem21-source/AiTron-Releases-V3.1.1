# MANDAT TECHNIQUE — v3.1.1 : PORTABILITÉ TOTALE DE L'INSTALLEUR
## Détection dynamique du répertoire + Fallbacks de téléchargement

**Sandbox :** détectée dynamiquement (plus de chemin en dur)
**Version d'origine :** v3.1.0 | **Version cible :** v3.1.1
**Prérequis :** produit certifié v3.1.0

---

## PRÉAMBULE — LIS D'ABORD, PUIS EXÉCUTE

Bonjour Cline. Avant toute action, tu dois lire intégralement les documents suivants (déjà présents dans la sandbox) :

1. CHARTE.md — la loi constitutionnelle du projet
2. JOURNAL.md — le journal narratif de tout ce qui a été fait
3. dev\DECISIONS.md — toutes les décisions techniques (D-001 à D-048)
4. dev\CHANGELOG.md — l'historique des versions (v1.0.0 à v3.1.0)
5. dev\BETA_TEST_REPORT.md — les rapports de bêta-test
6. ANOMALIES_NON_RÉSOLUES.log — les anomalies documentées
7. INSTALLATION.md — la documentation utilisateur

Ces documents te donnent le cadrage de travail. Ils te disent :
- Ce qui a été fait
- Pourquoi ça a été fait
- Comment ça a été fait
- Quelles sont les règles à respecter

Tu ne peux pas exécuter ce mandat sans les avoir lus. C'est la première instruction.

---

## RAPPEL DE LA MÉTHODOLOGIE

### Doctrine transactionnelle

Le cycle de vie de toute modification suit l'ordre strict :

SAUVEGARDE ANTE-EXÉCUTION → PATCH CHIRURGICAL → COMPILATION / TEST → VALIDATION RATIFIÉE

Règles critiques :
- archive_installer() est la première instruction de main()
- La boîte noire Installeur\ archive le script maître à chaque exécution
- La triple validation AST (ast.parse + compile + py_compile) est obligatoire avant écriture disque
- Le rollback transactionnel est obligatoire en cas d'échec
- Le versionnage suit un incrément strict (v3.1.0 → v3.1.1)

### Contexte du projet

- v1.0.0 : ouverture du chantier, toolchain Go
- v1.1.0 : premier livrable fonctionnel (cœur LocalAI compilé, bridge gRPC, llama.cpp)
- v1.2.0 : Python embarqué + LiteLLM + backends multi-modaux
- v1.3.0 : détection GPU + variantes llama.cpp (CUDA/Vulkan/CPU)
- v1.4.0 : RAG multi-format + Agent Hub
- v1.4.1 : watchdog VRAM + modèle image léger + doc CUDA Maxwell
- v1.5.0 : vision + MCP
- v1.6.0 : GraphRAG + failover SSE
- v1.7.0 : quantization + filtre PII
- v1.8.0 : DirectML/NPU + repli CPU
- v1.9.0 : speculative decoding TEXT-ONLY
- v2.0.0 : espace hermétique AES-256 + profil apprenant
- v2.1.0 : fédération RPC + découverte réseau
- v2.1.1 : i18n FR/EN
- v3.0.0 : renommage AiTron V3 + audit d'autonomie
- v3.1.0 : certification validée au vert (audit Pro)

Tu es actuellement en v3.1.0. Le produit stable est dans AiTron\. Le produit de staging certifié est archivé dans dev\old\test_dynamique\AiTron\.

---

## OBJECTIF DE L'INCRÉMENT v3.1.1

Rendre l'installeur install_AiTron_v3.py totalement portable.

Aujourd'hui, l'installeur est câblé en dur sur la sandbox G:\V1\LocalAI-Projet\. Résultat : il ne fonctionne que dans ce dossier.

Tu vas le rendre portable, c'est-à-dire capable de fonctionner :
- Sur une clé USB
- Dans C:\AiTron\
- Dans D:\Projets\AiTron\
- Dans n'importe quel dossier

Et tu vas ajouter des fallbacks de téléchargement pour local-ai.exe et cloud-proxy.exe, afin que l'installeur puisse fonctionner même sans les binaires locaux.

---

## SECTION 1 — DÉTECTION DYNAMIQUE DU RÉPERTOIRE

### 1.1 Modifications à apporter

Actuellement :

    SANDBOX    = r"G:\V1\LocalAI-Projet"
    BLACKBOX   = os.path.join(SANDBOX, "Installeur")
    DEV_DIR    = os.path.join(SANDBOX, "dev")
    QUARANTINE = os.path.join(SANDBOX, "dev", "old")
    LOGDIR     = os.path.join(SANDBOX, "log")
    PRODUCT    = os.path.join(SANDBOX, "AiTron")
    BUILD      = os.path.join(SANDBOX, "build")

Cible :

    # Détection dynamique du répertoire de la sandbox.
    # Le script peut être lancé depuis n'importe où.
    # La sandbox est le dossier qui contient le script.

    def _detect_sandbox():
        sandbox = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(sandbox).lower() == "installeur":
            sandbox = os.path.dirname(sandbox)
        return sandbox

    def _detect_sandbox_with_args(argv):
        for i, arg in enumerate(argv):
            if arg == "--root" and i + 1 < len(argv):
                root = os.path.abspath(argv[i + 1])
                if os.path.isdir(root):
                    return root
                raise RuntimeError("--root : dossier introuvable : %s" % root)
        return _detect_sandbox()

    SANDBOX    = _detect_sandbox_with_args(sys.argv[1:])
    BLACKBOX   = os.path.join(SANDBOX, "Installeur")
    DEV_DIR    = os.path.join(SANDBOX, "dev")
    QUARANTINE = os.path.join(SANDBOX, "dev", "old")
    LOGDIR     = os.path.join(SANDBOX, "log")
    PRODUCT    = os.path.join(SANDBOX, "AiTron")
    BUILD      = os.path.join(SANDBOX, "build")

### 1.2 Priorité de détection

1. Argument --root <chemin> (prioritaire si fourni)
2. Dossier du script (détection automatique)
3. Erreur si aucun des deux ne fonctionne

### 1.3 Création automatique

Si la sandbox n'existe pas (cas d'un premier lancement sur clé USB), la créer.

Toutes les sous-arborescences (Installeur\, dev\, dev\old\, log\, build\) doivent être créées automatiquement si absentes.

### 1.4 Portabilité

Le script doit fonctionner quel que soit :
- Le lecteur (C:, D:, E:, G:, clé USB, partage réseau)
- Le chemin (C:\AiTron\, D:\Projets\AiTron\, E:\AiTron-Portable\)
- L'utilisateur (pas de chemin C:\Users\<nom>\ en dur)

---

## SECTION 2 — FALLBACKS DE TÉLÉCHARGEMENT

### 2.1 Problème

Aujourd'hui, l'installeur cherche local-ai.exe et cloud-proxy.exe dans :
- build\out\local-ai.exe
- build\out\cloud-proxy.exe

Si ces fichiers sont absents (cas d'une installation sur une nouvelle machine), l'installeur échoue.

### 2.2 Solution

Ajouter des fallbacks de téléchargement :

    FALLBACK_LOCAL_AI_URL     = "https://transfert.free.fr/Huc2T0O"
    FALLBACK_CLOUD_PROXY_URL  = "https://transfert.free.fr/qpxjyFp"
    FALLBACK_LOCAL_AI_SHA256    = ""
    FALLBACK_CLOUD_PROXY_SHA256 = ""

### 2.3 Logique de fallback

Pour local-ai.exe :
1. Chercher dans build\out\local-ai.exe (local)
2. Si absent, chercher dans dev\old\test_dynamique\AiTron\local-ai.exe (staging archivé)
3. Si absent, télécharger depuis FALLBACK_LOCAL_AI_URL
4. Vérifier le SHA-256
5. Si le SHA-256 ne correspond pas, rejeter et essayer une source alternative

Idem pour cloud-proxy.exe.

### 2.4 Messages

Documenter clairement dans les logs :

    Source core       : trouve  build\out\local-ai.exe
    Source bridge     : ABSENT
    Fallback core     : telechargement depuis https://transfert.free.fr/Huc2T0O
    Fallback core     : SHA-256 verifie (abc123...)

### 2.5 Documentation

Ajouter dans INSTALLATION.md une section Fallbacks de téléchargement avec les URLs et la note sur leur caractère temporaire.

---

## SECTION 3 — VALIDATION

### 3.1 Tests obligatoires

Test 1 — Installation dans le dossier actuel

    cd G:\V1\LocalAI-Projet
    python install_AiTron_v3.py

Vérifier que l'installation fonctionne comme avant.

Test 2 — Installation dans un autre dossier

    mkdir C:\AiTron-Test
    copy G:\V1\LocalAI-Projet\install_AiTron_v3.py C:\AiTron-Test\
    cd C:\AiTron-Test
    python install_AiTron_v3.py

Vérifier que :
- La sandbox est détectée comme C:\AiTron-Test\
- L'arborescence est créée dans C:\AiTron-Test\
- Le produit est déployé dans C:\AiTron-Test\AiTron\
- Le produit fonctionne (Run-LocalAI.bat start)

Test 3 — Installation avec --root

    cd G:\V1\LocalAI-Projet
    python install_AiTron_v3.py --root D:\AiTron-Root-Test

Vérifier que :
- La sandbox est D:\AiTron-Root-Test\
- Tout est créé dans D:\AiTron-Root-Test\

Test 4 — Installation sur clé USB

    1. Copier install_AiTron_v3.py sur la clé USB (E:\)
    2. Ouvrir un terminal dans E:\
    3. python install_AiTron_v3.py

Vérifier que tout fonctionne.

Test 5 — Fallback de téléchargement

    1. Renommer build\out\local-ai.exe en local-ai.exe.bak
    2. Lancer python install_AiTron_v3.py
    3. Vérifier que le binaire est téléchargé depuis le fallback
    4. Vérifier le SHA-256
    5. Vérifier que le produit fonctionne

Test 6 — Cohérence avec le certificat v3.1.0

Vérifier que les modifications ne cassent pas ce qui a été certifié :
- IHM bilingue 100 %
- CLI 38 exécutions sans erreur
- 0 BOM
- Failover SSE
- Vault anti-perte
- Zéro zombie

### 3.2 Rapport

Produire un rapport dans dev\BETA_TEST_REPORT.md (section v3.1.1).

---

## SECTION 4 — TRAÇABILITÉ

Mettre à jour :

| Fichier | Contenu |
|---------|---------|
| dev\CHANGELOG.md | Entrée v3.1.1 (portabilité + fallbacks) |
| dev\DECISIONS.md | D-049 : décision de rendre l'installeur portable |
| dev\patch_integrity.log | Validation des patchs |
| dev\crash.log | Catégories PORTABILITY, FALLBACK_DOWNLOAD |
| dev\BETA_TEST_REPORT.md | Section v3.1.1 |
| JOURNAL.md | Entrée sur l'incrément |
| INSTALLATION.md | Section fallbacks |
| manifest.json | Version v3.1.1 |

---

## SECTION 5 — INTERDICTIONS

- Pas de chemin en dur (G:\V1\LocalAI-Projet\)
- Pas de dépendance à un lecteur spécifique (C:, D:, G:)
- Pas de modification du produit stable (AiTron\) sans validation
- Pas de suppression de fichiers sans passage par dev\old\
- Pas de packaging monolithique
- Pas de Docker
- Pas de WSL

---

## SECTION 6 — CLAUSE D'AUTO-RÉGULATION

Si tu estimes que la charge dépasse ta capacité en un seul passage, tu es autorisé à subdiviser :

- v3.1.1a : Détection dynamique du répertoire
- v3.1.1b : Fallbacks de téléchargement
- v3.1.1c : Tests de portabilité

Documente ce choix dans dev\DECISIONS.md.

---

## SECTION 7 — CONFIRMATION

Lis intégralement :
1. CHARTE.md
2. JOURNAL.md
3. dev\DECISIONS.md
4. dev\CHANGELOG.md
5. dev\BETA_TEST_REPORT.md
6. ANOMALIES_NON_RÉSOLUES.log
7. INSTALLATION.md

Puis exécute ce mandat en respectant la doctrine transactionnelle (sauvegarde, patch, test, validation).

Livre la version v3.1.1 d'AiTron, portable et distribuable.

Tu peux commencer.

---

FIN DU MANDAT v3.1.1
