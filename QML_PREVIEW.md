# Interface QML ZiRcoN — V1 candidate rc4

## Lancer

Dans le projet : **Lancer-ZiRcoN-Coach.vbs** ou `python run_app.py`.
Dans le paquet Windows : extraire tout le ZIP, ouvrir `ZiRcoN-Coach.exe`.
Fermer une éventuelle ancienne fenêtre avant de lancer ; la protection contre
les doubles ouvertures est commune aux deux interfaces.

Bel’Veth est le thème initial. **Bel’Veth / Turquoise** change instantanément
les couleurs, sans ouvrir une autre fenêtre ou refaire une analyse.
L’ancien lanceur Essayer-interface-QML.vbs force turquoise ;
Essayer-theme-Belveth.vbs force violet. Repli technique : `--classic`.

## Parcours, dans l’ordre

1. **Accueil** : dernier match à revoir et repères des 20 dernières parties.
2. **Mes parties** : compositions 5v5, objets réels sans emplacements vides,
   recherche par champion/rôle, filtres résultat/rôle/patch/favoris.
3. Une partie ouvre **Résumé**, **Coach**, **Objets**, **Déroulé**, **Notes**.
   Les équipes/statistiques finales restent séparées du contexte daté du build.
4. **Progression** : fenêtre 10/20/50 ou tout, agrégats, trois courbes et pool.
5. **Réglages** : compte EUW, clé masquée, vérification, activation et import.

Le parcours courant ne bascule plus vers l’ancienne fenêtre. Les clés ne sont
exposées ni dans les modèles de page, ni dans les messages/journaux affichés.
Une vérification seule n’active pas une clé ; une clé refusée conserve l’ancienne.

## Lire le bilan

La courbe d’or compare les équipes : doré/rose en violet, vert/rose en turquoise.
Une coupure est une information manquante, pas un zéro. Axes : temps et PO.
Les courbes de progression sont ordonnées par partie, des anciennes aux récentes ;
elles ne représentent pas le temps écoulé entre les games.
Le taux de victoire est glissant sur jusqu’à cinq parties à chaque relevé.

Coach : les pistes soutenues d’abord, puis les détails par thème, dépliables.
Les heures explicitement présentes donnent un repère dans Déroulé ; pas d’heure
inventée pour un contexte sans instant précis.
Objets : recommandations/alternatives existantes, achats conditionnels et adversaires
au moment du conseil. Anneau indicatif, sans probabilité ni garantie d’optimalité.

Notes : maximum 1000 caractères. Enregistrer pour conserver entre les ouvertures.
Les brouillons survivent à la navigation et aux mises à jour du même compte.
Enregistrer une note avant de changer de compte ; un avertissement protège la
fermeture avec des brouillons. Ils ne remplacent pas les analyses.

## Cadrage et limites

Viewport vérifié : 1600×960 et 1120×720. La taille initiale s’ajuste à l’espace
disponible du moniteur dans ces limites ; les longs identifiants sont élidés.
Les pages longues défilent verticalement. Contrôle automatique du débordement
horizontal des conteneurs de texte, plus inspection des captures représentatives.
Les animations peuvent être désactivées ; boutons utilisables au clavier.

Revue humaine sur le matériel réel, DPI, accessibilité complète et utilité des
conseils toujours requise. Les contrastes testés ne sont pas une certification.
Aucun moteur/analyzer n’est modifié ou automatiquement FROZEN.
