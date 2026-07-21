"""
Risk Model for CBOM entries.
Risk tier = f(algorithm_risk, data_sensitivity, years_to_secret_expiry, quantum_timeline)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# Quantum threat timeline (conservative NIST estimate)
QUANTUM_THREAT_YEAR = 2030          # CRQCs plausibly capable of breaking 2048-bit RSA
CURRENT_YEAR = 2026

DataSensitivity = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]
SENSITIVITY_SCORE: dict[str, int] = {
    "PUBLIC": 1,
    "INTERNAL": 2,
    "CONFIDENTIAL": 3,
    "SECRET": 4,
    "TOP_SECRET": 5,
}

ALGORITHM_BASE_RISK: dict[str, int] = {
    "RSA": 8,
    "ECDSA": 8,
    "ECDH": 8,
    "ECDSA/ECDH": 8,
    "DH": 7,
    "DSA": 7,
    "MD5": 10,
    "SHA-1": 7,
    "3DES/DES": 9,
    "DES": 9,
    "RC4": 10,
    "AES-ECB": 6,
    "AES-CBC": 4,
    "RSA-weak-key": 10,
    "TLS<1.2": 8,
    "RSA (OpenSSL)": 8,
    "ECDSA (OpenSSL)": 8,
    "ECDSA/ECDH (OpenSSL)": 8,
}


@dataclass
class RiskAssessment:
    risk_score: float           # 0–100
    risk_tier: str              # CRITICAL / HIGH / MEDIUM / LOW
    harvest_now_decrypt_later: bool
    years_until_vulnerable: int
    recommendation: str
    nqm_mapping: str            # India NQM / NCIIPC reference


def compute_risk(
    algorithm: str,
    data_sensitivity: DataSensitivity = "CONFIDENTIAL",
    years_data_must_stay_secret: int = 10,
) -> RiskAssessment:
    """
    Compute composite risk score for a cryptographic usage.
    
    Harvest-Now-Decrypt-Later (HNDL) risk = data_sensitivity × years_to_secret vs quantum timeline.
    If years_data_must_stay_secret + CURRENT_YEAR > QUANTUM_THREAT_YEAR, HNDL risk is active.
    """
    base = ALGORITHM_BASE_RISK.get(algorithm, 5)
    sens = SENSITIVITY_SCORE.get(data_sensitivity, 3)

    years_to_quantum = max(0, QUANTUM_THREAT_YEAR - CURRENT_YEAR)        # 4 years
    data_expiry_year = CURRENT_YEAR + years_data_must_stay_secret

    hndl = data_expiry_year > QUANTUM_THREAT_YEAR

    # HNDL multiplier: if data lives past quantum threat, urgency is maximum
    hndl_multiplier = 1.5 if hndl else 1.0

    score = min(100.0, base * sens * hndl_multiplier)

    if score >= 70:
        tier = "CRITICAL"
    elif score >= 45:
        tier = "HIGH"
    elif score >= 25:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # Recommendations
    rec_map = {
        "RSA": "Migrate to ML-KEM (Kyber768) for key exchange, ML-DSA (Dilithium3) for signatures",
        "ECDSA": "Migrate to ML-DSA (Dilithium3) or FALCON-512",
        "ECDSA/ECDH": "Migrate to ML-KEM (Kyber768) + ML-DSA (Dilithium3)",
        "DH": "Migrate to ML-KEM (Kyber768)",
        "DSA": "Migrate to ML-DSA (Dilithium3)",
        "MD5": "Replace with SHA-3-256 immediately — not quantum-specific, already broken",
        "SHA-1": "Replace with SHA-3-256 or SHA-512",
        "3DES/DES": "Replace with AES-256-GCM immediately",
        "DES": "Replace with AES-256-GCM immediately",
        "RC4": "Replace with ChaCha20-Poly1305 immediately",
        "AES-ECB": "Replace with AES-256-GCM (authenticated encryption)",
        "AES-CBC": "Add authentication: migrate to AES-256-GCM",
        "RSA-weak-key": "Increase to RSA-4096 as interim, then migrate to ML-KEM",
        "TLS<1.2": "Upgrade to TLS 1.3 with PQC cipher suites",
    }

    nqm_map = {
        "RSA": "NQM Pillar 2 (Quantum-Safe Cryptography) — DoT Guidelines §4.2",
        "ECDSA": "NQM Pillar 2 — NCIIPC PQC Readiness §3.1",
        "ECDSA/ECDH": "NQM Pillar 2 — NCIIPC PQC Readiness §3.1",
        "DH": "NQM Pillar 2 — DoT Guidelines §4.2",
        "MD5": "CERT-In Vulnerability Note — Broken Hash",
        "SHA-1": "CERT-In Advisory — Deprecated Hash",
        "3DES/DES": "CERT-In Advisory — Deprecated Cipher",
        "DES": "CERT-In Advisory — Deprecated Cipher",
        "RC4": "CERT-In Advisory — Broken Stream Cipher",
    }

    return RiskAssessment(
        risk_score=round(score, 1),
        risk_tier=tier,
        harvest_now_decrypt_later=hndl,
        years_until_vulnerable=years_to_quantum,
        recommendation=rec_map.get(algorithm, f"Evaluate migration for {algorithm}"),
        nqm_mapping=nqm_map.get(algorithm, "NQM Pillar 2 — General PQC Assessment"),
    )
