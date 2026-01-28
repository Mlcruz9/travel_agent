import os
from dotenv import load_dotenv
from types import SimpleNamespace

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:  # pragma: no cover - optional dependency
    Console = None
    Panel = None
    Text = None

from tools import (
    find_traditional_dishes_deep,
    create_interest_focused_plan,
    create_budget_focused_plan,
    create_enriched_discovery_plan
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """You are an expert global travel planner. Your goal is to choose the best tool and then format the output correctly based on which tool was used.

TOOL USAGE STRATEGY (in order of priority):
1. For ANY plan, you should FIRST call the `find_traditional_dishes_deep` tool to get local dish names for the city.
2. If the user mentions an INTEREST, after finding dishes you must call `create_interest_focused_plan`.
3. If the user mentions a BUDGET, after finding dishes you must call `create_budget_focused_plan`.
4. If the user asks for a general plan (no budget and no specific interest), after finding dishes you must call `create_enriched_discovery_plan`.
5. FALLBACK RULE: If a specific tool (interest or budget) fails or returns an error, acknowledge this briefly and then call `create_enriched_discovery_plan` as a fallback.

RESPONSE GENERATION (CRITICAL):
- After the final successful tool call, craft a friendly and detailed Markdown summary of the plan.
- For each location, you MUST create a clickable Markdown link.

CONDITIONAL FORMATTING RULES:
- IF you used the `create_budget_focused_plan` tool:
  - For each RESTAURANT, you MUST display its price level.
  - Use this format:
    * **[Name](Link)** (Rating: [Rating] ⭐) - Price: **[Price]**

- IF you used `create_enriched_discovery_plan` OR `create_interest_focused_plan`:
  - You MUST NOT display the price level.
  - Use this format:
    * **[Name](Link)** (Rating: [Rating] ⭐)

Your Final Answer must ONLY be this generated Markdown text (no JSON, no tool logs).
"""


def _message_content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_chunks = []
        for item in content:
            if isinstance(item, str):
                text_chunks.append(item)
            elif isinstance(item, dict):
                if "text" in item and isinstance(item["text"], str):
                    text_chunks.append(item["text"])
        return "\n".join(text_chunks)
    return ""


class AgentExecutorCompat:
    def __init__(self, graph, verbose=True):
        self._graph = graph
        self._verbose = verbose
        self._console = Console() if Console else None

    def invoke(self, inputs):
        if "messages" in inputs:
            state = inputs
        else:
            state = {"messages": [{"role": "user", "content": inputs.get("input", "")}]}

        result = self._graph.invoke(state)
        messages = result.get("messages", [])

        output = ""
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                output = _message_content_to_text(message.content)
                break

        intermediate_steps = []
        for message in messages:
            if isinstance(message, ToolMessage):
                tool_name = message.name or message.additional_kwargs.get("name")
                tool_output = _message_content_to_text(message.content)
                intermediate_steps.append((SimpleNamespace(tool=tool_name), tool_output))

        if self._verbose and self._console and Panel and Text:
            user_content = ""
            if state.get("messages"):
                last_user = state["messages"][-1]
                if isinstance(last_user, dict) and last_user.get("role") == "user":
                    user_content = last_user.get("content", "")
            if user_content:
                self._console.print(Panel(Text(user_content, style="bold white"), title="User", style="blue"))
            for action, tool_output in intermediate_steps:
                title = f"Tool: {action.tool or 'unknown'}"
                self._console.print(Panel(Text(tool_output, style="white"), title=title, style="cyan"))
            if output:
                self._console.print(Panel(Text(output, style="white"), title="Assistant", style="green"))

        return {"output": output, "intermediate_steps": intermediate_steps}


def get_agent():
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=openai_api_key,
    )

    tools = [
        find_traditional_dishes_deep, 
        create_interest_focused_plan,
        create_budget_focused_plan,
        create_enriched_discovery_plan
    ]

    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=False,
    )

    return AgentExecutorCompat(agent_graph, verbose=True)
