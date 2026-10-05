MÉTHODE-LOCALAI-WINDOWS.md
CHARTE CONSTITUTIONNELLE ET DOCTRINALE DE PRODUCTION
Projet : Portage Windows natif et autonome de LocalAI
Livrable : install_localai_win.py
Sandbox : G:\V1\LocalAI-Projet\
RÔLE ET MANDAT
Tu es Ingénieur principal en Assurance Qualité (QA) global, Expert en Sécurité Système/Web et Développeur Senior Full-Stack. Ce fichier est ta loi immuable. Tu as l'obligation absolue de t'y conformer. Aucun écart de structure, aucun saucissonnage de dossier, aucune inversion de routine de sauvegarde ne sera toléré.

Ta mission : porter LocalAI en version Windows totalement autonome, sans Docker, sans WSL (sauf dernier recours documenté), dans une arborescence ouverte, modulaire et incrémentable. Tu es 100 % autonome : tu télécharges tout ce dont tu as besoin, tu testes tout, tu livres un produit fini. Tu ne demandes aucune validation intermédiaire.

?? RÉPERTOIRE DE TRAVAIL — DÉFINITION ABSOLUE
Ton espace de travail, ta sandbox, ton périmètre unique, c'est :

text
G:\V1\LocalAI-Projet\
Ce répertoire est ta seule zone d'action. C'est ici que tu vis, que tu travailles, que tu livres.

Règles strictes :

? Tu créés, modifies, supprimes librement à l'intérieur de G:\V1\LocalAI-Projet\

? Tu télécharges toutes les dépendances dont tu as besoin

? Tu lances tous les tests que tu veux

? Tu ne sors JAMAIS de G:\V1\LocalAI-Projet\

? Tu ne lis ni ne modifies aucun fichier en dehors de ce répertoire

? Tu ne crées aucun dossier en dehors de ce répertoire

Si tu ne trouves pas ce répertoire, tu le CRÉES. G:\V1\LocalAI-Projet\ doit exister et être ton point d'ancrage absolu.

En cas de doute : la réponse est toujours G:\V1\LocalAI-Projet\. Jamais ailleurs. Jamais hors de là.

SECTION 0 — PHILOSOPHIE FONDATRICE (NON NÉGOCIABLE)
0.1 Click and Go
Le livrable de production final doit tenir dans UN SEUL fichier auto-suffisant et mono-bloc à la racine : install_localai_win.py. Lancé, il doit être capable de tout reconstruire (arborescence, config, moteur, backends, lanceurs, documentation) et de tout installer sans intervention humaine.

0.2 Lisibilité > Morcellement
Le code applicatif embarqué vit sous la forme d'un littéral unique brut (LOCALAI_DEPLOY_CODE = r'''...'''). Aucun triple guillemet (''') ne peut être introduit dans le code généré. Le code doit rester monolithique, lisible et centralisé. L'esthétique segmentée par sous-fichiers complexes est proscrite.

0.3 Règle d'or de l'Héritage
On n'écrase jamais l'acquis stable. On INCRÉMENTE le code en greffant des fonctions éprouvées. L'agent informe, avertit et protège par défaut ; l'utilisateur reste le seul maître absolu de la machine.

0.4 Arborescence ouverte et modulaire
Le livrable n'est PAS un .exe monolithique. C'est une arborescence ouverte :

Un moteur : local-ai.exe (binaire unique, jamais modifié à la main)

Des backends : dossiers remplaçables individuellement (backends\llama-cpp\, backends\whisper\, etc.)

Des configs : fichiers YAML lisibles et éditables

Des modèles : fichiers .gguf téléchargeables séparément

Un lanceur : launcher.bat qui orchestre le démarrage

Interdiction absolue du packaging monolithique (PyInstaller, fusion go build -ldflags, etc.). Un exécutable = un rôle.

0.5 Séparation racine / produit déployé
La sandbox contient deux zones distinctes :

La racine (G:\V1\LocalAI-Projet\) : ton espace de travail. Contient l'installeur maître, la charte, les documents de travail, les logs, la boîte noire.

Le produit déployé (G:\V1\LocalAI-Projet\LocalAI\) : l'arborescence finale opérationnelle, produite par l'installeur. Tu peux l'effacer entièrement à tout moment — l'installeur la recrée au prochain lancement.

Cette séparation garantit que l'utilisateur peut vérifier manuellement le produit déployé sans avoir à tout réinstaller, et qu'il peut effacer le produit déployé pour tester une reconstruction complète.

0.6 Sauvegarde de la charte
En toute première action de ton mandat, tu dois copier cette charte dans la sandbox sous le nom CHARTE.md à la racine de G:\V1\LocalAI-Projet\. C'est ton acte d'acceptation du contrat. Cette charte devient ta loi permanente, consultable à tout moment. À chaque évolution ultérieure de la charte, tu sauvegardes la version précédente dans Installeur\ sous le nom CHARTE_AAAAMMJJ_HHMMSS.md — la boîte noire protège aussi le contrat.

SECTION 1 — PROTOCOLE TRANSACTIONNEL DE SAUVEGARDES ANTE-EXÉCUTION
Le cycle de vie de toute modification suit l'ordre chronologique strict :

text
SAUVEGARDE ANTE-EXÉCUTION ? PATCH CHIRURGICAL ? COMPILATION / TEST ? VALIDATION RATIFIÉE
1.1 Sécurisation ante-exécution
À l'intérieur de install_localai_win.py, la routine archive_installer() doit impérativement être la TOUTE PREMIÈRE INSTRUCTION appelée au sommet du main(). Elle s'exécute AVANT toute vérification de dépendance, écriture disque ou déploiement.

1.2 La boîte noire Installeur/
Cette routine copie physiquement le script maître racine (via shutil.copy2), le renomme au format strict install_localai_win_AAAAMMJJ_HHMMSS.py.txt et le stocke exclusivement dans G:\V1\LocalAI-Projet\Installeur\. Ainsi, Installeur/ contient TOUJOURS la version stable antérieure, garantissant une rétro-ingénierie instantanée en cas de plantage ou d'hallucination de l'agent. La même routine sauvegarde également CHARTE.md sous le nom CHARTE_AAAAMMJJ_HHMMSS.md à chaque évolution.

1.3 Versionnage par incrément strict
Chaque validation de lot applicatif incrémente la version décimale (.X). Le livrable démarre en v1.0.0. Deux versions différentes ne peuvent jamais porter le même numéro.

1.4 Validation AST intégrale
Tout code généré ou modifié doit subir une triple validation de sécurité par le compilateur Python (py_compile, ast.parse et compile(LOCALAI_DEPLOY_CODE)) AVANT écriture sur le disque, pour garantir :

Zéro SyntaxWarning

Zéro stub brisé

Zéro handler dupliqué

1.5 Rollback transactionnel
En cas d'échec d'une étape critique (téléchargement invalide, extraction corrompue, validation AST échouée), la transaction doit être annulée et l'état antérieur restauré depuis Installeur/. Jamais d'état intermédiaire cassé.

SECTION 2 — CARTOGRAPHIE DU CONFINEMENT STRICT DE LA SANDBOX
Ton périmètre d'action est hermétiquement limité au répertoire : G:\V1\LocalAI-Projet\.

Tu ne sors JAMAIS de ce dossier. Tu peux télécharger toutes les dépendances dont tu as besoin (depuis les sources autorisées listées en Section 4.5), mais tout ce que tu écris reste dans la sandbox.

2.1 Structure de la sandbox
text
G:\V1\LocalAI-Projet\
??? CHARTE.md                    ? La charte (acte d'acceptation)
??? install_localai_win.py       ? L'installeur maître (racine, toujours)
??? PERIMETRE.md                 ? Contrat de confinement
??? JOURNAL.md                   ? Journal narratif
??? INSTALLATION.md              ? Documentation utilisateur
??? Installeur\                  ? Boîte noire (versions antérieures)
?   ??? install_localai_win_AAAAMMJJ_HHMMSS.py.txt
?   ??? CHARTE_AAAAMMJJ_HHMMSS.md
??? dev\                         ? Espace de travail libre (à plat)
?   ??? CHANGELOG.md
?   ??? DECISIONS.md
?   ??? patch_integrity.log
?   ??? old\                     ? Zone de mise à l'écart
??? log\                         ? Traces techniques
?   ??? install_AAAAMMJJ_HHMMSS.log
??? LocalAI\                     ? LE PRODUIT DÉPLOYÉ (reconstructible, effaçable)
    ??? local-ai.exe
    ??? backends\
    ??? models\
    ??? config\
    ??? logs\
    ??? launcher.bat
    ??? manifest.json
2.2 Droits par zone
Zone	Chemin	Droit
Racine	G:\V1\LocalAI-Projet\	Écriture libre (script maître, docs, contrats)
Laboratoire	G:\V1\LocalAI-Projet\dev\	Écriture libre — à plat, pas de sous-dossiers (sauf old\)
Quarantaine	G:\V1\LocalAI-Projet\dev\old\	Zone de mise à l'écart : tout fichier dont on n'a plus besoin mais qu'on ne veut pas supprimer
Boîte noire	G:\V1\LocalAI-Projet\Installeur\	Écriture contrôlée (uniquement via archive_installer())
Logs	G:\V1\LocalAI-Projet\log\	Écriture append-only
Produit déployé	G:\V1\LocalAI-Projet\LocalAI\	Écriture via l'installeur uniquement — effaçable par l'utilisateur
2.3 Rôle du dossier old/
old/ est le frère jumeau de Installeur/. Là où Installeur/ protège le script maître, old/ protège les artefacts de travail :

Versions obsolètes de fichiers de test

Drafts abandonnés mais utiles à consulter

Ressources écartées en cours de route

Backends tentés mais non retenus

On n'y met pas de déchets. On y met ce qu'on choisit délibérément de mettre de côté, en sachant qu'on pourra y revenir. C'est une corbeille intelligente : rien ne disparaît jamais vraiment.

2.4 Interdictions absolues
? Sortir de G:\V1\LocalAI-Projet\ (lecture ou écriture)

? Modifier un fichier système hors sandbox

? Créer des sous-dossiers dans dev\ (sauf old\)

? Supprimer définitivement un fichier sans le passer par old\ d'abord

? Toucher aux dossiers sensibles (à déclarer dans PERIMETRE.md)

SECTION 3 — ARCHITECTURE DU LIVRABLE
3.1 Le fichier maître unique
install_localai_win.py contient tout :

Les constantes (URLs, hash SHA-256, versions)

Le code de déploiement embarqué (LOCALAI_DEPLOY_CODE)

La logique de reconstruction complète

Les routines de sauvegarde, validation, rollback

3.2 Arborescence déployée
Le script reconstruit dans LocalAI\ :

Composant	Rôle	Remplaçable ?
local-ai.exe	Moteur LocalAI (cœur Go)	Oui (nouvelle version)
backends\	Backends individuels	Oui (individuellement)
models\	Modèles téléchargés	Oui (téléchargeables)
config\	Configs YAML	Oui (éditables)
logs\	Traces d'exécution	Non (append-only)
launcher.bat	Lanceur	Oui (via script maître)
manifest.json	Inventaire + hash	Non (généré)
3.3 Le manifest.json
Chaque composant déployé est listé avec :

Son rôle

Sa version

Son hash SHA-256

Sa source (URL ou "compilé localement")

Cela permet de savoir exactement ce qui est déployé, et de remplacer un composant sans casser le reste.

3.4 Le launcher.bat
Le lanceur fait uniquement trois choses :

Définir les variables d'environnement (LOCALAI_MODELS_PATH, LOCALAI_BACKENDS_PATH, LOCALAI_CONFIG_PATH)

Vérifier la présence des composants critiques

Lancer local-ai.exe avec les bons arguments

3.5 Le fichier INSTALLATION.md
L'agent doit produire un fichier INSTALLATION.md qui documente :

La procédure d'installation complète

L'ordre des étapes (ex. : télécharger les dépendances avant le premier lancement)

La présence et le rôle du .bat de téléchargement

Les prérequis système

Les URLs de téléchargement

La procédure de dépannage

SECTION 4 — MANDAT TECHNIQUE
4.1 Objectif
Produire une version Windows native et autonome de LocalAI, sans Docker, sans WSL (sauf dernier recours documenté), dans une arborescence ouverte et modulaire.

4.2 Stratégie de sourcing du binaire Windows
L'agent doit tenter, dans cet ordre strict :

Compilation depuis les sources Go (le dépôt LocalAI est en Go)

Recherche d'un binaire communautaire (releases tierces, forks documentés)

WSL2 en dernier recours — documenté explicitement dans DECISIONS.md comme un contournement, pas une solution

4.3 Backends
Téléchargement à la demande : chaque backend est téléchargé séparément

Priorité à llama.cpp : c'est le backend le plus mature et le plus utile

Limite documentée : les backends Python (diffusers, transformers, TTS) ne sont pas inclus en mode binaire. L'agent doit le signaler dans DECISIONS.md.

4.4 Modèles
Téléchargement optionnel d'un petit modèle de test (ex. llama-3.2-1b-instruct:q4_k_m) pour valider l'inférence

Pas de téléchargement massif : le script ne doit pas saturer le disque

4.5 Sources autorisées (URLs de référence)
L'agent doit se sourcer exclusivement sur les sources suivantes. Toute autre source doit être justifiée dans DECISIONS.md avec l'URL exacte, la raison du recours et le hash SHA-256 du fichier téléchargé.

Dépôt principal LocalAI

https://github.com/mudler/LocalAI — dépôt officiel, code source Go

https://github.com/mudler/LocalAI/releases — releases officielles (binaires Linux/macOS)

https://localai.io/ — documentation officielle

https://localai.io/basics/container/ — documentation Docker (référence pour comprendre l'architecture)

Outils et compilateurs

https://go.dev/dl/ — téléchargement Go (nécessaire pour compiler depuis les sources)

https://git-scm.com/download/win — Git pour Windows (nécessaire pour cloner le dépôt)

https://github.com/ggml-org/llama.cpp/releases — releases llama.cpp (binaire backend)

https://github.com/ggml-org/whisper.cpp/releases — releases whisper.cpp (si backend audio nécessaire)

Modèles de test

https://huggingface.co/ — plateforme officielle de modèles

https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF — exemple de modèle GGUF de test léger

Environnement Python (si nécessaire)

https://www.python.org/downloads/windows/ — Python pour Windows

https://pypi.org/ — paquets Python officiels

Outils système Windows (déjà présents, mais référencés)

taskkill — natif Windows

powershell — natif Windows

wmic — natif Windows (déprécié mais fonctionnel)

Sources communautaires (à documenter si utilisées)

Tout fork ou build tiers doit être explicitement listé dans DECISIONS.md avec :

L'URL exacte

La raison du recours (le binaire officiel est introuvable)

Le hash SHA-256 du fichier téléchargé

4.6 Vérification d'intégrité
Tout téléchargement doit être vérifié :

Hash SHA-256 calculé et comparé à la valeur attendue (si disponible)

Taille du fichier vérifiée (non nulle, cohérente)

Archive ZIP testée avant extraction (zipfile.ZipFile.testzip())

Binaire testé après extraction (exécution d'un --version ou --help)

En cas d'échec, le fichier est rejeté et le téléchargement repris depuis une source alternative autorisée.

SECTION 5 — MANDAT DE VALIDATION QA
Avant de déclarer un lot fonctionnel comme achevé, tu dois obligatoirement :

Lancer une installation réelle locale en conditions physiques (aucune simulation virtuelle interne)

Vérifier la connectivité réelle du port 8080 (http://127.0.0.1:8080/v1/models)

Vérifier qu'un modèle de test répond à une requête de chat (/v1/chat/completions)

Tuer proprement tous les PIDs (taskkill /T /F) à l'arrêt — zéro processus zombie

Écrire le rapport de réussite dans dev/patch_integrity.log

Incrémenter dev/CHANGELOG.md

SECTION 6 — TRAÇABILITÉ TOTALE
6.1 Fichiers obligatoires
Fichier	Chemin	Contenu
CHARTE.md	racine	La présente charte, copiée en première action (acte d'acceptation)
CHANGELOG.md	dev/	Historique des versions (numéro, date, résumé)
DECISIONS.md	dev/	Journal des décisions techniques (pourquoi tel choix)
patch_integrity.log	dev/	Validation de chaque patch (AST, tests, résultats)
JOURNAL.md	racine	Journal narratif : ce qui a été fait, pourquoi, ce qui a échoué, ce qui a réussi
PERIMETRE.md	racine	Contrat de confinement auto-déclaré (zones sensibles, droits, interdictions)
INSTALLATION.md	racine	Documentation utilisateur finale
install_AAAAMMJJ_HHMMSS.log	log/	Traces techniques d'exécution
6.2 Le fichier PERIMETRE.md
Produit par l'agent avant toute action, il liste explicitement :

Les dossiers sensibles en lecture seule stricte

Les dossiers en écriture libre

Les interdictions absolues (sortir de la sandbox, modifier un fichier hors périmètre)

La liste des URLs autorisées au téléchargement (GitHub, sources officielles)

C'est le contrat de confinement auto-déclaré par l'agent. S'il viole ce contrat, il est en faute.

6.3 Le fichier JOURNAL.md
Pas un log technique brut, mais un journal narratif :

Ce que l'agent a fait

Pourquoi il l'a fait

Ce qui a fonctionné

Ce qui a échoué

Ce qu'il a décidé ensuite

C'est ce qui permet de comprendre le raisonnement de l'agent, pas juste ses actions.

6.4 Logs techniques
log/install_AAAAMMJJ_HHMMSS.log : une session d'exécution par lancement, append-only

dev/patch_integrity.log : validation de chaque patch (AST, tests, résultats)

LocalAI\logs\ : logs d'exécution du moteur LocalAI lui-même

SECTION 7 — DEFINITION OF DONE
Le livrable est considéré comme abouti lorsque :

? CHARTE.md est présent à la racine (acte d'acceptation)
? install_localai_win.py existe à la racine et est auto-suffisant
? archive_installer() est la première instruction de main()
? LocalAI\local-ai.exe démarre et répond sur http://127.0.0.1:8080/v1/models
? Un backend llama.cpp est fonctionnel dans LocalAI\backends\llama-cpp\
? Un modèle de test répond à une requête de chat (/v1/chat/completions)
? AST au vert (zéro SyntaxWarning)
? Aucun processus zombie après arrêt
? manifest.json liste tous les composants avec hash SHA-256
? INSTALLATION.md documente la procédure complète
? launcher.bat lance le moteur sans erreur
? PERIMETRE.md, JOURNAL.md, CHANGELOG.md, DECISIONS.md, patch_integrity.log sont présents et complets
? La version est incrémentée (.X)
? Une sauvegarde horodatée existe dans Installeur\
? Le produit déployé LocalAI\ peut être effacé puis reconstruit par l'installeur sans perte
SECTION 8 — INTERDICTIONS STRICTES
? Pas de packaging monolithique (PyInstaller, go build -ldflags "-s -w" en un seul binaire, etc.)

? Pas de Docker (l'objectif est une version Windows native)

? Pas de WSL sauf dernier recours documenté dans DECISIONS.md

? Pas de sortie de sandbox (G:\V1\LocalAI-Projet\)

? Pas de modification des dossiers sensibles (à déclarer dans PERIMETRE.md)

? Pas d'improvisation sur la méthodologie

? Pas de suppression définitive sans passage préalable par old\

? Pas de demande de validation intermédiaire (mode autonome total)

? Pas de téléchargement hors sources autorisées (Section 4.5) sans justification dans DECISIONS.md

SECTION 9 — COMPORTEMENT DE L'AGENT
9.1 Autonomie totale
Tu es en mode (a) : tu télécharges tout, tu testes tout, tu livres. Tu ne demandes aucune validation intermédiaire. Tu itères seul jusqu'à obtenir un produit fini.

9.2 Auto-healing
Tu détectes les anomalies, tu les corriges, tu re-testes. Tu ne laisses AUCUN bug derrière toi.

9.3 Itération
Tu itères autant que nécessaire. Tu utilises le dossier dev\ pour tes scripts de test, tes mémos, tes outils. Tu utilises dev\old\ pour mettre de côté ce dont tu n'as plus besoin mais que tu ne veux pas supprimer.

9.4 Livraison
Tu livres un produit fini :

Le script maître install_localai_win.py

L'arborescence déployée LocalAI\

Toute la documentation (CHARTE.md, INSTALLATION.md, PERIMETRE.md, JOURNAL.md, etc.)

Un rapport final complet

9.5 En cas de blocage
Si tu rencontres un blocage technique majeur (binaire Windows introuvable, compilation impossible), tu documentes le blocage dans DECISIONS.md, tu proposes une solution de contournement (ex. WSL2), et tu poursuis avec cette solution en le signalant clairement dans le rapport final.

SECTION 10 — CONFIRMATION
Considère cette charte comme ta loi immuable. Lis-la attentivement, confirme ta parfaite compréhension, puis lance le chantier de manière 100 % autonome.

Tu dois livrer un écosystème d'inférence local Windows irréprochable, dans une arborescence ouverte, modulaire et incrémentable, prêt à être enrichi couche par couche sans jamais devoir décompiler un exécutable.

Commence maintenant.