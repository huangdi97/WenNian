"""Base agent abstraction with capability token enforcement.

All agents in the WenNian multi-agent system inherit from BaseAgent
and operate under a CapabilityToken that restricts available tools
and data scopes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentOutput(BaseModel):
    """Standardized output for any agent execution.

    Attributes:
        success: Whether the agent completed its task.
        data: The primary output payload.
        errors: List of error messages encountered.
        metadata: Arbitrary additional context.
    """

    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityToken:
    """Permission token controlling agent capabilities.

    Attributes:
        allowed_tools: Names of tools the agent may invoke.
        allowed_data_scopes: Data scopes the agent may access.
    """

    allowed_tools: List[str] = field(default_factory=list)
    allowed_data_scopes: List[str] = field(default_factory=list)

    def check(self, tool_name: str, data_scope: str) -> bool:
        """Verify that the agent is authorized for a given tool and data scope.

        Args:
            tool_name: The name of the tool being invoked.
            data_scope: The data scope being accessed.

        Returns:
            True if both are allowed.
        """
        return tool_name in self.allowed_tools and data_scope in self.allowed_data_scopes


class BaseAgent(ABC):
    """Abstract base class for all WenNian agents.

    Args:
        agent_id: Unique identifier for this agent instance.
        capability: CapabilityToken restricting the agent's permissions.
    """

    agent_id: str
    capability: CapabilityToken

    def __init__(self, agent_id: str, capability: Optional[CapabilityToken] = None) -> None:
        self.agent_id = agent_id
        self.capability = capability or CapabilityToken()

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Execute the agent's primary task.

        Args:
            context: Input context dictionary.

        Returns:
            AgentOutput with results and metadata.
        """

    def log(self, message: str, level: str = "INFO") -> None:
        """Emit a structured log message.

        Args:
            message: The log content.
            level: Log level (DEBUG, INFO, WARNING, ERROR).
        """
        import logging
        logger = logging.getLogger(f"agent.{self.agent_id}")
        getattr(logger, level.lower(), logger.info)(message)

    def can_access(self, tool_name: str, data_scope: str = "public") -> bool:
        """Check if this agent has permission to use a tool in a scope.

        Args:
            tool_name: Tool identifier.
            data_scope: Data scope identifier.

        Returns:
            True if authorized.
        """
        return self.capability.check(tool_name, data_scope)
