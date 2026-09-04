piece: C
origine: coin bas gauche du rectangle englobant, z=0 en face inferieure
bbox_x_mm: 120
bbox_y_mm: 80
bbox_z_mm: 15
epaisseur_extrusion_mm: 15
nb_trous_traversants: 4
convention_comptage: trous = percages traversants uniquement ; borgnes et poches comptes separement
trous: [ {diametre_mm: 8, centre_x_mm: 15, centre_y_mm: 15},
         {diametre_mm: 8, centre_x_mm: 15, centre_y_mm: 65},
         {diametre_mm: 8, centre_x_mm: 105, centre_y_mm: 15},
         {diametre_mm: 8, centre_x_mm: 105, centre_y_mm: 65}, ]
nb_poches: 2
poches: [{forme: cylindrique, diametre_mm: 12, profondeur_mm: 8, centre_x_mm: 85, centre_y_mm: 60, face: superieure a z=15},
         {forme: rectangulaire, longueur_x_mm: 40, largeur_y_mm: 25, profondeur_mm: 6, origine_coin_bas_gauche_x_mm: 35,    origine_coin_bas_gauche_y_mm: 25, face: superieure a z=15}]
volume_mm3: 134079
hors_perimetre: [percage borgne, "4x Ø8" pour définir le diamètre des 4 trous traversants, Annotation "Ra 3,2" sur la face du dessus → inutile, Tolérance de longueur de poche rectangulaire inutile "40 ±0,1", Profondeur de la poche rectangulaire comme annotation "▼6", chaine de cotes sur la position des trous traversans en x et en y, échelle 1:2, alignement des 4 trous traversants en x et en y implicite, "Tolérances générales ISO 2768-m" dans le cartouche → inutile]
plan: {format: A4, echelle: 1/2, nb_vues: 3, rasterisation_px: 2290x1619, identique aux pieces A et B}