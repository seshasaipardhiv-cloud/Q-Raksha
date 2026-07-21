"""
CBOM Crypto Pattern Definitions
Detects classical and weak cryptographic algorithms across Python, Java, JS, C/C++
"""

# ─── Python AST + import patterns ────────────────────────────────────────────

PYTHON_CRYPTO_PATTERNS = [
    # RSA
    {"pattern": r"RSA\.generate|RSA\.import_key|RSA\.construct|rsa\.generate_private_key",
     "algorithm": "RSA", "risk": "HIGH", "notes": "Vulnerable to CRQCs post-2030 est."},
    {"pattern": r"from\s+Crypto\.PublicKey\s+import\s+RSA|import\s+rsa",
     "algorithm": "RSA", "risk": "HIGH"},
    # ECDH / ECDSA
    {"pattern": r"ec\.generate_private_key|ECDH|ECDSA|ECC\.generate|elliptic",
     "algorithm": "ECDSA/ECDH", "risk": "HIGH", "notes": "Shor's algo breaks EC crypto"},
    {"pattern": r"from\s+Crypto\.PublicKey\s+import\s+ECC",
     "algorithm": "ECDSA", "risk": "HIGH"},
    # DH
    {"pattern": r"dh\.generate_parameters|DHParameters|DiffieHellman",
     "algorithm": "DH", "risk": "HIGH"},
    # DSA
    {"pattern": r"dsa\.generate_private_key|DSA\.generate",
     "algorithm": "DSA", "risk": "HIGH"},
    # Weak hashes
    {"pattern": r"hashlib\.md5|MD5\.new|\.md5\(",
     "algorithm": "MD5", "risk": "CRITICAL", "notes": "Collision attacks known"},
    {"pattern": r"hashlib\.sha1|SHA\.new|SHA1\.new|\.sha1\(",
     "algorithm": "SHA-1", "risk": "HIGH", "notes": "SHAttered collision 2017"},
    # Weak symmetric
    {"pattern": r"DES\.new|DES3\.new|3DES|TripleDES",
     "algorithm": "3DES/DES", "risk": "CRITICAL"},
    {"pattern": r"AES\.MODE_ECB|mode=AES\.MODE_ECB",
     "algorithm": "AES-ECB", "risk": "HIGH", "notes": "Deterministic, pattern-leaking"},
    {"pattern": r"AES\.MODE_CBC(?!.*PKCS)",
     "algorithm": "AES-CBC", "risk": "MEDIUM", "notes": "No authenticated encryption"},
    # RC4
    {"pattern": r"ARC4|RC4\.new|Cipher\.ARC4",
     "algorithm": "RC4", "risk": "CRITICAL"},
    # Small key sizes
    {"pattern": r"RSA\.generate\(1024|RSA\.generate\(512|RSA\.generate\(2048",
     "algorithm": "RSA-weak-key", "risk": "CRITICAL", "notes": "Key size < 3072 insufficient"},
    # TLS 1.0/1.1
    {"pattern": r"ssl\.PROTOCOL_TLSv1(?!_2)|TLSv1_0|TLSv1_1|PROTOCOL_SSLv",
     "algorithm": "TLS<1.2", "risk": "HIGH"},
    # OpenSSL via ctypes
    {"pattern": r"EVP_RSA|EVP_PKEY_RSA|RSA_generate_key",
     "algorithm": "RSA (OpenSSL)", "risk": "HIGH"},
]

JAVA_CRYPTO_PATTERNS = [
    {"pattern": r'KeyPairGenerator\.getInstance\("RSA"',
     "algorithm": "RSA", "risk": "HIGH"},
    {"pattern": r'KeyPairGenerator\.getInstance\("EC"',
     "algorithm": "ECDSA/ECDH", "risk": "HIGH"},
    {"pattern": r'KeyAgreement\.getInstance\("DH"',
     "algorithm": "DH", "risk": "HIGH"},
    {"pattern": r'MessageDigest\.getInstance\("MD5"',
     "algorithm": "MD5", "risk": "CRITICAL"},
    {"pattern": r'MessageDigest\.getInstance\("SHA-1"',
     "algorithm": "SHA-1", "risk": "HIGH"},
    {"pattern": r'Cipher\.getInstance\("DES',
     "algorithm": "DES", "risk": "CRITICAL"},
    {"pattern": r'Cipher\.getInstance\("AES/ECB',
     "algorithm": "AES-ECB", "risk": "HIGH"},
    {"pattern": r'SSLContext\.getInstance\("TLSv1\.\s*[01]"',
     "algorithm": "TLS<1.2", "risk": "HIGH"},
]

C_CPP_PATTERNS = [
    {"pattern": r"RSA_generate_key|RSA_new|EVP_PKEY_RSA",
     "algorithm": "RSA (OpenSSL)", "risk": "HIGH"},
    {"pattern": r"EC_KEY_new|EC_GROUP_new|ECDSA_sign",
     "algorithm": "ECDSA", "risk": "HIGH"},
    {"pattern": r"DH_new|DH_generate_parameters",
     "algorithm": "DH", "risk": "HIGH"},
    {"pattern": r"MD5_Init|MD5_Update|MD5_Final|EVP_md5",
     "algorithm": "MD5", "risk": "CRITICAL"},
    {"pattern": r"SHA1_Init|SHA1_Update|SHA1_Final|EVP_sha1",
     "algorithm": "SHA-1", "risk": "HIGH"},
    {"pattern": r"DES_ecb_encrypt|DES_cbc_encrypt|EVP_des",
     "algorithm": "DES", "risk": "CRITICAL"},
    {"pattern": r"RC4_set_key|EVP_rc4",
     "algorithm": "RC4", "risk": "CRITICAL"},
]

JS_TS_PATTERNS = [
    {"pattern": r'generateKeyPair\(\s*[\'"]rsa[\'"]|createSign\(\s*[\'"]RSA',
     "algorithm": "RSA", "risk": "HIGH"},
    {"pattern": r'generateKeyPair\(\s*[\'"]ec[\'"]',
     "algorithm": "ECDSA/ECDH", "risk": "HIGH"},
    {"pattern": r"createHash\(\s*['\"]md5",
     "algorithm": "MD5", "risk": "CRITICAL"},
    {"pattern": r"createHash\(\s*['\"]sha1",
     "algorithm": "SHA-1", "risk": "HIGH"},
    {"pattern": r"createCipheriv\(\s*['\"]des",
     "algorithm": "DES", "risk": "CRITICAL"},
    {"pattern": r"createCipheriv\(\s*['\"]aes.*ecb",
     "algorithm": "AES-ECB", "risk": "HIGH"},
]

# Map file extensions to pattern sets
LANGUAGE_MAP = {
    ".py": ("Python", PYTHON_CRYPTO_PATTERNS),
    ".pyw": ("Python", PYTHON_CRYPTO_PATTERNS),
    ".java": ("Java", JAVA_CRYPTO_PATTERNS),
    ".c": ("C/C++", C_CPP_PATTERNS),
    ".cpp": ("C/C++", C_CPP_PATTERNS),
    ".h": ("C/C++", C_CPP_PATTERNS),
    ".hpp": ("C/C++", C_CPP_PATTERNS),
    ".js": ("JavaScript", JS_TS_PATTERNS),
    ".ts": ("TypeScript", JS_TS_PATTERNS),
    ".jsx": ("JavaScript", JS_TS_PATTERNS),
    ".tsx": ("TypeScript", JS_TS_PATTERNS),
}

RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Algorithms safe for post-quantum (whitelist)
PQC_SAFE = {
    "KYBER", "DILITHIUM", "FALCON", "SPHINCS", "CRYSTALS",
    "ML-KEM", "ML-DSA", "AES-GCM", "AES-256", "SHA-3", "SHA-256", "SHA-512",
    "CHACHA20-POLY1305",
}
