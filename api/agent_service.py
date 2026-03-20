import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .config import settings
from . import prompts
from .tools import get_player_info, get_team_info, get_player_career_stats, think, web_search

# Global dictionary to store session history in memory (for local dev; Vercel is stateless)
session_histories = {}

def get_session_history(session_id: str):
    """Retrieve or create chat history for a given session."""
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    return session_histories[session_id]

# LangGraph checkpointer for state management
memory = MemorySaver()

def get_agent_executor():
    """Build the conversational agent using LangGraph's prebuilt ReAct agent."""
    llm = ChatOpenAI(
        model=settings.model_name,
        temperature=0,
        max_tokens=settings.max_tokens,
    )

    tools = [get_player_info, get_team_info, get_player_career_stats, think, web_search]

    system_message = prompts.SYSTEM_PROMPT.format(
        tools_list=settings.tools_list, current_date=settings.current_date
    )

    # Create the LangGraph ReAct agent
    # We use the checkpointer to manage history automatically
    agent = create_react_agent(
        llm, 
        tools, 
        prompt=system_message,
        checkpointer=memory
    )

    return agent
