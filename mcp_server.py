#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 03:48:06 2026

@author: walidajalil
"""

import tools
from mcp.server import MCPServer

mcp = MCPServer("Incident Response")


@mcp.tool()
def get_metrics() -> dict:
    """Get the current service metrics."""
    return tools.get_metrics()


@mcp.tool()
def get_deployment() -> dict:
    """Get information on current deployment and any changes to it."""
    return tools.get_deployment()


@mcp.tool()
def get_logs(service: str, limit: int) -> str:
    """Extract information from relevant logs."""
    return tools.get_logs(service, limit)
