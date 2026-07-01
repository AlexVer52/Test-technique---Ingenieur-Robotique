# Test technique - Ingénieur Robotique

## Besoin client

Le client souhaite automatiser une opération de tri manuel de pièces plastiques rouges et bleues arrivant sur un convoyeur existant. 
L’objectif est de saisir les pièces une par une à l’aide d’un robot collaboratif placé à côté du convoyeur, puis de les déposer dans deux bacs distincts selon leur couleur. Le client veut une solution simple à maintenir et peu coûteuse.

D’un point de vue robotique, le besoin principal n’est pas seulement de déplacer une pièce d’un point A vers un point B. 
Il faut garantir le cycle : détection, synchronisation avec le convoyeur, choix de la pièce à prendre, calcul du point d'accroche, suivi éventuel de la pièce en mouvement, prise, vérification, dépôt, et gestion des erreurs.

Deux points sont contraignants dans ce projet
1. La cadence à 30 pièces/minute
	    Cela signifie que **le cycle du robot doit prendre moins de 2 secondes**
2. La précision à ±0.1 mm.
	    Cette précision est relativement élevée pour une tâche de tri.

Dans cette configuration, je n'opterais pas nécessairement pour un robot collaboratif 6 axes. 
Pour cette opération, le besoin cinématique semble relativement simple : prendre une pièce sur un convoyeur puis la déposer dans l’un de deux bacs selon sa couleur. 
Si l'orientation de la pièce n'a pas besoin d'être contrôlée au dépôt, une solution 3 axes peut être suffisante. En revanche, si les pièces sont inclinées et que l'orientation devient une contrainte, un 4ème axe autour de Z peut être utile.

## Points à clarifier/challenger

Suite à la précédente partie, je demanderais des clarifications sur 2 points.

1. **Les pièces à manipuler**:
	    Pour designer un robot collaboratif performant et optimal, il faudrait les caractéristiques des pièces. 
	    Leurs dimensions, leurs masses, leurs formes, s'il y a une surface plane (qui pourrait justifier l'utilisation d'une ventouse) et si les pièces sont semblables entre elles.
	    Il serait également bien de savoir si les pièces sont fragiles ou déformables?

2. **Le convoyeur**:
	    Les pièces vont être en mouvement sur le convoyeur et donc il est nécessaire de connaître ses caractéristiques. Sa vitesse, si cette dernière est constante, s'il y a un **encodeur** ou s'il est possible d'en rajouter un. 
	    Nous savons déjà que le convoyeur tourne en continu et assumerons donc qu'il est impossible de l'arrêter pour prévoir une zone de prise dédiée.
	    La présence d'un encodeur me paraît nécessaire car même si le convoyeur a une vitesse constante, des variations de vitesse, des micro-arrêts ou des écarts de synchronisation vision-robot peuvent perturber les mesures.
	    Il faudrait aussi connaître les dimensions du convoyeur afin de designer la cinématique du robot.

Je challengerais **la précision** demandée car elle me paraît importante pour une tâche comme celle-là. Je voudrais demander ce qu'ils veulent dire par ±0.1 mm.
Il serait bon de clarifier si cette précision concerne :
    la position de dépôt,
    la position de préhension,
    la répétabilité robot,
    ou un autre critère

Le dernier point qui me semble important de mettre en évidence est la **durée disponible d'installation**. Il faudra préparer au maximum l'installation en amont et pas uniquement en simulation pour permettre une intégration fluide.

## Les risques techniques

Je vois 4 risques principaux, qui sont: **la cadence demandée, la prise sur convoyeur en mouvement, les pièces désorganisées sur le convoyeur ainsi que leur orientation et la demande de robustesse et de coût du robot**. 
Chacun de ces points sera traité dans la partie suivante.

## Architecture et logique robotique

Afin de limiter les risques identifiés précédemment et de proposer une solution robuste, simple et maintenable, je proposerais une architecture robotique basée sur un **robot collaboratif 4 axes** type robot SCARA.

L’objectif n’est pas de choisir automatiquement l’architecture la plus flexible, mais plutôt **la cinématique minimale répondant au besoin client**. Dans ce cas, le robot doit principalement être capable de :
- se positionner dans le plan du convoyeur : X, Y ;
- descendre et remonter pour saisir la pièce : Z ;
- orienter le préhenseur selon l’angle de la pièce : Rz.

Une architecture 4 axes de type X, Y, Z, Rz semble donc adaptée si les pièces restent globalement à plat sur le convoyeur. Elle permet de limiter la complexité mécanique, le coût et la maintenance, tout en assurant une bonne capacité de prise pour une opération répétitive de tri. 

Vous pouvez voir l'architecture dans le fichier **Architecture.pdf**.

### Choix du préhenseur

Le choix du préhenseur dépendra des caractéristiques réelles des pièces : géométrie, masse, état de surface, rigidité et accessibilité de la zone de prise.

Deux options principales peuvent être envisagées.

La première option est **une ventouse**. Elle serait pertinente si les pièces possèdent une surface suffisamment plane, large et accessible. Cette solution présente l’avantage d’être simple à commander, rapide à activer et généralement facile à maintenir.

La deuxième option est **une pince parallèle**. Elle peut offrir davantage de flexibilité si les pièces ne permettent pas une prise fiable par ventouse. En revanche, elle ajoute de la complexité : alignement plus précis avec la pièce, gestion de l’ouverture, force de serrage, risque de collision avec des pièces proches.

Dans une logique de simplicité, je privilégierais d’abord la ventouse si les essais sur pièces réelles confirment une prise fiable. Sinon, une pince parallèle ou un préhenseur plus spécifique devra être étudié.

### Limite principale de l’architecture 4 axes

Le principal point à valider concerne l’orientation réelle des pièces sur le convoyeur.

Si les pièces sont uniquement désaxées dans le plan du convoyeur, une architecture 4 axes convient bien. Le robot peut compenser cette orientation avec l’axe Rz du préhenseur.

En revanche, si les pièces sont inclinées en 3D, en appui sur une autre pièce ou partiellement superposées, le risque d’échec de prise augmente. Dans ce cas, une prise verticale avec un robot 4 axes peut être insuffisante : la ventouse peut ne pas adhérer correctement, la pince peut mal saisir la pièce, ou le préhenseur peut entrer en collision avec une pièce voisine.

Ce point doit donc être clarifié avant de valider définitivement l’architecture robotique.

### Réduction du risque de mauvaise prise

**Avant de complexifier le robot**, je privilégierais des solutions simples permettant de fiabiliser la prise :

- refuser les pièces trop proches, trop inclinées ou partiellement visibles ;
- demander à la vision un indicateur “pièce saisissable / non saisissable” ;
- utiliser un préhenseur tolérant : ventouse souple, ventouse à soufflet, pince avec doigts souples ;
- ajouter une compliance mécanique au niveau de l’outil pour absorber de légers défauts d’angle ou de hauteur ;
- ajouter un guidage mécanique simple en amont afin d’améliorer la présentation des pièces.

Cette approche me semble cohérente avec le besoin client : plutôt que d’utiliser directement un robot plus complexe, il est préférable de simplifier l’environnement et de rendre la prise plus tolérante.

Si les essais montrent malgré tout que les pièces sont régulièrement inclinées ou mal présentées, l’architecture 4 axes devra être challengée. Dans ce cas, un robot 6 axes ou un préhenseur spécifique pourrait devenir nécessaire.

### Équipements complémentaires

Pour fiabiliser la cellule, j’ajouterais les éléments suivants :

- **un éclairage stable** et contrôlé pour garantir une vision répétable ;
- **un capteur de vide ou de présence** sur le préhenseur pour confirmer la prise ;
- **un encodeur convoyeur** pour suivre précisément l’avancement des pièces ;
- **une interface opérateur** simple pour afficher l’état de la cellule, les compteurs, les erreurs et les commandes de marche/arrêt.

### Gestion des pièces détectées

Comme plusieurs pièces peuvent être visibles en même temps et arriver rapidement les unes après les autres, il est nécessaire de gérer une file d’attente des pièces détectées.

Cette file permet de :

- suivre les pièces détectées par la vision ;
- mettre à jour leur position en fonction de l’avancement du convoyeur ;
- sélectionner la pièce la plus pertinente à prendre ;
- ignorer les pièces non saisissables ;
- supprimer les pièces ayant quitté la zone atteignable par le robot.

Le robot ne doit donc pas forcément prendre la première pièce détectée, mais la première pièce valide, atteignable, suffisamment isolée, et compatible avec la fenêtre de prise.

### Interface opérateur

Enfin, une interface opérateur simple serait prévue afin de faciliter l’utilisation et la maintenance de la cellule. Elle afficherait notamment :

- l’état de la cellule : initialisation, attente pièce, prise, dépôt, erreur ;
- le nombre de pièces rouges triées ;
- le nombre de pièces bleues triées ;
- le nombre de défauts ou d’échecs de prise ;
- les messages d’erreur ;
- les commandes principales : marche, arrêt, réarmement.

L’objectif est de permettre à un opérateur de comprendre rapidement l’état de la cellule et d’intervenir facilement en cas de défaut.

## Informations attendues de la vision

Du côté vision, la caméra sera située au-dessus du convoyeur avec une rate relativement importante qui dépendra de la vitesse du convoyeur. J'attends comme informations de la part de mon collègue:
	- Identifiant pièce
    - La position x, y
    - La couleur
    - L'orientation de la pièce
    - La dimension si cette dernière est variable en fonction des pièces
    - Le timestamp (nécessaire pour l'encodeur)
	- Eventuellment un indicateur si la pièce est siasissable ou non

## Logique du robot
La logique robot est relativement simple avec une chaîne d'état: Initialization, part_detection, track_part, pick, drop, et return. Pour avoir plus d'informations sur cette partie, le fichier **logique_robotique.py** contient un pseudo-code décrivant les étapes.

## Gestion des erreurs

Une partie importante du développement d'un système robotique est la gestion des erreurs comme les pièces non détectées, les pièces non saisissables ou les échecs de prise ou de pose.

En cas d'échec de prise, je développerais une solution simple. **Ne pas tenter de rattraper la pièce et compter un défaut**. La même logique s'applique si il y a un drop avant le bac. Une erreur peut être envoyée à l'interface opérateur avec une description de l'erreur (mauvais drop, pièce non saisissable,...).


## Validation avant mise en service

La première étape de validation est une **simulation du robot et de son environnement** avec une implémentation de la logique contrôle, pour cela il faut les différentes informations demandées plus haut (vitesse du convoyeur, taille et forme des pièces,...). 
Après vérification que la logique en simulation fonctionne, il faudra **tester en environnement réel** avec un prototype car les deux jours d'installation me paraissent courts pour une validation complète.
	    - Test de saisie sur pièces réelles (simples, inclinées, proches d'une autre pièce)
	    - Test du cycle sur cadence attendue
	    - Test de communication vision-robot
	    - Test des défauts et de leur prise en charge

Afin de valider la solution, je proposerais 4 critères:
	    - Cadence est atteinte
	    - Taux d'échec inférieur à un certain seuil défini avec le client
	    - Implémentation avec opérateur fluide
	    - Gestion des défauts acceptables (redémarrage, aucun arrêt ou peu,...)
