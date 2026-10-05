# ZiRcoN Coach

Un coach League of Legends après-match, local sur Windows : retrouver sa partie,
comprendre les observations disponibles et choisir une habitude à tester.

## Essayer la V1 candidate

Le [guide de démarrage](RELEASE_GUIDE.md) décrit la version portable, la connexion
Riot et les limites. Extraire le ZIP complet puis ouvrir `ZiRcoN-Coach.exe`.
La version candidate est `1.0.0-rc3` ; aucun historique ni identifiant n’est livré.

Cette révision ajoute la courbe d’or au résumé, des objectifs cliquables sans
chevauchement, des conseils plus courts et la compatibilité objets avec le patch
26.19 (catalogue 16.19.1). « Comprendre ce conseil » ouvre les explications.
Les emplacements sans objet sont invisibles dans l’historique et les vues de partie.

Les cinq sections d’une partie sont **Résumé**, **Coach**, **Objets**, **Déroulé**
et **Notes**. Les conseils reposent sur des observations explicites, pas sur une
preuve qu’une décision a causé le résultat. Les données insuffisantes conduisent
à une abstention. Les phases avant-match et pendant-match ne sont pas incluses.

## Développement

Sous Windows, avec Python 3.13 : créer un environnement virtuel, installer
`requirements.txt`, puis lancer `python run_app.py`. La version source conserve
ses chemins locaux et ne migre pas automatiquement les données.

Validation : `python -m app.stabilization_checks final`,
`python -m app.v01_visual_check`, puis `python -m build_optimizer.validation`.
Le dernier programme retourne intentionnellement 2 quand les gates techniques
passent mais que la revue humaine demeure requise. Lire son `zero_gate.json`.

Construction Windows : installer `requirements-build.txt`, puis
`python -m app.build_release`. Le constructeur teste un profil vierge et une
copie temporaire de l’historique local avant de produire le ZIP et son SHA-256.

État et résultats : [PROJECT_STATE.md](PROJECT_STATE.md), [LAST_RUN.md](LAST_RUN.md).
Les fondations FROZEN restent protégées ; aucune fusion dans `main` ni aucun
freeze automatique. La diffusion publique exige les démarches Riot et le dossier
de licences décrits dans les documents de livraison.
