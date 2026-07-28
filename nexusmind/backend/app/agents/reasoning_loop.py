"""Reasoning Loop for autonomous tool-based agent execution.

This module implements the core agent reasoning loop:

    Agent
      ↓
    Think
      ↓
    Need tool?
      ↓
    YES → Tool Registry → Execute → Observe → Continue reasoning
      ↓
    NO
      ↓
    Return result

Features:
- Multi-tool execution chains
- Observation-based reasoning continuation
- LLM-driven tool selection
- Memory integration for context
- Graceful error recovery
- Execution tracing
"""

import asyncio
import json
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from app.agents.execution_engine import (
    AgentToolInvoker,
    ToolCall,
    ToolCallStatus,
    ToolExecutionContext,
    ToolResult,
    ToolType,
    get_tool_invoker,
)
from app.agents.base import AgentState
from app.agents.types import AgentType, get_agent_capabilities
from app.memory.chromadb import ChromaMemoryService, get_memory_service


class LoopState(str, Enum):
    """State of the reasoning loop."""
    
    THINKING = "thinking"
    SELECTING_TOOL = "selecting_tool"
    EXECUTING_TOOL = "executing_tool"
    OBSERVING = "observing"
    REASONING = "reasoning"
    COMPLETE = "complete"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class ReasoningStep:
    """A single step in the reasoning loop."""
    
    step_id: str
    state: LoopState
    thought: str
    tool_calls: list[ToolResult] = field(default_factory=list)
    continuation_reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReasoningTrace:
    """Complete trace of agent reasoning."""
    
    trace_id: str
    agent_type: str
    session_id: str
    task: str
    steps: list[ReasoningStep] = field(default_factory=list)
    final_result: Any = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the trace."""
        self.steps.append(step)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "agent_type": self.agent_type,
            "session_id": self.session_id,
            "task": self.task,
            "steps": [
                {
                    "step_id": s.step_id,
                    "state": s.state.value,
                    "thought": s.thought,
                    "tool_results": [r.to_dict() for r in s.tool_calls],
                    "continuation_reason": s.continuation_reason,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in self.steps
            ],
            "final_result": self.final_result,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ToolSelector:
    """LLM-driven tool selection from available tools."""
    
    def __init__(
        self,
        tool_invoker: AgentToolInvoker | None = None,
        llm_service: Any = None,
    ):
        self._tool_invoker = tool_invoker or get_tool_invoker()
        self._llm_service = llm_service
    
    async def select_tools(
        self,
        task: str,
        context: dict[str, Any],
        agent_type: AgentType,
        step_number: int,
        previous_results: list[ToolResult],
    ) -> list[dict[str, Any]]:
        """Select tools to use based on task and context.
        
        Returns list of tool call specifications:
        [
            {"tool_name": "web_search", "arguments": {"query": "..."}},
            {"tool_name": "browser", "arguments": {"action": "open", "url": "..."}},
        ]
        """
        # Get agent capabilities
        capabilities = get_agent_capabilities(agent_type)
        available_tools = self._tool_invoker.list_available_tools()
        
        # Build tool selection prompt
        tool_descriptions = "\n".join([
            f"- {t['name']}: {t.get('description', 'No description')}"
            for t in available_tools
        ])
        
        previous_observations = ""
        if previous_results:
            prev_list = []
            for i, r in enumerate(previous_results[-5:], 1):
                prev_list.append(f"{i}. {r.tool_name}: {r.status.value}")
                if r.result:
                    result_str = str(r.result)[:200]
                    prev_list.append(f"   Result: {result_str}")
                if r.error:
                    prev_list.append(f"   Error: {r.error[:200]}")
            previous_observations = "\nPrevious observations:\n" + "\n".join(prev_list)
        
        system_prompt = f"""You are a tool selection assistant. Given a task and available tools, select the best tools to use.

Available tools:
{tool_descriptions}

Your task is to decide which tools to call next. Return a JSON array of tool calls.
Each call should have:
- tool_name: exact name of the tool
- arguments: dict of arguments for the tool
- reasoning: why you chose this tool

Only select tools that are needed. If no tool is needed, return an empty array [].

IMPORTANT: Return ONLY a JSON array, no other text."""
        
        user_prompt = f"""Task: {task}

Agent type: {agent_type.value}
Step number: {step_number}
{previous_observations}

Context: {json.dumps(context, indent=2)[:1000]}

Which tools should I use next? Return JSON array:"""
        
        # Try to use LLM for tool selection
        if self._llm_service:
            try:
                response = await self._llm_service.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    provider="ollama",
                )
                
                content = response.get("content", "")
                
                # Parse JSON from response
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                if json_start >= 0 and json_end > json_start:
                    tool_calls = json.loads(content[json_start:json_end])
                    # Filter out 'reasoning' field, keep only tool_name and arguments
                    return [
                        {"tool_name": c["tool_name"], "arguments": c.get("arguments", {})}
                        for c in tool_calls
                        if "tool_name" in c
                    ]
            except Exception:
                pass
        
        # Fallback: return empty (no tools)
        return []
    
    async def should_continue(
        self,
        task: str,
        context: dict[str, Any],
        results: list[ToolResult],
        step_number: int,
    ) -> tuple[bool, str]:
        """Determine if the reasoning loop should continue.
        
        Returns:
            (should_continue, reason)
        """
        # Check if all tools succeeded
        if results and all(r.is_success() for r in results):
            # Check if we have enough information
            if self._llm_service:
                try:
                    observations = "\n".join([
                        f"- {r.tool_name}: {r.result if r.result else r.error}"
                        for r in results
                    ])
                    
                    response = await self._llm_service.chat(
                        messages=[
                            {
                                "role": "system",
                                "content": """You are a reasoning assistant. Based on the task and observations, determine if more tools are needed.
                                
Respond with ONLY one word:
- "YES" if more tools are needed to complete the task
- "NO" if the task is complete
- "DONE" if the task is fully completed"""
                            },
                            {
                                "role": "user",
                                "content": f"""Task: {task}
Observations:
{observations}

Should I continue? (YES/NO/DONE):"""
                            },
                        ],
                        provider="ollama",
                    )
                    
                    answer = response.get("content", "").strip().upper()
                    if answer == "NO":
                        return True, "More tools may be needed"
                    elif answer == "DONE":
                        return False, "Task appears complete"
                except Exception:
                    pass
        
        return True, "Continue reasoning"


class ReasoningLoop:
    """Main reasoning loop for autonomous tool execution.
    
    This loop implements:
    1. Think - Analyze task and context
    2. Select - Choose appropriate tools
    3. Execute - Run tools through invoker
    4. Observe - Collect results
    5. Reason - Determine if more tools needed
    6. Continue or Finalize
    """
    
    def __init__(
        self,
        max_iterations: int = 20,
        max_tools_per_step: int = 5,
        tool_timeout: float = 30.0,
        tool_invoker: AgentToolInvoker | None = None,
        memory_service: ChromaMemoryService | None = None,
    ):
        self.max_iterations = max_iterations
        self.max_tools_per_step = max_tools_per_step
        self.tool_timeout = tool_timeout
        self._invoker = tool_invoker or get_tool_invoker()
        self._memory = memory_service or get_memory_service()
        self._tool_selector = ToolSelector(self._invoker)
    
    async def execute(
        self,
        task: str,
        agent_type: AgentType,
        session_id: str,
        context: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> ReasoningTrace:
        """Execute the reasoning loop for a task.
        
        Args:
            task: The task description
            agent_type: Type of agent executing
            session_id: Session ID for memory context
            context: Additional context for execution
            execution_id: Optional execution ID for tracing
            
        Returns:
            ReasoningTrace with complete execution trace
        """
        execution_id = execution_id or str(uuid.uuid4())
        trace = ReasoningTrace(
            trace_id=execution_id,
            agent_type=agent_type.value,
            session_id=session_id,
            task=task,
        )
        
        # Build execution context
        exec_context = ToolExecutionContext(
            agent_type=agent_type.value,
            session_id=session_id,
            execution_id=execution_id,
            max_total_tools=self.max_iterations * self.max_tools_per_step,
            metadata=context or {},
        )
        
        all_results: list[ToolResult] = []
        iteration = 0
        
        try:
            while iteration < self.max_iterations:
                iteration += 1
                step_id = f"step_{iteration}"
                
                # STEP 1: THINKING - Analyze the current state
                thought = f"Analyzing task at iteration {iteration}"
                current_state = LoopState.THINKING
                
                step = ReasoningStep(
                    step_id=step_id,
                    state=current_state,
                    thought=thought,
                )
                
                # STEP 2: SELECT TOOL - Choose tools based on task
                current_state = LoopState.SELECTING_TOOL
                step.state = current_state
                
                tool_specs = await self._tool_selector.select_tools(
                    task=task,
                    context=exec_context.metadata,
                    agent_type=agent_type,
                    step_number=iteration,
                    previous_results=all_results,
                )
                
                # If no tools selected, we're done
                if not tool_specs:
                    step.continuation_reason = "No tools selected - task complete"
                    current_state = LoopState.COMPLETE
                    step.state = current_state
                    trace.add_step(step)
                    break
                
                # STEP 3: EXECUTE TOOLS - Run selected tools
                current_state = LoopState.EXECUTING_TOOL
                step.state = current_state
                
                for spec in tool_specs[:self.max_tools_per_step]:
                    tool_name = spec["tool_name"]
                    arguments = spec.get("arguments", {})
                    
                    # Determine tool type
                    tool_type = self._get_tool_type(tool_name)
                    
                    # Create tool call
                    tool_call = ToolCall.create(
                        tool_name=tool_name,
                        tool_type=tool_type,
                        arguments=arguments,
                        timeout=self.tool_timeout,
                    )
                    
                    # Execute tool
                    result = await self._invoker.invoke(tool_call, exec_context)
                    step.tool_calls.append(result)
                    all_results.append(result)
                
                # STEP 4: OBSERVE - Record observations
                current_state = LoopState.OBSERVING
                step.state = current_state
                
                # Store results in memory
                await self._store_observations(session_id, agent_type, step.tool_calls)
                
                # STEP 5: REASON - Determine if more tools needed
                current_state = LoopState.REASONING
                step.state = current_state
                
                should_continue, reason = await self._tool_selector.should_continue(
                    task=task,
                    context=exec_context.metadata,
                    results=all_results,
                    step_number=iteration,
                )
                
                step.continuation_reason = reason
                
                if not should_continue:
                    current_state = LoopState.COMPLETE
                    step.state = current_state
                    trace.add_step(step)
                    break
                
                # Update context with latest results
                exec_context.metadata["last_results"] = [
                    r.to_dict() for r in all_results[-5:]
                ]
                
                trace.add_step(step)
            
            # Check for max iterations
            if iteration >= self.max_iterations:
                step = ReasoningStep(
                    step_id=f"step_{iteration}",
                    state=LoopState.MAX_ITERATIONS,
                    thought=f"Reached maximum iterations ({self.max_iterations})",
                    continuation_reason="Max iterations reached",
                )
                trace.add_step(step)
            
            # Compile final result
            trace.final_result = self._compile_results(all_results)
            trace.completed_at = datetime.utcnow()
            
            # Store final result in memory
            await self._memory.store_output(
                session_id=session_id,
                output_type="reasoning_result",
                content=json.dumps(trace.to_dict()),
            )
            
        except Exception as e:
            trace.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            trace.completed_at = datetime.utcnow()
        
        return trace
    
    def _get_tool_type(self, tool_name: str) -> ToolType:
        """Determine the type of a tool."""
        # Check native tools
        if self._invoker._tool_registry.has_tool(tool_name):
            return ToolType.NATIVE
        
        # Check function tools
        if self._invoker._tool_registry.get_function(tool_name):
            return ToolType.FUNCTION
        
        # Default to MCP
        return ToolType.MCP
    
    async def _store_observations(
        self,
        session_id: str,
        agent_type: AgentType,
        results: list[ToolResult],
    ) -> None:
        """Store tool observations in memory."""
        for result in results:
            await self._memory.store_conversation(
                session_id=session_id,
                role="tool",
                content=json.dumps(result.to_dict()),
                agent_type=agent_type.value,
                metadata={
                    "tool_name": result.tool_name,
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                },
            )
    
    def _compile_results(self, results: list[ToolResult]) -> dict[str, Any]:
        """Compile all results into a final response."""
        successful = [r for r in results if r.is_success()]
        failed = [r for r in results if not r.is_success()]
        
        return {
            "total_calls": len(results),
            "successful_calls": len(successful),
            "failed_calls": len(failed),
            "total_execution_time": sum(r.execution_time for r in results),
            "results": [r.to_dict() for r in results],
            "summary": {
                "tools_used": list(set(r.tool_name for r in results)),
                "success_rate": len(successful) / len(results) if results else 0,
            },
        }


# Global loop instance
_reasoning_loop: ReasoningLoop | None = None


def get_reasoning_loop() -> ReasoningLoop:
    """Get the global reasoning loop instance."""
    global _reasoning_loop
    if _reasoning_loop is None:
        _reasoning_loop = ReasoningLoop()
    return _reasoning_loop
