# Règle 02 — Versionnage

## Principe
Incrément strict. Deux versions différentes ne portent jamais le même numéro.

## Règles actionnables

1. Versionnage :
   - Format : vMAJEUR.MINEUR.CORRECTIF (ex. v3.1.1)
   - MAJEUR : rupture (changement d'identité)
   - MINEUR : nouvelle fonctionnalité
   - CORRECTIF : correction / portabilité / finition

2. Mettre à jour partout :
   - __version__ dans install_AiTron_v3.py
   - "installer_version" dans manifest.json
   - Entrée dans dev\CHANGELOG.md
   - Entrée dans dev\DECISIONS.md (si décision structurante)
   - En-tête de INSTALLATION.md

3. Format CHANGELOG :
   ## vX.Y.Z — AAAAMMJJ (TITRE COURT)
   **Résumé en une phrase.**
   - Point 1
   - Point 2

4. Format DECISIONS :
   ## D-XXX — Titre
   **Contexte** : ...
   **Décision** : ...
   **Justification** : ...
   **Conséquences** : ...

## Interdictions
- Ne jamais réutiliser un numéro de version
- Ne jamais sauter un incrément sans justification
- Ne jamais oublier manifest.json
