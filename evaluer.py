"""Bloc 5, runs de bout en bout : une pièce par processus.

Enchaîne le pipeline réel (extraction, génération, sandbox, boucle de reprise),
puis confronte le solide produit à la vérité terrain. Les deux solides passent
par mesure() : la contrainte 4 s'exerce ici, boîte englobante, trous
traversants et volume contrôlés ensemble.

Une pièce par processus : le segfault OCCT au teardown ne peut pas toucher la
mesure d'une autre pièce. La trace JSON fait foi, pas le code de sortie.

Lancement depuis la racine du dépôt, Docker Desktop démarré :
    uv run python evaluer.py <plan.png> <verite.step>
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import agent
import verification

# Versionné, contrairement à artifacts/ : la trace est la pièce que lit le bloc 6.
EVALUATIONS = Path(__file__).resolve().parent / "evaluations"


def _ecrire(chemin: Path, trace: dict) -> None:
    """Écrit la trace en UTF-8, lisible sans outil."""
    chemin.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")


def evaluation(png: Path, step: Path) -> dict:
    """Évalue une pièce de bout en bout et écrit sa trace pour le bloc 6."""
    EVALUATIONS.mkdir(exist_ok=True)
    chemin = EVALUATIONS / f"{datetime.now():%Y%m%d_%H%M%S}_{step.stem}.json"

    # Espion sur l'extraction : même appel, même retour, on garde seulement les
    # primitives. Sans elles, le bloc 6 ne sépare pas une erreur de lecture
    # d'une erreur de génération.
    capture = {}
    extraire_reel = agent.extraire

    def extraire_trace(chemin_png):
        capture["primitives"] = extraire_reel(chemin_png)
        return capture["primitives"]

    agent.extraire = extraire_trace

    rapport = agent.pipeline(png)
    artefact = rapport["artifact_path"]
    trace = {
        "piece": step.stem,
        "plan": png.as_posix(),
        "reference": step.as_posix(),
        "modele": agent.MODEL,
        "produced": rapport["produced"],
        "tentatives": rapport["tentatives"],
        "error_message": rapport["error_message"],
        "artefact": Path(artefact).name if artefact else None,
        "primitives": capture.get("primitives"),
        "mesure_reference": None,
        "mesure_produit": None,
        "comparaison": None,
    }
    # Première écriture avant toute mesure : le run API est la partie coûteuse
    # et non reproductible. Si une mesure plante, il reste sur disque.
    _ecrire(chemin, trace)

    if not rapport["produced"]:
        # Aucun solide à mesurer : c'est un résultat, pas une panne.
        print(f"\n=== {step.stem} : aucun fichier produit après "
              f"{rapport['tentatives']} tentative(s) ===")
        print(f"trace : evaluations/{chemin.name}")
        return trace

    # La référence d'abord : compare() calcule la tolérance relative contre son
    # premier argument.
    trace["mesure_reference"] = verification.mesure(str(step))
    trace["mesure_produit"] = verification.mesure(artefact)
    trace["comparaison"] = verification.compare(trace["mesure_reference"], trace["mesure_produit"])
    _ecrire(chemin, trace)

    comparaison = trace["comparaison"]
    print(f"\n=== {step.stem} : {'CONFORME' if comparaison['conforme'] else 'NON CONFORME'}, "
          f"{comparaison['nb_controles']} contrôles, {rapport['tentatives']} tentative(s) ===")
    for champ, verdict in comparaison["verdicts"].items():
        print(f"  {verdict:<15} {champ} : référence {trace['mesure_reference'][champ]}, "
              f"produit {trace['mesure_produit'][champ]}")
    print(f"trace : evaluations/{chemin.name}")
    return trace


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage : uv run python evaluer.py <plan.png> <verite.step>")
    evaluation(Path(sys.argv[1]), Path(sys.argv[2]))