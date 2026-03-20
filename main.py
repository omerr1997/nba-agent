import logging
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_service import get_agent_executor
from config import settings
from tools import get_player_info, get_team_info, get_player_career_stats

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Agent API")

# Constants
THOUGHTS_MAX_LENGTH = 200
TEST_SESSION_ID = "-1"  # Magic session ID that bypasses the LLM for deterministic E2E testing

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


class ChatResponse(BaseModel):
    response: str
    thought: str = ""
    follow_ups: list[str] = []


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the LangChain agent with session-based history."""
    try:
        # Test mode: bypass LLM entirely and return raw tool output for deterministic E2E testing
        if request.session_id == TEST_SESSION_ID:
            return _handle_test_mode(request.message)

        agent_executor = get_agent_executor()
        result = agent_executor.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}},
        )

        full_output = result.get("output", "No response generated.")

        # Parse follow-up questions using constants from settings
        follow_ups = []
        clean_output = full_output
        if settings.FOLLOW_UP_INDICATOR in full_output:
            parts = full_output.split(settings.FOLLOW_UP_INDICATOR)
            clean_output = parts[0].strip()
            raw_follows = parts[1].strip()
            follow_ups = [
                q.strip()
                for q in raw_follows.split(settings.FOLLOW_UP_SEP)
                if q.strip()
            ]

        # Format intermediate steps for the "thought" field
        steps = result.get("intermediate_steps", [])
        thought_parts = []
        for i, (action, observation) in enumerate(steps, 1):
            tool_name = getattr(action, "tool", "Unknown Tool")
            if tool_name == "think":
                thought_val = getattr(action, "tool_input", "")
                if isinstance(thought_val, dict):
                    thought_val = thought_val.get("thought", "")
                display_thought = (
                    (thought_val[:THOUGHTS_MAX_LENGTH] + "...")
                    if len(thought_val) > THOUGHTS_MAX_LENGTH
                    else thought_val
                )
                thought_parts.append(f"{i}. Reasoning: {display_thought}")
            else:
                target = getattr(action, "tool_input", "")
                thought_parts.append(f"{i}. Use {tool_name}: {target}")

        thought_flow = "\n".join(thought_parts)

        return ChatResponse(
            response=clean_output, thought=thought_flow, follow_ups=follow_ups
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error occurred during chat processing: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


def _handle_test_mode(message: str) -> ChatResponse:
    """Direct tool invocation for E2E testing — bypasses the LLM entirely.

    The message must be in the format: 'TOOL_NAME:argument'.
    Supported commands:
      - get_player_info:LeBron James
      - get_team_info:Los Angeles Lakers
      - get_player_career_stats:2544
    """
    if ":" not in message:
        raise HTTPException(
            status_code=400,
            detail="Test mode requires format 'TOOL_NAME:argument'",
        )

    tool_name, _, arg = message.partition(":")
    tool_name = tool_name.strip()
    arg = arg.strip()

    tool_map = {
        "get_player_info": lambda: get_player_info.invoke({"full_name": arg}),
        "get_team_info": lambda: get_team_info.invoke({"team_name": arg}),
        "get_player_career_stats": lambda: get_player_career_stats.invoke({"player_id": int(arg)}),
    }

    if tool_name not in tool_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tool '{tool_name}'. Valid tools: {list(tool_map.keys())}",
        )

    raw_result = tool_map[tool_name]()
    return ChatResponse(response=raw_result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
