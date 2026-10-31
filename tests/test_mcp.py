import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_real_mcp_server_lists_and_executes(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "plugin"],
            cwd=str(Path(__file__).resolve().parents[1]),
            env={**os.environ, "NANOAGENT_WORKSPACE": str(tmp_path)},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            assert {tool.name for tool in listing.tools} == {"pin_case", "read_cues", "save_repair"}
            task = {"case_id": "tutorial", "offset_ms": -1500, "duration_ms": 10000, "gap_ms": 0}
            result = await session.call_tool("read_cues", task)
            assert not result.isError
            data = result.structuredContent
            assert data["task"] == task
            candidates = data["candidates"]
            output = await session.call_tool(
                "save_repair",
                {
                    "run": data["run"],
                    "task": task,
                    "subtitles": [c for c in candidates if c["start_ms"] < c["end_ms"]],
                    "dropped_ids": [c["id"] for c in candidates if c["start_ms"] >= c["end_ms"]],
                },
            )
            assert not output.isError
            assert (tmp_path / "reports" / (data["run"] + ".json")).is_file()

    anyio.run(run)
