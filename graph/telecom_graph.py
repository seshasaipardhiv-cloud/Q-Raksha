"""
Q-RAKSHA SENTINEL — Telecom Knowledge Graph (Step 2)
Builds a Neo4j-compatible graph (NetworkX in-memory) of:
  - Network Functions (AMF, SMF, UPF, NRF, UDM, etc.)
  - Certificates, APIs, Vendors, Slices, Subscriptions
  - Edges: Trust, Depends, Uses, Auth, Exposed
"""
from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False


# ─── Node / Edge type definitions ─────────────────────────────────────────────

NF_TYPES = ["AMF", "SMF", "UPF", "NRF", "UDM", "AUSF", "PCF", "NEF", "NSSF", "BSF", "SCP"]

ALGO_VULNERABLE  = ["RSA-2048", "ECDSA-P256", "DH-2048", "RSA-4096", "ECDH-P384"]
ALGO_PQC_READY   = ["ML-KEM-768", "ML-DSA-65", "SLH-DSA-128f", "FN-DSA-512"]
ALGO_TRANSITION  = ["RSA-4096+Kyber768", "ECDSA+Dilithium3"]

VENDORS = ["Ericsson", "Nokia", "Huawei", "ZTE", "Samsung", "Mavenir", "Radisys"]
SLICES  = ["eMBB", "URLLC", "mMTC", "V2X", "IIoT"]

TRUST_DOMAINS = ["Core-Domain", "RAN-Domain", "Edge-Domain", "Roaming-Domain", "Management-Plane"]


@dataclass
class NFNode:
    """A 5G Network Function node in the Knowledge Graph."""
    node_id: str
    nf_type: str                  # AMF, SMF, UPF ...
    vendor: str
    version: str
    slice_id: str
    trust_domain: str
    cert_algorithm: str           # Current crypto algorithm
    cert_expiry_days: int
    api_count: int
    subscriber_count: int         # Subscribers affected if this NF goes down
    pqc_ready: bool
    risk_score: float = 0.0
    centrality_score: float = 0.0
    migration_priority: int = 0   # 1 = highest


@dataclass
class CertNode:
    """A certificate node."""
    node_id: str
    subject_cn: str
    algorithm: str
    key_size: int
    expiry_days: int
    issuer: str
    is_quantum_safe: bool


@dataclass
class GraphEdge:
    """An edge in the Knowledge Graph."""
    source: str
    target: str
    edge_type: str        # TRUST / DEPENDS / USES / AUTH / EXPOSED
    weight: float = 1.0
    tls_version: str = "TLS1.3"
    cipher_suite: str = "TLS_AES_256_GCM_SHA384"


@dataclass
class TelecomGraph:
    """Complete Telecom Knowledge Graph."""
    graph_id: str
    timestamp: str
    nf_nodes: List[NFNode] = field(default_factory=list)
    cert_nodes: List[CertNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    summary: str = ""


# ─── Graph Builder ────────────────────────────────────────────────────────────

class TelecomKnowledgeGraph:
    """
    Builds and manages the Telecom Knowledge Graph.
    Models a realistic Open5GS/OpenAirInterface deployment
    with multi-vendor NFs, slices, and crypto inventory.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._graph: Optional[Any] = None   # nx.DiGraph if available
        self._nf_nodes: Dict[str, NFNode] = {}
        self._cert_nodes: Dict[str, CertNode] = {}
        self._edges: List[GraphEdge] = []
        self._built = False

    # ─── Public API ───────────────────────────────────────────────────────────

    def build(self, num_nfs: int = 24, seed: int | None = None) -> TelecomGraph:
        """Build the full Telecom Knowledge Graph from scratch."""
        if seed is not None:
            self._rng = random.Random(seed)

        self._nf_nodes.clear()
        self._cert_nodes.clear()
        self._edges.clear()

        # Step 1: Spawn NF nodes
        self._spawn_nf_nodes(num_nfs)

        # Step 2: Spawn certificate nodes
        self._spawn_cert_nodes()

        # Step 3: Spawn edges (topology)
        self._spawn_edges()

        # Step 4: Build NetworkX graph if available
        if NX_AVAILABLE:
            self._build_nx_graph()

        self._built = True

        graph_id = "KG-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return TelecomGraph(
            graph_id=graph_id,
            timestamp=timestamp,
            nf_nodes=list(self._nf_nodes.values()),
            cert_nodes=list(self._cert_nodes.values()),
            edges=self._edges,
            node_count=len(self._nf_nodes) + len(self._cert_nodes),
            edge_count=len(self._edges),
            summary=(
                f"Built Knowledge Graph with {len(self._nf_nodes)} NFs, "
                f"{len(self._cert_nodes)} certificates, {len(self._edges)} edges. "
                f"Quantum-vulnerable NFs: {sum(1 for n in self._nf_nodes.values() if not n.pqc_ready)}."
            ),
        )

    def get_nx_graph(self) -> Any:
        """Return the NetworkX DiGraph (None if networkx not installed)."""
        return self._graph

    def get_nf_nodes(self) -> List[NFNode]:
        return list(self._nf_nodes.values())

    def get_adjacency(self) -> Dict[str, List[str]]:
        """Return adjacency list for each NF."""
        adj: Dict[str, List[str]] = {nid: [] for nid in self._nf_nodes}
        for e in self._edges:
            if e.source in adj:
                adj[e.source].append(e.target)
        return adj

    def to_dict(self) -> dict:
        """Serialize graph for JSON export."""
        return {
            "nf_nodes": [asdict(n) for n in self._nf_nodes.values()],
            "cert_nodes": [asdict(c) for c in self._cert_nodes.values()],
            "edges": [asdict(e) for e in self._edges],
        }

    # ─── Internal builders ────────────────────────────────────────────────────

    def _spawn_nf_nodes(self, num_nfs: int):
        """Create NF nodes representing a realistic 5G core deployment."""
        # Ensure each mandatory NF type appears at least once
        mandatory = ["AMF", "SMF", "UPF", "NRF", "UDM", "AUSF"]
        nf_types_pool = mandatory + self._rng.choices(NF_TYPES, k=max(0, num_nfs - len(mandatory)))
        self._rng.shuffle(nf_types_pool)

        for i, nf_type in enumerate(nf_types_pool[:num_nfs]):
            node_id = f"{nf_type}-{i+1:02d}"
            algo = self._rng.choices(
                ALGO_VULNERABLE + ALGO_PQC_READY,
                weights=[0.65] * len(ALGO_VULNERABLE) + [0.35] * len(ALGO_PQC_READY),
            )[0]
            pqc_ready = algo in ALGO_PQC_READY
            node = NFNode(
                node_id=node_id,
                nf_type=nf_type,
                vendor=self._rng.choice(VENDORS),
                version=f"{self._rng.randint(1,3)}.{self._rng.randint(0,9)}.{self._rng.randint(0,9)}",
                slice_id=self._rng.choice(SLICES),
                trust_domain=self._rng.choice(TRUST_DOMAINS),
                cert_algorithm=algo,
                cert_expiry_days=self._rng.randint(30, 730),
                api_count=self._rng.randint(3, 25),
                subscriber_count=self._rng.randint(1_000, 10_000_000),
                pqc_ready=pqc_ready,
                risk_score=0.0,  # computed later by QMIE
            )
            self._nf_nodes[node_id] = node

    def _spawn_cert_nodes(self):
        """Create certificate nodes for each NF."""
        for nf_id, nf in self._nf_nodes.items():
            cert_id = f"CERT-{nf_id}"
            is_qs = nf.cert_algorithm in ALGO_PQC_READY
            self._cert_nodes[cert_id] = CertNode(
                node_id=cert_id,
                subject_cn=f"{nf_id}.5gc.operator.net",
                algorithm=nf.cert_algorithm,
                key_size=768 if "KEM" in nf.cert_algorithm else 2048,
                expiry_days=nf.cert_expiry_days,
                issuer="Operator-Root-CA",
                is_quantum_safe=is_qs,
            )
            # Edge: NF → uses → CERT
            self._edges.append(GraphEdge(
                source=nf_id, target=cert_id, edge_type="USES",
                weight=1.0, tls_version="TLS1.3",
                cipher_suite="TLS_AES_256_GCM_SHA384",
            ))

    def _spawn_edges(self):
        """Build realistic 5G topology edges between NFs."""
        nf_ids = list(self._nf_nodes.keys())

        # Known 5G SBA dependencies
        core_deps = [
            ("AMF", "NRF", "DEPENDS", 1.0),
            ("AMF", "AUSF", "AUTH", 0.95),
            ("AMF", "UDM", "AUTH", 0.9),
            ("AMF", "SMF", "DEPENDS", 0.9),
            ("SMF", "UPF", "DEPENDS", 1.0),
            ("SMF", "NRF", "DEPENDS", 0.9),
            ("SMF", "UDM", "DEPENDS", 0.8),
            ("PCF", "NRF", "DEPENDS", 0.9),
            ("PCF", "UDM", "DEPENDS", 0.8),
            ("NEF", "NRF", "EXPOSED", 0.7),
            ("AUSF", "UDM", "AUTH", 0.95),
            ("NSSF", "NRF", "DEPENDS", 0.85),
        ]

        for src_type, tgt_type, etype, weight in core_deps:
            src_nodes = [nid for nid, n in self._nf_nodes.items() if n.nf_type == src_type]
            tgt_nodes = [nid for nid, n in self._nf_nodes.items() if n.nf_type == tgt_type]
            for s in src_nodes:
                for t in tgt_nodes:
                    if s != t:
                        tls = self._rng.choice(["TLS1.2", "TLS1.3"])
                        cipher = ("TLS_AES_256_GCM_SHA384" if tls == "TLS1.3"
                                  else self._rng.choice(["TLS_ECDHE_RSA_AES256_GCM", "TLS_RSA_AES256_CBC"]))
                        self._edges.append(GraphEdge(
                            source=s, target=t, edge_type=etype,
                            weight=weight, tls_version=tls, cipher_suite=cipher,
                        ))

        # Random additional trust relationships
        for _ in range(max(0, len(nf_ids) // 2)):
            s, t = self._rng.sample(nf_ids, 2)
            self._edges.append(GraphEdge(
                source=s, target=t, edge_type="TRUST",
                weight=self._rng.uniform(0.3, 0.8),
                tls_version=self._rng.choice(["TLS1.2", "TLS1.3"]),
            ))

    def _build_nx_graph(self):
        """Build NetworkX DiGraph for centrality/path analysis."""
        G = nx.DiGraph()
        for nid, nf in self._nf_nodes.items():
            G.add_node(nid, **asdict(nf))
        for e in self._edges:
            if e.source in self._nf_nodes and e.target in self._nf_nodes:
                G.add_edge(e.source, e.target, weight=e.weight, edge_type=e.edge_type)
        self._graph = G


# Singleton
_kg_instance: Optional[TelecomKnowledgeGraph] = None


def get_knowledge_graph() -> TelecomKnowledgeGraph:
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = TelecomKnowledgeGraph()
    return _kg_instance


if __name__ == "__main__":
    kg = TelecomKnowledgeGraph()
    g = kg.build(num_nfs=24)
    print(f"Graph built: {g.summary}")
    print(f"  Nodes: {g.node_count}, Edges: {g.edge_count}")
    for nf in g.nf_nodes[:5]:
        print(f"  {nf.node_id} ({nf.nf_type}) | {nf.cert_algorithm} | PQC: {nf.pqc_ready}")
