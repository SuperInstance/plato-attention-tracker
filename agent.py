#!/usr/bin/env python3
"""
plato-attention-tracker — Track what the fleet is paying attention to
Monitor rate-attention streams, detect anomalies, and alert on elevated signals.
"""

import json, time
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class AttentionSignal:
    stream: str
    value: float
    baseline: float
    deviation: float
    timestamp: float
    elevated: bool = False

class AttentionTracker:
    def __init__(self, plato_url="http://147.224.38.131:8847"):
        self.plato_url = plato_url
        self.streams: Dict[str, List[float]] = {}  # stream name -> recent values
        self.baselines: Dict[str, float] = {}
        self.elevated: Dict[str, AttentionSignal] = {}
    
    def record(self, stream: str, value: float):
        """Record a value for a stream."""
        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(value)
        
        # Keep last 20 values
        if len(self.streams[stream]) > 20:
            self.streams[stream] = self.streams[stream][-20:]
        
        # Update baseline
        self.baselines[stream] = sum(self.streams[stream]) / len(self.streams[stream])
        
        # Check if elevated
        deviation = abs(value - self.baselines[stream])
        threshold = self.baselines[stream] * 0.3  # 30% deviation
        
        signal = AttentionSignal(
            stream=stream,
            value=value,
            baseline=self.baselines[stream],
            deviation=deviation,
            timestamp=time.time(),
            elevated=deviation > threshold
        )
        
        if signal.elevated:
            self.elevated[stream] = signal
            self._submit(f"Attention spike: {stream}", f"Value {value:.2f} deviates {deviation:.2f} from baseline {self.baselines[stream]:.2f}")
        
        return signal
    
    def get_attention_map(self) -> Dict:
        """Current attention landscape."""
        return {
            "streams_monitored": len(self.streams),
            "elevated_signals": len(self.elevated),
            "elevated_details": {s: {"value": sig.value, "baseline": sig.baseline, "deviation": sig.deviation}
                                for s, sig in self.elevated.items()},
            "all_streams": {s: {"current": vals[-1] if vals else 0, "baseline": self.baselines.get(s, 0)}
                           for s, vals in self.streams.items()}
        }
    
    def clear_elevated(self, stream: str):
        """Clear an elevated signal (after handling)."""
        if stream in self.elevated:
            del self.elevated[stream]
    
    def _submit(self, q: str, a: str):
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(f"{self.plato_url}/submit", data=json.dumps({"question": q, "answer": a, "agent": "plato-attention-tracker", "room": "attention"}).encode(), headers={"Content-Type": "application/json"}), timeout=5)
        except: pass

def demo():
    tracker = AttentionTracker()
    
    # Simulate attention streams
    for i in range(10):
        tracker.record("zeroclaw.alchemist", 5.0 + i * 0.5)
        tracker.record("instinct_training", 8.0)
        tracker.record("flux_isa", 3.0)
    
    # Spike
    tracker.record("zeroclaw.alchemist", 12.0)
    
    print("=== Attention Map ===")
    print(json.dumps(tracker.get_attention_map(), indent=2))

if __name__ == "__main__": demo()
