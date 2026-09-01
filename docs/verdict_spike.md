# Verdict du spike : agent d'ingénierie inverse (P15)

Exécuté le 01 et 02/09/2026. Budget 5 h, arrêt dur 5 h 30. Consommé : environ 2,5 h.
Modèle évalué : `claude-opus-5`, vision par API. Aucun modèle local, conformément au protocole.

## 1. Question posée

L'extraction de cotes depuis un plan technique par un modèle de vision est-elle assez fiable pour fonder le projet ?

## 2. Résultats contre les critères

| Critère | Seuil figé avant exécution | Résultat mesuré | Verdict |
|---|---|---|---|
| **C1 Extraction** | Toutes les cotes principales de A et B correctes, au plus 1 erreur sur B | 23/23 cotes lues sans erreur sur 4 passes. 2 erreurs sur B, portant toutes deux sur des valeurs dérivées | **ÉCHOUE** |
| **C2 Exécution** | Code CadQuery exécutable en 2 tentatives maximum sur A et B | Exécutable à la tentative 1 sur A et sur B. Zéro erreur d'API, zéro erreur de géométrie dans le code | **ACQUIS** |
| **C3 Correspondance** | bbox ±0,5 mm, comptage de trous exact, volume ±1 % | A : 0 écart bbox, 2/2 trous, volume +0,000 %. B : 0 écart bbox, 1/1 trou, volume +0,000 % | **ACQUIS** |

C2 et C3 sont mesurés depuis les cotes corrigées à la main, conformément au découplage imposé par le protocole.

Pièce C : non exécutée. Elle ne conditionnait aucun critère et servait à mesurer la dégradation sur plan réaliste. Le budget disponible ne justifiait pas de la dépenser une fois les trois critères tranchés. Point rouvert en cas de suite.

## 3. Qualification de la cause de l'échec C1

Le seuil est appliqué à la lettre : 2 erreurs sur B contre 1 tolérée, C1 échoue. Le seuil n'est pas réinterprété après coup.

Les deux erreurs sont classées topologie et non lecture, ce qui pointe dans la matrice de décision du protocole vers « projet non viable tel que cadré ». Ce n'est pas la cause réelle, et la distinction est le livrable le plus important du spike.

**Erreur 1.** Cylindre Ø64 de B placé en z_base 10 hauteur 40 au lieu de z_base 0 hauteur 50. Stable et fausse aux deux passes. Invisible à la relecture du JSON, détectée uniquement par le calcul de volume. Écart de volume impliqué : -2,4 %.

**Erreur 2.** `bbox_y` de B lu 64 en passe 1, 50 en passe 2 et dans une passe tronquée antérieure. Correct 1 fois sur 3.

Ces deux erreurs portent sur des **valeurs dérivées** de la géométrie, pas sur la géométrie elle-même. En regard, sur les mêmes passes, le modèle a :

- lu 23 cotes sur 4 passes sans une seule erreur, y compris le O8,5 qui est le plus petit texte du plan A ;
- déduit correctement une chaîne de cotes non cotée (50 - 15 - 15 = 20) aux deux passes de B, et signalé la déduction dans le champ incertitudes ;
- distingué systématiquement le perçage borgne du traversant, en consultant la coupe A-A ;
- produit des primitives stables entre passes.

**La géométrie est comprise. Ce qui échoue est le recalcul de grandeurs dérivées de cette géométrie.** Ce n'est pas un plafond de capacité du modèle : c'est une tâche qui n'aurait pas dû lui être confiée.

Un test de résolution écarte par ailleurs cette explication : 4756 tokens pour l'image, contre un plafond de 4784 au palier haute résolution, aucun redimensionnement. Aucune erreur imputable à la résolution.

En conséquence, **la branche « découpage en régions » du protocole est abandonnée** : elle traitait un problème de lecture qui n'existe pas.

## 4. Erreur composée mesurée

Run de bout en bout sur B, depuis les cotes extraites non corrigées.

Écart au protocole assumé : le run était prévu sur A. L'extraction de A étant parfaite, il aurait mesuré une erreur composée nulle par construction. B est la seule pièce porteuse d'information.

| Grandeur | Mesuré | Vérité terrain | Écart |
|---|---|---|---|
| bbox x / y / z | 140 / 64 / 50 | 140 / 64 / 50 | 0 |
| Trous | 1 | 1 | 0 |
| Volume mm3 | 156 520,35 | 160 339 | **-2,382 %** |

Trois observations qui fondent l'architecture cible :

1. L'erreur composée mesurée (-2,382 %) correspond à la prédiction analytique (-2,4 %). La propagation est celle de l'erreur 1 seule, et elle est déterministe.
2. La bbox sort juste sur les trois axes, alors que l'erreur 2 portait précisément sur `bbox_y`. Elle est ici mesurée sur le solide reconstruit, pas lue sur le plan. **La valeur dérivée fausse devient inoffensive dès qu'on cesse de la demander au modèle.**
3. Une vérification par bbox et comptage de trous seuls aurait déclaré ce solide conforme. Le cylindre mal positionné conserve l'empreinte, l'enveloppe et le nombre de trous. Seul le volume voit l'erreur : **un contrôle géométrique sans grandeur volumique ne contrôle rien.**

## 5. Décision

**GO. Le projet est confirmé, sous réserve de trois contraintes d'architecture.**

C1 a échoué, et le go est prononcé malgré cet échec parce que la cause qualifiée est éliminée par conception et non par espoir :

- La cause n'est pas une incompréhension géométrique, seul motif de non-viabilité prévu par la matrice de décision.
- Les deux erreurs portent sur des grandeurs que l'architecture cible ne demande plus au modèle. Elles disparaissent avec le changement, elles ne sont pas tolérées.
- C2 et C3, qui mesurent tout l'aval de la chaîne, sont acquis à la première tentative.
- L'erreur résiduelle est bornée, mesurée et déterministe.

**Contraintes d'architecture issues du spike, à reprendre au §3 du rapport :**

1. **Ne jamais demander de valeur dérivée à un modèle de vision.** Boîte englobante, volume et toute grandeur calculable se déduisent des primitives. Les deux seules erreurs du spike portent exactement sur les deux seules valeurs dérivées demandées.
2. **Un artefact valide peut sortir d'un processus en échec.** La validation porte sur le fichier produit, jamais sur le code de retour. Observé deux fois : STEP valides exportés avant plantage OCCT (0xC0000374 puis 0xC0000005 au teardown, sous Windows). Défaut non réparé, documenté, sans effet sur les livrables.
3. **Une boucle de reprise sans message d'erreur fait réécrire le modèle à l'aveugle.** Elle doit s'arrêter quand elle n'a rien à transmettre.

**Créneau.** Le créneau du projet libre est de 20 h, fixe, décidé avant le spike et indépendant de son résultat. Le go confirme le sujet, il n'ouvre aucune extension. Le projet de repli (amélioration mesurée de la pipeline ASR EFICAD) reste désigné et n'est pas activé.

## 6. Ce que le spike n'a pas mesuré

- La pièce C, donc la dégradation sur plan réaliste : cartouche, tolérances, symboles d'état de surface, chaînes de cotes, cotes demandant interprétation.
- Le comportement d'un modèle local ouvert. L'évaluation comparative API contre local est un travail d'analyse postérieur, traité au §3 du rapport sur specs et benchmarks publiés, sans implémentation.
- Toute brique agentique : serveur MCP, API, sandbox, boucle. Écartées volontairement du spike comme ingénierie connue, sans incertitude à réduire.