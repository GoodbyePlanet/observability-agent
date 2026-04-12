from fastapi import APIRouter, Request

from backend.agent.tool_bridge import mcp_tools_to_openai_functions

router = APIRouter()


@router.get("/api/mcp/servers")
async def list_servers(request: Request) -> dict:
    mcp_manager = request.app.state.mcp_manager
    return {"servers": mcp_manager.get_server_names()}


@router.get("/api/mcp/tools")
async def list_tools(request: Request) -> dict:
    mcp_manager = request.app.state.mcp_manager
    raw_tools = mcp_manager.get_all_tools()

    tools_by_server: dict[str, list[dict]] = {}
    for server_name, tool in raw_tools:
        tools_by_server.setdefault(server_name, []).append(
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
        )

    openai_functions = mcp_tools_to_openai_functions(raw_tools)

    return {
        "tools_by_server": tools_by_server,
        "openai_function_definitions": openai_functions,
        "total_tools": len(raw_tools),
    }
