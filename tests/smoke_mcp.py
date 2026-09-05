"""Verification du serveur MCP : handshake stdio, liste des outils,
un succes attendu, un echec attendu.
Lancement : uv run python tests/smoke_mcp.py
Docker Desktop doit tourner.
"""
import os
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent

SCRIPT_OK = """
import cadquery as cq
r = cq.Workplane("XY").box(20, 10, 5)
cq.exporters.export(r, "/work/out.step")
"""

SCRIPT_KO = """
import cadquery as cq
r = cq.Workplane("XY").box(20, 10)   # argument manquant, doit lever
cq.exporters.export(r, "/work/out.step")
"""

params = StdioServerParameters(
    command=sys.executable,
    args=[str(ROOT / "mcp_server.py")],
    env=dict(os.environ),
)


def payload(result):
    return getattr(result, "structured_content", None) or result.content


async def main() -> None:
    async with Client(params) as client:
        listing = await client.list_tools()
        print("outils exposes :", [t.name for t in listing.tools])

        for label, script in (("SUCCES attendu", SCRIPT_OK), ("ECHEC attendu", SCRIPT_KO)):
            print(f"\n--- {label} ---")
            result = await client.call_tool("run_cadquery_script", {"script": script})
            print(payload(result))


anyio.run(main)