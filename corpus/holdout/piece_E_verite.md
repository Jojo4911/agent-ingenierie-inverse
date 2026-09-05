piece: E
origine: coin bas gauche du rectangle englobant, z=0 en face inferieure
bbox_x_mm: 90
bbox_y_mm: 60
bbox_z_mm: 20
corps:
  - nom: plaque_coins_coupes
    type: contour_extrude
    rectangle_englobant: {x0: 0, y0: 0, l_x_mm: 90, l_y_mm: 60}
    evidements: "2 coins coupés sur toute la hauteur : au coin haut gauche et au coin haut droit, à 45°, triangles rectangles et isocèles de 20 x 20"
    epaisseur_extrusion_mm: 20
nb_trous_traversants: 2
convention_comptage: trous = percages traversants uniquement ; borgnes et poches comptes separement
trous: [ {diametre_mm: 10, centre_x_mm: 10, centre_y_mm: 10},
         {diametre_mm: 10, centre_x_mm: 60, centre_y_mm: 10}, ]
nb_poches: 2
poches: [{forme: cylindrique, diametre_mm: 14, profondeur_mm: 12, centre_x_mm: 45, centre_y_mm: 12, face: superieure a z=20},
         {forme: rectangulaire, longueur_x_mm: 25, largeur_y_mm: 25, profondeur_mm: 5, origine_coin_bas_gauche_x_mm: 32.5, origine_coin_bas_gauche_y_mm: 25, face: superieure a z=20}]
volume_mm3: 91886
hors_perimetre: []
plan: {format: A4, echelle: 1, nb_vues: 3, nb_coupes: 1, rasterisation_px: 1619x2290, orientation: portrait}