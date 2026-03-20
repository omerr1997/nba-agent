import logging
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_service import get_agent_executor
from config import settings

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Agent API")

# Constants
THOUGHTS_MAX_LENGTH = 200

# CORS: configurable via CORS_ORIGINS env var in production
_cors_origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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

    except Exception as e:
        logger.error(f"Error occurred during chat processing: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
