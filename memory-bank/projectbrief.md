# Project Brief — AiTron V3

## Identité
- **Nom** : AiTron V3
- **Nature** : Portage Windows natif et autonome de LocalAI (fork indépendant, licence MIT)
- **Version actuelle** : v3.1.0 (certifiée)
- **Version en cours** : v3.1.1 (portabilité)
- **Sandbox** : détectée dynamiquement (voir `.clinerules\04-structure.md`)
- **Installeur** : `install_AiTron_v3.py` (mono-bloc, auto-suffisant)

## Objectif
Fournir une plateforme d'IA locale **souveraine**, **portable**, **sans Docker**, **sans WSL**, avec :
- Un installeur unique auto-suffisant
- Une arborescence ouverte et modulaire
- Une doctrine transactionnelle (sauvegarde, AST, rollback)
- Une traçabilité complète
- Une certification par audit externe

## Cible
- Utilisateurs Windows qui veulent une stack IA locale souveraine
- Utilisateurs qui refusent Docker/WSL
- Utilisateurs avancés qui veulent tout contrôler
- Utilisateurs qui veulent une portabilité clé USB

## Positionnement
- **Pas** un concurrent de Lemonade (produit grand public)
- **Pas** un concurrent de LocalAI officiel (plateforme serveur)
- **Un outil souverain** : contrôle total, arborescence ouverte, doctrine rigoureuse

## Livrables clés
- `install_AiTron_v3.py` — installeur mono-bloc
- `AiTron\` — produit déployé (reconstructible)
- `CHARTE.md` — loi constitutionnelle
- `JOURNAL.md` — journal narratif
- `INSTALLATION.md` — guide utilisateur bilingue
- `dev\CHANGELOG.md` — historique des versions
- `dev\DECISIONS.md` — décisions techniques
- `ANOMALIES_NON_RÉSOLUES.log` — anomalies documentées
