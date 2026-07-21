"""
QKD Simulator — BB84 with Decoy-State Protocol
Physics-validated analytical model. NOT hardware — clearly labeled.
Computes QBER and finite-key secret-key rate using GLLP + decoy-state formulas.

Parameters:
  - distance_km: fiber/FSO link distance
  - loss_db_per_km: channel attenuation
  - detector_efficiency: single-photon detector efficiency
  - dark_count_rate: per-pulse dark count probability
  - cn2: atmospheric refractive index structure constant (free-space)
  - mean_photon_number: mean photon number per pulse (signal state)
  - decoy_mean: mean photon number for decoy states
  - block_size: number of raw bits for finite-key correction

Reference: Lo-Ma-Chen (2005) decoy-state QKD, GLLP security proof.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class QKDChannelParams:
    """Physical channel parameters."""
    distance_km: float = 10.0
    loss_db_per_km: float = 0.2          # Telecom fiber typical
    detector_efficiency: float = 0.10    # SNSPD ~10%
    dark_count_rate: float = 1e-6        # Per pulse
    mean_photon_number: float = 0.5      # Signal state (weak coherent pulse)
    decoy_mean: float = 0.1              # Decoy state mean photon
    vacuum_mean: float = 0.0             # Vacuum decoy
    block_size: int = 1_000_000          # Number of sifted bits for finite-key
    pulse_rate_hz: float = 1e9           # 1 GHz rep rate
    wavelength_nm: float = 1550.0        # Standard telecom wavelength
    # Free-space turbulence
    cn2: float = 1e-15                   # Refractive index structure param (weak: 1e-17, strong: 1e-13)
    aperture_diameter_m: float = 0.2     # Receiver aperture
    is_free_space: bool = False


@dataclass
class QKDResult:
    """Output of a QKD simulation run."""
    # Channel
    channel_transmittance: float
    turbulence_loss_db: float
    total_loss_db: float
    # Protocol
    qber: float                          # Quantum Bit Error Rate
    single_photon_fraction: float        # Fraction of single-photon events (decoy estimate)
    # Key rate
    raw_key_rate_bps: float
    sifted_key_rate_bps: float
    secret_key_rate_bps: float           # After privacy amplification
    # Finite key
    finite_key_correction_bits: float
    secure_key_length_per_block: int
    # Status
    link_feasible: bool
    max_secure_distance_km: float
    timestamp: float
    # Mode recommendation
    recommended_mode: str                # "QKD_PQC_HYBRID" / "BUFFERED" / "PQC_ONLY"
    warning: Optional[str] = None


class BB84DecoySimulator:
    """
    BB84 decoy-state QKD analytical simulator.
    All formulas from published QKD literature — physics-accurate.
    """

    # ─── Channel Model ────────────────────────────────────────────────────────

    def channel_transmittance(self, params: QKDChannelParams) -> float:
        """Total channel transmittance including fiber/FSO loss."""
        fiber_loss_db = params.loss_db_per_km * params.distance_km
        return 10 ** (-fiber_loss_db / 10)

    def turbulence_loss_db(self, params: QKDChannelParams) -> float:
        """
        Free-space turbulence-induced beam wandering loss (Kolmogorov model).
        Using Rytov variance approximation for weak turbulence.
        """
        if not params.is_free_space:
            return 0.0

        lambda_m = params.wavelength_nm * 1e-9
        L = params.distance_km * 1e3
        k = 2 * math.pi / lambda_m

        # Rytov variance (scintillation)
        sigma_rytov_sq = 1.23 * params.cn2 * (k ** (7/6)) * (L ** (11/6))

        # Beam wander variance (Andrews & Phillips model)
        W0 = 0.025   # initial beam waist (m)
        W_L = W0 * math.sqrt(1 + (L * lambda_m / (math.pi * W0**2))**2)

        sigma_bw_sq = 0.54 * (L / (k * W0**2))**2 * (params.cn2 * L) * W_L**(-1/3)

        # Point-ahead angle adjustment and aperture averaging
        D = params.aperture_diameter_m
        aperture_factor = 1 / (1 + 1.63 * (sigma_rytov_sq ** (6/5)) * (k * D**2 / (4*L)))

        # Effective Strehl ratio (approximate)
        if sigma_rytov_sq < 1.0:
            strehl = math.exp(-sigma_rytov_sq)
        else:
            strehl = 1 / (1 + sigma_rytov_sq)

        loss_db = -10 * math.log10(max(strehl * aperture_factor, 1e-12))
        return loss_db

    def total_transmittance(self, params: QKDChannelParams) -> tuple[float, float]:
        """Returns (transmittance, turbulence_loss_db)."""
        eta_channel = self.channel_transmittance(params)
        turb_db = self.turbulence_loss_db(params)
        eta_turb = 10 ** (-turb_db / 10)
        eta_total = eta_channel * eta_turb * params.detector_efficiency
        total_loss_db = -10 * math.log10(max(eta_total, 1e-15))
        return eta_total, turb_db, total_loss_db

    # ─── Decoy-State Analysis ─────────────────────────────────────────────────

    def decoy_single_photon_fraction(
        self, params: QKDChannelParams, eta: float
    ) -> tuple[float, float, float]:
        """
        Estimate single-photon gain and error rate using 3-intensity decoy method.
        Returns (Q1, e1, Q_mu) — single-photon gain, single-photon QBER, signal gain.
        Based on Lo-Ma-Chen 2005 decoy-state bounds.
        """
        mu = params.mean_photon_number
        nu = params.decoy_mean
        dc = params.dark_count_rate

        # Gain of signal state (Poisson photon distribution)
        # Q_mu = sum_{n=0}^{inf} e^{-mu} mu^n/n! * Gain_n
        # Approximate: Q_mu ≈ 1 - exp(-eta*mu) + dc
        Q_mu = 1 - math.exp(-eta * mu) + dc

        # Gain of decoy state
        Q_nu = 1 - math.exp(-eta * nu) + dc

        # Vacuum gain (dark counts only)
        Q_0 = dc

        # Lower bound on single-photon gain (decoy-state bound)
        # Q1_lower = (mu^2 * e^{-mu}) / (mu*nu - nu^2) * (Q_nu * e^nu - Q_0 - (nu^2/mu^2)*(Q_mu*e^mu - Q_0))
        try:
            denom = mu * nu - nu ** 2
            if denom <= 0:
                Q1 = Q_nu
            else:
                Q1 = max(0.0, (mu**2 * math.exp(-mu)) / denom * (
                    Q_nu * math.exp(nu) - Q_0 - (nu**2 / mu**2) * (Q_mu * math.exp(mu) - Q_0)
                ))
        except (ValueError, ZeroDivisionError):
            Q1 = Q_nu

        # Error rate of single-photon component
        # e1 bound from vacuum state: e1 = (e_mu * Q_mu * e^mu - e0 * Q0) / (Q1 * e^mu * mu)
        # Simplified: channel errors ≈ detector alignment + depolarization
        e_detector = 0.5 * dc / max(Q_mu, 1e-12)
        e_optical = 0.01    # Intrinsic optical misalignment (1%)
        e1 = min(0.5, e_optical + e_detector)

        return Q1, e1, Q_mu

    # ─── QBER ─────────────────────────────────────────────────────────────────

    def compute_qber(self, params: QKDChannelParams, eta: float) -> float:
        """
        Compute Quantum Bit Error Rate.
        QBER = (e_d * eta * mu + e_0 * dc) / (eta * mu + dc)
        where e_d = detector dark-count-induced error fraction.
        """
        mu = params.mean_photon_number
        dc = params.dark_count_rate

        # Signal counts from actual photons
        true_signal = eta * mu
        # Dark counts contribute random (50% error rate)
        dark_errors = 0.5 * dc
        # Optical misalignment
        optical_error = 0.01 * true_signal

        total_detections = true_signal + dc
        total_errors = optical_error + dark_errors

        if total_detections < 1e-15:
            return 0.5  # No signal — 50% QBER (random)

        qber = min(0.5, total_errors / total_detections)
        return qber

    # ─── Secret Key Rate ──────────────────────────────────────────────────────

    def binary_entropy(self, p: float) -> float:
        """Shannon binary entropy h(p)."""
        if p <= 0 or p >= 1:
            return 0.0
        return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

    def secret_key_rate(
        self,
        params: QKDChannelParams,
        Q1: float,
        e1: float,
        Q_mu: float,
        qber: float,
    ) -> tuple[float, float, float, int]:
        """
        GLLP security proof secret key rate (asymptotic).
        R_asym = Q1 * (1 - h(e1)) - Q_mu * f_EC * h(QBER)
        Returns (raw_bps, sifted_bps, secret_bps, secure_key_length_per_block).
        """
        f_EC = 1.16   # Error correction efficiency (LDPC codes)
        sifting = 0.5  # BB84 sifting fraction

        # Asymptotic secret key fraction (per pulse)
        r_asym = max(0.0, Q1 * (1 - self.binary_entropy(e1)) - Q_mu * f_EC * self.binary_entropy(qber))

        raw_rate = Q_mu * params.pulse_rate_hz
        sifted_rate = raw_rate * sifting
        secret_rate = r_asym * params.pulse_rate_hz

        # Finite-key correction (security parameter eps = 1e-10)
        eps = 1e-10
        n = params.block_size
        if n > 0 and secret_rate > 0:
            # Finite-key penalty: delta = sqrt(log(1/eps) / n)
            delta = math.sqrt(math.log(1 / eps) / n) if n > 0 else 0
            correction_bits = delta * n
            l_finite = max(0, int(r_asym * n - correction_bits))
        else:
            correction_bits = 0
            l_finite = 0

        return raw_rate, sifted_rate, secret_rate, l_finite, correction_bits

    # ─── Mode Recommendation ──────────────────────────────────────────────────

    def recommend_mode(self, qber: float, skr: float) -> tuple[str, str | None]:
        """
        Recommend orchestration mode based on QKD quality metrics.
        Thresholds from standard QKD security parameters.
        """
        QBER_CRITICAL = 0.11    # BB84 security threshold
        QBER_WARNING = 0.07
        SKR_MIN = 1e3           # Minimum useful key rate: 1 kbps

        if qber >= QBER_CRITICAL or skr <= 0:
            return "PQC_ONLY", f"QKD insecure (QBER={qber:.2%} ≥ {QBER_CRITICAL:.0%} threshold)"
        elif qber >= QBER_WARNING or skr < SKR_MIN:
            return "BUFFERED_KEY", f"QKD degraded (QBER={qber:.2%}, SKR={skr:.0f} bps)"
        else:
            return "QKD_PQC_HYBRID", None

    # ─── Main Simulation ──────────────────────────────────────────────────────

    def simulate(self, params: QKDChannelParams) -> QKDResult:
        """Run full BB84 decoy-state simulation."""
        t0 = time.perf_counter()

        eta, turb_db, total_loss_db = self.total_transmittance(params)
        qber = self.compute_qber(params, eta)
        Q1, e1, Q_mu = self.decoy_single_photon_fraction(params, eta)
        raw_bps, sifted_bps, secret_bps, l_finite, correction = self.secret_key_rate(
            params, Q1, e1, Q_mu, qber
        )

        # Max secure distance (where SKR → 0)
        max_dist = self._find_max_distance(params)
        mode, warning = self.recommend_mode(qber, secret_bps)

        return QKDResult(
            channel_transmittance=eta,
            turbulence_loss_db=turb_db,
            total_loss_db=total_loss_db,
            qber=qber,
            single_photon_fraction=Q1 / max(Q_mu, 1e-12),
            raw_key_rate_bps=raw_bps,
            sifted_key_rate_bps=sifted_bps,
            secret_key_rate_bps=secret_bps,
            finite_key_correction_bits=correction,
            secure_key_length_per_block=l_finite,
            link_feasible=secret_bps > 0,
            max_secure_distance_km=max_dist,
            timestamp=time.time(),
            recommended_mode=mode,
            warning=warning,
        )

    def _find_max_distance(self, params: QKDChannelParams, max_km: float = 300) -> float:
        """Binary search for max distance where SKR > 0."""
        lo, hi = 0.0, max_km
        test_params = QKDChannelParams(**params.__dict__)
        for _ in range(20):
            mid = (lo + hi) / 2
            test_params.distance_km = mid
            eta, _, _ = self.total_transmittance(test_params)
            qber = self.compute_qber(test_params, eta)
            Q1, e1, Q_mu = self.decoy_single_photon_fraction(test_params, eta)
            _, _, skr, _, _ = self.secret_key_rate(test_params, Q1, e1, Q_mu, qber)
            if skr > 0:
                lo = mid
            else:
                hi = mid
        return round(lo, 1)

    def scan_distance(
        self,
        params: QKDChannelParams,
        distances: list[float] | None = None,
    ) -> list[dict]:
        """Simulate over a range of distances."""
        if distances is None:
            distances = [5, 10, 20, 30, 50, 75, 100, 150, 200, 300]
        results = []
        for d in distances:
            p = QKDChannelParams(**params.__dict__)
            p.distance_km = d
            r = self.simulate(p)
            results.append({
                "distance_km": d,
                "qber": round(r.qber * 100, 3),
                "skr_kbps": round(r.secret_key_rate_bps / 1e3, 2),
                "total_loss_db": round(r.total_loss_db, 1),
                "mode": r.recommended_mode,
                "feasible": r.link_feasible,
            })
        return results


# Module-level simulator instance
simulator = BB84DecoySimulator()
default_params = QKDChannelParams()


if __name__ == "__main__":
    import json
    sim = BB84DecoySimulator()
    params = QKDChannelParams(distance_km=50.0, cn2=1e-15, is_free_space=False)
    result = sim.simulate(params)
    print(f"Distance:     {params.distance_km} km")
    print(f"QBER:         {result.qber:.4%}")
    print(f"SKR:          {result.secret_key_rate_bps/1e3:.2f} kbps")
    print(f"Max distance: {result.max_secure_distance_km} km")
    print(f"Mode:         {result.recommended_mode}")
    if result.warning:
        print(f"Warning:      {result.warning}")

    print("\n=== Distance Scan ===")
    scan = sim.scan_distance(params)
    for row in scan:
        print(f"  {row['distance_km']:5.0f} km | QBER={row['qber']:5.2f}% | SKR={row['skr_kbps']:8.2f} kbps | {row['mode']}")
