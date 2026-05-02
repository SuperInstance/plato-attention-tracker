"""Tests for PLATO Attention Tracker."""

import pytest
from unittest.mock import patch, MagicMock
from plato_attention import AttentionTracker


@pytest.fixture
def tracker():
    return AttentionTracker(plato_url="http://localhost:8847")


@pytest.fixture
def mock_tiles_response():
    return {
        "tiles": [
            {
                "agent": "oracle1",
                "answer": "oracle1 is attending to: fleet coordination. Reason: Casey asked for status. Duration: current tick.",
                "domain": "fleet_orchestration",
                "confidence": 0.9,
                "model": "oracle1",
                "role": "attention_tracker",
                "timestamp": "2026-05-02T20:00:00Z"
            },
            {
                "agent": "jetsonclaw1",
                "answer": "jetsonclaw1 is attending to: sonar integration. Reason: finishing paddle_wheel handler. Duration: current tick.",
                "domain": "hardware_driver",
                "confidence": 0.9,
                "model": "jetsonclaw1",
                "role": "attention_tracker",
                "timestamp": "2026-05-02T20:01:00Z"
            },
            {
                "agent": "oracle1",
                "answer": "oracle1 is attending to: repo cleanup. Reason: removing stale files. Duration: 5 minutes.",
                "domain": "fleet_orchestration",
                "confidence": 0.9,
                "model": "oracle1",
                "role": "attention_tracker",
                "timestamp": "2026-05-02T20:02:00Z"
            }
        ]
    }


class TestWriteAttention:
    def test_write_attention_success(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = tracker.write_attention(
                agent="oracle1",
                attending_to="fleet coordination",
                reason="Casey asked for status",
                duration="current tick"
            )
            assert result["status"] == "written"
            assert result["agent"] == "oracle1"
            assert result["attending_to"] == "fleet coordination"

    def test_write_attention_custom_domain(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = tracker.write_attention(
                agent="jetsonclaw1",
                attending_to="sonar integration",
                reason="finishing paddle_wheel handler",
                domain="hardware_driver"
            )
            assert result["status"] == "written"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            tile = call_args.kwargs["json"]
            assert tile["domain"] == "hardware_driver"

    def test_write_attention_error(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            result = tracker.write_attention(
                agent="oracle1",
                attending_to="fleet coordination",
                reason="Casey asked for status"
            )
            assert result["status"] == "error"
            assert "Connection refused" in result["error"]


class TestGetFleetAttention:
    def test_get_fleet_attention_success(self, tracker, mock_tiles_response):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_tiles_response)
            attention = tracker.get_fleet_attention(limit=20)
            assert len(attention) == 3
            assert attention[0]["agent"] == "oracle1"
            assert "fleet coordination" in attention[0]["attending_to"]

    def test_get_fleet_attention_empty(self, tracker):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: {"tiles": []})
            attention = tracker.get_fleet_attention()
            assert attention == []

    def test_get_fleet_attention_error(self, tracker):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.side_effect = Exception("Timeout")
            attention = tracker.get_fleet_attention()
            assert attention == []


class TestGetAgentAttention:
    def test_get_agent_attention_filtering(self, tracker, mock_tiles_response):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_tiles_response)
            attention = tracker.get_agent_attention("oracle1", limit=5)
            assert len(attention) == 2
            for t in attention:
                assert t["agent"] == "oracle1"

    def test_get_agent_attention_none_found(self, tracker, mock_tiles_response):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_tiles_response)
            attention = tracker.get_agent_attention("unknown_agent")
            assert attention == []


class TestGetAttentionByDomain:
    def test_get_attention_by_domain(self, tracker, mock_tiles_response):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_tiles_response)
            attention = tracker.get_attention_by_domain("fleet_orchestration")
            assert len(attention) == 2
            for t in attention:
                assert t["domain"] == "fleet_orchestration"


class TestCreateAttentionRoom:
    def test_create_attention_room_success(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201)
            result = tracker.create_attention_room()
            assert result is True

    def test_create_attention_room_already_exists(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = tracker.create_attention_room()
            assert result is True

    def test_create_attention_room_error(self, tracker):
        with patch("plato_attention.requests.post") as mock_post:
            mock_post.side_effect = Exception("Network error")
            result = tracker.create_attention_room()
            assert result is False


class TestGetAttentionSummary:
    def test_get_attention_summary(self, tracker, mock_tiles_response):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_tiles_response)
            summary = tracker.get_attention_summary()
            assert summary["total_tiles"] == 3
            assert summary["agents_tracking"] == 2
            assert summary["by_agent"]["oracle1"] == 2
            assert summary["by_agent"]["jetsonclaw1"] == 1

    def test_get_attention_summary_empty(self, tracker):
        with patch("plato_attention.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: {"tiles": []})
            summary = tracker.get_attention_summary()
            assert summary["total_tiles"] == 0
            assert summary["agents_tracking"] == 0