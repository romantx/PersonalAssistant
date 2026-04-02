import subprocess
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from state import AgentState
from config import settings
from email_tools import read_emails, send_email

@tool
def execute_python_code(code: str) -> str:
    """Executes python code locally and returns the standard output."""
    try:
        result = subprocess.run(
            ["python", "-c", code], 
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return f"Success:\n{result.stdout}"
        else:
            return f"Error:\n{result.stderr}"
    except Exception as e:
        return f"Execution Failed: {str(e)}"

def get_coder_llm():
    if not settings.openrouter_api_key or settings.openrouter_api_key == "your_openrouter_api_key_here":
        return None
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        model="anthropic/claude-3.5-sonnet"
    )
    return llm.bind_tools([execute_python_code])

def get_planner_llm():
    if not settings.gemini_api_key or settings.gemini_api_key.startswith("your"):
        return None
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.gemini_api_key)

def research_agent(state: AgentState):
    """The Gemini Planner that researches and writes plans."""
    llm = get_planner_llm()
    messages = state.get("messages", [])
    if not llm:
        return {"messages": [AIMessage(content="[Planner Stub]: Gemini API Key missing.")], "next_agent": "end"}
    
    prompt = "You are the Gemini Planner. Analyze the user's request. If it requires coding, output a detailed plan and append the exact phrase 'HANDOFF_TO_CODER' at the very end. If it does NOT require coding, just answer normally."
    api_messages = [SystemMessage(content=prompt)] + list(messages)
    try:
        response = llm.invoke(api_messages)
        res_text = response.content
        next_agent = "end"
        active_plan = state.get("active_plan", "")
        
        if "HANDOFF_TO_CODER" in res_text:
            next_agent = "coding_agent"
            res_text = res_text.replace("HANDOFF_TO_CODER", "").strip()
            active_plan = res_text
            
        return {"messages": [AIMessage(content=f"[Gemini Planner]: {res_text}")], "next_agent": next_agent, "active_plan": active_plan}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Gemini Error: {str(e)}")], "next_agent": "end"}

def coding_agent(state: AgentState):
    """The Claude Execution Agent that writes and runs code."""
    llm = get_coder_llm()
    messages = state.get("messages", [])
    plan = state.get("active_plan", "No active plan provided.")
    
    if not llm:
        return {"messages": [AIMessage(content="[Claude Coder Stub]: Claude API missing.")], "next_agent": "end"}
    
    prompt = f"You are Claude, the execution agent. Your task is to execute the following plan from Gemini:\n<plan>{plan}</plan>\nYou have access to the execute_python_code tool. Implement the plan and report the outcome."
    api_messages = [SystemMessage(content=prompt)] + list(messages)
    
    try:
        response = llm.invoke(api_messages)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            api_messages.append(response)
            for tool_call in response.tool_calls:
                if tool_call["name"] == "execute_python_code":
                    tool_result = execute_python_code.invoke(tool_call["args"])
                    api_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
            
            final_response = llm.invoke(api_messages)
            return {"messages": [AIMessage(content=f"[Claude Execution]:\n{final_response.content}")], "next_agent": "end"}

        return {"messages": [AIMessage(content=f"[Claude Execution]: {response.content}")], "next_agent": "end"}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Claude Error: {str(e)}")], "next_agent": "end"}

def comms_agent(state: AgentState):
    """Handles emails (Proton/Gmail) and calendaring."""
    if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("your"):
        return {"messages": [AIMessage(content="[Comms Agent Stub]: OpenRouter API missing.")], "next_agent": "end"}
        
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        model="openai/gpt-4o"
    ).bind_tools([read_emails, send_email])
    
    messages = state.get("messages", [])
    prompt = "You are the Communications Agent. You use tools to read and send emails via Gmail or Proton mail. You MUST use the tools provided. If the user doesn't specify which provider (gmail or proton), you must ask them."
    api_messages = [SystemMessage(content=prompt)] + list(messages)
    
    try:
        response = llm.invoke(api_messages)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_map = {"read_emails": read_emails, "send_email": send_email}
            api_messages.append(response)
            for tool_call in response.tool_calls:
                tool_fn = tool_map.get(tool_call["name"])
                if tool_fn:
                    tool_result = tool_fn.invoke(tool_call["args"])
                    api_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
            
            final_response = llm.invoke(api_messages)
            return {"messages": [AIMessage(content=f"[Comms Output]:\n{final_response.content}")], "next_agent": "end"}
            
        return {"messages": [AIMessage(content=f"[Comms Agent]: {response.content}")], "next_agent": "end"}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Comms Error: {str(e)}")], "next_agent": "end"}

def router_node(state: AgentState):
    """Master router."""
    messages = state.get("messages", [])
    last_message = messages[-1].content.lower() if messages else ""
    
    # Send all planning tasks to Gemini first
    next_agent = "research_agent"
    if "email" in last_message or "schedule" in last_message:
        next_agent = "comms_agent"
        
    return {"next_agent": next_agent}

def router_edge(state: AgentState) -> str:
    return state.get("next_agent", "end")
