from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_service import get_agent_executor
import uvicorn

app = FastAPI(title="NBA Agent API")

THOUGHTS_MAX_LENGTH = 200

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
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
    try:
        agent_executor = get_agent_executor()
        result = agent_executor.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}},
        )


        # Extract the final output
        full_output = result.get("output", "No response generated.")

        # Parse follow-up questions
        follow_ups = []
        clean_output = full_output
        if "FOLLOW_UP:" in full_output:
            parts = full_output.split("FOLLOW_UP:")
            clean_output = parts[0].strip()
            raw_follows = parts[1].strip()
            # Split by | and clean up
            follow_ups = [q.strip() for q in raw_follows.split("|") if q.strip()]

        # Format intermediate steps for the "thought" field
        steps = result.get("intermediate_steps", [])
        thought_parts = []
        for i, (action, observation) in enumerate(steps, 1):
            tool_name = getattr(action, "tool", "Unknown Tool")
            if tool_name == "think":
                thought_val = getattr(action, "tool_input", "")
                if isinstance(thought_val, dict):
                    thought_val = thought_val.get("thought", "")
                # Truncate to first 200 chars for conciseness
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
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
