"""Câblage bout en bout, une seule passe, sans boucle de reprise.

raster PNG -> primitives JSON -> script CadQuery -> sandbox MCP -> rapport.

La boucle de reprise n'existe pas ici : une tentative, un verdict.
Contraintes appliquées :
1. le modèle ne produit que des primitives, aucune grandeur derivée n'est
   demandée ni utilisée.
2. le succès se lit sur le fichier produit, jamais sur un code de retour.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anyio
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
ARTIFACTS = ROOT / "artifacts"

MAX_TOKENS = 16000  # saturation silencieuse constatée, dimensionne d'emblée
PLACEHOLDER = "SORTIE.step"
CIBLE = "/work/out.step"
MAX_TENTATIVES = 2

load_dotenv()
MODEL = os.environ["MODEL_ID"]

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    default_headers={"anthropic-workspace-id": os.environ["ANTHROPIC_WORKSPACE_ID"]},
)


def _texte(message) -> str:
    """Concatène les blocs texte, après contrôle du motif d'arret.

    stop_reason different de end_turn lève une exception : une réponse
    tronquée ne doit jamais devenir un fichier.
    """
    if message.stop_reason != "end_turn":
        raise RuntimeError(
            f"stop_reason={message.stop_reason}, réponse interrompue. "
            f"max_tokens={MAX_TOKENS}, sortie non exploitable."
        )
    return "".join(b.text for b in message.content if b.type == "text").strip()


def _sans_balises(brut: str) -> str:
    """Filet de sécurité : les prompts interdisent les balises, on les retire quand même."""
    if brut.startswith("```"):
        lignes = brut.splitlines()
        lignes = lignes[1:]
        if lignes and lignes[-1].strip() == "```":
            lignes = lignes[:-1]
        return "\n".join(lignes).strip()
    return brut


def extraire(png: Path) -> dict:
    """Lit le plan et rend les primitives. Aucune grandeur derivée n'est exploitée."""
    if png.suffix.lower() != ".png":
        raise ValueError(f"raster PNG attendu, recu {png.suffix}")
    donnees = base64.standard_b64encode(png.read_bytes()).decode("ascii")
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/png", "data": donnees}},
                {"type": "text", "text": (PROMPTS / "prompt_extraction.txt").read_text(encoding="utf-8")},
            ],
        }],
    )
    return json.loads(_sans_balises(_texte(message)))


def generer(primitives: dict) -> str:
    """Rend le script CadQuery, chemin de sortie substitué pour le sandbox."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{
            "role": "user",
            "content": (
                (PROMPTS / "prompt_generation.txt").read_text(encoding="utf-8")
                + "\n\nJSON :\n"
                + json.dumps(primitives, ensure_ascii=False, indent=2)
            ),
        }],
    )
    code = _sans_balises(_texte(message))
    if PLACEHOLDER not in code:
        raise RuntimeError(
            f"placeholder {PLACEHOLDER} absent du code généré. Le script n'ecrirait "
            "nulle part et le sandbox rendrait un faux signal d'arrêt de boucle."
        )
    return code.replace(PLACEHOLDER, CIBLE)


async def _executer(code: str) -> dict:
    params = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "mcp_server.py")], env=dict(os.environ)
    )
    async with Client(params) as mcp_client:
        resultat = await mcp_client.call_tool("run_cadquery_script", {"script": code})
        return json.loads(resultat.content[0].text)


def corriger(primitives: dict, code_fautif: str, message_erreur: str) -> str:
    """Régénère le script à partir du code précédent et de l'erreur mesurée."""


def pipeline(png: Path) -> dict:
    ARTIFACTS.mkdir(exist_ok=True)
    horodatage = f"{datetime.now():%Y%m%d_%H%M%S}_{png.stem[:12]}"

    print(f"[1/3] extraction  {png.name}", flush=True)
    primitives = extraire(png)
    (ARTIFACTS / f"{horodatage}_primitives.json").write_text(
        json.dumps(primitives, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[2/3] génération du script CadQuery", flush=True)
    code = generer(primitives)
    rapport, tentative = None, 0

    while tentative < MAX_TENTATIVES:
        tentative += 1
        (ARTIFACTS / f"{horodatage}_script_t{tentative}.py").write_text(
            code, encoding="utf-8")

        print(f"[3/3] exécution en sandbox, tentative {tentative}", flush=True)
        # aucun try/except ici : une ToolError signale une panne
        # d'infrastructure, jamais une erreur de script. La laisser remonter
        # évite de réécrire du CadQuery contre un daemon Docker arrêté.
        rapport = anyio.run(_executer, code)

        if rapport["produced"]:
            break

        message = rapport.get("error_message")
        if message is None:
            # Contrainte 3 : sans message à transmettre, le modèle réécrirait
            # à l'aveugle. On s'arrête plutôt que de deviner.
            print("arrêt : échec sans message d'erreur exploitable", flush=True)
            break

        if tentative < MAX_TENTATIVES:
            print(f"reprise sur erreur : {message.splitlines()[0][:120]}", flush=True)
            code = corriger(primitives, code, message)

    rapport["tentatives"] = tentative

    print("\n--- rapport ---")
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    print(f"\nprimitives : artifacts/{horodatage}_primitives.json")
    print(f"script     : artifacts/{horodatage}_script_t{rapport['tentatives']}.py")
    print(f"trous lus : {len(primitives.get('trous', []))}   "
          f"poches lues : {len(primitives.get('poches', []))}   "
          f"incertitudes : {len(primitives.get('incertitudes', []))}")
    return rapport


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage : uv run python agent.py <chemin_du_raster.png>")
    pipeline(Path(sys.argv[1]))