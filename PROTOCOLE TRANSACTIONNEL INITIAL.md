# MANDAT TECHNIQUE ET DIRECTIVE D'AUDIT DYNAMIQUE PRO — VERSION v3.1.0
## Certificat de Conformité, Installation Réelle, Validation IHM & Inférence Physique 
**Modèle requis :** Modèle d'inférence Pro d'élite `anthropic/claude-sonnet-5.5`. **Interdiction formelle d'utiliser un modèle de classe 'Flash' pour cet audit.**
**Sandbox racine :** `G:\V1\LocalAI-Projet\`  
**Version d'origine :** v3.0.0 | **Version cible :** v3.1.0 (Incrément d'Audit et de Certification)

Bonjour Cline. L'infrastructure v3.0.0 d'AiTron V3 a été figée. Tu as maintenant l'ORDRE STRICT d'endosser le rôle de Super-Auditeur QA Pro en conditions physiques réelles, avec mandat d'Auto-Réparation dynamique et d'isolation étanche.

================================================================================
 PROTOCOLE D'ISOLATION ET DE STAGING DYNAMIQUE (SANDBOXÉ)
================================================================================
Pour garantir l'étanchéité absolue de l'audit et ne pas polluer l'acquis stable v3.0.0, tu dois exécuter les étapes suivantes avant tout test :
1. **CRÉATION DU LABORATOIRE D'AUDIT :** Crée un répertoire dédié nommé exactement `G:\V1\LocalAI-Projet\dev\test_dynamique\`.
2. **ACQUISITION DES ARTEFACTS :** Copie le script maître d'installation `install_AiTron_v3.py` et le fichier d'orchestration `Run-LocalAI.bat` à l'intérieur de ce nouveau sous-dossier.
3. **EXÉCUTION À BLANC :** Exécute l'installeur Python exclusivement depuis ce répertoire `dev\test_dynamique\`. Tu dois y déployer une arborescence `AiTron\` temporaire complète. C'est sur ce produit de staging que tu effectueras l'ensemble de tes tests d'interactions.
4. **SAUVEGARDE DE TOI-MÊME :** Appelle la routine `archive_installer()` pour copier le script maître dans `Installeur\`.
5. **VERSIONNAGE :** Passe la version globale du script maître et du manifest à "v3.1.0".

================================================================================
SECTION 1 — INSPECTION CHIRURGICALE DE L'IHM, DU COMMAND CLI ET DES LANGUES
================================================================================
Tu dois analyser minutieusement le comportement du système lors de ses interactions réelles :

1. **AUDIT DE L'IHM WEB EMBARQUÉE (EMBEDDEDUI) :** Inspecte dynamiquement les fichiers et les templates HTML/JS/React de ton interface pour t'assurer qu'aucun libellé, bouton ou message d'erreur n'est resté figé en anglais (sauf en mode EN). Vérifie la traduction et le comportement des boutons critiques : "Lancer le serveur", "Interagir", "Arrêter", "Model Manager". L'interface doit être bilingue à chaud, fluide et ergonomique.
2. **AUDIT DE LA CONSOLE ET ENCODAGE (.BAT) :** Exécute le script `dev\check_terminal_encoding.py`. Vérifie que l'exécution de `Run-LocalAI.bat lang fr` et `lang en` bascule instantanément la totalité des messages du terminal au pixel près. Grâce à la commande `chcp 65001`, assure-toi qu'aucun accent n'est corrompu (zéro caractère brisé à l'affichage).
3. **AUDIT DE L'ACCÉLÉRATEUR SÉMANTIQUE (DIRECTML) :** Simule ou exécute `Run-LocalAI.bat npu-probe` et `hardware-status`. Inspecte l'en-tête de journalisation pour vérifier qu'en cas d'échec d'initialisation DirectML, la bascule sur CPU se fait de manière transparente sans casser l'expérience utilisateur, et que l'alerte est correctement catégorisée sous `GPU_DETECT` dans `dev\crash.log`.

================================================================================
SECTION 2 — EXTRACTION ET VÉRIFICATION PHYSIQUE DES MODALITÉS (RAG & FAILOVER)
================================================================================
1. **TEST PHYSIQUE DU PIPELINE RAG :** Exécute le script de stress-test `dev\test_rag_stress.py`. Assure-toi que les fonctions de lecture NumPy et de similarité cosinus n'ont pas d'angles morts sur les caractères spéciaux, les ligatures (cœur, œil) ou les structures complexes de documents.
2. **VÉRIFICATION DE L'INTÉGRITÉ BINAIRE (ANTI-BOM) :** Inspecte le pipeline d'écriture des fichiers de commandes du moteur (`llama-cmd.json`). Vérifie qu'aucun octet parasite (BOM UTF-8) n'est introduit lors de la sérialisation, ce qui ferait échouer le parsing JSON des actions correctives.
3. **ÉTANCHÉITÉ DU REPLAY SSE :** Audite minutieusement le code de ton proxy de bufferisation (`failover_proxy.py`). Assure-toi qu'en cas de crash simulé d'un moteur, le relais vers le cloud s'effectue sans aucune duplication de tokens à l'écran.
4. **ÉTANCHÉITÉ DU FILTRE PII (BEST-EFFORT) :** Simule l'envoi d'une requête complexe contenant des variables sensibles vers la route Cloud (`openrouter-claude`). Vérifie que le masquage réversible s'active *uniquement* lorsque le contenu quitte la machine, et que les journaux d'audit de masquage sont bien consignés dans `dev\crash.log`, catégorie `PRIVACY_FILTER`.
5. **AUDIT DE L'ESPACE HERMÉTIQUE (VAULT) :** Inspecte le script `vault.py`. Assure-toi que la routine `seal` applique l'anti-perte structurelle en vérifiant la réversibilité complète du conteneur chiffré AES-256-GCM avant de supprimer les fichiers en clair du disque.

================================================================================
SECTION 3 — HIÉRARCHIE DES LIVRABLES ET PROTOCOLE DE SORTIE
================================================================================
En fin d'exécution, tu dois produire l'arborescence documentaire réglementaire suivante à la racine :

### 1. LIVRABLE MAÎTRE ET CERTIFICAT DE SÉCURITÉ (À la racine)
Génère le fichier de certification nommé exactement : `G:\V1\LocalAI-Projet\CHECK_DE_CONTRÔLE_FINAL.log`
```text
================================================================================
               AITRON V3 — RAPPORT D'AUDIT ET DE CONTRÔLE FINAL
================================================================================
Date : [AAAAMMJJ_HHMMSS] | Validateur : Cline (Moteur Sémantique Pro)
Version certifiée : v3.1.0 | Sandbox : G:\V1\LocalAI-Projet\
 CONTRÔLE DE L'IHM ET DU BILINGUISME (FR/EN) :
    - État de la traduction des boutons ("Interagir", etc.) : [CONFORME/ANOMALIE]
    - Comportement de la bascule à chaud via CLI : [CONFORME/ANOMALIE]
    - Statut de l'encodage des accents console (chcp 65001) : [CONFORME/ANOMALIE]
    - Comportement du repli CPU sur l'accélérateur ONNX : [CONFORME/ANOMALIE]
 CONTRÔLE DE L'AUTONOMIE ET DES PIPELINES :
    - Intégrité de l'extraction multi-format NumPy (RAG) : [CONFORME/ANOMALIE]
    - Intégrité de l'écriture des commandes JSON (Anti-BOM) : [CONFORME/ANOMALIE]
    - Fluidité de la bufferisation du proxy et du Failover SSE : [CONFORME/ANOMALIE]
    - Étanchéité du masquage et de l'anonymisation Cloud (PII) : [CONFORME/ANOMALIE]
    - Fiabilité de l'anti-perte de la zone hermétique (Vault) : [CONFORME/ANOMALIE]
    - État des processus orphelins à l'arrêt (zéro zombie) : [CONFORME/ANOMALIE]
 SYNTHÈSE DES AMÉLIORATIONS APPORTÉES PAR AUTO-HEALING :
    (Liste ici chaque micro-ajustement ergonomique, correctif de code ou de traduction appliqué durant la boucle d'auto-réparation)
 VERDICT DE CERTIFICATION TERMINAL :
    [INSCRIRE L'UN DES DEUX BLOCS SELON LES RÉSULTATS FINAUX :]
    
    >>> EN CAS DE SUCCÈS (INITIAL OU APRÈS AUTO-RÉPARATION EFFECTIVE) :
    LE PRODUIT REMPLIT 100% DES CRITÈRES PHYSIQUES ET SÉMANTIQUES. CERTIFICATION VALIDÉE AU VERT.
    
    >>> EN CAS D'ANOMALIE INCURABLE MALGRÉ LA BOUCLE D'AUTO-RÉPARATION :
    CERTIFICATION REFUSÉE. LISTE DES ANOMALIES BLOQUANTES CI-DESSOUS. LE PRODUIT NE PEUT PAS ÊTRE CERTIFIÉ TANT QUE CES ANOMALIES NE SONT PAS CORRIGÉES.
================================================================================
```

### 2. LE JOURNAL DES DÉFAILLANCES HISTORIQUES OU RÉSIDUELLES (À la racine)
Si des anomalies ont été détectées (qu'elles aient été réparées par auto-healing ou qu'elles soient restées incurables), consigne-les obligatoirement dans : `G:\V1\LocalAI-Projet\ANOMALIES_NON_RÉSOLUES.log`
Chaque entrée doit respecter le format sémantique standardisé hérité :
```text
[AAAAMMJJ_HHMMSS] [CATEGORIE] [SEVERITE] Description
Impact : ...
Contournement : ...
Recommandation / Action corrective appliquée : ...
Statut : [RÉSOLU PAR AUTO-HEALING / SANS SOLUTION RÉSIDUELLE]
---
```
*(Sévrités acceptées : CRITICAL, ERROR, WARN, INFO. Tout statut 'SANS SOLUTION RÉSIDUELLE' de niveau ERROR ou CRITICAL entraîne le refus immédiat du certificat VERT).*

### 3. TRAÇABILITÉ ET COMPTABILITÉ HISTORIQUE (Dans dev\)
Mets à jour les fichiers de registre habituels : `dev\CHANGELOG.md` (v3.1.0), `dev\patch_integrity.log` et `dev\BETA_TEST_REPORT.md` pour refléter ton passage, tes actions de réparation et ton verdict final.

Fige définitivement le produit une fois ces fichiers écrits. Le chantier est clos. Tu peux commencer.

================================================================================
 PROTOCOLE D'AUTO-RÉPARATION APPLICATIVE (AUTO-HEALING LOOP)
================================================================================
**Tu as l'AUTORISATION EXPLICITE ET L'ORDRE de modifier le code si et seulement si tu détectes une anomalie ou un défaut de conformité lors de ton audit.**
* **Étape A (Détection) :** Si une anomalie (caractère brisé, libellé anglais, mauvaise route, plantage de script) apparaît, interromps l'audit.
* **Étape B (Réparation) :** Modifie le code source concerné (dans l'installeur maître ou le script incriminé) pour corriger l'anomalie de manière définitive.
* **Étape C (Triple Validation AST) :** Relance la validation AST complète sur le code modifié pour t'assurer qu'aucune régression syntaxique n'a été introduite.
* **Étape D (Re-Test complet) :** Réinitialise l'environnement de test et **relance l'intégralité du processus d'audit de zéro**.
* **Itération :** Tu répéteras ce cycle d'auto-réparation jusqu'à obtenir un parcours d'audit physique 100 % vierge de tout défaut.
