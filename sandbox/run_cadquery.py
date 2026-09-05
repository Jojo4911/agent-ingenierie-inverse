"""Execute un script CadQuery en isolation et rend compte du fichier produit.

Contraintes heritées du spike, appliquées ici structurellement :
2. la validation porte sur le fichier produit, jamais sur le code de retour.
   Le script est lancé en sous-processus : un segfault OCCT au teardown ne
   peut pas empêcher ce runner de constater qu'un STEP valide à été écrit.
3. la boucle de reprise s'arrête quand elle n'a pas de message d erreur à
   transmettre. produced=false avec error_message=null est ce signal d'arret.
"""

import json
import pathlib
import subprocess
import sys

WORK = pathlib.Path("/work")
CODE = WORK / "script.py"
OUT = WORK / "out.step"
REPORT = WORK / "report.json"
TIMEOUT_S = 120


def main():
    if OUT.exists():
        OUT.unlink()

    if not CODE.exists():
        write({"produced": False, "error_message": f"{CODE} absent", "returncode": None})
        return

    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, str(CODE)],
            capture_output=True, text=True, timeout=TIMEOUT_S, cwd=str(WORK),
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        rc, out, err = None, e.stdout or "", e.stderr or ""

    produced = OUT.exists() and OUT.stat().st_size > 0

    if produced:
        message = None
    elif timed_out:
        message = f"timeout depasse : {TIMEOUT_S} s"
    else:
        message = err.strip()[-4000:] or None

    write({
        "produced": produced,
        "path": str(OUT) if produced else None,
        "size_bytes": OUT.stat().st_size if produced else 0,
        "returncode": rc,
        "timed_out": timed_out,
        "error_message": message,
        "stdout": out[-4000:],
        "stderr": err[-4000:],
    })


def write(report):
    report.setdefault("produced", False)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("produced", "returncode", "error_message")}, indent=2))


if __name__ == "__main__":
    main()
