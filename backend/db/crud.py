import logging
from sqlalchemy.orm import Session
from db.models import Conversation, AgentRun
import hashlib

logger = logging.getLogger(__name__)

def log_conversation(db: Session, session_id: str, role: str, content: str):
    """Silently logs conversation rows without throwing errors up the chain."""
    try:
        conv = Conversation(session_id=session_id, role=role, content=content)
        db.add(conv)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log conversation to custom schema: {e}")
        db.rollback()

def log_agent_run(db: Session, session_id: str, agent_name: str, duration_ms: float, status: str, input_text: str):
    """Silently logs agent run execution metrics."""
    try:
        input_hash = hashlib.md5(input_text.encode('utf-8')).hexdigest()
        run_record = AgentRun(
            session_id=session_id,
            agent_name=agent_name,
            duration_ms=duration_ms,
            status=status,
            input_hash=input_hash
        )
        db.add(run_record)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log agent_run to custom schema: {e}")
        db.rollback()
