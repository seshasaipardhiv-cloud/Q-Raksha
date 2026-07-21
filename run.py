"""
QuantumShield — Convenient launch script
Runs: AI training (if needed) + Streamlit dashboard
"""
import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

def main():
    print("""
==============================================================
         QuantumShield  -  Crypto-Agile QKD-PQC         
         India NQM-Aligned | TCOE Hackathon Demo             
==============================================================
    """)
    
    # Check if AI model is trained
    model_path = os.path.join(ROOT, "ai", "model.pkl")
    if not os.path.exists(model_path):
        print("[*] Training AI channel predictor (first run - ~20s)...")
        try:
            from ai.predictor import ChannelPredictor
            p = ChannelPredictor()
            result = p.train(n_samples=20_000, verbose=True)
            print(f"[OK] AI trained: R^2={result.get('r2',0):.4f}\n")
        except Exception as e:
            print(f"[!] AI training skipped: {e}")
    else:
        print("[OK] AI model found - skipping training")

    print("[*] Launching Streamlit dashboard...")
    print("[*] Dashboard URL: http://localhost:8501")
    print("[*] Press Ctrl+C to stop\n")

    dashboard = os.path.join(ROOT, "dashboard", "app.py")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", dashboard, 
        "--server.port=8501", 
        "--server.headless=true", 
        "--browser.gatherUsageStats=false"
    ])


if __name__ == "__main__":
    main()
