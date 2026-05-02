"""
PLATO Attention Tracker — attention as a first-class resource

Every agent writes what it's attending to, why, and for how long.
This makes the fleet's cognitive resources visible and allocable.

Based on Attention Schema Theory (Graziano):
- The fleet has an attention schema (Oracle1's self-tiles)
- Agents model their own attention
- Attention is metered, not speculative

Usage:
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
    print(attention)  # [{"agent": "oracle1", "attending_to": "...", "when": "..."}]
"""

import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

class AttentionTracker:
    def __init__(self, plato_url: str = "http://localhost:8847"):
        self.plato_url = plato_url.rstrip("/")
        self.room = "fleet_attention"
    
    def write_attention(
        self,
        agent: str,
        attending_to: str,
        reason: str,
        duration: str = "current tick",
        domain: str = "fleet_orchestration"
    ) -> Dict[str, Any]:
        """Write an attention tile to PLATO."""
        tile = {
            "question": f"What is {agent} attending to?",
            "answer": f"{agent} is attending to: {attending_to}. Reason: {reason}. Duration: {duration}.",
            "agent": agent,
            "domain": domain,
            "confidence": 0.9,
            "model": agent,
            "role": "attention_tracker"
        }
        
        try:
            resp = requests.post(
                f"{self.plato_url}/room/{self.room}",
                json=tile,
                timeout=5
            )
            return {"status": "written", "agent": agent, "attending_to": attending_to}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_fleet_attention(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most recent attention tiles from all agents."""
        try:
            resp = requests.get(
                f"{self.plato_url}/room/{self.room}?limit={limit}",
                timeout=5
            )
            if resp.status_code == 200:
                tiles = resp.json().get("tiles", [])
                return [
                    {
                        "agent": t.get("agent", "unknown"),
                        "attending_to": t.get("answer", ""),
                        "when": t.get("timestamp", "unknown"),
                        "confidence": t.get("confidence", 0.5)
                    }
                    for t in tiles
                ]
        except:
            pass
        return []
    
    def get_agent_attention(self, agent: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get what a specific agent is attending to."""
        try:
            resp = requests.get(
                f"{self.plato_url}/room/{self.room}?limit=100",
                timeout=5
            )
            if resp.status_code == 200:
                tiles = resp.json().get("tiles", [])
                agent_tiles = [t for t in tiles if t.get("agent") == agent]
                return agent_tiles[:limit]
        except:
            pass
        return []
    
    def get_attention_by_domain(self, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get what agents are attending to within a specific domain."""
        try:
            resp = requests.get(
                f"{self.plato_url}/room/{self.room}?limit=100",
                timeout=5
            )
            if resp.status_code == 200:
                tiles = resp.json().get("tiles", [])
                domain_tiles = [t for t in tiles if t.get("domain") == domain]
                return domain_tiles[:limit]
        except:
            pass
        return []
    
    def create_attention_room(self) -> bool:
        """Ensure the fleet_attention room exists."""
        try:
            resp = requests.post(
                f"{self.plato_url}/room/{self.room}",
                json={"action": "create", "room": self.room},
                timeout=5
            )
            return resp.status_code in (200, 201)
        except:
            return False
    
    def get_attention_summary(self) -> Dict[str, Any]:
        """Get a summary of fleet attention across all domains."""
        attention = self.get_fleet_attention(limit=50)
        
        # Group by agent
        by_agent: Dict[str, int] = {}
        by_domain: Dict[str, int] = {}
        
        for t in attention:
            agent = t.get("agent", "unknown")
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        return {
            "total_tiles": len(attention),
            "agents_tracking": len(by_agent),
            "by_agent": by_agent,
            "recent": attention[:10]
        }