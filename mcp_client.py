"""
MCP Client for Order Management System
Handles communication with the MCP server using Streamable HTTP transport
"""
import httpx
import json
from typing import Any, Optional


class MCPClient:
    """Client for communicating with the MCP server"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        self._request_id = 0
        self._initialized = False
    
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def _send_request(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id()
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.server_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def initialize(self) -> dict:
        """Initialize the MCP connection"""
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "support-chatbot", "version": "1.0.0"}
        })
        self._initialized = True
        return result
    
    async def list_tools(self) -> list:
        """List available tools from the MCP server"""
        if not self._initialized:
            await self.initialize()
        result = await self._send_request("tools/list")
        return result.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call a tool on the MCP server"""
        if not self._initialized:
            await self.initialize()
        
        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Extract the text content from the response
        content = result.get("result", {}).get("content", [])
        if content and len(content) > 0:
            return {"result": content[0].get("text", "")}
        return {"result": "No content returned"}


# Tool definitions for the LLM
MCP_TOOLS = [
    {
        "name": "list_products",
        "description": "List products with optional filters. Use this to browse inventory by category or check stock levels.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (e.g., 'Computers', 'Monitors', 'Printers', 'Accessories', 'Networking')"
                },
                "is_active": {
                    "type": "boolean",
                    "description": "Filter by active status (true/false)"
                }
            }
        }
    },
    {
        "name": "get_product",
        "description": "Get detailed product information by SKU. Use this to get current price, check inventory for specific item, or verify product details.",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Product SKU (e.g., 'COM-0001', 'MON-0054')"
                }
            },
            "required": ["sku"]
        }
    },
    {
        "name": "search_products",
        "description": "Search products by name or description. Use this for natural language product lookup.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (case-insensitive, partial match)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_customer",
        "description": "Get customer information by ID. Use this to look up customer details or verify shipping address.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer UUID"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "verify_customer_pin",
        "description": "Verify customer identity with email and PIN. Use this to authenticate customer before order placement.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer email address"
                },
                "pin": {
                    "type": "string",
                    "description": "4-digit PIN code"
                }
            },
            "required": ["email", "pin"]
        }
    },
    {
        "name": "list_orders",
        "description": "List orders with optional filters. Use this to view customer order history or track pending orders.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Filter by customer UUID"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (draft|submitted|approved|fulfilled|cancelled)"
                }
            }
        }
    },
    {
        "name": "get_order",
        "description": "Get detailed order information including items. Use this to view order details or check order contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order UUID"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "create_order",
        "description": "Create a new order with items. Customer must be verified first. Order starts in 'submitted' status.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer UUID (must be verified first)"
                },
                "items": {
                    "type": "array",
                    "description": "List of items to order",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string", "description": "Product SKU"},
                            "quantity": {"type": "integer", "description": "Quantity (must be > 0)"},
                            "unit_price": {"type": "string", "description": "Price as string"},
                            "currency": {"type": "string", "description": "Currency code (default: USD)"}
                        },
                        "required": ["sku", "quantity", "unit_price"]
                    }
                }
            },
            "required": ["customer_id", "items"]
        }
    }
]


def get_tool_definitions_for_gemini():
    """Convert tool definitions to Gemini function declaration format"""
    from google.generativeai.types import FunctionDeclaration, Tool
    
    function_declarations = []
    for tool in MCP_TOOLS:
        func_decl = FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"]
        )
        function_declarations.append(func_decl)
    
    return Tool(function_declarations=function_declarations)
