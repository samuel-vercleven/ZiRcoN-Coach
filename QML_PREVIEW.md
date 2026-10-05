# Qt Quick / QML — aperçu ZiRcoN

## Essayer

Double-cliquer `Essayer-interface-QML.vbs` dans le projet. Le lanceur utilise
l’environnement Python existant, sans console ni boucle de relancement.
Alternative : `.venv\Scripts\python.exe run_app.py --qml`.

La protection contre les doubles ouvertures est partagée avec la version
classique : fermer une éventuelle fenêtre ZiRcoN déjà ouverte avant le lancement.

## Ce qui fonctionne

- Accueil, historique filtrable avec les deux équipes, progression réelle.
- Partie : Résumé, Coach, Objets, Déroulé des objectifs enregistrés.
- Inventaires sans cases vides, compositions, KDA, CS, or, courbe signée.
  Survol d’un participant : dégâts, vision et rôle disponibles.
- Conseils issus des observations étayées, détails dépliables.
- Conseil d’achat, adversaires observés à son instant, achats conditionnels,
  alternatives, anneau de pertinence sans `/100`.
- Navigation dans une seule fenêtre ; chargement du build en arrière-plan.
- Interface classique dans le même processus pour les réglages, imports,
  notes et analyses détaillées. Bouton pour revenir à l’aperçu.
- Animations désactivables, accès clavier aux boutons et aux parties.

## Limites explicites

Exploration native Qt Quick, pas une interface 3D ni une migration complète.
Les surfaces/éclairages et animations sont natifs, sans nouveau moteur de thème.
La progression présente les agrégats et le nombre de parties par champion ;
les tendances avancées existantes restent accessibles dans la version classique.
Images manquantes : fond de secours ; pas de données ou de conseils inventés.
La formulation et les seuils analytiques existants restent inchangés.

Le ZIP `1.0.0-rc3` livré précédemment n’a pas été reconstruit pour cet aperçu.
La recette de construction inclut maintenant les sources QML, mais le nouveau
bundle Qt Quick n’a pas été validé ici. Essayer la version source ci-dessus.

## Vérification

`python -m app.quick_checks` : contrats de présentation, données manquantes,
contexte temporel conservé, livraison sur le thread graphique, cache et comptes.

`python run_app.py --qml --smoke-check --smoke-output logs/qml-smoke.json` :
navigation réelle, trois parties locales lorsque présentes, quatre onglets,
captures 1600×960 / 1120×720, passage classique et retour, arrêt propre.
Captures locales dans `.cache/zircon/quick-visual-check`.
Le mode de vérification n’effectue pas de téléchargement d’images QML.

Le profil vierge utilise un dossier de données séparé, sans remplacer l’historique.
Vérifications automatisées sur le rendu logiciel ; lancement Windows normal et
capture d’accueil aussi inspectés. Revue complète sur écran / rendu GPU,
contraste et mise à l’échelle Windows à poursuivre avec l’utilisateur.

TECHNICAL PASS / REVIEW_REQUIRED pour le produit — NO FREEZE.
