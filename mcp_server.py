"""Serveur MCP : expose l'execution CadQuery en sandbox conteneurisé.

Transport stdio. Conséquence structurelle : stdout est le canal JSON-RPC.
Aucun print() dans ce fichier. Les logs vont sur stderr, la sortie de docker
est capturée et jamais heritée.

Contraintes heritées du spike, appliquées ici :
2. La validation porte sur le fichier produit. Ce serveur ne lit jamais le
   code de retour de docker pour décider du succés, il relit report.json.
3. La boucle de reprise s'arrête quand elle n'a pas de message a transmettre.
   Une panne d'infrastructure n'est pas un message transmissible au modèle :
   elle lève ToolError et sort de la boucle au lieu de la nourrir.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

REPO_ROOT = Path(__file__).resolve().parent
WORK_DIR = REPO_ROOT / "sandbox" / "work"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
IMAGE = "cq-sandbox"
DOCKER_TIMEOUT_S = 180  # supérieur au TIMEOUT_S=120 du runner interne

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("mcp-sandbox")

mcp = MCPServer("agent-ingenierie-inverse")


def _mount_source(path: Path) -> str:
    """Chemin Windows en slashes avant, forme prouvée avec pwd -W."""
    return str(path.resolve()).replace("\\", "/")


@mcp.tool()
def run_cadquery_script(script: str) -> dict:
    """Execute un script CadQuery dans un conteneur isolé.

    Le script doit écrire son solide dans /work/out.step.
    Retourne produced, error_message, artifact_path, size_bytes, returncode,
    timed_out. produced=false avec error_message=null est le signal d'arrêt
    de la boucle de reprise.
    """
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = WORK_DIR / "report.json"
    if report_path.exists():
        report_path.unlink()  # sinon on relirait le rapport de la passe précédente
    (WORK_DIR / "script.py").write_text(script, encoding="utf-8")

    cmd = ["docker", "run", "--rm", "-v", f"{_mount_source(WORK_DIR)}:/work", IMAGE]
    log.info("lancement : %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_S
        )
    except FileNotFoundError as exc:
        raise ToolError(f"docker introuvable sur le PATH : {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            f"conteneur bloqué au delà de {DOCKER_TIMEOUT_S} s"
        ) from exc

    if not report_path.exists():
        raise ToolError(
            "aucun report.json produit, panne d'infrastructure et non erreur de "
            f"script. returncode={proc.returncode} "
            f"stderr={proc.stderr.strip()[-1000:]}"
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))

    artifact_path = None
    if report.get("produced"):
        run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
        artifact = ARTIFACTS_DIR / f"{run_id}.step"
        shutil.copy2(WORK_DIR / "out.step", artifact)
        artifact_path = str(artifact)
        log.info("STEP conservé : %s", artifact.name)
    else:
        log.info("échec, error_message présent : %s", report.get("error_message") is not None)

    # stdout et stderr complets rèstent dans report.json sur disque.
    # Ils ne remontent pas : error_message porte deja les 4000 derniers
    # caracteres de stderr, les dupliquer gonfle le contexte du modèle.
    return {
        "produced": report.get("produced", False),
        "error_message": report.get("error_message"),
        "artifact_path": artifact_path,
        "size_bytes": report.get("size_bytes", 0),
        "returncode": report.get("returncode"),
        "timed_out": report.get("timed_out", False),
    }


if __name__ == "__main__":
    mcp.run()  # stdio par defaut