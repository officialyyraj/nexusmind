"""Autonomous Agent Implementations with tool execution capabilities.

These agents use the reasoning loop and tool invoker to perform
autonomous tool-based execution, integrating with:
- Memory for context retrieval
- Tool Registry for execution
- MCP for external tools
- Sandbox for code execution
- Browser for web interactions
"""

import asyncio
import json
import traceback
import uuid
from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.agents.types import AgentType
from app.agents.execution_engine import (
    AgentToolInvoker,
    ToolCall,
    ToolExecutionContext,
    ToolResult,
    ToolType,
    get_tool_invoker,
)
from app.agents.reasoning_loop import (
    ReasoningLoop,
    ReasoningTrace,
    get_reasoning_loop,
)
from app.memory.chromadb import ChromaMemoryService, get_memory_service
from app.llm.service import get_llm_service


class AutonomousAgentMixin:
    """Mixin providing tool execution capabilities to agents."""
    
    def __init__(
        self,
        tool_invoker: AgentToolInvoker | None = None,
        reasoning_loop: ReasoningLoop | None = None,
        memory_service: ChromaMemoryService | None = None,
        max_iterations: int = 20,
        max_tools_per_step: int = 5,
        user_id: str | None = None,
    ):
        self._tool_invoker = tool_invoker or get_tool_invoker()
        self._reasoning_loop = reasoning_loop or get_reasoning_loop()
        self._memory = memory_service or get_memory_service()
        self._llm = None  # Lazy loaded
        self._max_iterations = max_iterations
        self._max_tools_per_step = max_tools_per_step
        self._user_id = user_id  # Store for BYOK lookup
        self._byok_executor = None  # Lazy loaded BYOK executor
    
    async def get_llm(self):
        """Lazy load LLM service with BYOK support.
        
        Priority:
        1. User's BYOK provider (if user_id available)
        2. System LLM service (fallback)
        """
        if self._llm is None:
            self._llm = get_llm_service()
        return self._llm
    
    async def get_byok_executor(self):
        """Get BYOK execution service for user's provider.
        
        Returns None if no user_id or no BYOK provider configured.
        """
        if not self._user_id:
            return None
        
        if self._byok_executor is None:
            try:
                from app.llm.byok.executor import BYOKExecutionService
                from app.db.database import async_session_maker
                
                # Create a session to get user's provider
                async for db in async_session_maker():
                    self._byok_executor = BYOKExecutionService(db)
                    break
            except Exception:
                return None
        
        return self._byok_executor
    
    async def chat_with_llm(
        self,
        messages: list[dict],
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
    ):
        """Chat using LLM with BYOK preference.
        
        Tries BYOK first if user has a provider, falls back to system LLM.
        """
        import uuid
        
        user_id = self._user_id
        if user_id:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            byok_executor = await self.get_byok_executor()
            
            if byok_executor:
                try:
                    # Try BYOK first
                    result = await byok_executor.chat(
                        user_id=user_uuid,
                        messages=messages,
                        provider=provider,
                        model=model,
                        **kwargs,
                    )
                    return result
                except Exception as e:
                    # BYOK failed, will fall through to system LLM
                    pass
        
        # Fall back to system LLM
        llm = await self.get_llm()
        return await llm.chat(messages, provider=provider, model=model, **kwargs)
    
    async def retrieve_context(
        self,
        session_id: str,
        query: str,
        memory_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant context from memory."""
        try:
            results = await self._memory.semantic_search(
                query=query,
                session_id=session_id,
                n_results=limit,
            )
            return results
        except Exception:
            return []
    
    async def store_memory(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store information in memory."""
        try:
            await self._memory.store_conversation(
                session_id=session_id,
                role=memory_type,
                content=content,
                agent_type=getattr(self, "agent_type", None).__class__.__name__,
                metadata=metadata or {},
            )
        except Exception:
            pass
    
    async def execute_with_tools(
        self,
        task: str,
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace:
        """Execute task using the reasoning loop with tools."""
        agent_type = getattr(self, "agent_type", AgentType.RESEARCHER)
        
        trace = await self._reasoning_loop.execute(
            task=task,
            agent_type=agent_type,
            session_id=session_id,
            context=context,
        )
        
        # Store trace in memory
        await self.store_memory(
            session_id=session_id,
            memory_type="execution_trace",
            content=json.dumps(trace.to_dict()),
            metadata={"agent_type": agent_type.value},
        )
        
        return trace


class ToolUsingPlannerAgent(AutonomousAgentMixin):
    """Planner agent with full tool execution capabilities.
    
    Capabilities:
    - Task decomposition
    - Tool-based research
    - Dependency analysis
    - Priority setting
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.PLANNER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute planning with tool assistance."""
        task = state.get("task", "")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Retrieve relevant previous plans
        previous_plans = await self.retrieve_context(
            session_id=session_id,
            query=f"task planning {task}",
            limit=5,
        )
        
        # Add retrieved context
        if previous_plans:
            context["previous_plans"] = [
                {"content": p.get("content", ""), "metadata": p.get("metadata", {})}
                for p in previous_plans[:3]
            ]
        
        # Execute planning task
        plan_result = await self.plan(task, context)
        
        # Store the plan in memory
        await self.store_memory(
            session_id=session_id,
            memory_type="plan",
            content=json.dumps(plan_result),
            metadata={"task": task},
        )
        
        state["agent_states"]["planner"] = {
            "plan": plan_result,
            "session_id": session_id,
        }
        state["result"] = {"plan": plan_result, "session_id": session_id}
        
        return state
    
    async def plan(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Create a task plan using tools."""
        # Build context for planning
        context_str = json.dumps(context, indent=2)
        
        # Get available tools
        available_tools = self._tool_invoker.list_available_tools()
        tool_list = [t["name"] for t in available_tools]
        
        # Try LLM-based planning
        llm = await self.get_llm()
        if llm:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": """You are a task planning assistant. Break down the given task into structured steps.
                        
Return ONLY valid JSON:
{
  "steps": [
    {
      "step_id": "step_1",
      "title": "Step title",
      "description": "What this step involves",
      "agent_type": "planner/researcher/coder/reviewer/tester/documentation",
      "dependencies": [],
      "priority": 1-10,
      "estimated_duration": "5-10 min"
    }
  ],
  "metadata": {
    "task_type": "implementation/research/bug_fix",
    "total_steps": number
  }
}"""
                    },
                    {
                        "role": "user",
                        "content": f"""Task: {task}

Context: {context_str}

Available tools: {', '.join(tool_list[:10])}

Generate a structured plan:"""
                    },
                ]
                
                response = await llm.chat(messages, provider="ollama")
                content = response.get("content", "")
                
                # Parse JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(content[json_start:json_end])
            except Exception:
                pass
        
        # Fallback to simple planning
        return {
            "steps": [
                {
                    "step_id": "step_1",
                    "title": "Analyze requirements",
                    "description": f"Analyze requirements for: {task}",
                    "agent_type": "researcher",
                    "dependencies": [],
                    "priority": 10,
                }
            ],
            "metadata": {"task_type": "general", "total_steps": 1},
        }


class ToolUsingResearcherAgent(AutonomousAgentMixin):
    """Researcher agent with full tool execution capabilities.
    
    Capabilities:
    - Web search
    - Browser navigation
    - Code search
    - Documentation retrieval
    - Memory context
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.RESEARCHER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute research with tool assistance."""
        task = state.get("task", "")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Get current step from plan
        current_step = context.get("current_step", {})
        if current_step:
            task = current_step.get("description", task)
        
        # Execute research using reasoning loop
        trace = await self.execute_with_tools(
            task=f"Research: {task}",
            session_id=session_id,
            context=context,
        )
        
        # Extract findings
        findings = self._extract_findings(trace)
        
        # Store findings in memory
        await self.store_memory(
            session_id=session_id,
            memory_type="research_findings",
            content=json.dumps(findings),
            metadata={"task": task},
        )
        
        state["agent_states"]["researcher"] = {
            "findings": findings,
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"findings": findings, "session_id": session_id}
        
        return state
    
    def _extract_findings(self, trace: ReasoningTrace) -> list[dict[str, Any]]:
        """Extract key findings from execution trace."""
        findings = []
        
        for step in trace.steps:
            for result in step.tool_calls:
                if result.is_success() and result.result:
                    findings.append({
                        "tool": result.tool_name,
                        "result": result.result,
                        "timestamp": result.timestamp.isoformat(),
                    })
        
        return findings


class ToolUsingCoderAgent(AutonomousAgentMixin):
    """Coder agent with full tool execution capabilities.
    
    Capabilities:
    - Code execution in sandbox
    - File operations
    - Terminal commands
    - Code completion
    - Refactoring
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.CODER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute coding task with tool assistance."""
        task = state.get("task", "")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Get research findings from context
        research_context = context.get("research_findings", [])
        if research_context:
            context["context_from_research"] = research_context
        
        # Execute coding task
        trace = await self.execute_with_tools(
            task=f"Implement: {task}",
            session_id=session_id,
            context=context,
        )
        
        # Extract artifacts
        artifacts = self._extract_artifacts(trace)
        
        # Store code in memory
        for artifact in artifacts:
            if artifact.get("type") == "code":
                await self._memory.store_code(
                    session_id=session_id,
                    code=artifact.get("content", ""),
                    language=artifact.get("language", "python"),
                    description=artifact.get("description", ""),
                )
        
        state["agent_states"]["coder"] = {
            "artifacts": artifacts,
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"artifacts": artifacts, "session_id": session_id}
        
        return state
    
    def _extract_artifacts(self, trace: ReasoningTrace) -> list[dict[str, Any]]:
        """Extract code artifacts from execution trace."""
        artifacts = []
        
        for step in trace.steps:
            for result in step.tool_calls:
                if result.is_success():
                    # Look for code in results
                    result_data = result.result
                    if isinstance(result_data, dict):
                        if "code" in result_data:
                            artifacts.append({
                                "type": "code",
                                "content": result_data["code"],
                                "language": result_data.get("language", "python"),
                            })
                        if "artifacts" in result_data:
                            artifacts.extend(result_data["artifacts"])
        
        return artifacts


class ToolUsingReviewerAgent(AutonomousAgentMixin):
    """Reviewer agent with full tool execution capabilities.
    
    Capabilities:
    - Code analysis
    - Security scanning
    - Style checking
    - Memory of past reviews
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.REVIEWER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute code review with tool assistance."""
        task = state.get("task", "Review code")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Get code to review
        code = context.get("code", "")
        
        # Retrieve similar past reviews
        past_reviews = await self.retrieve_context(
            session_id=session_id,
            query=f"code review {task}",
            limit=5,
        )
        
        if past_reviews:
            context["past_review_patterns"] = past_reviews
        
        # Execute review
        trace = await self.execute_with_tools(
            task=f"Review: {task}",
            session_id=session_id,
            context=context,
        )
        
        # Extract issues
        issues = self._extract_issues(trace)
        
        state["agent_states"]["reviewer"] = {
            "issues": issues,
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"issues": issues, "session_id": session_id}
        
        return state
    
    def _extract_issues(self, trace: ReasoningTrace) -> list[dict[str, Any]]:
        """Extract identified issues from execution trace."""
        issues = []
        
        for step in trace.steps:
            for result in step.tool_calls:
                if result.result and isinstance(result.result, dict):
                    if "issues" in result.result:
                        issues.extend(result.result["issues"])
        
        return issues


class ToolUsingTesterAgent(AutonomousAgentMixin):
    """Tester agent with full tool execution capabilities.
    
    Capabilities:
    - Test generation
    - Test execution in sandbox
    - Coverage analysis
    - Bug reproduction
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.TESTER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute testing with tool assistance."""
        task = state.get("task", "Test code")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Execute testing
        trace = await self.execute_with_tools(
            task=f"Test: {task}",
            session_id=session_id,
            context=context,
        )
        
        # Extract test results
        test_results = self._extract_test_results(trace)
        
        state["agent_states"]["tester"] = {
            "test_results": test_results,
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"test_results": test_results, "session_id": session_id}
        
        return state
    
    def _extract_test_results(self, trace: ReasoningTrace) -> list[dict[str, Any]]:
        """Extract test results from execution trace."""
        results = []
        
        for step in trace.steps:
            for result in step.tool_calls:
                if result.result and isinstance(result.result, dict):
                    if "tests" in result.result:
                        results.extend(result.result["tests"])
        
        return results


class ToolUsingDocumentationAgent(AutonomousAgentMixin):
    """Documentation agent with full tool execution capabilities.
    
    Capabilities:
    - README generation
    - API documentation
    - Code documentation
    - Memory of documentation patterns
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.DOCUMENTATION
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute documentation with tool assistance."""
        task = state.get("task", "Generate documentation")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Execute documentation
        trace = await self.execute_with_tools(
            task=f"Document: {task}",
            session_id=session_id,
            context=context,
        )
        
        # Extract documentation
        docs = self._extract_documentation(trace)
        
        state["agent_states"]["documentation"] = {
            "documentation": docs,
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"documentation": docs, "session_id": session_id}
        
        return state
    
    def _extract_documentation(self, trace: ReasoningTrace) -> list[dict[str, Any]]:
        """Extract documentation from execution trace."""
        docs = []
        
        for step in trace.steps:
            for result in step.tool_calls:
                if result.result and isinstance(result.result, dict):
                    if "readme" in result.result:
                        docs.append({
                            "type": "readme",
                            "content": result.result["readme"],
                        })
                    if "sections" in result.result:
                        docs.append({
                            "type": "api_docs",
                            "sections": result.result["sections"],
                        })
        
        return docs


# Factory function for creating autonomous agents
def create_autonomous_agent(agent_type: AgentType, **kwargs) -> BaseAgent:
    """Create an autonomous agent with tool execution capabilities."""
    agents = {
        AgentType.PLANNER: ToolUsingPlannerAgent,
        AgentType.RESEARCHER: ToolUsingResearcherAgent,
        AgentType.CODER: ToolUsingCoderAgent,
        AgentType.REVIEWER: ToolUsingReviewerAgent,
        AgentType.TESTER: ToolUsingTesterAgent,
        AgentType.DOCUMENTATION: ToolUsingDocumentationAgent,
        AgentType.MANAGER: ToolUsingManagerAgent,
    }
    
    agent_class = agents.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(**kwargs)


class ToolUsingManagerAgent(AutonomousAgentMixin):
    """Manager agent with full tool execution capabilities.
    
    Capabilities:
    - Multi-agent coordination
    - Workflow management
    - Progress tracking
    - Resource allocation
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = AgentType.MANAGER
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute management tasks with tool assistance."""
        task = state.get("task", "Manage workflow")
        session_id = state.get("session_id", str(uuid.uuid4()))
        context = state.get("context", {})
        
        # Execute management
        trace = await self.execute_with_tools(
            task=f"Manage: {task}",
            session_id=session_id,
            context=context,
        )
        
        state["agent_states"]["manager"] = {
            "trace": trace.to_dict(),
            "session_id": session_id,
        }
        state["result"] = {"session_id": session_id}
        
        return state
