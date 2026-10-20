#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 03:48:06 2026

@author: walidajalil
"""

from mcp.server import MCPServer
import incident_tools

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
def get_logs(service: str, limit: int) -> str:
    """Extract information from relevant logs."""
    return incident_tools.get_logs(service, limit)


if __name__ == "__main__":
    mcp.run()
