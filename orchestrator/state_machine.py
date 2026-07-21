"""
Mode Switch State Machine — Crypto-Agile Orchestrator
Transitions between QKD-PQC Hybrid / Buffered / PQC-Only modes.
Drives real PQC re-keying on every state transition.
"""
from __future__ import annotations

import enum
import hashlib
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Callable, Optional

from pqc.engine import PQCEngine


class Mode(str, enum.Enum):
    QKD_PQC_HYBRID = "QKD_PQC_HYBRID"    # Both QKD + PQC active — highest security
    BUFFERED_KEY   = "BUFFERED_KEY"        # QKD degraded — using buffered key + PQC
    PQC_ONLY       = "PQC_ONLY"           # QKD unavailable — pure PQC


MODE_COLORS = {
    Mode.QKD_PQC_HYBRID: "#00C853",   # Green
    Mode.BUFFERED_KEY:   "#FF6D00",   # Orange
    Mode.PQC_ONLY:       "#D50000",   # Red
}

MODE_SECURITY = {
    Mode.QKD_PQC_HYBRID: "MAXIMUM — ITS + PQC",
    Mode.BUFFERED_KEY:   "HIGH — Pre-shared QKD + PQC",
    Mode.PQC_ONLY:       "STANDARD — PQC only (NIST ML-KEM)",
}


@dataclass
class ChannelMetrics:
    """Live channel metrics used for mode decision."""
    qber: float = 0.03
    skr_kbps: float = 100.0
    predicted_skr_kbps: float = 100.0
    distance_km: float = 50.0
    loss_db: float = 12.0
    ai_predicted_mode: str = "QKD_PQC_HYBRID"
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModeTransition:
    """Record of a mode switch event."""
    transition_id: str
    from_mode: str
    to_mode: str
    trigger: str
    qber_at_switch: float
    skr_at_switch: float
    rekey_time_ms: float
    new_session_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionKey:
    """Active session cryptographic key material."""
    session_id: str
    mode: str
    shared_secret_hex: str
    qkd_key_hex: Optional[str]
    pqc_key_hex: str
    created_at: float
    expires_at: float
    rotation_count: int = 0


class ModeStateMachine:
    """
    Crypto-agile mode switch orchestrator.
    
    Thresholds:
        QBER < 7%  → QKD_PQC_HYBRID  (QKD secure)
        7% ≤ QBER < 11%  → BUFFERED_KEY  (QKD degraded, use buffer)
        QBER ≥ 11% → PQC_ONLY  (QKD broken, pure PQC)
        
    AI pre-emption: if AI predicts degradation within 30s, proactively switch.
    """

    # Security thresholds
    QBER_HYBRID_MAX   = 0.07
    QBER_CRITICAL     = 0.11
    SKR_MIN_HYBRID    = 1.0    # kbps
    KEY_BUFFER_MAX    = 1024   # bytes of buffered QKD key material
    SESSION_TTL       = 300    # seconds — re-key every 5 min

    def __init__(self, pqc_engine: PQCEngine | None = None):
        self.pqc = pqc_engine or PQCEngine()
        self.current_mode = Mode.PQC_ONLY
        self.current_session: Optional[SessionKey] = None
        self.key_buffer: bytes = b""           # Buffered QKD key material
        self.transitions: list[ModeTransition] = []
        self._lock = threading.RLock()
        self._on_mode_change: list[Callable] = []
        self._running = False

        # Initialize with a PQC-only session
        self._do_rekey(Mode.PQC_ONLY, trigger="INIT", qber=0.0, skr=0.0)

    # ─── Public API ───────────────────────────────────────────────────────────

    def update(self, metrics: ChannelMetrics) -> Optional[ModeTransition]:
        """
        Update channel metrics and trigger mode switch if needed.
        Returns ModeTransition if a switch occurred, else None.
        """
        with self._lock:
            target_mode = self._compute_target_mode(metrics)
            if target_mode != self.current_mode:
                return self._switch_to(target_mode, metrics)
            # Check if re-key needed (TTL expiry)
            if self.current_session and time.time() > self.current_session.expires_at:
                return self._switch_to(self.current_mode, metrics, trigger="TTL_REKEY")
            return None

    def buffer_qkd_key(self, key_material: bytes):
        """Append QKD-derived key material to buffer."""
        with self._lock:
            self.key_buffer = (self.key_buffer + key_material)[-self.KEY_BUFFER_MAX:]

    def get_state(self) -> dict:
        """Return full orchestrator state."""
        with self._lock:
            return {
                "mode": self.current_mode.value,
                "mode_color": MODE_COLORS[self.current_mode],
                "mode_security": MODE_SECURITY[self.current_mode],
                "session_id": self.current_session.session_id if self.current_session else None,
                "session_rotation_count": self.current_session.rotation_count if self.current_session else 0,
                "key_buffer_bytes": len(self.key_buffer),
                "total_transitions": len(self.transitions),
                "last_transition": asdict(self.transitions[-1]) if self.transitions else None,
                "pqc_status": self.pqc.status(),
            }

    def on_mode_change(self, callback: Callable):
        """Register callback for mode change events."""
        self._on_mode_change.append(callback)

    def get_transitions(self) -> list[dict]:
        with self._lock:
            return [asdict(t) for t in self.transitions]

    # ─── Internal Logic ───────────────────────────────────────────────────────

    def _compute_target_mode(self, m: ChannelMetrics) -> Mode:
        """Determine target mode from channel metrics and AI prediction."""
        # Hard thresholds (immediate)
        if m.qber >= self.QBER_CRITICAL or m.skr_kbps <= 0:
            return Mode.PQC_ONLY

        if m.qber >= self.QBER_HYBRID_MAX or m.skr_kbps < self.SKR_MIN_HYBRID:
            return Mode.BUFFERED_KEY

        # AI pre-emption: if AI predicts PQC_ONLY in 30s, switch to BUFFERED now
        if m.ai_predicted_mode == "PQC_ONLY":
            return Mode.BUFFERED_KEY

        # Check buffer availability for HYBRID
        if self.current_mode == Mode.QKD_PQC_HYBRID and len(self.key_buffer) < 32:
            return Mode.BUFFERED_KEY

        return Mode.QKD_PQC_HYBRID

    def _switch_to(
        self,
        new_mode: Mode,
        metrics: ChannelMetrics | None = None,
        trigger: str | None = None,
    ) -> ModeTransition:
        """Execute mode switch with re-keying."""
        old_mode = self.current_mode
        qber = metrics.qber if metrics else 0.0
        skr = metrics.skr_kbps if metrics else 0.0

        if trigger is None:
            if new_mode == Mode.PQC_ONLY:
                trigger = f"QBER_CRITICAL({qber:.3%})" if qber >= self.QBER_CRITICAL else "SKR_ZERO"
            elif new_mode == Mode.BUFFERED_KEY:
                trigger = f"QKD_DEGRADED(QBER={qber:.3%},SKR={skr:.1f}kbps)"
            else:
                trigger = f"QKD_RECOVERED(QBER={qber:.3%},SKR={skr:.1f}kbps)"

        t0 = time.perf_counter()
        session = self._do_rekey(new_mode, trigger, qber, skr)
        rekey_ms = (time.perf_counter() - t0) * 1000

        tid = "TRN-" + hashlib.sha256(f"{old_mode}{new_mode}{time.time()}".encode()).hexdigest()[:8].upper()
        transition = ModeTransition(
            transition_id=tid,
            from_mode=old_mode.value,
            to_mode=new_mode.value,
            trigger=trigger,
            qber_at_switch=qber,
            skr_at_switch=skr,
            rekey_time_ms=round(rekey_ms, 2),
            new_session_id=session.session_id,
        )
        self.transitions.append(transition)
        self.current_mode = new_mode

        for cb in self._on_mode_change:
            try:
                cb(transition)
            except Exception:
                pass

        return transition

    def _do_rekey(
        self,
        mode: Mode,
        trigger: str,
        qber: float,
        skr: float,
    ) -> SessionKey:
        """Perform actual PQC re-keying for the new session."""
        # Generate new PQC session key
        pk, sk, _ = self.pqc.kem_keygen()
        ct, pqc_ss, _ = self.pqc.kem_encapsulate(pk)

        # Combine with QKD key material if available
        if mode == Mode.QKD_PQC_HYBRID and len(self.key_buffer) >= 32:
            qkd_key = self.key_buffer[:32]
            self.key_buffer = self.key_buffer[32:]
            # XOR-combine QKD + PQC (information-theoretically secure when QKD is active)
            final_key = bytes(a ^ b for a, b in zip(qkd_key, pqc_ss[:32]))
            qkd_key_hex = qkd_key.hex()
        elif mode == Mode.BUFFERED_KEY and len(self.key_buffer) >= 32:
            qkd_key = self.key_buffer[:32]
            self.key_buffer = self.key_buffer[32:]
            final_key = bytes(a ^ b for a, b in zip(qkd_key, pqc_ss[:32]))
            qkd_key_hex = qkd_key.hex()
        else:
            final_key = pqc_ss[:32]
            qkd_key_hex = None

        rotation_count = (self.current_session.rotation_count + 1) if self.current_session else 0
        session_id = "SES-" + hashlib.sha256(final_key + trigger.encode()).hexdigest()[:12].upper()

        session = SessionKey(
            session_id=session_id,
            mode=mode.value,
            shared_secret_hex=final_key.hex(),
            qkd_key_hex=qkd_key_hex,
            pqc_key_hex=pqc_ss.hex()[:64],
            created_at=time.time(),
            expires_at=time.time() + self.SESSION_TTL,
            rotation_count=rotation_count,
        )
        self.current_session = session
        return session


# Singleton
state_machine = ModeStateMachine()


if __name__ == "__main__":
    import json

    sm = ModeStateMachine()
    print("=== Mode Switch Demo ===")
    print(f"Initial: {sm.current_mode.value}")

    # Buffer some QKD key material
    sm.buffer_qkd_key(os.urandom(256))

    # Scenario 1: Good QKD → hybrid
    t = sm.update(ChannelMetrics(qber=0.03, skr_kbps=100.0, predicted_skr_kbps=95.0))
    print(f"After good QKD:  {sm.current_mode.value}  (transition: {t})")

    # Scenario 2: QKD degraded
    t = sm.update(ChannelMetrics(qber=0.085, skr_kbps=0.5, predicted_skr_kbps=0.1))
    if t:
        print(f"After degradation: {sm.current_mode.value}  trigger={t.trigger}  rekey={t.rekey_time_ms:.1f}ms")

    # Scenario 3: QKD fails
    t = sm.update(ChannelMetrics(qber=0.15, skr_kbps=0.0, predicted_skr_kbps=0.0))
    if t:
        print(f"After QKD fail:   {sm.current_mode.value}  trigger={t.trigger}  rekey={t.rekey_time_ms:.1f}ms")

    # Scenario 4: QKD recovers
    sm.buffer_qkd_key(os.urandom(256))
    t = sm.update(ChannelMetrics(qber=0.02, skr_kbps=80.0, predicted_skr_kbps=85.0))
    if t:
        print(f"After recovery:   {sm.current_mode.value}  trigger={t.trigger}  rekey={t.rekey_time_ms:.1f}ms")

    print(f"\nTotal transitions: {len(sm.transitions)}")
    for tr in sm.transitions:
        print(f"  {tr.from_mode} → {tr.to_mode}  [{tr.trigger}]  rekey={tr.rekey_time_ms:.1f}ms")
