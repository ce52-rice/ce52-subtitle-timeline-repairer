import os
from pathlib import Path
from typing import Any

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from slimconfig import build_output, output_schema, plain_output

from contract import TOOLS, Tool

from .pin_case import pin_case
from .read_cues import read_cues
from .save_repair import save_repair

server = Server("ce52-subtitle-timeline-repairer")
IMPLEMENTATIONS = {Tool.PIN_CASE: pin_case, Tool.READ_CUES: read_cues, Tool.SAVE_REPAIR: save_repair}


@server.list_tools()
async def list_tools():
    return [
        types.Tool(name=t.value, inputSchema=output_schema(i), outputSchema=output_schema(o))
        for t, (i, o) in TOOLS.items()
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    tool = Tool(name)
    input_type, output_type = TOOLS[tool]
    value = IMPLEMENTATIONS[tool](build_output(arguments, input_type), Path(os.environ["NANOAGENT_WORKSPACE"]))
    if not isinstance(value, output_type):
        raise TypeError("tool returned the wrong contract type")
    return plain_output(value)


def main():
    if "NANOAGENT_WORKSPACE" not in os.environ:
        raise SystemExit("NANOAGENT_WORKSPACE is required; run tests for an offline smoke test")

    async def run():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    anyio.run(run)


if __name__ == "__main__":
    main()
