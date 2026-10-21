#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 22:52:55 2026

@author: walidajalil
"""

from mcp import Client, StdioServerParameters
import anyio


server_params = StdioServerParameters(command="python", args=["mcp_server.py"])


async def get_tool_definitions():
    async with Client(server_params) as client:
        tool_definitions = []

        result = await client.list_tools()

        # Print tools, it will list all of the tools defined in the mcp_server.py file.
        # Along with names, arguments, input and output schema.
        # print(result)
        for tool in result.tools:
            # print("\nTool name:")
            # print(tool.name)
            # print("\nTool description:")
            # print(tool.description)
            # print("\nTool input schema:")
            # print(tool.input_schema)

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


if __name__ == "__main__":
    tool_definitions = anyio.run(get_tool_definitions)
    print(tool_definitions)
