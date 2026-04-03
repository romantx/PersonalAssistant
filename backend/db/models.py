from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)  # 'user', 'assistant', 'system'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentRun(Base):
    __tablename__ = 'agent_runs'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    agent_name = Column(String)
    duration_ms = Column(Float)
    status = Column(String)
    input_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

import enum
from sqlalchemy import Enum

class AgentType(str, enum.Enum):
    STRATEGIST = "STRATEGIST"
    RESEARCH = "RESEARCH"
    CODING = "CODING"
    SCHEDULING = "SCHEDULING"
    COMMUNICATIONS = "COMMUNICATIONS"
    SOCIAL = "SOCIAL"
    DESIGN = "DESIGN"

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    parent_task_id = Column(Integer, index=True, nullable=True)
    task_type = Column(String, nullable=False)
    assigned_agent = Column(Enum(AgentType), nullable=False)
    status = Column(String) # 'pending', 'in_progress', 'completed', 'failed'
    input_params_json = Column(Text, nullable=True)
    result_summary_text = Column(Text, nullable=True)
    result_artifacts_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AgentStateLayer(Base):
    __tablename__ = 'agent_state'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CalendarCache(Base):
    __tablename__ = 'calendar_cache'
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True)
    summary = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

class CouncilRun(Base):
    __tablename__ = 'council_runs'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, index=True, nullable=True)
    query = Column(Text, nullable=False)
    member_a_model = Column(String, nullable=False)
    member_a_response = Column(Text, nullable=False)
    member_b_model = Column(String, nullable=False)
    member_b_response = Column(Text, nullable=False)
    member_c_model = Column(String, nullable=False)
    member_c_response = Column(Text, nullable=False)
    chairman_model = Column(String, nullable=False, default='gemini-2.5-pro')
    chairman_synthesis = Column(Text, nullable=False)
    rankings_json = Column(Text, nullable=False)
    consensus_points = Column(Text)
    disagreements = Column(Text)
    total_latency_ms = Column(Integer)
    total_tokens = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
