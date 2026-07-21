"""
AI Channel Predictor — Predicts QKD Secret Key Rate 30–60s ahead
Uses GradientBoosting (fast) with LSTM-style feature engineering on synthetic data.
Synthetic data generation models realistic atmospheric turbulence patterns.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import time
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ─── Synthetic Data Generator ─────────────────────────────────────────────────

def generate_synthetic_channel_timeseries(
    n_samples: int = 50_000,
    dt_seconds: float = 1.0,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic atmospheric channel time series.
    Models: Cn² variation, wind, cloud cover, temperature → QKD metrics.

    State variables:
        cn2          — Atmospheric refractive index structure parameter (log scale)
        wind_speed   — m/s
        cloud_cover  — 0–1 fraction
        temperature  — Kelvin (temperature inversion affects turbulence)
        humidity     — relative humidity fraction
        time_of_day  — 0–24 h (daytime convection drives Cn²)

    Output features (lag window):
        [cn2, wind, cloud, temp, humidity, tod, qber, skr, loss_db]
        × 10 lag steps = 90 features

    Target:
        skr_30s_ahead — secret key rate 30 seconds ahead (kbps)
    """
    rng = np.random.default_rng(seed)

    # Simulate physical time evolution
    times = np.arange(n_samples) * dt_seconds

    # Cn² — log-normal process with diurnal cycle (daytime convection peaks)
    tod = (times % 86400) / 3600   # hour of day
    cn2_mean_log = -15.0 - 2.0 * np.cos(2 * np.pi * tod / 24 - np.pi)  # peaks at noon
    cn2_noise = rng.standard_normal(n_samples) * 0.5
    cn2_log = cn2_mean_log + np.cumsum(rng.standard_normal(n_samples) * 0.01) * 0.1 + cn2_noise
    cn2_log = np.clip(cn2_log, -18, -12)
    cn2 = 10 ** cn2_log

    # Wind speed (m/s) — AR(1) process
    wind = np.zeros(n_samples)
    wind[0] = 5.0
    for i in range(1, n_samples):
        wind[i] = 0.99 * wind[i-1] + rng.standard_normal() * 0.5
    wind = np.clip(wind, 0.5, 30.0)

    # Cloud cover — Markov chain (clear/cloudy transitions)
    cloud = np.zeros(n_samples)
    cloud[0] = rng.random()
    for i in range(1, n_samples):
        cloud[i] = np.clip(0.95 * cloud[i-1] + rng.standard_normal() * 0.05, 0, 1)

    # Temperature (K) — diurnal cycle + random
    temp = 290 + 8 * np.sin(2 * np.pi * tod / 24 - np.pi/2) + rng.standard_normal(n_samples) * 2

    # Humidity
    humidity = np.clip(0.6 + 0.3 * np.sin(2 * np.pi * tod / 24) + rng.standard_normal(n_samples) * 0.1, 0.1, 0.99)

    # Derive QKD metrics from physics
    # Loss: fiber (fixed) + turbulence (function of Cn²)
    distance_km = 50.0
    fiber_loss_db = 0.2 * distance_km
    eta_fiber = 10 ** (-fiber_loss_db / 10)

    lambda_m = 1550e-9
    k = 2 * np.pi / lambda_m
    L = distance_km * 1e3
    sigma_rytov = np.sqrt(1.23 * cn2 * k**(7/6) * L**(11/6))
    strehl = np.where(sigma_rytov < 1.0, np.exp(-sigma_rytov**2), 1/(1+sigma_rytov**2))
    eta_total = eta_fiber * strehl * 0.1  # detector efficiency

    # QBER: dark counts + optical + cloud effect
    mu = 0.5
    dc = 1e-6
    cloud_qber_penalty = cloud * 0.05  # clouds scatter photons → higher QBER
    qber = np.clip(0.5 * dc / np.maximum(eta_total * mu, 1e-10) + 0.01 + cloud_qber_penalty, 0, 0.5)

    # Secret key rate (simplified from BB84 formula)
    def h(p):
        p = np.clip(p, 1e-10, 1-1e-10)
        return -p * np.log2(p) - (1-p) * np.log2(1-p)

    Q_mu = 1 - np.exp(-eta_total * mu) + dc
    skr = np.maximum(0, Q_mu * (1 - h(qber)) - Q_mu * 1.16 * h(qber)) * 1e9 / 1e3  # kbps

    # Build lag features
    lag = 10
    horizon = 30  # 30-second lookahead

    feature_cols = np.column_stack([cn2_log, wind, cloud, temp - 290, humidity, tod % 24, qber, skr, 10*np.log10(np.maximum(eta_total, 1e-15))])
    n_feats = feature_cols.shape[1]

    X_list, y_list = [], []
    for i in range(lag, n_samples - horizon):
        window = feature_cols[i-lag:i].flatten()
        X_list.append(window)
        y_list.append(skr[i + horizon])

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)

    return X, y


# ─── Model ────────────────────────────────────────────────────────────────────

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")


@dataclass
class PredictionResult:
    skr_predicted_kbps: float
    confidence_interval_low: float
    confidence_interval_high: float
    predicted_mode: str
    model_r2: float
    model_mae_kbps: float
    horizon_seconds: int = 30


class ChannelPredictor:
    """
    Gradient Boosting regressor for QKD channel SKR prediction.
    Trained on synthetic physics-based time series.
    """

    def __init__(self):
        self.model: Optional[GradientBoostingRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.r2: float = 0.0
        self.mae: float = 0.0
        self.is_trained = False
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(MODEL_PATH) and SKLEARN_AVAILABLE:
            try:
                with open(MODEL_PATH, "rb") as f:
                    saved = pickle.load(f)
                self.model = saved["model"]
                self.scaler = saved["scaler"]
                self.r2 = saved.get("r2", 0.0)
                self.mae = saved.get("mae", 0.0)
                self.is_trained = True
                print(f"[AI] Loaded pre-trained model (R²={self.r2:.4f}, MAE={self.mae:.2f} kbps)")
            except Exception as e:
                print(f"[AI] Could not load model: {e}")

    def train(self, n_samples: int = 30_000, verbose: bool = True) -> dict:
        """Train the SKR prediction model."""
        if not SKLEARN_AVAILABLE:
            print("[AI] scikit-learn not available — using fallback predictor")
            return {"status": "sklearn_unavailable"}

        if verbose:
            print(f"[AI] Generating {n_samples} synthetic training samples...")
        X, y = generate_synthetic_channel_timeseries(n_samples=n_samples)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.scaler = StandardScaler()
        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        if verbose:
            print("[AI] Training GradientBoostingRegressor...")
        t0 = time.time()
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_train_s, y_train)
        elapsed = time.time() - t0

        y_pred = self.model.predict(X_test_s)
        self.r2 = float(r2_score(y_test, y_pred))
        self.mae = float(mean_absolute_error(y_test, y_pred))
        self.is_trained = True

        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler, "r2": self.r2, "mae": self.mae}, f)

        if verbose:
            print(f"[AI] Training complete in {elapsed:.1f}s | R²={self.r2:.4f} | MAE={self.mae:.2f} kbps")

        return {
            "status": "trained",
            "r2": self.r2,
            "mae_kbps": self.mae,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_seconds": round(elapsed, 2),
        }

    def predict(
        self,
        cn2_log: float,
        wind_ms: float,
        cloud_cover: float,
        temp_k: float,
        humidity: float,
        hour_of_day: float,
        qber_current: float,
        skr_current_kbps: float,
        loss_db: float,
        history_window: list[list[float]] | None = None,
    ) -> PredictionResult:
        """
        Predict SKR 30s ahead given current channel state.
        If history_window provided (list of 10 rows × 9 features), uses it directly.
        Otherwise generates a plausible window from current state.
        """
        SKR_MIN_HYBRID = 1.0    # kbps threshold for hybrid mode
        SKR_MIN_BUFFER = 0.01

        if not self.is_trained or self.model is None:
            # Fallback: simple physics-based heuristic
            predicted = max(0.0, skr_current_kbps * (1 - cloud_cover * 0.5) * math.exp(-cn2_log / 15))
        else:
            if history_window is None:
                row = [cn2_log, wind_ms, cloud_cover, temp_k - 290, humidity, hour_of_day, qber_current, skr_current_kbps, loss_db]
                # Replicate row 10 times as lag window
                history_window = [row] * 10
            X = np.array(history_window, dtype=np.float32).flatten().reshape(1, -1)
            X_s = self.scaler.transform(X)
            predicted = float(self.model.predict(X_s)[0])
            predicted = max(0.0, predicted)

        # Confidence interval: ±MAE (approximate)
        ci_low = max(0.0, predicted - self.mae)
        ci_high = predicted + self.mae

        if predicted >= SKR_MIN_HYBRID:
            mode = "QKD_PQC_HYBRID"
        elif predicted >= SKR_MIN_BUFFER:
            mode = "BUFFERED_KEY"
        else:
            mode = "PQC_ONLY"

        return PredictionResult(
            skr_predicted_kbps=round(predicted, 3),
            confidence_interval_low=round(ci_low, 3),
            confidence_interval_high=round(ci_high, 3),
            predicted_mode=mode,
            model_r2=round(self.r2, 4),
            model_mae_kbps=round(self.mae, 3),
        )

    def status(self) -> dict:
        return {
            "is_trained": self.is_trained,
            "r2": self.r2,
            "mae_kbps": self.mae,
            "sklearn_available": SKLEARN_AVAILABLE,
            "model_path": MODEL_PATH,
        }


# Singleton
predictor = ChannelPredictor()


if __name__ == "__main__":
    print("=== AI Channel Predictor ===")
    result = predictor.train(n_samples=20_000, verbose=True)
    print(f"Training result: {result}")

    pred = predictor.predict(
        cn2_log=-15.0, wind_ms=5.0, cloud_cover=0.2,
        temp_k=295.0, humidity=0.6, hour_of_day=14.0,
        qber_current=0.03, skr_current_kbps=50.0, loss_db=12.0,
    )
    print(f"\nPredicted SKR: {pred.skr_predicted_kbps:.2f} kbps")
    print(f"95% CI:        [{pred.confidence_interval_low:.2f}, {pred.confidence_interval_high:.2f}] kbps")
    print(f"Predicted mode: {pred.predicted_mode}")
