# Logiciels et ressources tiers

ZiRcoN Coach utilise Python (licence PSF), PySide6 / Qt (LGPLv3 et licences associées),
Requests (Apache 2.0), urllib3 (MIT), certifi (MPL 2.0), charset-normalizer (MIT),
idna (BSD) et python-dotenv (BSD). Les textes fournis par les distributions Python
sont placés dans le dossier `licenses/` de la livraison.

PyInstaller construit le paquet selon sa licence GPL et son exception permettant
la distribution des exécutables produits. La livraison en dossier conserve les
bibliothèques Qt séparées dans `_internal`, permettant leur remplacement.

Cette livraison est une candidate pour essais locaux, pas une autorisation de
diffusion publique. Avant de la distribuer, compléter la fourniture des sources
correspondantes Qt/PySide6, des textes GPL/LGPL applicables et des notices des
composants intégrés. Les roues Python installées ici n’incluent qu’un texte de
licence commerciale Qt, bien que leurs métadonnées indiquent aussi GPL/LGPL.
La copie des notices disponibles ne remplace pas cette vérification.

Les catalogues, noms et images League of Legends sont des ressources Riot Games.
Ils sont utilisés pour afficher et expliquer des statistiques de partie.
ZiRcoN Coach n’est pas affilié à Riot Games et ne reflète pas ses opinions.

Sources : [Qt](https://www.qt.io/licensing/open-source-lgpl-obligations),
[PyInstaller](https://pyinstaller.org/en/stable/license.html),
[Riot Games](https://developer.riotgames.com/policies/general).
