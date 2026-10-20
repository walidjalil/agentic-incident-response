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
