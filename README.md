# ZiRcoN Coach

Un coach League of Legends après-match, local sur Windows : retrouver sa partie,
comprendre les observations disponibles et choisir une habitude à tester.

## Nouvelle interface complète — V1 candidate 1.0.0-rc5

Dans le projet, double-cliquer **Lancer-ZiRcoN-Coach.vbs**, ou lancer
`python run_app.py`. L’interface QML Bel’Veth est maintenant le lancement normal :
violet profond, lavande et doré. Turquoise reste disponible dans la barre latérale.
Fermer une ancienne fenêtre ZiRcoN avant de relancer : une seule instance est autorisée.

Le parcours courant est entièrement dans QML :

- Accueil et historique avec les deux équipes, recherche, rôle, patch et favoris.
- Résumé de partie, coaching et ses détails dépliables, conseil d’objets contextuel,
  déroulé et notes personnelles.
- Progression sur 10/20/50 parties ou tout l’historique, courbes avec unités,
  relevés au survol et informations manquantes conservées.
- Réglages, compte Riot, clé masquée, vérification/activation et import avec suivi.
- Notes/favoris enregistrés localement, brouillons conservés pendant la navigation
  et avertissement avant de quitter avec une note non enregistrée.

Les moteurs, recettes, règles temporelles et fondations FROZEN sont inchangés.
Les conseils distinguent maintenant la situation, une question de replay, une
alternative conditionnelle et un réflexe à vérifier. [Préparation LLM](COACH_LANGUAGE_CONTRACT.md) :
contrat de faits/textes contrôlés prêt, aucun modèle ou service externe connecté.
Les conseils ne prouvent pas qu’une décision a causé le résultat ; des données
insuffisantes conduisent à une abstention. Avant-match/live-game restent hors scope.

## Version Windows autonome

Extraire entièrement le ZIP rc5, puis ouvrir `ZiRcoN-Coach.exe`.
Python/Qt et les catalogues exacts sont inclus, sans clé, compte ni historique.
Le [guide de démarrage](RELEASE_GUIDE.md) décrit les réglages et les limites.
Le manifeste dans `dist/` donne le SHA source, les vérifications et le SHA-256 du ZIP.

## Développement et vérification

Python 3.13, `requirements.txt`, puis `python run_app.py`.
Repli classique : `python run_app.py --classic`. Thème turquoise :
`python run_app.py --theme turquoise`. Les chemins de données source restent
inchangés ; aucune migration automatique de l’historique.

Contrôles : `python -m app.quick_checks`,
`python run_app.py --smoke-check --smoke-output logs/qml-final-layout.json`,
`python -m app.stabilization_checks final`.
Le smoke vérifie aussi le cadrage horizontal, les clés masquées et les brouillons.
Les tests de connexion utilisent des réponses simulées, sans contacter Riot.

Construction Windows : `requirements-build.txt`, puis
`python -m app.build_release`. Vérifie QML et le repli classique sur un profil
vierge et une copie isolée de l’historique, sans fournir de clé.

[Guide QML](QML_PREVIEW.md), [état du projet](PROJECT_STATE.md),
[dernier bilan](LAST_RUN.md). Candidate personnelle, pas une publication approuvée :
revue humaine, conditions Riot/licences/signature et NO FREEZE restent explicites.
