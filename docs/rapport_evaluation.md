# Rapport d'évaluation : pipeline d'ingénierie inverse

Runs de bout en bout du 10/09/2026, exécutés par `evaluer.py` sur le pipeline réel, sans aucune fonction remplacée, une exécution par pièce. Modèle `claude-opus-5`, identique au spike. Prompts d'extraction et de génération gelés. Critères et tolérances C3 repris du spike sans retouche. Une trace JSON par run dans `evaluations/`.

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
