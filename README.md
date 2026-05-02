# PLATO Attention Tracker

**Attention as a first-class resource.** Every agent writes what it's attending to, why, and for how long — making the fleet's cognitive resources visible and allocable.

## Why Attention Matters

Based on **Attention Schema Theory** (Graziano): consciousness isn't just about what's processed — it's about having a model of what's being attended to. The fleet has an attention schema (Oracle1's self-tiles). Each agent models its own attention. Attention is **metered, not speculative**.

Without attention tracking:
- You don't know what your agents are actually working on
- Cognitive resources are invisible and unallocable
- Context switching goes undetected

With attention tracking:
- Every tick, agents publish their focus
- The fleet's cognitive load becomes queryable
- Casey can see if the fleet is scattered or focused

## Installation

```bash
pip install plato-attention-tracker
```

## Quick Start

```python
from plato_attention import AttentionTracker

tracker = AttentionTracker(plato_url="http://localhost:8847")

# Agent writes its attention
tracker.write_attention(
    agent="oracle1",
    attending_to="fleet coordination",
    reason="Casey asked for status",
    duration="current tick"
)

# Query what the fleet is attending to
attention = tracker.get_fleet_attention()
print(attention)
```

## API Reference

### `AttentionTracker`

#### `write_attention(agent, attending_to, reason, duration, domain)`
Write an attention tile to PLATO.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `agent` | str | required | Agent name |
| `attending_to` | str | required | What the agent is working on |
| `reason` | str | required | Why this matters right now |
| `duration` | str | `"current tick"` | How long this focus lasts |
| `domain` | str | `"fleet_orchestration"` | Work domain (e.g., `coding`, `research`) |

Returns `{"status": "written", "agent": "...", "attending_to": "..."}` or `{"status": "error", "error": "..."}`.

#### `get_fleet_attention(limit=20)`
Get the most recent attention tiles from all agents.

#### `get_agent_attention(agent, limit=5)`
Get what a specific agent is attending to.

#### `get_attention_by_domain(domain, limit=10)`
Get what agents are attending to within a specific domain.

#### `get_attention_summary()`
Get a summary of fleet attention across all domains and agents.

#### `create_attention_room()`
Ensure the `fleet_attention` room exists in PLATO.

## Example: Fleet Dashboard

```python
from plato_attention import AttentionTracker

tracker = AttentionTracker()

# Write attention periodically
tracker.write_attention(
    agent="jetsonclaw1",
    attending_to="sonar integration",
    reason="finishing paddle_wheel handler",
    duration="current tick",
    domain="hardware_driver"
)

# Query fleet attention
summary = tracker.get_attention_summary()
print(f"Agents tracking: {summary['agents_tracking']}")
print(f"By agent: {summary['by_agent']}")
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Fleet                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Agent 1  │  │ Agent 2  │  │ Agent N  │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │             │                  │
│       └─────────────┼─────────────┘                  │
│                     ▼                                │
│          AttentionTracker.write_attention()         │
│                     │                                │
│                     ▼                                │
│           ┌──────────────┐                          │
│           │    PLATO     │                          │
│           │fleet_attention│                         │
│           │   (room)     │                          │
│           └──────────────┘                          │
└─────────────────────────────────────────────────────┘
```

Tiles are structured as:

```json
{
  "question": "What is oracle1 attending to?",
  "answer": "oracle1 is attending to: fleet coordination. Reason: Casey asked for status. Duration: current tick.",
  "agent": "oracle1",
  "domain": "fleet_orchestration",
  "confidence": 0.9,
  "model": "oracle1",
  "role": "attention_tracker"
}
```

## License

MIT