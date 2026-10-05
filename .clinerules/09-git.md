# Regle 09 - Git

## Principe
Le projet est versionne avec Git.
Chaque modification significative fait l'objet d'un commit.

## Regles actionnables

1. Le depot Git est cree a l'initialisation du projet.
2. Chaque version (vX.Y.Z) fait l'objet d'un tag Git.
3. Chaque commit suit le format :
   type(scope): description courte
   Types : init, feat, fix, docs, refactor, test, chore, style
4. Avant chaque commit :
   - Verifier que l'AST est valide
   - Verifier que les tests passent
   - Verifier que le Memory Bank est a jour
5. A la fin de CHAQUE mandat, faire un commit avec un message clair.
6. Le fichier .gitignore exclut :
   - log/
   - dev/crash.log
   - build/
   - __pycache__/
   - *.pyc
   - *.pyo
   - .env
   - config/cloud-keys.env
   - config/keys.env

## Format de message de commit

    <type>(<scope>): <description>

    <corps optionnel>

    Version: vX.Y.Z

## Interdictions
- Ne jamais commit sans avoir valide l'AST
- Ne jamais commit un etat casse
- Ne jamais commit des fichiers sensibles (cloud-keys.env, keys.env, etc.)
- Ne jamais forcer un push (--force)
- Ne jamais commit sur une branche protegee (main/master) sans validation
