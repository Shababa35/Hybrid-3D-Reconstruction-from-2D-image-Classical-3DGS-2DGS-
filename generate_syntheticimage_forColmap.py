import os
import subprocess
import numpy as np
import csv
import shutil

# ==================== Parameter Settings ====================
NUM_IMAGES = 1
PBRT_EXECUTABLE = r"C:\Users\Jiachen\pbrt\Release\pbrt.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Original monkey head model
ORIGINAL_MODEL = os.path.join(SCRIPT_DIR, "monkey.pbrt")
MODIFIED_MODEL = os.path.join(SCRIPT_DIR, "monkey_colmap_ready.pbrt")

if not os.path.exists(ORIGINAL_MODEL):
    print(f"{ORIGINAL_MODEL} not found!")
    exit(1)

# ==================== Inject Colorful Checkerboard Material ====================
print("Injecting material into pbrt")
with open(ORIGINAL_MODEL, "r", encoding="utf-8") as f:
    model_lines = f.readlines()

modified_lines = []
inserted = False

for line in model_lines:
    modified_lines.append(line)
    if "AttributeBegin" in line and not inserted:
        material_pbrtv4 = """
    # High-frequency color checkerboard texture (red/blue alternating, highly distinctive features)
    Texture "colmap_texture" "spectrum" "checkerboard"
        "float uscale" [50]
        "float vscale" [50]
        "rgb tex1" [0.9 0.2 0.2]   # Bright red
        "rgb tex2" [0.2 0.2 0.9]   # Bright blue
    
    Material "diffuse"
        "texture reflectance" "colmap_texture"
"""
        modified_lines.append(material_pbrtv4)
        inserted = True

with open(MODIFIED_MODEL, "w", encoding="utf-8") as f:
    f.writelines(modified_lines)
print("Color checkerboard material injected successfully!")

# ==================== Prepare Render Directory ====================
BASE_DIR = os.path.join(SCRIPT_DIR, "dataset")
if os.path.exists(BASE_DIR):
    try:
        shutil.rmtree(BASE_DIR)
    except Exception:
        pass

RENDER_DIR = os.path.join(BASE_DIR, "renders")
os.makedirs(RENDER_DIR, exist_ok=True)

print(f"Starting dataset rendering (total {NUM_IMAGES} images)")
print("Configuration: Six-direction uniform white light illumination + Color checkerboard texture + Extended camera trajectory\n")
camera_positions = []


# ==================== Batch Rendering ====================
for i in range(NUM_IMAGES):
    t = i / NUM_IMAGES
    
    # Camera trajectory: Extended radius, full vertical coverage
    angle = 2 * np.pi * t
    radius = 6.0  # Increased from 4.5 to 6.0
    
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    
    # Height: oscillates between -0.5 and 3.5 (covers top of head and chin)
    # 2 oscillations per full circle, ensuring different viewing heights from all angles
    z = 1.5 + 2.0 * np.sin(4 * np.pi * t)  # Range -0.5 ~ 3.5
    
    img_name = f"img_{i:04d}.png"
    img_path = os.path.join(RENDER_DIR, img_name).replace("\\", "/")
    model_path = MODIFIED_MODEL.replace("\\", "/")
    
    pbrt = f"""
LookAt {x} {y} {z}  0 0 1.5  0 0 1
Camera "perspective" "float fov" [50]

Sampler "halton" "integer pixelsamples" [128]
Integrator "path" "integer maxdepth" [5]
Film "rgb" "string filename" "{img_path}" "integer xresolution" [1024] "integer yresolution" [1024]

WorldBegin

# Ambient light
LightSource "infinite" "rgb L" [0.10 0.10 0.10]

# Main light
LightSource "distant" "point3 from" [3 4 5] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [2.0]

# Front fill light
LightSource "distant" "point3 from" [0 5 2] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [0.6]

# Back fill light
LightSource "distant" "point3 from" [0 -5 2] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [0.6]

# Left fill light
LightSource "distant" "point3 from" [-4 0 2] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [0.5]

# Right fill light
LightSource "distant" "point3 from" [4 0 2] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [0.5]

# Bottom fill light
LightSource "distant" "point3 from" [0 0 -3] "point3 to" [0 0 1.5] "rgb L" [1 1 1] "float scale" [0.5]

AttributeBegin
    Translate 0 0 1.2
    Include "{model_path}"
AttributeEnd
"""
    
    scene_file = os.path.join(BASE_DIR, f"scene_{i:04d}.pbrt")
    with open(scene_file, 'w', encoding="utf-8") as f:
        f.write(pbrt)
    
    print(f"[{i+1:3d}/{NUM_IMAGES}] Rendering {img_name}...", end=" ", flush=True)
    
    result = subprocess.run([PBRT_EXECUTABLE, scene_file], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr[:300]}")
        break
    else:
        print(f"(Camera position: [{x:.1f}, {y:.1f}, {z:.1f}])")
        camera_positions.append({'image': img_name, 'x': x, 'y': y, 'z': z})

# ==================== Save Camera Trajectory ====================
if len(camera_positions) == NUM_IMAGES:
    with open(os.path.join(BASE_DIR, "camera_positions.csv"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["image", "x", "y", "z"])
        for pos in camera_positions:
            writer.writerow([pos['image'], pos['x'], pos['y'], pos['z']])
    
    print(f"Rendering complete! {NUM_IMAGES} images saved to: {RENDER_DIR}")
    print(f"Camera trajectory saved to: {os.path.join(BASE_DIR, 'camera_positions.csv')}")
    
    # Print camera trajectory statistics
    z_values = [p['z'] for p in camera_positions]
    print(f"Camera height range: {min(z_values):.1f} ~ {max(z_values):.1f}")
    print(f"   Covers top of head (z≈3.5) and chin (z≈-0.5)")
    
    print("Optimization Summary:")
    print("   - Camera radius: 4.5 → 6.0 (wider view)")
    print("   - Camera height: 1.5~3.5 → -0.5~3.5 (covers top of head and chin)")
    print("   - Six-direction uniform white light illumination (all sides are lit)")
    print("   - Color checkerboard texture (rich feature points)")
    print("This is the ideal input configuration for COLMAP reconstruction")
else:
    print(f"Rendering failed, only {len(camera_positions)} images were generated")