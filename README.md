# Bubble Dungeon

Prototype 2D en Python et Pygame inspire des arcade-platformers fixes.

## Lancer le jeu en local

```bash
python main.py
```

## Editer les niveaux

Un editeur Pygame est disponible pour modifier directement les fichiers JSON du dossier `levels/`.

```bash
python editor.py
```

Il peut aussi etre lance avec :

```bash
python main.py --editor
```

Controles de l'editeur :

- `Ctrl+S` ou `F5` : sauvegarder le niveau courant
- `Ctrl+R` : recharger le niveau courant et annuler les changements non sauvegardes
- `[` / `]` ou `Page Up` / `Page Down` : changer de niveau
- `1` : mode plateformes
- `2` : mode joueur
- `3` : mode ennemis
- `Suppr` / `Retour arriere` : supprimer l'element selectionne
- `Fleches` : deplacer l'element selectionne sur la grille
- `Shift + Fleches` : ajustement fin pixel par pixel
- clic gauche en mode plateformes : creer ou selectionner une plateforme
- glisser une plateforme selectionnee : la deplacer
- glisser sa poignee en bas a droite : la redimensionner
- clic gauche en mode joueur : placer le spawn du joueur
- clic gauche en mode ennemis : ajouter ou selectionner un ennemi
- clic droit sur une plateforme ou un ennemi : supprimer

## Generer une version web jouable

Le projet peut etre compile en page web avec [Pygbag](https://pygame-web.github.io/). Le code contient une boucle `async` compatible navigateur, tout en gardant le lancement local via `python main.py`.

Prerequis recommande : `uv` installe sur la machine.

```bash
scripts/build_web.sh
```

La version web est generee dans :

```text
build/web/
```

Pour tester localement :

```bash
scripts/serve_web.sh 8010
```

Puis ouvrir :

```text
http://127.0.0.1:8010/
```

Sur la page web, cliquer sur `Ready to start !`, puis appuyer sur `Entree` pour lancer la partie.

## Controles

- `Entree` : lancer la partie depuis l'ecran titre
- `A / D` ou `← / →` : bouger
- `Espace / W / ↑` : sauter
- `F / Ctrl` : tirer une bulle
- `Entree / R` : recommencer apres fin de campagne / game over
- `Esc` : quitter

## Ce qui est deja en place

- ecran titre puis phase `READY`
- 3 niveaux JSON
- transition verticale automatique entre les niveaux
- joueur, saut, gravite, plateformes
- ennemis patrouilleurs
- bulles, capture, elimination
- bulles qui restent bloquees aux bords/plafond si elles arrivent lentement
- bulles qui eclatent sur impact rapide contre un bord ou une plateforme
- collisions et repulsion legere entre bulles
- reaction en chaine entre bulles proches quand une bulle eclate
- joueur capable d'eclater les bulles en sautant vers le haut
- ennemis captures qui montent dans leur bulle et interagissent avec les autres bulles
- score, vies, invulnerabilite de respawn
- bonus collectables
- HUD arcade avec police pixel

## Comportement actuel des bulles

- la bulle part tres vite horizontalement
- elle parcourt une bonne distance, grossit puis freine brutalement
- ensuite elle monte
- un ennemi ne peut etre capture que tant que la bulle garde une vitesse horizontale suffisante
- les bulles sont actuellement plus grandes qu'au debut du prototype
- une bulle lente se bloque contre le plafond ou les bords au lieu de sortir de l'ecran
- une bulle rapide eclate si elle percute un bord ou une plateforme
- les bulles proches se repoussent legerement
- si une bulle eclate, les bulles tres proches eclatent aussi
- le joueur peut eclater une bulle en la touchant pendant la montee d'un saut
- une bulle contenant un ennemi monte, repousse les autres bulles et peut eclater par reaction en chaine

## Comportement actuel sur perte de vie

- le niveau ne recommence pas entierement
- le joueur joue une petite animation de mort
- il reapparait ensuite au spawn du niveau avec une courte invulnerabilite
