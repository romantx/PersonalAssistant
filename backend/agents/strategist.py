import os
import sys
import json
import asyncio
from typing import TypedDict, Annotated, Sequence, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Path appending so this runs locally if invoked dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, START, END
from db.models import AgentType, AgentRun
from db.database import SessionLocal

# 1. State Definition
class StrategistState(TypedDict):
    query: str
    messages: list
    current_phase: str
    validation_status: str
    plan: str
    next_agent: Optional[AgentType]

# 2. Nodes
async def node_observe(state: StrategistState):
    print("[Observe] Pulling new events from the world state...")
    return {"current_phase": "observed", "messages": state.get("messages", []) + [{"role": "system", "content": "Observe complete"}]}

async def node_orient(state: StrategistState):
    print(f"[Orient] Grounding Gemini into context for query: '{state['query']}'")
    return {"current_phase": "oriented", "plan": "Drafting plan based on query."}

async def node_validate(state: StrategistState):
    print("[Validate] Checking plan against recent observations (simulated PASS)...")
    return {"validation_status": "PASS"}

async def node_decide(state: StrategistState):
    print("[Decide] Utilizing Gemini to choose discrete sub-agent...")
    # Mocking the Gemini JSON extraction output for the standalone execution test!
    raw_llm_json_output = {"next_agent": "CODING"} 
    
    # Casting to Enum natively as mandated by the other agent's review boundary conditions:
    try:
        chosen_enum = AgentType(raw_llm_json_output["next_agent"])
    except ValueError:
        print(f"[Decide] WARNING: LLM hallucinated agent string {raw_llm_json_output['next_agent']}. Defaulting to STRATEGIST.")
        chosen_enum = AgentType.STRATEGIST
        
    return {"current_phase": "decided", "next_agent": chosen_enum}

async def node_act(state: StrategistState):
    # This node executes synchronously to handle immediate DB write locks cleanly, except for the async agent task.
    shadow_mode = os.environ.get("SHADOW_MODE", "true").lower() == "true"
    chosen_agent = state.get("next_agent", AgentType.STRATEGIST)
    
    print(f"[Act] Routing to {chosen_agent.name}...")
    
    db = SessionLocal()
    
    def log_agent_run(agent_name: str, status: str, duration: float = 0.0):
        try:
            run_log = AgentRun(
                session_id="mock_session",
                agent_name=agent_name,
                duration_ms=duration,
                status=status,
                input_hash=state["query"]
            )
            db.add(run_log)
            db.commit()
            print(f"[Act] \033[92mSUCCESS\033[0m: {status} log committed using IMMEDIATE transaction lock.")
        except Exception as e:
            db.rollback()
            print(f"[Act] \033[91mFAILURE\033[0m: DB write failed: {e}")
        finally:
            db.close()

    if shadow_mode:
        print(f"[Act] SHADOW_MODE enabled. Logging mock traversal to SQLite agent_runs without execution.")
        log_agent_run(chosen_agent.name, "SHADOW")
    else:
        if chosen_agent == AgentType.CODING:
            print(f"[Act] Executing real agent dispatch for CODING...")
            from coding_agent import invoke_coding_agent
            import time
            start = time.perf_counter_ns()
            
            # Execute actual Claude Logic!
            result_text = await invoke_coding_agent(state["query"])
            
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            print(f"[Act] Coding Agent Complete. Result:\n{result_text}")
            log_agent_run(chosen_agent.name, "SUCCESS", elapsed_ms)
        else:
            print(f"[Act] Agent {chosen_agent.name} has no module yet. Defaulting to SHADOW fallback.")
            log_agent_run(chosen_agent.name, "SHADOW")
        
    return {"current_phase": "acted"}

# 3. Routing Functions
def check_validation(state: StrategistState):
    if state.get("validation_status") == "PASS":
        return "decide"
    return "observe"

def build_graph():
    graph = StateGraph(StrategistState)
    graph.add_node("observe", node_observe)
    graph.add_node("orient", node_orient)
    graph.add_node("validate", node_validate)
    graph.add_node("decide", node_decide)
    graph.add_node("act", node_act)
    
    graph.add_edge(START, "observe")
    graph.add_edge("observe", "orient")
    graph.add_edge("orient", "validate")
    graph.add_conditional_edges("validate", check_validation, {"decide": "decide", "observe": "observe"})
    graph.add_edge("decide", "act")
    graph.add_edge("act", END)
    
    return graph.compile()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Write a python script to parse logs."
    app = build_graph()
    
    print(f"\n\033[1m--- INITIATING LANGGRAPH OODA LOOP ---\033[0m")
    print(f"Goal: {query}\n")
    
    initial_state = {"query": query, "messages": [], "current_phase": "start", "validation_status": "", "plan": "", "next_agent": None}
    
    async def run():
        async for output in app.astream(initial_state):
            pass # Node prints handle console logging natively
        print(f"\n\033[1m--- OODA LOOP COMPLETE ---\033[0m\n")
                
    asyncio.run(run())
