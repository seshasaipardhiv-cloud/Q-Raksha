# QuantumShield 🛡️

**Crypto-Agile QKD-PQC Orchestration Platform** | India NQM-Aligned | TCOE Hackathon

> A working, demoable quantum-secure communications system proving: CBOM scanning, real NIST PQC cryptography, physics-validated QKD simulation, AI-driven channel prediction, crypto-agile mode switching, and tamper-evident certification evidence generation.

---

## What's Real vs. Simulated

| Component | Reality | Details |
|---|---|---|
| **CBOM Scanner** | ✅ 100% Real | AST + regex across Python/Java/C/JS — HNDL risk model |
| **PQC Engine** | ✅ 100% Real | liboqs Kyber768 (ML-KEM) + Dilithium3 (ML-DSA) |
| **Mode Switch** | ✅ 100% Real | Live PQC re-keying on threshold breach — real crypto |
| **Evidence Ledger** | ✅ 100% Real | SHA3-256 hash chain — NQM certification mapped |
| **AI Predictor** | ✅ Real ML | GBM trained on physics-based synthetic data |
| **QKD Simulator** | 🔬 Physics Sim | BB84 decoy-state GLLP — honest simulation, no hardware |

---

## Quick Start

### 1. Install dependencies
```powershell
cd quantumshield
pip install -r requirements.txt
```

### 2. (Optional) Install liboqs for REAL NIST PQC
```powershell
# On Linux/Mac:
pip install liboqs-python
# On Windows: use WSL or pre-built wheel from OQS project
```

### 3. Pre-train AI model (optional, ~30s)
```powershell
python -m ai.trainer
```

### 4. Launch dashboard
```powershell
streamlit run dashboard/app.py
```

Dashboard runs at **http://localhost:8501**

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│               STREAMLIT DASHBOARD (port 8501)           │
│  Live Monitor | CBOM Report | PQC Engine | Evidence Log  │
└────────────────────────┬────────────────────────────────┘
                         │ (local Python calls)
          ┌──────────────┼──────────────┬─────────────────┐
          │              │              │                  │
    ┌─────▼─────┐  ┌─────▼────┐  ┌────▼─────┐  ┌────────▼──────┐
    │CBOM Scanner│  │ PQC Engine│  │QKD Sim   │  │ AI Predictor  │
    │(cbom/)     │  │(pqc/)    │  │(qkd/)    │  │(ai/)          │
    └────────────┘  └──────────┘  └──────────┘  └───────────────┘
                         │              │                  │
                         └──────────────┴──────────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  Mode Switch Orchestrator   │
                          │  (orchestrator/)            │
                          └─────────────┬──────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │  Evidence Ledger (ledger/)  │
                          │  SHA3-256 hash chain        │
                          └────────────────────────────┘
```

---

## Demo Scenarios

### 1. CBOM Scan
1. Open **CBOM Scanner** tab
2. Target path: `tests/fixtures/` 
3. Set sensitivity: `SECRET`, years: `15`
4. Click "Run CBOM Scan"
5. Shows RSA-2048, ECDSA, MD5, DES, RC4 findings with HNDL risk

### 2. PQC Handshake (Live)
1. Open **PQC Engine** tab
2. Click "Run Kyber768 Handshake"
3. Watch real Kyber768 KEM exchange — shared secrets match in <5ms
4. Click "Run Dilithium3 Sign/Verify"

### 3. QKD Channel Stress Test
1. Open **Live Monitor** tab
2. Drag **Distance** slider from 10km → 200km
3. Watch QBER rise, SKR collapse
4. Mode automatically switches: HYBRID → BUFFERED → PQC_ONLY
5. Click "💥 Degrade" button for instant demo degradation

### 4. AI-Predicted Failover
1. Watch **Predicted SKR** line (purple) lead the actual SKR
2. AI pre-empts the mode switch before QBER hits threshold
3. Click "✅ Recover" — system transitions back to HYBRID

### 5. Evidence Ledger Verification
1. Open **Evidence Ledger** tab
2. Click "Verify Chain Integrity"
3. Export certification report JSON
4. Each event shows SHA3-256 hash linking to previous

---

## Module Reference

```
quantumshield/
├── cbom/
│   ├── scanner.py          # Main CBOM scanner
│   ├── patterns.py         # Crypto detection patterns (Python/Java/C/JS)
│   └── risk_model.py       # Risk scoring + HNDL assessment
├── pqc/
│   └── engine.py           # Kyber768 KEM + Dilithium3 signatures
├── qkd/
│   └── bb84_sim.py         # BB84 decoy-state physics simulator
├── ai/
│   ├── predictor.py        # GBM channel predictor
│   └── trainer.py          # Training script
├── orchestrator/
│   ├── state_machine.py    # Mode switch + re-keying
│   └── api.py              # FastAPI REST server (optional)
├── ledger/
│   └── chain.py            # Hash-chained evidence log
├── dashboard/
│   └── app.py              # Streamlit main dashboard
└── tests/fixtures/         # Legacy crypto samples for CBOM demo
```

---

## NQM Alignment

| NQM Pillar | Feature | Implementation |
|---|---|---|
| Pillar 2 — Quantum-Safe Crypto | CBOM Scanner | Flags RSA/ECDSA/DH in codebase |
| Pillar 2 — PQC Migration | PQC Engine | NIST ML-KEM + ML-DSA (live) |
| Pillar 3 — Quantum Comms | QKD Simulator | BB84 decoy-state, mode switching |
| Pillar 2 — Evidence | Evidence Ledger | SHA3-256 chain, NCIIPC mapped |

---

## References

- NIST FIPS 203 (ML-KEM / Kyber) | FIPS 204 (ML-DSA / Dilithium)
- Lo, Ma, Chen (2005): Decoy-State QKD — Physical Review Letters
- GLLP Security Proof for BB84 (Gottesman, Lo, Lütkenhaus, Preskill 2004)
- India National Quantum Mission (2023) — DST
- NCIIPC PQC Readiness Guidelines
- Open Quantum Safe (OQS) — liboqs
