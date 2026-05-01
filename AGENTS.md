# AGENTS.md

## Objectif du projet

Créer un jeu 2D en Python avec Pygame, inspiré du gameplay arcade de type Bubble Bobble, mais avec une identité originale.

Le jeu doit être développé progressivement en vibe-coding avec Codex dans VSCode.

Nom provisoire du jeu : `Bubble Dungeon`



L’objectif est de créer un jeu similaire dans l’esprit :
- plateforme 2D fixe ;
- personnage qui saute ;
- bulles/projectiles ;
- ennemis capturables ;
- niveaux courts ;
- scoring arcade ;
- progression simple.

---

## Technologie imposée

Utiliser uniquement :

- Python 3.11 ou supérieur
- Pygame
- Aucun moteur externe
- Aucun framework lourd
- Pas d’assets propriétaires

Le projet doit pouvoir se lancer avec :

```bash
python main.py
```

---

## Etat actuel du projet

Le projet n'est plus vide. Une base jouable existe deja sous le nom `Bubble Dungeon`.

Structure actuelle :

```text
bubble_dungeon/
├── main.py
├── editor.py
├── README.md
├── AGENTS.md
├── assets/
│   ├── fonts/
│   └── sprites/
├── levels/
│   ├── level_01.json
│   ├── level_02.json
│   └── level_03.json
└── src/
    ├── assets.py
    ├── camera.py
    ├── game.py
    ├── level.py
    ├── settings.py
    ├── states.py
    ├── entities/
    ├── systems/
    └── ui/
```

## Fonctionnalites deja implementees

- fenetre Pygame et boucle de jeu
- resolution logique retro `224x256`
- fenetre agrandie par `WINDOW_SCALE` dans `src/settings.py`
- classe `Game`
- chargement des niveaux JSON
- joueur avec deplacement, saut, gravite et collisions simples
- saut plus tolerant avec `jump buffer` et `coyote time`
- plateformes fixes
- ennemis qui patrouillent
- ennemis avec variantes sauvegardees dans les niveaux
- tir de bulles
- capture des ennemis dans les bulles
- elimination des ennemis captures
- score
- vies
- invulnerabilite de spawn / respawn
- bonus ramassables avec petit arc de saut
- ecran titre
- phase `READY`
- transition verticale automatique entre niveaux
- fin de campagne et game over
- HUD arcade avec police `assets/fonts/emulogic.ttf`
- sprites historiques et fallbacks charges depuis `assets/sprites/sprites.png`
- sprites joueur charges depuis `assets/sprites/player_animations/`
- animation de mort du joueur depuis `assets/sprites/player_animations/death*.png`
- animations de bulles et eclatement depuis `assets/sprites/bobbles_animations/`
- Zen-Chan charge depuis `assets/sprites/zen_chan/` sur la variante ennemie `0`
- Mighta charge depuis `assets/sprites/mighta/` sur la variante ennemie `1`
- items / bonus encore charges depuis la spritesheet
- editeur de niveaux lanceable avec `python editor.py` ou `python main.py --editor`
- palette d'ennemis dans l'editeur pour choisir la variante a placer
- bulles avec dash horizontal rapide, freinage brutal, croissance puis montee
- capture d'ennemi seulement pendant la phase de deplacement horizontal rapide
- bulles agrandies avec hitbox coherente avec le visuel
- bulles bloquees aux bords/plafond quand elles arrivent lentement
- bulles qui eclatent sur impact rapide contre un bord ou une plateforme
- collisions et repulsion legere entre bulles
- reaction en chaine entre bulles proches quand une bulle eclate
- joueur capable d'eclater les bulles en sautant vers le haut
- ennemis captures qui montent dans leur bulle, repoussent les autres bulles et eclatent par reaction en chaine
- quand la bulle d'un ennemi capture eclate, l'ennemi joue une animation de mort
- l'ennemi mort part en arc parabolique, reste dans l'aire de jeu, et son animation de mort boucle pendant la trajectoire
- le bonus d'un ennemi mort apparait seulement quand l'ennemi touche le sol ou une plateforme

## Comportements importants a conserver

- le jeu se lance avec `python main.py`
- l'editeur se lance avec `python editor.py`
- la logique de jeu reste en `224x256`, la taille de fenetre depend de `WINDOW_SCALE`
- pendant `READY`, les entites tombent sous gravite, mais le joueur ne peut pas bouger
- quand le joueur perd une vie, le niveau ne redemarre pas entierement
- le joueur reapparait au point de depart du niveau avec invulnerabilite
- l'animation de mort du joueur issue de `player_animations/death*.png` dure 2 secondes avant le respawn
- pendant sa mort, le joueur continue a tomber s'il etait en l'air
- aucun overlay sombre ou message `OOPS!` ne doit masquer l'animation de mort
- les niveaux acceptent les ennemis au format `[x, y, variant]`
- les anciens spawns ennemis `[x, y]` restent compatibles
- quand le dernier ennemi meurt, il y a un delai avant la transition pour laisser le temps de ramasser le dernier bonus
- le passage au niveau suivant est automatique, sans appui touche
- une bulle ne capture pas un ennemi pendant sa montee, seulement si sa vitesse horizontale est encore suffisante
- la bulle part tres vite horizontalement, parcourt une bonne distance, grossit, freine fort puis monte
- une bulle lente reste dans la scene au contact des bords ou du plafond
- une bulle rapide eclate sur impact avec un bord ou une plateforme
- les bulles libres et les bulles contenant un ennemi se repoussent legerement
- si une bulle eclate, les bulles tres proches eclatent aussi
- le joueur ne peut eclater une bulle que pendant la montee d'un saut
- une bulle contenant un ennemi continue a monter et peut etre eclatee par une autre bulle proche
- quand une bulle contenant un ennemi eclate, l'ennemi ne disparait pas instantanement
- l'ennemi mort garde une impulsion verticale et horizontale, rebondit sur les bords de l'ecran et genere son item a l'atterrissage
- les sprites d'ennemis sont flippes horizontalement selon leur direction de deplacement

## Fichiers centraux

- `main.py` : point d'entree
- `editor.py` : point d'entree de l'editeur
- `src/game.py` : boucle principale, etats, transitions, gameplay
- `src/settings.py` : constantes globales
- `src/assets.py` : chargement des spritesheets, dossiers d'animations, police et surfaces
- `src/level.py` : chargement / decouverte des niveaux
- `src/editor.py` : edition des niveaux, grille, palette ennemis, sauvegarde JSON
- `src/entities/` : joueur, ennemi, bulle, bonus, particules
- `src/ui/` : HUD, overlays, ecran titre

## Priorites naturelles pour la suite

- ajouter plus tard un point d'attraction des bulles dans les niveaux
- ajouter des power-ups jouables a partir des icones deja presentes
- enrichir les niveaux et leur rythme
- continuer a verifier les decoupes exactes dans `assets/sprites/sprites.png` quand une animation fallback semble decalee
- continuer a completer les dossiers dedies pour les variantes ennemies restantes
- ajouter sons et musique originaux
- ameliorer les animations
- ajouter un vrai menu / ecran de selection / attract mode
- stabiliser et nettoyer le code si la base gameplay est jugee suffisante
