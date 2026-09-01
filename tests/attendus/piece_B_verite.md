piece: B
origine: coin bas gauche du rectangle englobant de la plaque en H, z=0 en face inferieure
bbox_x_mm: 140
bbox_y_mm: 64
bbox_z_mm: 50
etendue_y_mm: de -7 a 57 dans ce repere, le cylindre deborde la plaque
corps:
  - nom: plaque_H
    type: contour_extrude
    rectangle_englobant: {x0: 0, y0: 0, l_x_mm: 140, l_y_mm: 50}
    evidements: [{x0: 0,   y0: 15, l_x_mm: 30, l_y_mm: 20},
                 {x0: 110, y0: 15, l_x_mm: 30, l_y_mm: 20}]
    hauteur_extrusion_mm: 10
    z_base_mm: 0
  - nom: cylindre
    type: cercle_extrude
    diametre_mm: 64
    centre_x_mm: 70
    centre_y_mm: 25
    hauteur_extrusion_mm: 50
    z_base_mm: 0
operation: union des deux corps
nb_trous_traversants: 0
trous: []
nb_poches: 1
poches: [{forme: cylindrique, diametre_mm: 40, profondeur_mm: 24,
          centre_x_mm: 70, centre_y_mm: 25, face: superieure du cylindre a z=50}]
volume_mm3: 160300
volume_recalcule_mm3: 160339
hors_perimetre: [percage borgne, contour circulaire extrude, union de deux corps,
                 deux hauteurs d extrusion, cylindre en debord de la plaque en y]
plan: {format: A4, echelle: 1/2, nb_vues: 3, vue_isometrique: retiree,
       image_px: , texte_cote_mm: , texte_percu_px: }