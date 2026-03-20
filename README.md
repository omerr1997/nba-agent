# NBA Agent

A conversational AI agent built with LangChain that provides real-time NBA information, player statistics, and team data. It features a sophisticated reasoning loop and session-based chat history.

## Architecture

The project follows a modular architecture designed for scalability and maintainability:
- **FastAPI Backend**: Provides a robust REST API to handle chat messages and session management.
- **LangChain Agent**: An OpenAI Tools-based agent that leverages a "Chain of Thought" reasoning process.
- **Session Management**: Uses `RunnableWithMessageHistory` to manage isolated chat contexts for different users/sessions.
- **Design Pattern**: Decoupled tool definitions, prompt management, and service orchestration.

## Code Structure

- `main.py`: FastAPI server, request validation, and API response formatting.
- `agent_service.py`: Orchestrates the LangChain agent, LLM configuration, and session history logic.
- `tools.py`: Definition of all tools available to the agent (NBA API wrappers, web search).
- `config.py`: Centralized configuration management using Pydantic Settings.
- `prompts.py`: Central repository for all system prompts and documentation strings.
- `utils.py`: Common helpers for JSON formatting, error handling, and tool decorators.

## Tools

1.  **think**: A specialized tool that allows the agent to record and display its internal reasoning steps.
2.  **get_player_info**: Retrieves IDs and basic details for NBA players.
3.  **get_team_info**: Fetches core data for NBA teams.
4.  **get_player_career_stats**: Provides summarized career statistics (points, assists, rebounds, etc.).
5.  **web_search**: Powered by Tavily, enabling the agent to access current NBA news and real-time events.

## How to Run

### 1. Prerequisites
- Python 3.10 or higher.
- A virtual environment (recommended).

### 2. Setup
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    # OR if using poetry
    poetry install
    ```
2.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    OPENROUTER_API_KEY=your_openrouter_key
    TAVILY_API_KEY=your_tavily_key
    MODEL_NAME=openai/gpt-4o-mini
    ```

### 3. Execution
- **Start the Backend**:
  ```bash
  python main.py
  ```
  The API will be available at `http://localhost:8000`.

- **Start the Frontend** (optional):
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## Future Enhancements
- **Persistent Storage**: Migration from in-memory session history to a database (Redis or PostgreSQL).
- **Proactive Insights**: Adding a scheduling layer to alert users of upcoming games or trades.
- **Rich UI Components**: Supporting player headshots and team logos in the chat interface.
- **Comparison Engine**: A specialized tool for head-to-head statistical player comparisons.
