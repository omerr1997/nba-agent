import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from config import settings
import prompts
from tools import get_player_info, get_team_info, get_player_career_stats, think, web_search
from langchain.agents.format_scratchpad.tools import format_to_tool_messages
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser

# Constants for session management
SESSION_INPUT_KEY = "input"
SESSION_HISTORY_KEY = "chat_history"
SESSION_OUTPUT_KEY = "output"

# Global dictionary to store session history in memory
session_histories = {}


def get_session_history(session_id: str):
    """Retrieve or create chat history for a given session."""
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    return session_histories[session_id]


def get_agent_executor():
    """Build the conversational agent with structured reasoning and tool support."""
    llm = ChatOpenAI(
        model=settings.model_name,
        temperature=0,
    )

    tools = [get_player_info, get_team_info, get_player_career_stats, think, web_search]

    prompt_text = prompts.SYSTEM_PROMPT.format(
        tools_list=settings.tools_list, current_date=settings.current_date
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            MessagesPlaceholder(variable_name=SESSION_HISTORY_KEY, optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm_with_tools = llm.bind_tools(tools)

    # Simplified agent chain
    agent = (
        {
            SESSION_INPUT_KEY: lambda x: x["input"],
            SESSION_HISTORY_KEY: lambda x: x.get("chat_history", []),
            "agent_scratchpad": lambda x: format_to_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | ToolsAgentOutputParser()
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    return RunnableWithMessageHistory(
        executor,
        get_session_history,
        input_messages_key=SESSION_INPUT_KEY,
        history_messages_key=SESSION_HISTORY_KEY,
        output_messages_key=SESSION_OUTPUT_KEY,
    )


