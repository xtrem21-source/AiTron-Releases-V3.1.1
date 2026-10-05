# Règle 06 — Cadrage

## Principe
À CHAQUE session, avant toute action, tu DOIS lire les documents de cadrage du projet.
Ces documents te donnent le contexte, l'historique, et l'état actuel.

## Ordre de lecture (priorité absolue)

### 1. État actuel (à lire EN PREMIER)
- memory-bank\activeContext.md — où on en est MAINTENANT
- memory-bank\progress.md — ce qui marche, ce qui reste

### 2. Documents constitutionnels (la loi)
- CHARTE.md — loi constitutionnelle du projet
- PERIMETRE.md — contrat de confinement

### 3. Documents narratifs (l'histoire)
- JOURNAL.md — journal narratif complet
- dev\CHANGELOG.md — historique des versions
- dev\DECISIONS.md — toutes les décisions techniques

### 4. Documents de test (les preuves)
- dev\BETA_TEST_REPORT.md — rapports de bêta-test
- dev\patch_integrity.log — validation des patchs
- ANOMALIES_NON_RÉSOLUES.log — anomalies ouvertes

### 5. Documents utilisateur (la doc)
- INSTALLATION.md — aiguillage FR/EN
- INSTALLATION.fr.md — guide complet FR
- INSTALLATION.en.md — guide complet EN

## Règles actionnables

1. À CHAQUE session, tu lis ces documents AVANT toute action.
2. Tu appliques leur contenu (règles, doctrine, méthodologie).
3. Tu ne demandes PAS à l'utilisateur de te les résumer.
4. Si un document est absent, tu le signales.
5. Si un document est obsolète, tu le signales.
6. Si le Memory Bank est vide ou absent, tu le signales.

## Documents par ordre de priorité

### Priorité 1 — Obligatoires (toujours lus)
- memory-bank\activeContext.md
- CHARTE.md
- JOURNAL.md

### Priorité 2 — Importants (à lire si applicable)
- memory-bank\progress.md
- dev\DECISIONS.md
- dev\CHANGELOG.md
- PERIMETRE.md

### Priorité 3 — Contextuels (à lire si le mandat le demande)
- dev\BETA_TEST_REPORT.md
- dev\patch_integrity.log
- ANOMALIES_NON_RÉSOLUES.log
- INSTALLATION.md (et versions FR/EN)

## Interdictions
- Ne jamais exécuter un mandat sans avoir lu ces documents
- Ne jamais ignorer la CHARTE
- Ne jamais sauter la lecture du Memory Bank
- Ne jamais faire confiance à ta mémoire seule (le contexte peut être long)

## Évolution de cette règle

Ce fichier est le POINT D'ENTRÉE du cadrage. Si le projet change :
- Ajouter/retirer des documents ici
- Mettre à jour l'ordre de priorité
- Adapter au contexte

Pour exporter sur un autre projet : copier ce fichier et adapter la liste.
