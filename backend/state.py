from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """The graph state representing our multi-agent conversation."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    active_plan: str
    next_agent: str
    requires_approval: bool
