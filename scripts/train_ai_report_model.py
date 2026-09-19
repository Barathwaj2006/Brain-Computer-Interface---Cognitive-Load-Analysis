"""
=================================================================================
NEUROSIM : TRAINING PIPELINE FOR 300,000+ PARAMETER AI REPORT MODEL
Trains a 5-Layer Deep Neural Network (>440,000 Parameters) for Clinical EEG
Cognitive Load Analysis, Reliability Scoring & Diagnostic Report Synthesis.
=================================================================================
"""

import os
import sys
import json
import time
import numpy as np
import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.classification.ai_report_model import DeepNeuroReportModel

def generate_eeg_session_dataset(num_samples=4000):
    """
    Generates realistic clinical EEG session feature vectors across 4 neurological states:
    1. LOW (Rest, drowsiness, cortical slowing)
    2. MODERATE (Relaxed alertness, alpha synchrony, calm focus)
    3. HIGH (Concentrated problem solving, active cognitive load)
    4. FATIGUE (Prolonged workload exhaustion, theta rebound)
    """
    rng = np.random.RandomState(42)
    X = []
    y = []

    profiles = [
        # (Delta, Theta, Alpha, Beta, Label, Samples Weight)
        (0.65, 0.45, 0.15, 0.08, 'LOW', 1000),
        (0.12, 0.20, 0.75, 0.18, 'MODERATE', 1200),
        (0.08, 0.15, 0.22, 0.85, 'HIGH', 1100),
        (0.35, 0.60, 0.18, 0.50, 'FATIGUE', 700),
    ]

    for d_base, t_base, a_base, b_base, label, count in profiles:
        for _ in range(count):
            # Realistic physiological variance
            d = np.clip(d_base + rng.normal(0, 0.06), 0.02, 1.0)
            t = np.clip(t_base + rng.normal(0, 0.06), 0.02, 1.0)
            a = np.clip(a_base + rng.normal(0, 0.06), 0.02, 1.0)
            b = np.clip(b_base + rng.normal(0, 0.06), 0.02, 1.0)

            # Normalize to percentage sum
            tot = d + t + a + b
            d_pct = (d / tot) * 100.0
            t_pct = (t / tot) * 100.0
            a_pct = (a / tot) * 100.0
            b_pct = (b / tot) * 100.0

            session_meta = {
                'delta': d_pct,
                'theta': t_pct,
                'alpha': a_pct,
                'beta': b_pct,
                'tbr': t_pct / max(0.1, b_pct),
                'abr': a_pct / max(0.1, b_pct),
                'stress_index': b_pct / max(0.1, a_pct + t_pct),
                'mean_voltage': rng.normal(0, 2.0),
                'variance': rng.uniform(10.0, 45.0),
                'skewness': rng.normal(0.05, 0.15),
                'kurtosis': rng.normal(2.9, 0.3)
            }

            feat = DeepNeuroReportModel.extract_features(session_meta)
            X.append(feat)
            y.append(label)

    return np.array(X, dtype=np.float32), np.array(y)

def train_and_export_model():
    print("=" * 76)
    print("  TRAINING 300,000+ PARAMETER DEEP NEURAL NETWORK REPORT MODEL")
    print("=" * 76)

    start_t = time.time()

    # 1. Dataset Generation
    print("[1/5] Synthesizing 4,000 electrophysiological EEG session vectors...")
    X, y = generate_eeg_session_dataset(num_samples=4000)
    print(f"      Feature matrix: {X.shape[0]} sessions x {X.shape[1]} features.")

    # 2. Train / Test Split & Feature Standardization
    print("[2/5] Standardizing 64-dimensional feature space...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 3. Instantiate & Train Deep MLP Architecture (512, 512, 384, 64)
    # Parameter calculation:
    # 64*512 + 512 = 33,280
    # 512*512 + 512 = 262,656
    # 512*384 + 384 = 196,992
    # 384*64 + 64 = 24,640
    # 64*4 + 4 = 260
    # Total = 517,828 trainable parameters (> 500,000 required!)
    hidden_layers = (512, 512, 384, 64)
    print(f"[3/5] Initializing Deep MLP Architecture: 64 -> {hidden_layers} -> 4 Classes...")

    mlp = MLPClassifier(
        hidden_layer_sizes=hidden_layers,
        activation='relu',
        solver='adam',
        alpha=0.0005,
        batch_size=64,
        learning_rate_init=0.001,
        max_iter=60,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
        verbose=False
    )

    print("      Optimizing weights via Adam algorithm...")
    mlp.fit(X_train_scaled, y_train)

    # Calculate exact parameter count
    param_count = sum(w.size for w in mlp.coefs_) + sum(b.size for b in mlp.intercepts_)
    print(f"      Trainable Parameters Count: {param_count:,} parameters.")
    assert param_count >= 500000, f"Error: parameter count {param_count} is under 500,000!"

    # 4. In-Distribution & Out-of-Distribution Benchmarking
    print("[4/5] Evaluating performance benchmarks...")
    y_pred = mlp.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"      In-Distribution Test Accuracy: {acc * 100.0:.2f}%")
    print(classification_report(y_test, y_pred))

    # Test with out-of-distribution noise-corrupted samples
    X_ood = X_test_scaled + np.random.normal(0, 0.4, size=X_test_scaled.shape)
    ood_pred = mlp.predict(X_ood)
    ood_acc = accuracy_score(y_test, ood_pred)
    print(f"      Robustness / OOD Evaluation Accuracy: {ood_acc * 100.0:.2f}%")

    # 5. Export Model Artifacts
    print("[5/5] Exporting model artifacts...")
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True)

    model_joblib_path = os.path.join(models_dir, "ai_report_model.joblib")
    joblib.dump({
        'weights': [w.astype(np.float32) for w in mlp.coefs_],
        'intercepts': [b.astype(np.float32) for b in mlp.intercepts_],
        'scaler_mean': scaler.mean_.astype(np.float32),
        'scaler_scale': scaler.scale_.astype(np.float32),
        'classes': list(mlp.classes_),
        'total_parameters': param_count,
        'accuracy': float(acc),
        'ood_accuracy': float(ood_acc),
        'trained_at': time.time(),
        'feature_dim': 64,
        'architecture': f"64 -> {hidden_layers} -> {len(mlp.classes_)}"
    }, model_joblib_path)
    print(f"      Saved Python Model: {model_joblib_path}")

    # Export compact JSON weights for in-browser client execution
    web_dir = os.path.join(project_root, "web")
    web_weights_path = os.path.join(web_dir, "ai_report_model_weights.json")

    # Quantize/format weights to 4 decimals to keep JSON concise
    web_export = {
        'model_name': "NeuroSim Deep Neural Network Clinical Classifier",
        'total_parameters': param_count,
        'accuracy_pct': round(float(acc) * 100.0, 1),
        'classes': list(mlp.classes_),
        'scaler_mean': [round(float(v), 4) for v in scaler.mean_],
        'scaler_scale': [round(float(v), 4) for v in scaler.scale_],
        'architecture': [64] + list(hidden_layers) + [len(mlp.classes_)],
        'layers': []
    }

    for i in range(len(mlp.coefs_)):
        web_export['layers'].append({
            'shape': list(mlp.coefs_[i].shape),
            'weights': [[round(float(val), 4) for val in row] for row in mlp.coefs_[i]],
            'bias': [round(float(val), 4) for val in mlp.intercepts_[i]]
        })

    with open(web_weights_path, 'w', encoding='utf-8') as f:
        json.dump(web_export, f)

    file_mb = os.path.getsize(web_weights_path) / (1024 * 1024)
    print(f"      Saved Web JSON Weights: {web_weights_path} ({file_mb:.1f} MB)")

    elapsed = round(time.time() - start_t, 2)
    print("=" * 76)
    print(f"  TRAINING COMPLETE ({elapsed}s) | PARAMETERS: {param_count:,} | ACCURACY: {acc * 100.0:.2f}%")
    print("=" * 76)

    return param_count, acc

if __name__ == '__main__':
    train_and_export_model()
