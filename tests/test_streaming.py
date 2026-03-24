"""Tests for the SSE streaming boardroom endpoint and on_event callback."""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aegis_gov.api import app
from aegis_gov.council.boardroom import Boardroom, BoardroomConfig
from aegis_gov.council.schemas import BoardroomSession

MOCK_RESPONSE_HIGH = (
    "Mock LLM response\n"
    "VOTE_TALLY: approve=3, conditional=1, reject=0, abstain=0\n"
    "CONFIDENCE: 0.85"
)
MOCK_RESPONSE_MED = (
    "Mock response\n"
    "VOTE_TALLY: approve=2, conditional=0, reject=0, abstain=0\n"
    "CONFIDENCE: 0.9"
)
MOCK_RESPONSE_LOW = (
    "Mock response\n"
    "VOTE_TALLY: approve=1, conditional=0, reject=0, abstain=0\n"
    "CONFIDENCE: 0.7"
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit test: on_event callback in Boardroom.convene
# ---------------------------------------------------------------------------

class TestBoardroomCallback:
    """Test that Boardroom.convene calls on_event at each phase."""

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_HIGH)
    def test_on_event_receives_phase_events(self, mock_llm):
        """on_event should be called with phase_start and phase_complete for each phase."""
        events = []

        config = BoardroomConfig(api_key="test-key")
        boardroom = Boardroom(config=config)
        boardroom.convene(
            topic="Test topic",
            category="TACTICAL",
            on_event=lambda e: events.append(e),
        )

        phase_starts = [e for e in events if e["type"] == "phase_start"]
        phase_completes = [e for e in events if e["type"] == "phase_complete"]

        # 6 phases: opening, executive_council, advisory, critical_review, debate, synthesis
        assert len(phase_starts) == 6
        assert len(phase_completes) == 6

        # Verify phase names
        start_phases = [e["phase"] for e in phase_starts]
        assert "opening" in start_phases
        assert "executive_council" in start_phases
        assert "advisory" in start_phases
        assert "critical_review" in start_phases
        assert "debate" in start_phases
        assert "synthesis" in start_phases

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_MED)
    def test_on_event_receives_agent_responses(self, mock_llm):
        """on_event should emit agent_response for each agent that responds."""
        events = []

        config = BoardroomConfig(api_key="test-key")
        boardroom = Boardroom(config=config)
        boardroom.convene(
            topic="Test topic",
            category="TACTICAL",
            on_event=lambda e: events.append(e),
        )

        agent_responses = [e for e in events if e["type"] == "agent_response"]
        assert len(agent_responses) > 0

        # Each agent_response should have agent name and content
        for resp in agent_responses:
            assert "agent" in resp
            assert "content" in resp
            assert "phase" in resp

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_LOW)
    def test_convene_still_returns_session_with_callback(self, mock_llm):
        """convene should return a valid BoardroomSession even with on_event set."""
        config = BoardroomConfig(api_key="test-key")
        boardroom = Boardroom(config=config)
        session = boardroom.convene(
            topic="Test topic",
            category="TACTICAL",
            on_event=lambda e: None,
        )

        assert isinstance(session, BoardroomSession)
        assert session.topic == "Test topic"
        assert session.synthesis != ""

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_LOW)
    def test_convene_works_without_callback(self, mock_llm):
        """convene should work identically when on_event is None (backward compat)."""
        config = BoardroomConfig(api_key="test-key")
        boardroom = Boardroom(config=config)
        session = boardroom.convene(
            topic="Test topic",
            category="TACTICAL",
        )

        assert isinstance(session, BoardroomSession)
        assert session.topic == "Test topic"

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_LOW)
    def test_no_critical_review_when_disabled(self, mock_llm):
        """When require_red_team=False, critical_review phase should be skipped."""
        events = []

        config = BoardroomConfig(api_key="test-key", require_red_team=False)
        boardroom = Boardroom(config=config)
        boardroom.convene(
            topic="Test topic",
            category="TACTICAL",
            on_event=lambda e: events.append(e),
        )

        phase_starts = [e for e in events if e["type"] == "phase_start"]
        start_phases = [e["phase"] for e in phase_starts]
        assert "critical_review" not in start_phases
        # 5 phases without critical review
        assert len(phase_starts) == 5


# ---------------------------------------------------------------------------
# Integration test: SSE endpoint
# ---------------------------------------------------------------------------

class TestStreamEndpoint:
    """Test the /api/v1/boardroom/stream SSE endpoint."""

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_HIGH)
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_stream_returns_sse_content_type(self, mock_llm, client):
        """Streaming endpoint should return text/event-stream content type."""
        response = client.post(
            "/api/v1/boardroom/stream",
            json={"topic": "Test topic", "category": "TACTICAL"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_HIGH)
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_stream_emits_complete_event(self, mock_llm, client):
        """Stream should end with a 'complete' event containing the session."""
        response = client.post(
            "/api/v1/boardroom/stream",
            json={"topic": "Test topic", "category": "TACTICAL"},
        )
        body = response.text

        # Parse SSE events
        events = _parse_sse(body)

        # Must have at least one complete event
        complete_events = [e for e in events if e["event"] == "complete"]
        assert len(complete_events) == 1

        # Complete event should have session data
        data = complete_events[0]["data"]
        assert "session_id" in data
        assert data["topic"] == "Test topic"
        assert "synthesis" in data

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_MED)
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_stream_emits_phase_events(self, mock_llm, client):
        """Stream should emit phase_start and phase_complete events."""
        response = client.post(
            "/api/v1/boardroom/stream",
            json={"topic": "Test topic", "category": "TACTICAL"},
        )
        events = _parse_sse(response.text)

        phase_starts = [e for e in events if e["event"] == "phase_start"]
        phase_completes = [e for e in events if e["event"] == "phase_complete"]

        assert len(phase_starts) >= 5  # At least 5 phases (6 with red team)
        assert len(phase_completes) >= 5

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_stream_requires_api_key_env(self, client):
        """Should return 400 when no LLM API key is set."""
        # Clear both keys
        with patch.dict(
            "os.environ",
            {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""},
            clear=False,
        ):
            response = client.post(
                "/api/v1/boardroom/stream",
                json={"topic": "Test topic"},
            )
            assert response.status_code == 400

    def test_stream_rejects_empty_topic(self, client):
        """Should return 422 when topic is empty."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            response = client.post(
                "/api/v1/boardroom/stream",
                json={"topic": "", "category": "TACTICAL"},
            )
            assert response.status_code == 422

    @patch.object(Boardroom, "_call_llm", return_value=MOCK_RESPONSE_LOW)
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_stream_emits_agent_response_events(self, mock_llm, client):
        """Stream should include agent_response events with agent names."""
        response = client.post(
            "/api/v1/boardroom/stream",
            json={"topic": "Test topic", "category": "TACTICAL"},
        )
        events = _parse_sse(response.text)

        agent_responses = [e for e in events if e["event"] == "agent_response"]
        assert len(agent_responses) > 0

        for evt in agent_responses:
            assert "agent" in evt["data"]
            assert "content" in evt["data"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sse(body: str) -> list[dict]:
    """Parse SSE text into a list of {event, data} dicts."""
    events = []
    current_event = None
    current_data = None

    for line in body.split("\n"):
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data: "):
            current_data = line[6:].strip()
        elif line == "" and current_event is not None and current_data is not None:
            try:
                data = json.loads(current_data)
            except json.JSONDecodeError:
                data = current_data
            events.append({"event": current_event, "data": data})
            current_event = None
            current_data = None

    return events
