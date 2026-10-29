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
    """Get metrics for the synthetic API/worker/database incident environment. Not Hadoop."""
    return incident_tools.get_metrics()


@mcp.tool()
def get_deployment() -> dict:
    """Get deployment changes for the synthetic API incident environment. Not Hadoop."""
    return incident_tools.get_deployment()


@mcp.tool()
def get_logs(service: Literal["api", "worker", "db"], limit: int) -> str:
    """Read synthetic API, worker, or database service logs. Not Hadoop logs."""
    return incident_tools.get_logs(service, limit)


@mcp.tool()
def search_runbooks(query: str, top_k: int = 3) -> list[dict]:
    """Search runbooks for the synthetic API/worker/database incident environment."""
    return retrieve(query, top_k)


@mcp.tool()
def search_logs(
    application_id: str, query: str, limit: int = 20, start_line: int = 1
) -> list:
    """Search Hadoop logs using one case-insensitive literal substring.
    Use separate tool calls for different search terms."""
    return incident_tools.search_logs(application_id, query, limit, start_line)


if __name__ == "__main__":
    mcp.run()
