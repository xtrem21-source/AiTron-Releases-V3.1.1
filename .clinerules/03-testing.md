# Règle 03 — Tests

## Principe
Bêta-testeur fou après chaque implémentation. Aucun bug laissé en vie.

## Règles actionnables

1. Après chaque modification, exécuter :
   - Test nominal (fonctionne comme avant)
   - Test de rupture (casse ce qui doit casser)
   - Test de portabilité (si applicable)

2. Tests obligatoires pour v3.1.1 :
   - Installation dans G:\V1\LocalAI-Projet\
   - Installation dans C:\AiTron-Test\
   - Installation avec --root D:\AiTron-Root-Test
   - Installation sur clé USB
   - Fallback de téléchargement (renommer le binaire local)
   - Cohérence avec le certificat v3.1.0

3. Arrêt propre obligatoire :
   - Vérifier 0 processus
   - Vérifier 0 port TCP
   - Vérifier 0 UDP 47653

4. Traçabilité :
   - dev\patch_integrity.log : résultats des tests
   - dev\crash.log : catégories PORTABILITY, FALLBACK_DOWNLOAD
   - dev\BETA_TEST_REPORT.md : rapport structuré

## Interdictions
- Ne jamais déclarer "fini" sans test physique
- Ne jamais masquer une anomalie
- Ne jamais supprimer une entrée de crash.log
