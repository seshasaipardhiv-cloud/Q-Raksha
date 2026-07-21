"""
Legacy Crypto Sample — CBOM Scanner Test Fixture
This file intentionally uses quantum-vulnerable cryptographic primitives
to demonstrate CBOM detection capabilities.
DO NOT USE IN PRODUCTION.
"""
# ─── RSA Key Generation (VULNERABLE) ─────────────────────────────────────────
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import MD5, SHA1
import hashlib
import ssl

# RSA-2048 key generation — vulnerable to Shor's algorithm
rsa_key = RSA.generate(2048)
rsa_key_small = RSA.generate(1024)   # Also too small by classical standards

# ─── ECDSA (VULNERABLE) ───────────────────────────────────────────────────────
from cryptography.hazmat.primitives.asymmetric import ec
ec_key = ec.generate_private_key(ec.SECP256R1())

# ─── Diffie-Hellman (VULNERABLE) ─────────────────────────────────────────────
from cryptography.hazmat.primitives.asymmetric import dh
dh_params = dh.generate_parameters(generator=2, key_size=2048)
dh_private = dh_params.generate_private_key()

# ─── Broken Hashes ───────────────────────────────────────────────────────────
md5_hash = hashlib.md5(b"sensitive_data").hexdigest()
sha1_hash = hashlib.sha1(b"sensitive_data").hexdigest()

# ─── Weak Symmetric (VULNERABLE) ─────────────────────────────────────────────
from Crypto.Cipher import DES3, ARC4
# 3DES — deprecated since NIST SP 800-131A Rev 2
cipher_3des = DES3.new(b"12345678901234567890123", DES3.MODE_ECB)

# RC4 — broken stream cipher
rc4_cipher = ARC4.new(b"weakkey")

# ─── AES-ECB (VULNERABLE pattern) ────────────────────────────────────────────
from Crypto.Cipher import AES
aes_ecb = AES.new(b"0" * 16, AES.MODE_ECB)   # ECB mode — deterministic, leaks patterns
aes_cbc = AES.new(b"0" * 16, AES.MODE_CBC, iv=b"0" * 16)  # CBC — no auth

# ─── Insecure TLS ─────────────────────────────────────────────────────────────
# TLS 1.0/1.1 — deprecated
ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

# ─── What SHOULD be used instead (safe algorithms, not flagged) ───────────────
# from pqc.engine import engine
# pk, sk, _ = engine.kem_keygen()    # Kyber768 — NIST ML-KEM ✅
# sig_pk, sig_sk, _ = engine.sig_keygen()  # Dilithium3 — NIST ML-DSA ✅
# sha3_hash = hashlib.sha3_256(b"sensitive_data").hexdigest()  # SHA-3 ✅
# Modern: AES-256-GCM, ChaCha20-Poly1305, TLS 1.3 with PQC ✅
