import asyncio
from state import AgentState
from agents import research_agent
from langchain_core.messages import HumanMessage

state = {"messages": [HumanMessage(content="Hey can you tell me what is the latest on news about the US situation in Iran?")]}
res = research_agent(state)
print("FINAL RESPONSE:")
print(repr(res))
