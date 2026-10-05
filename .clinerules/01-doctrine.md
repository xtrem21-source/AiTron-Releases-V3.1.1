# Règle 01 — Doctrine transactionnelle

## Principe
Toute modification suit cet ordre strict, sans exception :
SAUVEGARDE → PATCH → TEST → VALIDATION

## Règles actionnables

1. archive_installer() est la première instruction de main().
   - Copie install_AiTron_v3.py vers Installeur\install_AiTron_v3_AAAAMMJJ_HHMMSS.py.txt
   - Copie CHARTE.md vers Installeur\CHARTE_AAAAMMJJ_HHMMSS.md

2. Validation AST obligatoire avant toute écriture disque :
   - ast.parse(code)
   - compile(code, "<AITRON_DEPLOY_CODE>", "exec")
   - py_compile.compile(tmp, cfile=..., doraise=True)

3. Rollback obligatoire en cas d'échec :
   - Staging dans AiTron.new\
   - Bascule transactionnelle : AiTron\ → AiTron.old\ → AiTron.new\ → AiTron\
   - Jamais de suppression préalable

4. Garde préalable : refuser la reconstruction si un service tourne.
   - Vérifier data\pids.txt
   - _guard_running_services() avant tout déploiement

## Interdictions

- Ne jamais modifier le produit stable (AiTron\) sans passer par l'installeur
- Ne jamais supprimer un fichier sans le déplacer dans dev\old\ d'abord
- Ne jamais écrire hors de la sandbox
- Ne jamais faire de bascule destructive en amont (écarter → installer → purger)
