# Rapport d'évaluation : pipeline d'ingénierie inverse

Runs de bout en bout du 10/09/2026, exécutés par `evaluer.py` sur le pipeline réel, sans aucune fonction remplacée, une exécution par pièce. Modèle `claude-opus-5`, identique au spike. Prompts d'extraction et de génération gelés. Critères et valeurs de tolérance C3 repris du spike, règle d'application précisée en section 2. Une trace JSON par run dans `evaluations/`.

Corpus : A, B et C pour le développement (`corpus/dev/`), D et E tenus à l'écart (`corpus/holdout/`), jamais utilisés pendant le développement.

## 1. Ce qui passe, ce qui casse

| Pièce | Jeu | Verdict C3 | Tentatives | Primitives confrontées à la vérité |
|---|---|---|---|---|
| A | développement | conforme, 5 contrôles sur 5 | 1 | non |
| B | développement | non conforme : volume à -9,87 %, 4 contrôles sur 5 | 1 | oui : deux erreurs d'affectation |
| C | développement | conforme, 5 contrôles sur 5 | 1 | oui : conformes au millimètre |
| D | tenu à l'écart | conforme, 5 contrôles sur 5 | 1 | non |
| E | tenu à l'écart | conforme, 5 contrôles sur 5 | 1 | non |

### Ce qui passe

- A, C, D et E sont conformes en une tentative. Sur A, D et E, le volume produit égale celui de la référence à l'arrondi numérique près.
- Le jeu tenu à l'écart passe, deux pièces sur deux. Chacune a été exécutée une seule fois, sans retouche de prompt ni de code, sous une règle de relance figée avant le premier run et restée inutilisée.
- C, le plan réaliste (cartouche, tolérances, état de surface, chaînes de cotes, symbole de profondeur), est aussi conforme en position : les six entités usinées des primitives tombent au millimètre sur la vérité, dans un repère identique. L'erreur du run préalable de T28, profondeur du Ø12 non rattachée et alésage sorti traversant, ne s'est pas reproduite.
- Portée du verdict : « conforme » signifie enveloppe et quantité de matière justes. Sur A, D et E, la position des trous et des poches n'est pas contrôlée.

### Ce qui casse

B est non conforme sur le volume seul : 144 520 mm³ produits contre 160 339 mm³ de référence, soit -9,87 %. La boîte englobante et le comptage des trous sont conformes : seul le volume voit l'erreur. Elle combine deux défauts, tous deux dans la tranche basse, de z = 0 à z = 10.

1. **Base du cylindre.** Le cylindre Ø64 part du dessus de la semelle, à z = 10, au lieu de z = 0 : la cote 40, hauteur visible au-dessus de la semelle, est prise pour la hauteur du cylindre entier. Comme le cylindre déborde de la semelle (Ø64 pour 50 de large), les deux segments qui dépassent sous z = 10 manquent.
2. **Encoches.** Au lieu de s'ouvrir aux deux extrémités (30 × 20, centrées en y), elles s'ouvrent sur les deux grands côtés (80 × 15). Les dimensions 30 et 20 se retrouvent portées par la matière au lieu des vides : vue de dessus, la semelle en H paraît tournée d'un quart de tour.

Les deux défauts expliquent l'écart entier : le volume recalculé depuis les primitives vaut 144 520,3 mm³. Ils sont couplés, les encoches passant sous le disque du cylindre, et l'écart ne se répartit donc pas entre eux.

### Où naît l'erreur

- **À l'extraction, dans la compréhension de la géométrie, pas dans la lecture des valeurs.** Toutes les valeurs lues sur B sont justes, c'est leur affectation qui est fausse. Le profil des encoches est décrit sans ambiguïté, et faux ; la base du cylindre est portée par un champ structuré, `z_base_mm: 10`.
- **La génération recopie fidèlement les primitives.** `z_base_mm: 10` devient `workplane(offset=10)`, les échancrures de 80 × 15 deviennent `rect(80, 15)` en y = ±17,5. Sur B comme sur C, rien ne se perd et rien ne s'ajoute entre les primitives et le script.
- **La valeur dérivée revient, sans effet.** `bbox_y_mm` est lu à 50 au lieu de 64, comme au spike. Le script ne l'utilise pas, et la boîte englobante, mesurée sur le solide, sort conforme : la contrainte 1 tient sur le système final.

### Comparaisons entre runs d'un même plan

- **B, du spike à T40.** Le défaut du cylindre revient à l'identique : les -2,382 % du spike sont exactement sa contribution seule, -3 818,7 mm³. Les encoches, justes au spike, sont fausses en T40.
- **C, de T28 à T40.** La profondeur du Ø12, non rattachée en T28, l'est correctement en T40.
- **Lien avec les incertitudes déclarées.** Les deux zones qui ont varié d'un run à l'autre figurent parmi les incertitudes déclarées en T40 : les trois premières de B portent sur les encoches, la première et la troisième de C sur le rattachement et la face du Ø12. Le cylindre de B, absent des incertitudes, sort faux deux fois à l'identique. Deux observations, pas une règle.

## 2. Taux mesurés

Chaque taux porte son dénominateur : sur cinq pièces, un pourcentage afficherait une précision que la mesure n'a pas. Le jeu de développement (A, B, C) a servi pendant le développement ; seul le jeu tenu à l'écart (D, E) mesure le comportement sur des plans jamais vus. Le détail par pièce est dans la section 1.

| Critère           | Question                                                        | Résultat                                                            |
|-------------------|-----------------------------------------------------------------|---------------------------------------------------------------------|
| C2 Exécution      | Le script généré s'exécute-t-il et produit-il un fichier STEP ? | 5 runs sur 5 en tentative 1                                         |
| C3 Correspondance | Le solide produit correspond-il au STEP de référence ?          | 4 pièces sur 5 : 2 sur 3 en développement, 2 sur 2 tenues à l'écart |
| C1 Extraction     | Les primitives décrivent-elles correctement la pièce ?          | Mesuré sur 2 pièces sur 5 : B fausse en géométrie, C juste          |

### C2 : exécution

Mesure directe : le champ `tentatives` de chaque trace. Les cinq runs produisent un fichier à la première tentative, sans `error_message`, développement et jeu tenu à l'écart confondus. La boucle de reprise n'a donc jamais été empruntée en run réel.

Hors taux : les runs à fautes injectées de T39. Ils établissent que la boucle fonctionne, pas la fréquence à laquelle elle sert.

### C3 : correspondance

La référence de C3 n'est pas le plan mais un solide : le STEP modélisé à la main pour chaque pièce du corpus. `evaluer.py` mesure les deux solides de la même façon et les compare.

- **Contrôles** : les trois dimensions de la boîte englobante, le nombre de trous traversants, le volume. Le nombre de poches, que la mesure ne sait pas établir, vaut `null` des deux côtés sur les cinq pièces : déclaré non vérifiable, il sort du décompte, d'où cinq contrôles et non six.
- **Tolérances** : `compare()` (`verification.py`) déclare un contrôle conforme si l'écart est d'au plus 0,5 mm en absolu ou d'au plus 1 % en relatif à la référence, les deux tolérances étant alternatives. Le comptage exige donc l'égalité. Le script du spike, `verify.py`, appliquait 0,5 mm aux dimensions et 1 % au volume, séparément : au-delà de 50 mm, `compare()` est plus large sur les dimensions. Tous les écarts de boîte englobante et de comptage étant nuls à l'arrondi numérique près, aucun verdict ne dépend de cette différence.
- **Résultat** : B est la seule pièce non conforme, sur le volume seul.
- **Erreur composée** : chaque run enchaîne l'extraction brute et la génération, sans correction manuelle entre les deux. L'écart de volume est donc l'erreur composée du système final : nulle à l'arrondi numérique près sur A, C, D et E, -9,87 % sur B. La comparaison avec le spike (-2,382 %) est dans la section 1.

### C1 : extraction

Mesure manuelle, entité par entité, des primitives contre la vérité terrain. Faite sur deux pièces, là où un résultat demandait une explication : B parce qu'elle échoue en C3 (T44), C parce que c'est le plan réaliste (T45).

- **B** : toutes les cotes lues sont justes, deux affectations sont fausses. La cote 40, hauteur du cylindre au-dessus de la semelle, devient la hauteur du cylindre entier ; les cotes 30 et 20 décrivent la matière au lieu des encoches. Au sens du spike, c'est une erreur de géométrie, pas de lecture.
- **C** : les six entités usinées tombent au millimètre sur la vérité, face d'usinage comprise.
- **A, D, E** : non mesuré. C1 ne se déduit pas de C3, une pièce conforme pouvant porter un trou mal placé (section 3).

Hors C1 : la valeur dérivée `bbox_y_mm`, lue à 50 au lieu de 64 sur B, n'est pas utilisée par le script (contrainte 1, section 1).

### Plantage au teardown

Une *segmentation fault* est le plantage d'un code natif qui accède à une zone mémoire qui ne lui appartient pas : le système d'exploitation tue le processus. Le plantage est attribué à OCCT, le noyau géométrique C++ que CadQuery appelle, et survient au teardown, pendant la fermeture du processus.

- **Fréquence** : 3 runs sur 5, un sur trois en développement et les deux tenus à l'écart. Le plantage ne figure pas dans les traces, il est relevé à l'exécution.
- **Moment** : toujours après les mesures. Chaque trace est réécrite une fois les mesures faites, et les cinq contiennent mesures et verdicts : aucun résultat n'est perdu.
- **Traitement** : neutralisé, non réparé. `evaluer.py` exécute une pièce par processus : un plantage n'emporte que le processus d'une pièce déjà mesurée. Même principe que la contrainte 2 : le résultat se lit dans le fichier écrit, pas dans le code de sortie. La réparation est hors périmètre.

## 3. Limites nommées

Chaque limite est donnée avec sa preuve et sa conséquence.

### Les angles morts des trois grandeurs

La boîte englobante, le comptage des traversants et le volume contrôlent l'enveloppe et la quantité de matière. Ils ne contrôlent ni l'emplacement ni la taille fine des entités. Calculs sur A, plaque de 84 × 52 × 12 percée de deux Ø8,5, à la tolérance de 1 % sur le volume :

- un traversant déplacé dans la matière ne modifie aucune des trois grandeurs ;
- les deux trous pèsent 2,67 % du volume de la pièce ;
- un seul trou lu à n'importe quel diamètre entre Ø4,25 et Ø11,24 passe ;
- lus tous deux au même diamètre faux, les deux trous passent entre Ø6,72 et Ø9,97.

Deux autres cas relèvent du même mécanisme :

- **Face d'usinage** : une poche ou un borgne usiné sur la mauvaise face garde les trois grandeurs. C, D et E déclarent cette face incertaine ; seule C a été confrontée à la vérité, et elle est juste.
- **Poches** : non comptées, elles ne sont contrôlées que par le volume pour leur présence et leur taille, et par rien pour leur position.

Conséquence : « conforme » signifie enveloppe et quantité de matière justes, rien de plus. La position des entités de A, D et E n'est pas contrôlée et ne le sera pas : ce serait un critère ajouté après les résultats.

### Aucune grandeur n'est suffisante seule

Deux erreurs réelles, chacune vue par une seule des trois grandeurs :

- **C, run préalable de T28, hors taux** : alésage Ø12 sorti traversant. Volume à -0,59 %, dans la tolérance ; seul le comptage a vu l'erreur.
- **B, run de T40** : boîte englobante et comptage conformes ; seul le volume a vu l'erreur, à -9,87 %.

Conséquence : les trois grandeurs ensemble, comme l'impose la contrainte 4. Sans le comptage, C passait en T28 ; sans le volume, B passait en T40.

### L'usage sans vérité terrain

En évaluation, le STEP de référence sert de corrigé. En usage réel, l'utilisateur n'a que le plan : s'il avait le modèle 3D, il n'aurait pas besoin de l'outil. La vérification ne peut alors comparer le solide qu'aux primitives, et seuls deux contrôles restent calculables : la hauteur et le nombre de traversants. Les dimensions en X et Y et le volume attendus ne se calculent pas, le profil étant décrit en texte libre ; la boîte que le modèle déclare est une valeur dérivée, écartée par la contrainte 1.

Preuve : sur B, la hauteur (50 mm) et le comptage (aucun traversant) sont justes. B aurait été livré sans alerte.

Conséquence : la contrainte 4 protège l'évaluation, pas l'utilisateur. Un contrôle volumique en usage exigerait l'aire de section dans le schéma des primitives, changement refusé en T34. Les incertitudes que déclare le modèle ne compensent pas : sur B, elles signalaient les encoches, jamais le cylindre, pourtant faux deux fois à l'identique.

### La variance

Le modèle ne rend pas toujours la même extraction pour un même plan : un run par pièce mesure un tirage, pas un taux. Preuve : les encoches de B, justes au spike, sont fausses en T40 ; le Ø12 de C, non rattaché en T28, est juste en T40.

Conséquence : les taux de la section 2 décrivent cinq tirages. La variance n'est pas mesurée et rien n'a été relancé, par choix de cadrage : une exécution par pièce, sous une règle fixée avant le premier run.

### Le corpus

Cinq pièces, dans un périmètre borné (contours extrudés, trous traversants et borgnes, poches rectangulaires), sur des plans propres et normalisés, restriction de cadrage décidée après le run de T28. Tous les plans sont dessinés par une seule personne, l'auteur du projet.

Conséquence : le jeu tenu à l'écart protège contre un biais, l'ajustement des prompts sur les pièces de test. Il ne protège pas contre un autre : toutes les pièces sortent de la même main. Rien n'est établi sur les plans d'un autre dessinateur, scannés ou hors normes, ni hors du périmètre.

### Deux limites de détail

- **`_traversant`** : un trou dont l'axe prolongé rencontre de la matière ailleurs dans la pièce est compté borgne, même s'il traverse la paroi où il est percé. Le cas ne se présente sur aucune des cinq pièces.
- **Champs interprétés de façon variable** : d'après la note de T28, le modèle nomme les vues de C autrement que le plan ; et `position_x_mm` et `position_y_mm` désignent le coin du contour sur A et E, son centre sur B, C et D. Sans effet observé : le script n'utilise pas les étiquettes de vue, et la génération a absorbé les deux conventions.