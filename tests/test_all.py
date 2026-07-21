"""
Unit Tests — QuantumShield
Run with: python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ─── CBOM Scanner Tests ───────────────────────────────────────────────────────
class TestCBOMScanner:
    def test_scan_fixture(self, tmp_path):
        from cbom.scanner import CBOMScanner
        # Write a tiny python file with RSA usage
        p = tmp_path / "test_crypto.py"
        p.write_text("from Crypto.PublicKey import RSA\nrsa_key = RSA.generate(2048)\n")
        scanner = CBOMScanner(data_sensitivity="CONFIDENTIAL")
        report = scanner.scan_path(tmp_path)
        assert report.total_findings >= 1
        assert any(e.algorithm in ("RSA", "RSA-weak-key") for e in report.entries)

    def test_risk_tiers(self):
        from cbom.risk_model import compute_risk
        ra = compute_risk("RSA", "SECRET", 15)
        assert ra.risk_tier in ("CRITICAL", "HIGH")
        assert ra.harvest_now_decrypt_later is True  # 2026+15=2041 > 2030

    def test_safe_file_not_flagged(self, tmp_path):
        from cbom.scanner import CBOMScanner
        p = tmp_path / "safe.py"
        p.write_text("import hashlib\nhash = hashlib.sha3_256(b'data').hexdigest()\n")
        scanner = CBOMScanner()
        report = scanner.scan_path(tmp_path)
        assert report.total_findings == 0

    def test_json_output(self, tmp_path):
        import json
        from cbom.scanner import CBOMScanner
        p = tmp_path / "rsa.py"
        p.write_text("import rsa\n")
        scanner = CBOMScanner()
        report = scanner.scan_path(tmp_path)
        j = json.loads(scanner.to_json(report))
        assert "cbom_version" in j
        assert "findings" in j

    def test_hndl_detection(self):
        from cbom.risk_model import compute_risk, QUANTUM_THREAT_YEAR, CURRENT_YEAR
        # Data that must stay secret past quantum threat year
        ra = compute_risk("RSA", "CONFIDENTIAL", years_data_must_stay_secret=10)
        expected_hndl = (CURRENT_YEAR + 10) > QUANTUM_THREAT_YEAR
        assert ra.harvest_now_decrypt_later == expected_hndl


# ─── PQC Engine Tests ─────────────────────────────────────────────────────────
class TestPQCEngine:
    def setup_method(self):
        from pqc.engine import PQCEngine
        self.eng = PQCEngine()

    def test_kem_shared_secrets_match(self):
        pk, sk, _ = self.eng.kem_keygen()
        ct, ss_b, _ = self.eng.kem_encapsulate(pk)
        ss_a, _ = self.eng.kem_decapsulate(sk, ct)
        assert ss_a == ss_b, "KEM shared secrets must match"

    def test_kem_key_sizes(self):
        pk, sk, meta = self.eng.kem_keygen()
        assert len(pk) > 0
        assert len(sk) > 0
        assert meta["public_key_bytes"] > 0

    def test_signature_valid(self):
        spk, ssk, _ = self.eng.sig_keygen()
        msg = b"QuantumShield test message"
        sig, _ = self.eng.sign(msg, ssk)
        valid, _ = self.eng.verify(msg, sig, spk)
        assert valid is True

    def test_kem_speed(self):
        pk, sk, meta = self.eng.kem_keygen()
        assert meta["keygen_ms"] < 5000, "KEM keygen should complete in <5s"
        ct, ss, emeta = self.eng.kem_encapsulate(pk)
        assert emeta["encap_ms"] < 5000

    def test_hybrid_combine(self):
        ss1 = b"\x01" * 32
        ss2 = b"\x02" * 32
        combined = self.eng.hybrid_kem_combine(ss1, ss2)
        assert len(combined) == 32
        assert combined != ss1
        assert combined != ss2

    def test_aes_gcm_roundtrip(self):
        key = b"\x00" * 32
        plaintext = b"secret data for quantum shield"
        nonce, ct = self.eng.encrypt_aes_gcm(key, plaintext)
        recovered = self.eng.decrypt_aes_gcm(key, nonce, ct)
        assert recovered == plaintext


# ─── QKD Simulator Tests ──────────────────────────────────────────────────────
class TestQKDSimulator:
    def setup_method(self):
        from qkd.bb84_sim import BB84DecoySimulator, QKDChannelParams
        self.sim = BB84DecoySimulator()
        self.params = QKDChannelParams()

    def test_short_distance_feasible(self):
        from qkd.bb84_sim import QKDChannelParams
        p = QKDChannelParams(distance_km=10.0)
        r = self.sim.simulate(p)
        assert r.link_feasible is True
        assert r.secret_key_rate_bps > 0
        assert 0 <= r.qber <= 0.5

    def test_long_distance_infeasible(self):
        from qkd.bb84_sim import QKDChannelParams
        p = QKDChannelParams(distance_km=250.0, loss_db_per_km=0.4)
        r = self.sim.simulate(p)
        assert r.link_feasible is False or r.secret_key_rate_bps == 0

    def test_qber_increases_with_distance(self):
        from qkd.bb84_sim import QKDChannelParams
        p1 = QKDChannelParams(distance_km=10.0)
        p2 = QKDChannelParams(distance_km=100.0)
        r1 = self.sim.simulate(p1)
        r2 = self.sim.simulate(p2)
        assert r2.qber >= r1.qber, "QBER should increase with distance"

    def test_skr_decreases_with_distance(self):
        from qkd.bb84_sim import QKDChannelParams
        p1 = QKDChannelParams(distance_km=10.0)
        p2 = QKDChannelParams(distance_km=80.0)
        r1 = self.sim.simulate(p1)
        r2 = self.sim.simulate(p2)
        assert r2.secret_key_rate_bps <= r1.secret_key_rate_bps

    def test_mode_recommendation(self):
        from qkd.bb84_sim import QKDChannelParams
        p_good = QKDChannelParams(distance_km=10.0)
        r_good = self.sim.simulate(p_good)
        assert r_good.recommended_mode in ("QKD_PQC_HYBRID", "BUFFERED_KEY", "PQC_ONLY")

    def test_binary_entropy(self):
        h = self.sim.binary_entropy(0.11)
        assert 0 < h < 1
        assert abs(self.sim.binary_entropy(0.0)) < 1e-10
        assert abs(self.sim.binary_entropy(1.0)) < 1e-10

    def test_distance_scan(self):
        scan = self.sim.scan_distance(self.params, distances=[10, 50, 100])
        assert len(scan) == 3
        assert all("skr_kbps" in r for r in scan)


# ─── Mode State Machine Tests ─────────────────────────────────────────────────
class TestStateMachine:
    def setup_method(self):
        import os
        from orchestrator.state_machine import ModeStateMachine, ChannelMetrics
        self.sm = ModeStateMachine()
        self.sm.buffer_qkd_key(os.urandom(256))

    def test_hybrid_on_good_qkd(self):
        from orchestrator.state_machine import ChannelMetrics
        t = self.sm.update(ChannelMetrics(qber=0.03, skr_kbps=100.0, predicted_skr_kbps=95.0))
        assert self.sm.current_mode.value == "QKD_PQC_HYBRID"

    def test_pqc_only_on_critical_qber(self):
        from orchestrator.state_machine import ChannelMetrics
        self.sm.update(ChannelMetrics(qber=0.03, skr_kbps=100.0))
        self.sm.update(ChannelMetrics(qber=0.15, skr_kbps=0.0, predicted_skr_kbps=0.0))
        assert self.sm.current_mode.value == "PQC_ONLY"

    def test_rekey_speed(self):
        import os
        from orchestrator.state_machine import ChannelMetrics
        self.sm.buffer_qkd_key(os.urandom(256))
        self.sm.update(ChannelMetrics(qber=0.03, skr_kbps=100.0))
        t = self.sm.update(ChannelMetrics(qber=0.15, skr_kbps=0.0))
        if t:
            assert t.rekey_time_ms < 10000, "Re-key should complete in <10s"

    def test_transition_logged(self):
        import os
        from orchestrator.state_machine import ChannelMetrics
        self.sm.buffer_qkd_key(os.urandom(256))
        self.sm.update(ChannelMetrics(qber=0.03, skr_kbps=100.0))
        self.sm.update(ChannelMetrics(qber=0.15, skr_kbps=0.0))
        assert len(self.sm.transitions) >= 1

    def test_session_created(self):
        assert self.sm.current_session is not None
        assert self.sm.current_session.session_id.startswith("SES-")


# ─── Evidence Ledger Tests ────────────────────────────────────────────────────
class TestEvidenceLedger:
    def setup_method(self, tmp_path=None):
        import tempfile, os
        self.tmpdir = tempfile.mkdtemp()
        path = os.path.join(self.tmpdir, "test_ledger.jsonl")
        from ledger.chain import EvidenceLedger
        self.ledger = EvidenceLedger(ledger_path=path)

    def test_genesis_created(self):
        assert len(self.ledger._entries) >= 1
        assert self.ledger._entries[0].event_type == "SYSTEM_START"

    def test_append_and_verify(self):
        self.ledger.append("MODE_SWITCH", {"from": "A", "to": "B"})
        valid, errors = self.ledger.verify_chain()
        assert valid is True
        assert len(errors) == 0

    def test_hash_chain_integrity(self):
        self.ledger.append("KEY_ROTATION", {"count": 1})
        self.ledger.append("CBOM_ALERT", {"algo": "RSA"})
        for i in range(1, len(self.ledger._entries)):
            curr = self.ledger._entries[i]
            prev = self.ledger._entries[i-1]
            assert curr.previous_hash == prev.entry_hash

    def test_tamper_detection(self):
        self.ledger.append("PQC_HANDSHAKE", {"algo": "Kyber768"})
        # Tamper with an entry
        self.ledger._entries[1].event_data["TAMPERED"] = True
        valid, errors = self.ledger.verify_chain()
        assert valid is False
        assert len(errors) > 0

    def test_export_report(self):
        report = self.ledger.export_report()
        assert "chain_valid" in report
        assert "entries" in report
        assert report["chain_valid"] is True

    def test_sequence_numbers(self):
        n = len(self.ledger._entries)
        self.ledger.append("TEST", {})
        assert self.ledger._entries[-1].sequence == n
