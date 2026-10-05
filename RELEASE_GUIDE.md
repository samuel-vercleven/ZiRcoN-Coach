# ZiRcoN Coach V1 — version candidate Windows

Cette version permet de consulter et analyser tes parties SoloQ EUW après match.
Elle fonctionne sous Windows 10/11 64 bits, sans installer Python.

## Démarrer

1. Extrais tout le ZIP dans un dossier de ton choix. Garde l’exécutable et son dossier `_internal` ensemble.
2. Ouvre `ZiRcoN-Coach.exe`.
3. Clique sur **Configurer mon compte**, puis renseigne ton Riot ID `Pseudo#TAG` et ta clé personnelle Riot.
4. Clique sur **Enregistrer et activer**, puis **Importer mes parties**.

Pour un usage personnel de développement, la clé est disponible sur le [portail Riot](https://developer.riotgames.com/).
Elle peut expirer : remplace-la dans Réglages. Aucune clé n’est fournie dans le paquet.

## Comprendre le bilan

- **Résumé** : les deux équipes, les statistiques finales et une seule piste « À retenir » lorsqu’elle est étayée.
- **Coach** : observation, repères disponibles et habitude à tester. Ouvre un thème pour voir ses événements.
- **Objets** : une piste d’achat liée à une situation de la partie. Le cercle donne un repère comparatif.
- **Déroulé** : l’écart d’or des équipes selon la minute. Au-dessus de zéro, ton équipe avait davantage d’or.
- **Notes** : ta leçon personnelle et les parties à revoir.

Survole une courbe pour lire son relevé. Dans Coach, clique sur une heure pour la mettre en évidence dans Déroulé.
Les grandes périodes sans heure précise ne disposent pas de raccourci vers un instant inventé.

Les observations ne prouvent pas qu’une décision a causé la victoire ou la défaite.
Un conseil d’objet peut manquer si le patch, l’historique ou l’inventaire ne permettent pas une proposition fiable.
La couverture exacte des objets porte sur les patchs 16.8, 16.9, 16.11, 16.12, 16.14, 16.15, 16.16, 16.17 et 16.18.

## Données et mises à jour

La version Windows conserve tes parties, notes, préférences et clé dans `%LOCALAPPDATA%\ZiRcoN-Coach`.
Remplacer le dossier de l’application garde ces données. Les parties déjà importées sont consultables hors connexion.
La clé est masquée dans l’interface ; son fichier local n’est pas chiffré. Ne partage pas ton dossier de données.
Le paquet distribué ne contient ni clé, ni compte, ni historique du développeur.
Les communications réseau concernent Riot Games et les images de Data Dragon ; aucun service de télémétrie n’est intégré.
La version source conserve ses anciens chemins de développement ; elle ne déplace pas ton historique existant.

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
