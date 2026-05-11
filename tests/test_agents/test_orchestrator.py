"""Tests for TaskOrchestrator."""

import pytest
from src.agents.task_orchestrator import TaskOrchestrator, CircuitBreaker
from src.agents.protocols import AgentTask, AgentMessageType


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.allow_request()

    def test_opens_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert not cb.allow_request()

    def test_recovers_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=-1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request()  # Recovery timeout already passed
        assert cb.state == "half_open"

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == "closed"


class TestTaskOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return TaskOrchestrator()

    def test_register_agent(self, orchestrator):
        def handler(payload):
            return {"result": "ok"}
        orchestrator.register_agent("test_agent", handler)
        assert "test_agent" in orchestrator._agents

    def test_dispatch_success(self, orchestrator):
        def handler(payload):
            return {"value": payload.get("x", 0) * 2}
        orchestrator.register_agent("doubler", handler)
        task = AgentTask(
            task_id="t1", agent_id="doubler",
            message_type=AgentMessageType.ASSESSMENT_REQUEST,
            payload={"x": 5}
        )
        result = orchestrator.dispatch(task)
        assert result["value"] == 10

    def test_dispatch_unknown_agent(self, orchestrator):
        task = AgentTask(
            task_id="t1", agent_id="nonexistent",
            message_type=AgentMessageType.ASSESSMENT_REQUEST,
        )
        with pytest.raises(ValueError):
            orchestrator.dispatch(task)

    def test_degradation_fallback(self, orchestrator):
        import time
        def fallback_handler(payload):
            return {"fallback": True}
        def main_handler(payload):
            return {"main": True}
        orchestrator.register_agent("fallback", fallback_handler)
        orchestrator.register_agent("main", main_handler, fallback_id="fallback")
        # Force circuit open and set last failure time to now (prevent immediate recovery)
        cb = orchestrator._circuit_breakers["main"]
        cb._state = "open"
        cb._last_failure_time = time.time()
        task = AgentTask(
            task_id="t1", agent_id="main",
            message_type=AgentMessageType.ASSESSMENT_REQUEST,
        )
        result = orchestrator.dispatch(task)
        assert result["fallback"] is True

    def test_agent_status(self, orchestrator):
        orchestrator.register_agent("a1", lambda p: {})
        status = orchestrator.get_agent_status("a1")
        assert status["registered"]
        assert status["circuit_state"] == "closed"

    def test_deadlock_detection_no_cycles(self, orchestrator):
        orchestrator.register_agent("a1", lambda p: {}, fallback_id="a2")
        orchestrator.register_agent("a2", lambda p: {}, fallback_id="a3")
        orchestrator.register_agent("a3", lambda p: {})
        cycles = orchestrator.detect_deadlock()
        assert len(cycles) == 0

    def test_deadlock_detection_with_cycle(self, orchestrator):
        orchestrator.register_agent("a1", lambda p: {}, fallback_id="a2")
        orchestrator.register_agent("a2", lambda p: {}, fallback_id="a1")
        cycles = orchestrator.detect_deadlock()
        assert len(cycles) > 0
