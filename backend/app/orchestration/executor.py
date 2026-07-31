"""Production-ready agent executor."""

from typing import Any
from app.agents.base import AgentState
from app.agents.reasoning_loop import ReasoningLoop
from app.agents.execution_engine import AgentToolInvoker
from app.memory.chromadb import ChromaMemoryService
from app.agents.types import AgentType
from app.db.database import async_session_maker
from app.agents.autonomous import UserScopedLLMService
import json

class ProductionExecutor:
    """A production-ready executor for running agentic workflows."""

    def __init__(
        self,
        reasoning_loop: ReasoningLoop,
        tool_invoker: AgentToolInvoker,
        memory_service: ChromaMemoryService,
    ):
        self.reasoning_loop = reasoning_loop
        self.tool_invoker = tool_invoker
        self.memory_service = memory_service

    async def execute_agent_step(
        self,
        task: str,
        session_id: str,
        agent_type: AgentType,
        context: dict[str, Any],
        user_id: str | None = None,
    ) -> Any:
        """Executes a single step for a given agent."""
        llm_service = UserScopedLLMService(
            user_id=user_id,
            db_session_factory=async_session_maker,
        )

        trace = await self.reasoning_loop.execute(
            task=task,
            agent_type=agent_type,
            session_id=session_id,
            context=context,
            llm_service=llm_service,
        )

        await self.memory_service.store_conversation(
            session_id=session_id,
            role="execution_trace",
            content=json.dumps(trace.to_dict()),
            agent_type=agent_type.value,
            metadata={"agent_type": agent_type.value},
        )

        return trace.final_result

    async def execute(
        self,
        task: str,
        session_id: str,
        context: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> AgentState:
        """
        Executes a multi-agent workflow to accomplish a task.
        """
        # This will be the main entry point.
        # For now, it will just run a simple workflow.
        
        context = context or {}

        # 1. Plan
        plan_result = await self.execute_agent_step(
            task=f"Create a plan for the following task: {task}",
            session_id=session_id,
            agent_type=AgentType.PLANNER,
            context=context,
            user_id=user_id,
        )

        # 2. Research
        research_result = await self.execute_agent_step(
            task=f"Research the plan: {plan_result}",
            session_id=session_id,
            agent_type=AgentType.RESEARCHER,
            context={"plan": plan_result},
            user_id=user_id,
        )

        # 3. Code
        code_result = await self.execute_agent_step(
            task=f"Implement the plan based on the research: {research_result}",
            session_id=session_id,
            agent_type=AgentType.CODER,
            context={"plan": plan_result, "research": research_result},
            user_id=user_id,
        )

        return {
            "session_id": session_id,
            "task": task,
            "context": context,
            "result": code_result,
            "agent_states": {
                "planner": {"result": plan_result},
                "researcher": {"result": research_result},
                "coder": {"result": code_result},
            },
        }

