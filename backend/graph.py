from langgraph.graph import StateGraph, END
from state import AgentState
from agents import research_agent, coding_agent, comms_agent, router_node, router_edge

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("research_agent", research_agent)
    workflow.add_node("coding_agent", coding_agent)
    workflow.add_node("comms_agent", comms_agent)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        router_edge,
        {
            "research_agent": "research_agent",
            "coding_agent": "coding_agent",
            "comms_agent": "comms_agent",
            "end": END
        }
    )
    
    # Research agent can conditionally hand off to Claude Coder, or end.
    workflow.add_conditional_edges(
        "research_agent",
        router_edge,
        {
            "coding_agent": "coding_agent",
            "end": END
        }
    )
    workflow.add_edge("coding_agent", END)
    workflow.add_edge("comms_agent", END)
    
    return workflow.compile()

app_graph = build_graph()
