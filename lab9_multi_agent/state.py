import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The state shared across all agents in the multi-agent system."""
    
    # The list of chat messages
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # The next node to run
    next: str
    
    # Trace log to keep track of what agents are doing
    trace: Annotated[list[str], operator.add]
