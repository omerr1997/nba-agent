import logging
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .agent_service import get_agent_executor
from .config import settings

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Agent API")

# Constants
THOUGHTS_MAX_LENGTH = 200

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
    """Process a chat message through the LangGraph agent."""
    try:
        agent = get_agent_executor()
        
        # LangGraph uses a thread_id for state persistence
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Invoke the agent with a HumanMessage
        result = agent.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )

        # The response is the content of the last AI message
        messages = result.get("messages", [])
        if not messages:
            raise ValueError("Agent returned no messages.")
            
        last_message = messages[-1]
        full_output = last_message.content if isinstance(last_message, AIMessage) else "No response generated."

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

        # Format tool calls (thoughts) for the frontend
        # In LangGraph, we step through messages to find tool usage
        thought_parts = []
        step_idx = 1
        for msg in messages:
            # Look for AI messages that had tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name", "Unknown Tool")
                    tool_input = tc.get("args", {})
                    
                    if tool_name == "think":
                        thought_val = tool_input.get("thought", str(tool_input))
                        display_thought = (
                            (thought_val[:THOUGHTS_MAX_LENGTH] + "...")
                            if len(thought_val) > THOUGHTS_MAX_LENGTH
                            else thought_val
                        )
                        thought_parts.append(f"{step_idx}. Reasoning: {display_thought}")
                    else:
                        target = str(tool_input)
                        thought_parts.append(f"{step_idx}. Use {tool_name}: {target}")
                    step_idx += 1

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
