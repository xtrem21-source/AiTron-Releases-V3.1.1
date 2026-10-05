# Active Context — Où on en est MAINTENANT

## Date
2026-10-05

## Version actuelle
- **Produit stable** : v3.1.2 (binaires GitHub Releases)
- **Version en cours** : aucune — v3.1.2 livrée, testée et documentée
- **Certificat** : `CHECK_DE_CONTRÔLE_FINAL.log` — CERTIFICATION v3.1.0 VALIDÉE AU VERT

## Travail en cours
**Aucun mandat actif.** Les mandats **v3.1.1** (portabilité totale) et **v3.1.2** (binaires
GitHub Releases) sont livrés, testés en conditions réelles et documentés.

## Prochaines étapes
1. Publier le dépôt Git (commit initial + tag `v3.1.2`) — en cours
2. Publier la release GitHub (binaires hébergés : `xtrem21-source/AiTron-Releases-V3.1.1@v3.1.1`)
3. Signature numérique (SignPath) et segmentation des binaires (limite GitHub 25 Mo/fichier)

## Décisions récentes
- **D-049** : portabilité totale — détection dynamique du répertoire (+ option `--root`)
- **D-050** : fallbacks de téléchargement + garde-fou d'intégrité PE « MZ »
- **D-051** : intégration des binaires GitHub Releases (URLs pérennes + SHA-256)

## Anomalies en cours
Voir `ANOMALIES_NON_RÉSOLUES.log`. L'anomalie `FALLBACK_DOWNLOAD` (URLs HTML de v3.1.1) est
**RÉSOLUE en v3.1.2** par l'usage de GitHub Releases.

## Points d'attention
- Produit stable `AiTron\` déployé en **v3.1.2** (sandbox G:\ + produit de test C:\TestGitHub).
- `.gitignore` : seules les SOURCES sont versionnées (produits/caches lourds exclus).
- IHM : rendu navigateur non vérifié (limite historique, non bloquante).

## Ressources
- **Sandbox** : `G:\V1\LocalAI-Projet\` (détectée dynamiquement)
- **Produit stable** : `G:\V1\LocalAI-Projet\AiTron\`
- **Staging archivé** : `G:\V1\LocalAI-Projet\dev\old\test_dynamique\AiTron\`
- **Boîte noire** : `G:\V1\LocalAI-Projet\Installeur\`
- **Releases binaires** : `github.com/xtrem21-source/AiTron-Releases-V3.1.1`
