"""
AI Model Trainer — Run once to pre-train and cache the channel predictor.
Run before launching the dashboard for faster startup.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.predictor import ChannelPredictor

if __name__ == "__main__":
    print("=" * 60)
    print("QuantumShield — AI Channel Predictor Training")
    print("=" * 60)
    p = ChannelPredictor()
    if p.is_trained:
        print(f"Model already trained: R²={p.r2:.4f}, MAE={p.mae:.3f} kbps")
        retrain = input("Retrain? (y/N): ").strip().lower()
        if retrain != "y":
            print("Using existing model.")
            exit(0)
    
    print("Generating 50,000 synthetic channel samples...")
    result = p.train(n_samples=50_000, verbose=True)
    print(f"\nTraining complete!")
    print(f"  R²  = {result.get('r2', 0):.4f}  (1.0 = perfect)")
    print(f"  MAE = {result.get('mae_kbps', 0):.3f} kbps")
    print(f"  Time = {result.get('train_seconds', 0):.1f}s")
    print(f"  Model saved to: {p.model_path if hasattr(p, 'model_path') else 'ai/model.pkl'}")
