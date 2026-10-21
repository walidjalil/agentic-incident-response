#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 22:52:55 2026

@author: walidajalil
"""

from mcp import Client, StdioServerParameters
from mcp.types import TextContent
import anyio


server_params = StdioServerParameters(command="python", args=["mcp_server.py"])


async def get_tool_definitions():
    # Discovery
    async with Client(server_params) as client:
        tool_definitions = []

        result = await client.list_tools()

        for tool in result.tools:
            tool_definition = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            tool_definitions.append(tool_definition)
        return tool_definitions


async def call_mcp_tool(tool_name, arguments):
    blocks = []
    # Execution
    async with Client(server_params) as client:
        result = await client.call_tool(tool_name, arguments)
        for block in result.content:
            if isinstance(block, TextContent):
                blocks.append(block.text)
        blocks_string = "\n".join(blocks)

        return blocks_string


if __name__ == "__main__":
    tool_definitions = anyio.run(get_tool_definitions)
    print(tool_definitions)
