#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 03:48:06 2026

@author: walidajalil
"""

from mcp.server import MCPServer
import incident_tools
from rag import retrieve

# Import Literal, this is on order to replace enum in the JSON-dict for input arguments.
# Literal ----> samma som enum["a", "b", "c"]
from typing import Literal

mcp = MCPServer("Incident Response")


@mcp.tool()
def get_metrics() -> dict:
    """Get the current service metrics."""
    return incident_tools.get_metrics()


@mcp.tool()
def get_deployment() -> dict:
    """Get information on current deployment and any changes to it."""
    return incident_tools.get_deployment()


@mcp.tool()
def get_logs(service: Literal["api", "worker", "db"], limit: int) -> str:
    """Extract information from relevant logs."""
    return incident_tools.get_logs(service, limit)


@mcp.tool()
def search_runbooks(query: str, top_k: int = 3) -> list[dict]:
    """Search incident-response runbooks for relevant troubleshooting guidance."""
    return retrieve(query, top_k)


if __name__ == "__main__":
    mcp.run()
