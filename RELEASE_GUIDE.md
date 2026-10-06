# ZiRcoN Coach V1 — version candidate Windows

Cette version permet de consulter et analyser tes parties SoloQ EUW après match.
Elle fonctionne sous Windows 10/11 64 bits, sans installer Python.

## Démarrer

1. Extrais tout le ZIP dans un dossier de ton choix. Garde l’exécutable et son dossier `_internal` ensemble.
2. Ouvre `ZiRcoN-Coach.exe`.
3. Ouvre **Réglages**, puis renseigne ton Riot ID `Pseudo#TAG` et ta clé personnelle Riot.
4. Clique sur **Vérifier et enregistrer**, puis **Importer mes parties**.

La candidate rc5 utilise directement la nouvelle interface QML Bel’Veth.
Les boutons Bel’Veth / Turquoise changent la palette sans relancer l’application.
Le parcours courant, y compris les réglages, imports et notes, reste dans cette fenêtre.

Pour un usage personnel de développement, la clé est disponible sur le [portail Riot](https://developer.riotgames.com/).
Elle peut expirer : remplace-la dans Réglages. Aucune clé n’est fournie dans le paquet.

## Comprendre le bilan

- **Résumé** : les deux équipes, les statistiques finales, la courbe d’or et une piste « À retenir » lorsqu’elle est étayée.
- **Coach** : un constat court et un réflexe à tester. « Comprendre ce conseil » affiche les preuves et les nuances. Ouvre un thème pour voir ses événements.
- **Objets** : une piste d’achat liée à une situation de la partie. Le cercle donne un repère comparatif.
- **Déroulé** : l’écart d’or des équipes selon la minute. Au-dessus de zéro, ton équipe avait davantage d’or.
- **Notes** : ta leçon personnelle et les parties à revoir.

Survole une courbe pour lire son relevé. Dans Coach, clique sur une heure pour la mettre en évidence dans Déroulé.
Le doré indique l’avance de ton équipe dans le thème violet, le vert dans le thème turquoise ; le rose indique un retard. Une coupure indique un relevé manquant.
Le déroulé conserve les objectifs avec leur heure. Coach donne accès aux autres événements, dans ses thèmes dépliables.
Les grandes périodes sans heure précise ne disposent pas de raccourci vers un instant inventé.

Les conseils distinguent les reprises après mort, avant/après un objectif ou
suivies d’une mort, ainsi que les morts en avance/en retard et les périodes de
déplacements. Les détails proposent une question de replay et une alternative
conditionnelle. Un objectif pris plus tard n’est pas un compte à rebours d’apparition.
Aucun modèle de langage n’est encore connecté ; les textes restent produits localement.

Les observations ne prouvent pas qu’une décision a causé la victoire ou la défaite.
Un conseil d’objet peut manquer si le patch, l’historique ou l’inventaire ne permettent pas une proposition fiable.
La couverture exacte des objets porte sur les catalogues 16.8, 16.9, 16.11, 16.12, 16.14, 16.15, 16.16, 16.17, 16.18 et 16.19.
Le patch public 26.19 correspond au catalogue 16.19.1. Au début d’un nouveau patch,
le conseil peut attendre plusieurs parties comparables : les anciennes versions ne servent pas de référence de remplacement.

## Données et mises à jour

La version Windows conserve tes parties, notes, préférences et clé dans `%LOCALAPPDATA%\ZiRcoN-Coach`.
Remplacer le dossier de l’application garde ces données. Les parties déjà importées sont consultables hors connexion.
La clé est masquée dans l’interface ; son fichier local n’est pas chiffré. Ne partage pas ton dossier de données.
Le paquet distribué ne contient ni clé, ni compte, ni historique du développeur.
Les communications réseau concernent Riot Games et les images de Data Dragon ; aucun service de télémétrie n’est intégré.
La version source conserve ses anciens chemins de développement ; elle ne déplace pas ton historique existant.

Enregistre tes notes avant de quitter : les brouillons sont conservés pendant la
navigation, mais ne sont pas des notes persistantes. Un avertissement protège la
fermeture. Les favoris apparaissent dans le filtre de l’historique.

## Limites de cette livraison

Il s’agit d’une version candidate pour installation et essais personnels. La qualité des conseils reste à vérifier en jeu.
Une distribution publique avec import Riot nécessite l’enregistrement du produit et une solution d’accès de production approuvée par Riot :
[documentation du portail](https://developer.riotgames.com/docs/portal), [politiques générales](https://developer.riotgames.com/policies/general).
Le paquet n’est pas signé numériquement. Windows peut afficher une demande de vérification de l’éditeur.
Avant une diffusion publique, compléter aussi le dossier de conformité des licences Qt/PySide6 décrit dans `THIRD_PARTY_NOTICES.md`.

ZiRcoN Coach n’est pas affilié à Riot Games et ne reflète pas les opinions de Riot Games.
Riot Games et League of Legends sont des marques de Riot Games.

## Reproduire la livraison

Depuis le dépôt sous Windows : `python -m pip install -r requirements-build.txt`, puis `python -m app.build_release`.
Le constructeur vérifie le démarrage sur un profil vierge et, si disponible, une copie temporaire de l’historique local sans clé.
Le ZIP et son manifeste SHA-256 sont produits dans `dist/`.
