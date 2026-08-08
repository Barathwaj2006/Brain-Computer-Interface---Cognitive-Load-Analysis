import shutil
import os

src_path = r"C:\Users\barat\.gemini\antigravity\brain\5d3ba892-50bd-4dad-be2d-269e9c1d5ff2\neurosim_logo_1786178206321.jpg"

dest1 = r"C:\Users\barat\.gemini\antigravity\scratch\neurosim-eeg-cognitive-analysis\src\assets\logo.jpg"
dest2 = r"C:\Users\barat\.gemini\antigravity\scratch\neurosim-eeg-cognitive-analysis\docs\assets\logo.jpg"

os.makedirs(os.path.dirname(dest1), exist_ok=True)
os.makedirs(os.path.dirname(dest2), exist_ok=True)

shutil.copyfile(src_path, dest1)
shutil.copyfile(src_path, dest2)

print("Logo successfully copied to src/assets/logo.jpg and docs/assets/logo.jpg!")
