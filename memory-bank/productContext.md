# Product Context — Pourquoi AiTron V3

## Le problème
- LocalAI officiel **ne publie pas de binaire Windows**
- Les solutions existantes (Lemonade, LM Studio, GPT4All) sont **lourdes** (Electron, Docker)
- Aucune solution ne combine : installeur unique + arborescence ouverte + doctrine transactionnelle + portabilité clé USB

## La solution
AiTron V3 est un **fork de LocalAI** (licence MIT) enrichi d'une **couche d'orchestration souveraine** pour Windows :
- Installeur unique auto-suffisant
- Arborescence ouverte (moteur + backends + configs séparés)
- Doctrine transactionnelle (sauvegarde, AST, rollback)
- Portabilité clé USB
- Traçabilité complète

## Ce qui distingue AiTron V3

1. **Installeur unique** (~330 Ko) qui reconstruit tout
2. **Doctrine transactionnelle** : sauvegarde ante-exécution, boîte noire, validation AST triple, rollback
3. **Bêta-testeur fou** : validation physique après chaque incrément
4. **Arborescence ouverte** : chaque composant est remplaçable individuellement
5. **Portabilité** : détection dynamique du répertoire, fallbacks de téléchargement
6. **Certification** : audit externe, `CHECK_DE_CONTRÔLE_FINAL.log`

## Fonctionnalités clés

- **Multi-modal** : texte, vision, image, audio, TTS
- **RAG multi-format** : PDF, Word, Excel, code, images (NumPy, sans faiss)
- **GraphRAG** : extraction par LLM local
- **MCP** : 6 outils standardisés (SDK officiel)
- **Failover SSE** : bufferisation + bascule locale/cloud
- **Filtre PII** : masquage réversible best-effort
- **DirectML/NPU** : repli CPU automatique
- **Speculative Decoding** : TEXT-ONLY, OPT-IN
- **Espace hermétique** : AES-256-GCM au repos
- **Profil apprenant** : auto-régulation à chaud
- **Fédération RPC** : calcul distribué
- **i18n** : FR/EN avec bascule à chaud

## Ce qu'AiTron V3 n'est pas
- Pas un produit grand public (pas de GUI native)
- Pas un serveur multi-utilisateur (mono-utilisateur)
- Pas un remplacement de LocalAI officiel (c'est un fork)

## Vision
Devenir **l'outil de référence** pour les utilisateurs Windows qui veulent une stack IA locale souveraine, portable, et entièrement sous leur contrôle.
