# Règle 05 — Communication

## Principe
Rapports structurés, honnêtes, actionnables.
Mise à jour AUTOMATIQUE du Memory Bank à la fin de chaque mandat.

## Règles actionnables

1. Format de rapport :
   ## [Titre de l'étape]
   **Statut** : ✅ VERT / ⚠️ PARTIEL / ❌ ROUGE
   **Fait** : ...
   **Tests** : ...
   **Anomalies** : ...
   **Suivant** : ...

2. Langue : français (sauf termes techniques anglais)

3. Honnêteté :
   - Signaler les anomalies, même mineures
   - Signaler les limites ("non testé", "non vérifié")
   - Ne jamais masquer un échec

4. Traçabilité :
   - Chaque action importante → dev\patch_integrity.log
   - Chaque anomalie → dev\crash.log
   - Chaque décision → dev\DECISIONS.md

5. MISE À JOUR AUTOMATIQUE DU MEMORY BANK (OBLIGATOIRE) :

   À la fin de CHAQUE mandat, AVANT de rendre la main, tu DOIS mettre à jour
   automatiquement ces deux fichiers :

   a) memory-bank\activeContext.md
      - Date : date du jour
      - Version actuelle : nouvelle version livrée
      - Travail en cours : mandat suivant (si applicable)
      - Prochaines étapes : liste mise à jour
      - Décisions récentes : nouvelles décisions (D-XXX)
      - Anomalies en cours : mise à jour
      - Points d'attention : mise à jour

   b) memory-bank\progress.md
      - Tableau des versions : ajouter la nouvelle ligne
      - Ce qui marche : ajouter les nouvelles fonctionnalités
      - Ce qui reste à faire : retirer ce qui est fait, ajouter le nouveau
      - Réalisations notables : mise à jour

   Cette mise à jour est AUTOMATIQUE. Tu n'attends PAS que l'utilisateur
   te le demande. Tu le fais à la fin de chaque mandat, sans exception.

6. Auto-régulation :
   - Si la charge dépasse la capacité, subdiviser
   - Documenter le choix dans dev\DECISIONS.md
   - Ne jamais forcer un mandat trop gros

## Interdictions
- Ne jamais dire "tout est parfait" sans preuve
- Ne jamais mentir sur un test
- Ne jamais cacher une anomalie
- Ne JAMAIS oublier la mise à jour du Memory Bank à la fin d'un mandat
