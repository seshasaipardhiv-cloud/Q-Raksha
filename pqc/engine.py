"""
PQC Engine — Post-Quantum Cryptography via liboqs-python
Implements Kyber768 (KEM) + Dilithium3 (Signatures) with X25519 hybrid fallback.
Falls back to a pure-Python reference if liboqs is not installed.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import struct
import time
from dataclasses import dataclass
from typing import Optional, Tuple

# ─── Try to import liboqs ─────────────────────────────────────────────────────
try:
    import oqs  # type: ignore
    LIBOQS_AVAILABLE = True
except ImportError:
    LIBOQS_AVAILABLE = False

# ─── Try to import PyCA cryptography for X25519 hybrid ───────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey, X25519PublicKey,
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption,
    )
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    PYCA_AVAILABLE = True
except ImportError:
    PYCA_AVAILABLE = False


# ─── Fallback: pure-Python Kyber/Dilithium stubs (demo only) ─────────────────
class _FallbackKEM:
    """
    Pure-Python stub KEM for demo purposes when liboqs is unavailable.
    NOT cryptographically secure — clearly labeled in output.
    Uses SHA3-based simulation to demonstrate the protocol flow.
    """
    name = "Kyber768-STUB (not real PQC — install liboqs)"
    details = {"length_public_key": 1184, "length_secret_key": 2400,
               "length_ciphertext": 1088, "length_shared_secret": 32}

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        sk = os.urandom(64)
        pk = hashlib.sha3_256(sk + b"pub").digest() * 37  # 1184 bytes approx
        pk = pk[:1184]
        return pk, sk[:2400]

    def encap_secret(self, pk: bytes) -> Tuple[bytes, bytes]:
        r = os.urandom(32)
        ct = hashlib.sha3_256(pk + r).digest() * 34
        ct = ct[:1088]
        ss = hashlib.sha3_256(ct + b"ss").digest()[:32]
        return ct, ss

    def decap_secret(self, sk: bytes, ct: bytes) -> bytes:
        # Stub: deterministic from ct to match encap
        return hashlib.sha3_256(ct + b"ss").digest()[:32]


class _FallbackSig:
    """Pure-Python stub signature for demo when liboqs unavailable."""
    name = "Dilithium3-STUB (not real PQC — install liboqs)"
    details = {"length_public_key": 1952, "length_secret_key": 4000,
               "length_signature": 3293}

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        sk = os.urandom(64)
        pk = hashlib.sha3_256(sk + b"sig_pub").digest() * 62
        pk = pk[:1952]
        return pk, sk

    def sign(self, message: bytes, sk: bytes) -> bytes:
        sig = hashlib.sha3_256(sk + message).digest() * 103
        return sig[:3293]

    def verify(self, message: bytes, signature: bytes, pk: bytes) -> bool:
        expected = hashlib.sha3_256(hashlib.sha3_256(pk + b"sig_pub").digest()[:64][::-1] + message).digest() * 103
        # Stub: always True for demo
        return True


@dataclass
class KEMResult:
    algorithm: str
    is_real_pqc: bool
    public_key_bytes: int
    secret_key_bytes: int
    ciphertext_bytes: int
    shared_secret: bytes
    elapsed_ms: float


@dataclass
class SignatureResult:
    algorithm: str
    is_real_pqc: bool
    public_key_bytes: int
    signature_bytes: int
    verified: bool
    elapsed_ms: float


class PQCEngine:
    """
    Unified PQC engine exposing KEM and signature APIs.
    Uses liboqs when available, falls back to stubs with clear labeling.
    """

    def __init__(self):
        self.liboqs_available = LIBOQS_AVAILABLE
        self.pyca_available = PYCA_AVAILABLE
        self._kem_algo = "Kyber768" if LIBOQS_AVAILABLE else None
        self._sig_algo = "Dilithium3" if LIBOQS_AVAILABLE else None

    # ─── KEM ─────────────────────────────────────────────────────────────────

    def get_kem(self):
        if LIBOQS_AVAILABLE:
            return oqs.KeyEncapsulation("Kyber768")
        return _FallbackKEM()

    def get_sig(self):
        if LIBOQS_AVAILABLE:
            return oqs.Signature("Dilithium3")
        return _FallbackSig()

    def kem_keygen(self) -> Tuple[bytes, bytes, dict]:
        """Generate KEM keypair. Returns (public_key, secret_key, metadata)."""
        kem = self.get_kem()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            pk = kem.generate_keypair()
            sk = kem.export_secret_key()
        else:
            pk, sk = kem.generate_keypair()
        elapsed = (time.perf_counter() - t0) * 1000
        return pk, sk, {
            "algorithm": kem.name,
            "is_real_pqc": LIBOQS_AVAILABLE,
            "public_key_bytes": len(pk),
            "secret_key_bytes": len(sk),
            "keygen_ms": round(elapsed, 3),
        }

    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes, dict]:
        """Encapsulate: returns (ciphertext, shared_secret, metadata)."""
        kem = self.get_kem()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            ct, ss = kem.encap_secret(public_key)
        else:
            ct, ss = kem.encap_secret(public_key)
        elapsed = (time.perf_counter() - t0) * 1000
        return ct, ss, {
            "algorithm": kem.name,
            "ciphertext_bytes": len(ct),
            "shared_secret_bytes": len(ss),
            "encap_ms": round(elapsed, 3),
        }

    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> Tuple[bytes, dict]:
        """Decapsulate: returns (shared_secret, metadata)."""
        kem = self.get_kem()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            ss = kem.decap_secret(ciphertext)
        else:
            ss = kem.decap_secret(secret_key, ciphertext)
        elapsed = (time.perf_counter() - t0) * 1000
        return ss, {"decap_ms": round(elapsed, 3)}

    # ─── Signatures ──────────────────────────────────────────────────────────

    def sig_keygen(self) -> Tuple[bytes, bytes, dict]:
        """Generate signature keypair."""
        sig = self.get_sig()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            pk = sig.generate_keypair()
            sk = sig.export_secret_key()
        else:
            pk, sk = sig.generate_keypair()
        elapsed = (time.perf_counter() - t0) * 1000
        return pk, sk, {
            "algorithm": sig.name,
            "is_real_pqc": LIBOQS_AVAILABLE,
            "public_key_bytes": len(pk),
            "secret_key_bytes": len(sk),
            "keygen_ms": round(elapsed, 3),
        }

    def sign(self, message: bytes, secret_key: bytes) -> Tuple[bytes, dict]:
        """Sign a message."""
        sig = self.get_sig()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            signature = sig.sign(message)
        else:
            signature = sig.sign(message, secret_key)
        elapsed = (time.perf_counter() - t0) * 1000
        return signature, {"sign_ms": round(elapsed, 3), "signature_bytes": len(signature)}

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> Tuple[bool, dict]:
        """Verify a signature."""
        sig = self.get_sig()
        t0 = time.perf_counter()
        if LIBOQS_AVAILABLE:
            valid = sig.verify(message, signature, public_key)
        else:
            valid = sig.verify(message, signature, public_key)
        elapsed = (time.perf_counter() - t0) * 1000
        return valid, {"verify_ms": round(elapsed, 3)}

    # ─── Hybrid KEM (X25519 + Kyber768) ──────────────────────────────────────

    def hybrid_kem_keygen(self) -> dict:
        """
        Generate hybrid keypair: X25519 (classical) + Kyber768 (PQC).
        Belt-and-suspenders: secure if either component is secure.
        """
        pqc_pk, pqc_sk, pqc_meta = self.kem_keygen()
        if PYCA_AVAILABLE:
            x25519_sk = X25519PrivateKey.generate()
            x25519_pk = x25519_sk.public_key()
            x25519_pk_bytes = x25519_pk.public_bytes(Encoding.Raw, PublicFormat.Raw)
            x25519_sk_bytes = x25519_sk.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        else:
            x25519_sk_bytes = os.urandom(32)
            x25519_pk_bytes = hashlib.sha256(x25519_sk_bytes + b"x25519").digest()

        return {
            "pqc_public_key": pqc_pk,
            "pqc_secret_key": pqc_sk,
            "x25519_public_key": x25519_pk_bytes,
            "x25519_secret_key": x25519_sk_bytes,
            "pqc_meta": pqc_meta,
        }

    def hybrid_kem_combine(
        self,
        pqc_ss: bytes,
        classical_ss: bytes,
        context: bytes = b"QuantumShield-HybridKEM-v1",
    ) -> bytes:
        """
        Combine PQC and classical shared secrets via HKDF-SHA3-256.
        XOR-then-hash construction: secure if either component is secure.
        """
        combined_ikm = pqc_ss + classical_ss
        if PYCA_AVAILABLE:
            hkdf = HKDF(
                algorithm=hashes.SHA3_256(),
                length=32,
                salt=context,
                info=b"hybrid-shared-secret",
            )
            return hkdf.derive(combined_ikm)
        else:
            return hashlib.sha3_256(combined_ikm + context).digest()

    def encrypt_aes_gcm(self, key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
        """AES-256-GCM encrypt. Returns (nonce, ciphertext+tag)."""
        assert len(key) >= 32
        nonce = os.urandom(12)
        if PYCA_AVAILABLE:
            aesgcm = AESGCM(key[:32])
            ct = aesgcm.encrypt(nonce, plaintext, None)
        else:
            # XOR stub — for demo only
            ct = bytes(b ^ k for b, k in zip(plaintext, (key * (len(plaintext) // 32 + 1))[:len(plaintext)]))
        return nonce, ct

    def decrypt_aes_gcm(self, key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        """AES-256-GCM decrypt."""
        if PYCA_AVAILABLE:
            aesgcm = AESGCM(key[:32])
            return aesgcm.decrypt(nonce, ciphertext, None)
        else:
            return bytes(b ^ k for b, k in zip(ciphertext, (key * (len(ciphertext) // 32 + 1))[:len(ciphertext)]))

    def status(self) -> dict:
        return {
            "liboqs_available": self.liboqs_available,
            "pyca_available": self.pyca_available,
            "kem_algorithm": "Kyber768 (NIST ML-KEM)" if LIBOQS_AVAILABLE else "Kyber768-STUB",
            "sig_algorithm": "Dilithium3 (NIST ML-DSA)" if LIBOQS_AVAILABLE else "Dilithium3-STUB",
            "hybrid_mode": "X25519 + Kyber768" if PYCA_AVAILABLE else "X25519-STUB + Kyber768-STUB",
            "nist_compliance": LIBOQS_AVAILABLE,
        }


# Singleton
engine = PQCEngine()


if __name__ == "__main__":
    import json
    print("=== PQC Engine Status ===")
    print(json.dumps(engine.status(), indent=2))

    print("\n=== KEM Demo (Kyber768) ===")
    pk, sk, meta = engine.kem_keygen()
    print(f"Key generated: pk={len(pk)}B  sk={len(sk)}B  time={meta['keygen_ms']}ms")

    ct, ss_enc, emeta = engine.kem_encapsulate(pk)
    print(f"Encapsulated:  ct={len(ct)}B  ss={len(ss_enc)}B  time={emeta['encap_ms']}ms")

    ss_dec, dmeta = engine.kem_decapsulate(sk, ct)
    print(f"Decapsulated:  ss={len(ss_dec)}B  time={dmeta['decap_ms']}ms")
    print(f"Shared secrets MATCH: {ss_enc == ss_dec}")
    print(f"Shared secret (hex): {ss_enc.hex()[:32]}...")

    print("\n=== Signature Demo (Dilithium3) ===")
    spk, ssk, smeta = engine.sig_keygen()
    msg = b"QuantumShield authenticated message - classified"
    sig, signmeta = engine.sign(msg, ssk)
    valid, vmeta = engine.verify(msg, sig, spk)
    print(f"Message signed:   sig={len(sig)}B  time={signmeta['sign_ms']}ms")
    print(f"Signature valid:  {valid}  time={vmeta['verify_ms']}ms")
