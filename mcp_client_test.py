#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 22:52:55 2026

@author: walidajalil
"""

from mcp import Client, StdioServerParameters
import anyio


server_params = StdioServerParameters(command="python", args=["mcp_server.py"])


async def main():
    async with Client(server_params) as client:
        tools = await client.list_tools()

        # Print tools, it will list all of the tools defined in the mcp_server.py file.
        # Along with names, arguments, input and output schema.
        print(tools)


anyio.run(main)
