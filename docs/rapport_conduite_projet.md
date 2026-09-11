# Rapport de conduite de projet : agent d'ingénierie inverse

## 5. Contrôle et suivi

Le projet est piloté par budgets fixes et règles décidées d'avance : le périmètre s'ajuste au temps disponible, jamais l'inverse. Chaque règle d'arrêt a été écrite avant la mesure qui pouvait la déclencher.

### 5.1 Tableau de bord de pilotage

#### Indicateurs

| Indicateur                | Cible fixée d'avance | Réalisé | Source |
|---------------------------|---|---|---|
| Délai                     | Fin des travaux visée du 18 au 22/09 | Deux jours d'avance sur le planning au 11/09             | Horodatage des commits |
| Coût, projet 15 entier    | 47 à 55 h, planifié 55,5 h           | 28,9 h réelles pour 41,5 h estimées au 10/09, ratio 70 % | CSV de suivi           |
| Coût, projet libre        | Créneau fixe de 20 h                 | Clos à 12,7 h le 11/09, 7,3 h rendues au calendrier      | CSV, blocs 1 à 7       |
| Coût, spike               | 5 h, arrêt dur à 5 h 30              | 2,5 h                                                    | [Verdict du spike](verdict_spike.md) |
| Livrables du projet libre | Blocs 1 à 7 du cadrage               | Tous livrés, dépôt publié et tagué `v0.1.0`              | Dépôt                  |
| Performance               | Seuils C1 à C3 figés au spike        | C2 : 5 sur 5 ; C3 : 4 sur 5                              | [Rapport d'évaluation](rapport_evaluation.md), section 2 |

L'unité de coût suivie est l'heure de travail. Le CSV de suivi porte, pour chaque tâche, l'estimé, le réel, l'écart et le statut ; il est joint en annexe. [Chiffres finaux à la clôture.]

#### Ce que le suivi a appris : le prédicteur des écarts

Sur le créneau du projet libre, le rapport entre réel et estimé suit la quantité de code réellement nouveau. Les tâches sans code nouveau sortent très sous l'estimation : 29 % et 35 % pour les runs de bout en bout, 25 % pour le README. La règle d'arrêt de la boucle de reprise, seule notion inconnue au départ, sort à 144 %. Les tâches de rédaction du rapport d'évaluation restent proches de l'estimation (84 % et 101 %), avec une part de latence de génération que les estimations n'intégraient pas. Ce constat alimente les estimations des projets suivants.

#### Méthode de gestion

- **Pilotage à trois niveaux.** Une feuille de route globale fixe le budget et l'ordre des projets de la formation. Un brief par projet fixe budget, périmètre et définition de terminé ; le projet 15 en a reçu deux, le second émis après le verdict du spike. Le niveau projet produit le planning jour par jour et le CSV de suivi, chaque journée s'exécute contre ce plan et en remonte les temps réels. La capacité hebdomadaire, planifiée d'abord à 35 h, a été corrigée en cours de formation à 19 h, valeur observée.
- **Deux étiquettes par tâche.** La priorité : essentielle, requise pour la validation, ou secondaire, première à sauter en cas de dépassement. La catégorie, qui fixe l'effort d'apprentissage et non l'importance : ancrage (notion à maîtriser, produite par l'auteur en trois jets), compréhension (un jet, puis solution expliquée), utilitaire (plomberie, reçue directement).
- **Créneau fixe.** Le projet libre dispose de 20 h, décidées avant le spike et indépendamment de son résultat. Le périmètre géométrique est borné en conséquence ; toute addition impose une coupe équivalente.
- **Coupe-circuit à 150 %.** Une tâche qui atteint 150 % de son estimation s'arrête : une version minimale qui satisfait la définition de terminé est livrée et le point est noté. Distinct du plafond de 30 à 40 minutes par blocage, au-delà duquel la solution complète est demandée.
- **Revue hebdomadaire du vendredi.** Cumul réel contre prévu, débit effectif, date de fin projetée.
- **Jalon de bascule du 14/09.** Contrôle sur les heures produites, pas sur l'avancement : sous 30 h cumulées sur les deux premières semaines, replanification automatique à 12 h par semaine, non renégociable. [Verdict du jalon.]
- **Arbitrages écrits.** Chaque décision est tranchée, motivée et non rouverte. Exemples : la vérification géométrique reste hors de la boucle de reprise ; les prompts sont gelés ; la pièce B, non conforme, n'est ni relancée ni corrigée ; le jeu tenu à l'écart, une fois consommé, n'autorise plus aucun ajustement.

#### Le spike, instrument de décision

Avant tout développement, un spike a acheté l'information qui manquait : l'extraction de cotes par un modèle de vision est-elle assez fiable pour fonder le projet ?

- **Cadre fixé avant exécution** : budget de 5 h, arrêt dur à 5 h 30 ; trois critères avec leurs seuils ; matrice de décision écrite ; projet de repli désigné d'avance, pour ne pas le choisir sous la pression d'un échec.
- **Seuil appliqué à la lettre** : C1 échoue, 2 erreurs sur B contre 1 tolérée, et le seuil n'est pas réinterprété. C2 et C3 sont acquis. Consommé : 2,5 h.
- **Décision par la cause, pas par le taux** : la matrice exigeait de qualifier la nature des erreurs. Cette qualification fonde un GO argumenté (verdict, sections 3 et 5).
- **Test de falsification** : une pièce réaliste, exécutée ensuite sur le reliquat du budget, était le seul test capable de renverser le GO. L'interprétation de son résultat avait été fixée avant le test ; il a conduit à restreindre l'entrée aux plans propres et normalisés.

Le verdict est joint tel quel en annexe : [`verdict_spike.md`](verdict_spike.md).

### 5.2 Outils et process de suivi

#### Journalisation

- **Traces d'évaluation** (`evaluations/`, versionnées) : une trace JSON par run, avec le plan, la référence, le modèle, les primitives extraites, le nombre de tentatives, le message d'erreur éventuel, les mesures des deux solides et le verdict par contrôle. Une trace est écrite même sans fichier produit.
- **Artefacts** (`artifacts/`, non versionnés) : primitives, script de chaque tentative et STEP produit, horodatés.

#### Méthodologie de test

- **Tests de fumée** (`tests/`). `smoke_mcp.py` vérifie le serveur MCP : poignée de main, liste des outils, un succès et un échec attendus. `smoke_pipeline_exit.py` exerce les trois arrêts de la boucle de reprise sur le vrai pipeline, attendus figés avant exécution : 3 conformes sur 3, sans modifier `agent.py`.
- **Sandbox** : le script généré s'exécute dans un conteneur Docker jetable, sous un utilisateur non root, avec un délai borné et le seul répertoire de travail monté. Le succès se lit dans le fichier produit, jamais dans le code de retour.
- **Évaluation de bout en bout** : `evaluer.py` confronte chaque solide produit au STEP de référence sur cinq contrôles, aux tolérances figées au spike, une pièce par processus.
- **Jeu tenu à l'écart** : deux pièces jamais vues pendant le développement, exécutées une seule fois, sous une règle de relance figée avant le premier run et restée inutilisée. Aucun ajustement après lecture : les taux restent comparables.
- **Hors périmètre** : ni suite de tests unitaires, ni tests de charge, ni monitoring de production de type Prometheus ou Grafana. Le projet est une preuve de concept sans déploiement ; le suivi en usage relève des perspectives (section 6).

#### Traçabilité

Un commit atomique par tâche. Le code des runs mesurés est celui du commit `2143428` ; le tag `v0.1.0` marque l'état livré, les commits postérieurs ne touchant que la documentation et le suivi git.