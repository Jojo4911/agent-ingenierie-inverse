"""Exercice des trois arrêts de la boucle de reprise de pipeline().

agent.py n'est pas modifié. On remplace, dans l'espace de noms du module
agent, les fonctions qui fabriquent le code envoyé au sandbox. Le sandbox
reste réel : chaque error_message est écrit par le runner, jamais fabriqué.

Lancement depuis la racine du dépôt, Docker Desktop démarré :
    uv run python tests/smoke_pipeline_exit.py
"""
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))  # agent.py est à la racine, pas dans tests/

import agent  # l'objet module : c'est son espace de noms qu'on modifie

corriger_reel = agent.corriger  # capturée avant tout remplacement

# Primitives de la pièce A, au format exact de extraire(), écrites par un run réel.
candidats = sorted((RACINE / "artifacts").glob("*_piece_A_plan_primitives.json"))
if not candidats:
    sys.exit("aucune primitive de la pièce A dans artifacts/ : lancer d'abord agent.py sur A")
PRIMITIVES = json.loads(candidats[-1].read_text(encoding="utf-8"))
agent.extraire = lambda png: PRIMITIVES  # commun aux trois scénarios

# Script sain : sortie réelle de generer(), donc déjà au contrat du sandbox.
SAIN = agent.generer(PRIMITIVES)

# Fautes ajoutées en tête : indépendantes de la structure du script,
# la ligne d'export qui porte /work/out.step reste intacte.
FAUTE_BRUYANTE = "print(cq.__version__)\n" + SAIN  # cq pas encore importé : traceback
FAUTE_MUETTE = "import sys\nsys.exit(0)\n" + SAIN  # aucun fichier, stderr vide
FAUTE_BRUYANTE_T2 = "raise RuntimeError('faute injectée, tentative 2')\n" + SAIN

appels = []  # arguments reçus par corriger(), un tuple par appel


def espion(fonction):
    """Enregistre les arguments de chaque appel, puis délègue à fonction."""
    def enveloppe(*args):
        appels.append(args)
        return fonction(*args)
    return enveloppe


def scenario(nom, script_t1, corriger, produced, tentatives, message_nul, nb_appels):
    """Injecte, exécute le vrai pipeline(), compare aux attendus figés d'avance."""
    appels.clear()
    agent.generer = lambda primitives: script_t1
    agent.corriger = espion(corriger)
    rapport = agent.pipeline(Path(f"{nom}.png"))  # le nom étiquette les artefacts
    constats = {
        "produced": (rapport["produced"], produced),
        "tentatives": (rapport["tentatives"], tentatives),
        "error_message nul": (rapport["error_message"] is None, message_nul),
        "appels à corriger()": (len(appels), nb_appels),
    }
    conforme = all(obtenu == attendu for obtenu, attendu in constats.values())
    print(f"\n=== {nom} : {'CONFORME' if conforme else 'NON CONFORME'} ===")
    for champ, (obtenu, attendu) in constats.items():
        marque = "ok" if obtenu == attendu else "ÉCART"
        print(f"  {marque:<5} {champ} : obtenu {obtenu}, attendu {attendu}")
    if appels:
        print(f"  message transmis à corriger() : {appels[0][2].splitlines()[-1]}")
    print()
    return conforme


resultats = [
    # S1, arrêt ligne 149. Console : « reprise sur erreur », puis tentative 2.
    scenario("S1_reprise", FAUTE_BRUYANTE, corriger_reel,
             produced=True, tentatives=2, message_nul=True, nb_appels=1),
    # S2, arrêt ligne 156. Console : « arrêt : échec sans message d'erreur exploitable ».
    # Leurre sans appel API : s'il est appelé à tort, l'écart est compté et rien n'est payé.
    scenario("S2_sans_msg", FAUTE_MUETTE, lambda *args: SAIN,
             produced=False, tentatives=1, message_nul=True, nb_appels=0),
    # S3, arrêt ligne 137. Console : « reprise sur erreur », tentative 2, rien après.
    scenario("S3_plafond", FAUTE_BRUYANTE, lambda *args: FAUTE_BRUYANTE_T2,
             produced=False, tentatives=agent.MAX_TENTATIVES, message_nul=False, nb_appels=1),
]
print(f"bilan : {sum(resultats)} scénarios conformes sur {len(resultats)}")
sys.exit(0 if all(resultats) else 1)