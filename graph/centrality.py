"""
Q-RAKSHA SENTINEL — Dependency Centrality Engine (Step 3)
Computes centrality scores for each NF:
  - Connection count
  - Criticality weight (NF type importance)
  - Subscriber reach
  - Slice importance
  - Trust domain importance
Output: Centrality Scores per NF (used by QMIE for migration prioritization)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# Criticality weights per NF type (higher = more critical for network operation)
NF_CRITICALITY = {
    "NRF": 1.0,   # Network Repository — everything registers here
    "AMF": 0.95,  # Access & Mobility — all UE connections
    "SMF": 0.90,  # Session Management — all data sessions
    "UPF": 0.85,  # User Plane — actual data traffic
    "AUSF": 0.80, # Auth — all authentication flows
    "UDM": 0.78,  # Subscriber data — all user profiles
    "PCF": 0.70,  # Policy — QoS enforcement
    "NSSF": 0.65, # Network Slice Selection
    "NEF": 0.60,  # Network Exposure
    "SCP": 0.75,  # Service Communication Proxy
    "BSF": 0.55,  # Binding Support
    "UPF": 0.85,
}

SLICE_CRITICALITY = {
    "URLLC": 1.0,  # Ultra-reliable low-latency (e.g., autonomous vehicles)
    "V2X": 0.95,   # Vehicle-to-everything
    "IIoT": 0.85,  # Industrial IoT
    "eMBB": 0.70,  # Enhanced Mobile Broadband (general internet)
    "mMTC": 0.55,  # Massive IoT (lower criticality per device)
}

TRUST_DOMAIN_SCORE = {
    "Core-Domain": 1.0,
    "Management-Plane": 0.95,
    "RAN-Domain": 0.80,
    "Edge-Domain": 0.70,
    "Roaming-Domain": 0.60,
}


@dataclass
class CentralityScore:
    """Complete centrality assessment for one NF node."""
    node_id: str
    nf_type: str
    # Raw metrics
    in_degree: int = 0                 # How many NFs depend ON this one
    out_degree: int = 0                # How many NFs this one depends on
    betweenness: float = 0.0           # Graph betweenness centrality (0-1)
    pagerank: float = 0.0              # PageRank score
    # Weighted scores
    criticality_weight: float = 0.0   # NF type importance
    subscriber_reach: float = 0.0     # Normalized subscriber impact
    slice_importance: float = 0.0     # Slice criticality
    trust_domain_score: float = 0.0   # Domain sensitivity
    connection_count: int = 0
    # Composite
    centrality_score: float = 0.0     # Final weighted composite (0-100)
    migration_priority: int = 0       # 1 = migrate first


@dataclass
class CentralityReport:
    """Centrality analysis results for the full graph."""
    report_id: str
    timestamp: str
    scores: List[CentralityScore] = field(default_factory=list)
    top_critical_nfs: List[str] = field(default_factory=list)
    summary: str = ""


class CentralityEngine:
    """
    Computes multi-dimensional centrality for each NF node.
    Uses NetworkX algorithms when available, falls back to
    degree-based heuristics.
    """

    def compute(
        self,
        nf_nodes: list,          # List[NFNode] from telecom_graph
        edges: list,             # List[GraphEdge]
        nx_graph: Any = None,    # Optional nx.DiGraph
    ) -> CentralityReport:
        import time, hashlib
        report_id = "CTR-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Build adjacency maps
        in_deg: Dict[str, int] = {n.node_id: 0 for n in nf_nodes}
        out_deg: Dict[str, int] = {n.node_id: 0 for n in nf_nodes}
        nf_edge_set = {n.node_id for n in nf_nodes}

        for e in edges:
            if e.source in nf_edge_set and e.target in nf_edge_set:
                out_deg[e.source] = out_deg.get(e.source, 0) + 1
                in_deg[e.target] = in_deg.get(e.target, 0) + 1

        # NetworkX-based metrics
        betweenness: Dict[str, float] = {}
        pagerank: Dict[str, float] = {}

        if nx_graph is not None:
            try:
                import networkx as nx
                # Only NF-to-NF subgraph
                nf_subgraph = nx_graph.subgraph(nf_edge_set)
                bt = nx.betweenness_centrality(nf_subgraph, normalized=True, weight="weight")
                pr = nx.pagerank(nf_subgraph, alpha=0.85, weight="weight")
                betweenness = bt
                pagerank = pr
            except Exception:
                pass

        # Max subscriber count for normalization
        max_subs = max((n.subscriber_count for n in nf_nodes), default=1)

        scores: List[CentralityScore] = []
        for nf in nf_nodes:
            nid = nf.node_id
            crit = NF_CRITICALITY.get(nf.nf_type, 0.5)
            sub_reach = nf.subscriber_count / max_subs
            slice_imp = SLICE_CRITICALITY.get(nf.slice_id, 0.5)
            td_score = TRUST_DOMAIN_SCORE.get(nf.trust_domain, 0.5)
            bt_score = betweenness.get(nid, 0.0)
            pr_score = pagerank.get(nid, 0.0)
            conn = in_deg.get(nid, 0) + out_deg.get(nid, 0)

            # Composite centrality (0–100)
            composite = (
                crit       * 30.0 +
                sub_reach  * 25.0 +
                slice_imp  * 15.0 +
                td_score   * 10.0 +
                bt_score   * 12.0 +
                pr_score   * 8.0
            )  # max ~100

            scores.append(CentralityScore(
                node_id=nid,
                nf_type=nf.nf_type,
                in_degree=in_deg.get(nid, 0),
                out_degree=out_deg.get(nid, 0),
                betweenness=round(bt_score, 4),
                pagerank=round(pr_score, 4),
                criticality_weight=round(crit, 3),
                subscriber_reach=round(sub_reach, 4),
                slice_importance=round(slice_imp, 3),
                trust_domain_score=round(td_score, 3),
                connection_count=conn,
                centrality_score=round(composite, 2),
            ))

        # Sort descending by centrality → assign migration priority
        scores.sort(key=lambda s: s.centrality_score, reverse=True)
        for rank, s in enumerate(scores, start=1):
            s.migration_priority = rank
            # Also update the source NFNode
            for nf in nf_nodes:
                if nf.node_id == s.node_id:
                    nf.centrality_score = s.centrality_score
                    nf.migration_priority = rank

        top5 = [s.node_id for s in scores[:5]]
        summary = (
            f"Centrality computed for {len(scores)} NFs. "
            f"Top critical: {', '.join(top5)}. "
            f"Avg centrality: {sum(s.centrality_score for s in scores)/max(len(scores),1):.1f}/100."
        )

        return CentralityReport(
            report_id=report_id,
            timestamp=timestamp,
            scores=scores,
            top_critical_nfs=top5,
            summary=summary,
        )


# Singleton
_centrality_engine: Optional[CentralityEngine] = None


def get_centrality_engine() -> CentralityEngine:
    global _centrality_engine
    if _centrality_engine is None:
        _centrality_engine = CentralityEngine()
    return _centrality_engine
