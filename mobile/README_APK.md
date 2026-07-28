# NeuroSim Android APK & Mobile Application Packaging Guide

NeuroSim is available both as a standalone Windows `.exe` desktop application and a Progressive Web App (PWA) / Android APK package.

## Option 1: Progressive Web App (PWA) / Instant Mobile Install

1. Open `web/index.html` on your mobile browser (or host on GitHub Pages).
2. Tap **Add to Home Screen** or **Install App**.
3. NeuroSim will run as a native full-screen application on Android and iOS devices.

## Option 2: Android APK Packaging with Capacitor / Bubblewrap

To build a standalone `.apk` installer file for Android:

```bash
# Install Capacitor CLI
npm install -g @capacitor/cli @capacitor/core @capacitor/android

# Initialize Capacitor inside web directory
cd web
npx cap init NeuroSim com.neurosim.eeg

# Add Android Platform
npx cap add android

# Build APK package
npx cap open android
```

In Android Studio:
- Select **Build** -> **Build Bundle(s) / APK(s)** -> **Build APK(s)**.
- Generated output: `app-debug.apk` / `NeuroSim.apk`.
