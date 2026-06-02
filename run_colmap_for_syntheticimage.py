import os
import subprocess

# ==================== Path Configuration ====================
# Modify this line to your local absolute path
COLMAP_EXE = r"E:\StudyMaterial\France\3D_Vision\Project\Colmap\colmap.bat"  
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.join(SCRIPT_DIR, "dataset")
RENDER_DIR = os.path.join(BASE_DIR, "renders")
DATABASE_PATH = os.path.join(BASE_DIR, "monkey.db")
SPARSE_DIR = os.path.join(BASE_DIR, "sparse")

# Create sparse point cloud output directory
os.makedirs(SPARSE_DIR, exist_ok=True)

print("Starting efficient COLMAP command-line reconstruction pipeline...")

# ==================== 1. Feature Extraction ====================
# Precisely injecting the pinhole camera model and perfect intrinsic parameters you entered in the GUI
print("\n[Step 1/4] Extracting SIFT features...")
extract_cmd = [
    COLMAP_EXE, "feature_extractor",
    "--database_path", DATABASE_PATH,
    "--image_path", RENDER_DIR,
    "--ImageReader.camera_model", "PINHOLE",
    "--ImageReader.single_camera", "1",           
    "--ImageReader.camera_params", "1098.02,1098.02,512.0,512.0" # Ground truth intrinsics
]
res = subprocess.run(extract_cmd, capture_output=True, text=True)
if res.returncode != 0:
    print(f"Feature extraction failed:\n{res.stderr}")
    exit(1)
print("Feature extraction complete!")


# ==================== 2. Feature Matching ====================
print("\n[Step 2/4] Running exhaustive matching...")
match_cmd = [
    COLMAP_EXE, "exhaustive_matcher",
    "--database_path", DATABASE_PATH
]
res = subprocess.run(match_cmd, capture_output=True, text=True)
if res.returncode != 0:
    print(f"Feature matching failed:\n{res.stderr}")
    exit(1)
print("Feature matching complete!")


# ==================== 3. Sparse 3D Reconstruction ====================
print("\n[Step 3/4] Running 3D reconstruction (Mapper)...")
mapper_cmd = [
    COLMAP_EXE, "mapper",
    "--database_path", DATABASE_PATH,
    "--image_path", RENDER_DIR,
    "--output_path", SPARSE_DIR
]
res = subprocess.run(mapper_cmd, capture_output=True, text=True)
if res.returncode != 0:
    print(f"3D reconstruction failed:\n{res.stderr}")
    exit(1)
print(" 3D reconstruction complete! Results saved in sparse folder.")


# ==================== 4. Convert Point Cloud Format (Optional but Recommended) ====================
# COLMAP outputs binary .bin files by default. Convert to text .txt format for Python reading or Meshlab viewing
print("\n[Step 4/4] Converting model to text format (txt)...")
TEXT_DIR = os.path.join(SPARSE_DIR, "text")
os.makedirs(TEXT_DIR, exist_ok=True)

# Find the first sub-model folder from reconstruction (usually '0')
model_0_dir = os.path.join(SPARSE_DIR, "0")
if os.path.exists(model_0_dir):
    export_cmd = [
        COLMAP_EXE, "model_converter",
        "--input_path", model_0_dir,
        "--output_path", TEXT_DIR,
        "--output_type", "TXT"
    ]
    subprocess.run(export_cmd)
    print(f"All done!")
else:
    print("Failed to generate a valid sparse model")