"""
Synthetic ML Model Training Script
Generates a diverse synthetic EEG dataset, extracts features, trains a Random Forest model,
evaluates in-distribution and out-of-distribution (OOD) accuracy, and exports models/trained_rf_model.joblib.

LIMITATION NOTE:
Full clinical validation requires real human EEG datasets (e.g., PhysioNet EEG Motor Imagery Database).
Current training and OOD evaluation metrics reflect synthetic-only performance.
"""

import os
import sys
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Ensure src module is on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.simulation.eeg_generator import SyntheticEEGGenerator
from src.processing.filter import EEGFilter
from src.processing.psd import PSDAnalyzer
from src.features.extractor import EEGFeatureExtractor

def generate_ood_dataset(num_samples=300):
    """
    Generates out-of-distribution (OOD) synthetic evaluation dataset with:
    - Shifted frequency parameters
    - High-variance amplitude scaling
    - Heavy non-Gaussian noise distributions
    """
    generator = SyntheticEEGGenerator(sampling_rate=250)
    filter_obj = EEGFilter(sampling_rate=250)
    psd_analyzer = PSDAnalyzer(sampling_rate=250)

    X_ood = []
    y_ood = []

    # OOD Profiles with shifted frequency profiles and non-standard amplitude ranges
    ood_profiles = [
        (0.95, 0.45, 0.15, 0.05, 'LOW'),       # Deep drowsiness shift
        (0.15, 0.25, 0.95, 0.15, 'MODERATE'),  # High alpha peak shift
        (0.05, 0.15, 0.15, 0.95, 'HIGH'),      # Extreme beta burst shift
    ]

    samples_per_p = num_samples // len(ood_profiles)

    for d, t, a, b, label in ood_profiles:
        for _ in range(samples_per_p):
            # Heavy OOD variance and noise jitter
            d_var = np.clip(d + np.random.normal(0, 0.15), 0.01, 1.0)
            t_var = np.clip(t + np.random.normal(0, 0.15), 0.01, 1.0)
            a_var = np.clip(a + np.random.normal(0, 0.15), 0.01, 1.0)
            b_var = np.clip(b + np.random.normal(0, 0.15), 0.01, 1.0)
            noise_var = np.clip(0.35 + np.random.normal(0, 0.10), 0.1, 0.6)  # 3x noise level

            generator.set_amplitudes(d_var, t_var, a_var, b_var)
            generator.set_noise(noise_var)

            waveform, _ = generator.generate_chunk(1250)  # 5 sec window
            filtered = filter_obj.process(waveform)
            freqs, psd = psd_analyzer.compute_psd(filtered)
            metrics = psd_analyzer.analyze_bands(freqs, psd)
            features = EEGFeatureExtractor.extract_features(metrics)

            X_ood.append(features)
            y_ood.append(label)

    return np.array(X_ood), np.array(y_ood)

def train_and_save():
    print("[ML Training] Generating synthetic EEG dataset...")
    generator = SyntheticEEGGenerator(sampling_rate=250)
    filter_obj = EEGFilter(sampling_rate=250)
    psd_analyzer = PSDAnalyzer(sampling_rate=250)

    X_data = []
    y_data = []
    classes = ['LOW', 'MODERATE', 'HIGH']

    # Generate 1500 synthetic samples across different state profiles
    profiles = [
        # (Delta, Theta, Alpha, Beta, Label)
        (0.8, 0.6, 0.2, 0.1, 'LOW'),       # Deep rest / drowsiness
        (0.6, 0.8, 0.3, 0.1, 'LOW'),       # Theta dominance
        (0.2, 0.3, 0.9, 0.2, 'MODERATE'),  # Relaxed alertness (Alpha)
        (0.1, 0.2, 0.8, 0.3, 'MODERATE'),  # Baseline focus
        (0.1, 0.2, 0.2, 0.9, 'HIGH'),      # Active stress / problem solving (Beta)
        (0.2, 0.3, 0.3, 0.8, 'HIGH')       # Elevated cognitive load
    ]

    samples_per_profile = 250

    for d, t, a, b, label in profiles:
        for _ in range(samples_per_profile):
            # Add random perturbation to simulate natural variance
            d_var = np.clip(d + np.random.normal(0, 0.08), 0.05, 1.0)
            t_var = np.clip(t + np.random.normal(0, 0.08), 0.05, 1.0)
            a_var = np.clip(a + np.random.normal(0, 0.08), 0.05, 1.0)
            b_var = np.clip(b + np.random.normal(0, 0.08), 0.05, 1.0)
            noise_var = np.clip(0.1 + np.random.normal(0, 0.03), 0.02, 0.3)

            generator.set_amplitudes(d_var, t_var, a_var, b_var)
            generator.set_noise(noise_var)

            waveform, _ = generator.generate_chunk(1250)  # 5 sec window
            filtered = filter_obj.process(waveform)
            freqs, psd = psd_analyzer.compute_psd(filtered)
            metrics = psd_analyzer.analyze_bands(freqs, psd)
            features = EEGFeatureExtractor.extract_features(metrics)

            X_data.append(features)
            y_data.append(label)

    X_data = np.array(X_data)
    y_data = np.array(y_data)

    print(f"[ML Training] Dataset generated: {X_data.shape[0]} samples, {X_data.shape[1]} features.")

    # Split Train/Test
    X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.2, random_state=42, stratify=y_data)

    # Train Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)

    # Evaluate In-Distribution
    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[ML Training] In-Distribution Test Accuracy: {acc * 100.0:.2f}%")
    print(classification_report(y_test, y_pred, target_names=classes))

    # Independent OOD Evaluation Pass
    print("[ML Training] Running Independent Out-Of-Distribution (OOD) Evaluation Pass...")
    X_ood, y_ood = generate_ood_dataset(num_samples=300)
    y_ood_pred = rf.predict(X_ood)
    ood_acc = accuracy_score(y_ood, y_ood_pred)
    print(f"[ML Training] Out-Of-Distribution (OOD) Test Accuracy: {ood_acc * 100.0:.2f}%")

    # Save model artifact with both accuracy metrics
    output_dir = os.path.join(project_root, "models")
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "trained_rf_model.joblib")

    joblib.dump({
        'model': rf,
        'classes': classes,
        'accuracy': float(acc),
        'ood_accuracy': float(ood_acc),
        'feature_names': EEGFeatureExtractor.feature_names(),
        'validation_note': "Metrics reflect synthetic-only performance. Clinical validation requires real EEG datasets."
    }, model_path)

    print(f"[ML Training] Model & metadata successfully saved to: {model_path}")

if __name__ == '__main__':
    train_and_save()
