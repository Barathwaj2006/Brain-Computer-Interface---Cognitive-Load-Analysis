"""
NeuroSim Branding Asset Generator Script
Generates high-resolution minimalist scientific NeuroSim logos (Stylized N + EEG waveform)
Output locations: src/assets/ and docs/assets/
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

def generate_logo(size=512, bg_color=(11, 15, 25), fg_color=(14, 165, 233), wave_color=(16, 185, 129)):
    # Create high-res canvas
    img = Image.new("RGBA", (size, size), bg_color + (255,))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.18)
    left = margin
    right = size - margin
    top = margin
    bottom = size - margin
    width = right - left
    height = bottom - top

    stroke_w = max(4, int(size * 0.055))

    # Outer subtle rounded frame glow
    draw.rounded_rectangle(
        [margin // 2, margin // 2, size - margin // 2, size - margin // 2],
        radius=int(size * 0.08),
        outline=(31, 41, 55, 255),
        width=max(2, int(size * 0.015))
    )

    # Stylized N Left Stem
    draw.line([(left, bottom), (left, top)], fill=fg_color + (255,), width=stroke_w)
    
    # Stylized N Right Stem
    draw.line([(right, bottom), (right, top)], fill=fg_color + (255,), width=stroke_w)

    # Diagonal N stem with integrated EEG waveform overlay
    num_points = 200
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = left + t * (right - left)
        # Linear N diagonal path
        base_y = top + t * (bottom - top)
        # Superimpose sine wave oscillation along the diagonal
        wave = math.sin(t * math.pi * 4.0) * (height * 0.12) * math.sin(t * math.pi)
        y = base_y + wave
        points.append((x, y))

    # Draw EEG Diagonal
    draw.line(points, fill=wave_color + (255,), width=stroke_w, joint="round")

    # Add 2 electrode node dots at top-left and bottom-right vertices
    r = stroke_w * 0.8
    draw.ellipse([left - r, top - r, left + r, top + r], fill=(249, 250, 251, 255))
    draw.ellipse([right - r, bottom - r, right + r, bottom + r], fill=(249, 250, 251, 255))

    return img

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_assets = os.path.join(root_dir, "src", "assets")
    docs_assets = os.path.join(root_dir, "docs", "assets")
    os.makedirs(src_assets, exist_ok=True)
    os.makedirs(docs_assets, exist_ok=True)

    print("[Branding Generator] Generating NeuroSim logo assets...")

    # Master 512x512
    logo_512 = generate_logo(512)
    logo_512.save(os.path.join(src_assets, "splash_logo.png"))
    logo_512.save(os.path.join(docs_assets, "logo.png"))

    # 256x256
    logo_256 = generate_logo(256)
    logo_256.save(os.path.join(src_assets, "logo.png"))
    logo_256.convert("RGB").save(os.path.join(src_assets, "logo.jpg"), quality=95)

    # 64x64 Icon
    logo_64 = generate_logo(64)
    logo_64.save(os.path.join(src_assets, "logo_icon.png"))

    # ICO Favicon
    logo_32 = generate_logo(32)
    logo_32.save(os.path.join(src_assets, "favicon.ico"), format="ICO")

    print("[Branding Generator] Logo assets generated successfully in src/assets and docs/assets!")

if __name__ == '__main__':
    main()
