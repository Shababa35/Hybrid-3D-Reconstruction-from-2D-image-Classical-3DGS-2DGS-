import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

# ==================== Load Model ====================
obj_path = r"E:\StudyMaterial\France\3D_Vision\Project\Colmap\Synthetic\monkey_524.obj"
mesh = trimesh.load(obj_path, process=False)
verts = mesh.vertices

# Get vertex colors if available
if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
    face_colors = mesh.visual.vertex_colors[mesh.faces].mean(axis=1)[:, :3] / 255.0
else:
    # Fallback colors based on face orientation
    face_normals = mesh.face_normals
    face_colors = np.zeros((len(mesh.faces), 3))
    for i, n in enumerate(face_normals):
        if abs(n[0]) > 0.5:
            face_colors[i] = [0.9, 0.2, 0.2]   # reddish for x-facing
        elif abs(n[1]) > 0.5:
            face_colors[i] = [0.2, 0.2, 0.9]   # blueish for y-facing
        else:
            face_colors[i] = [0.7, 0.7, 0.7]   # gray for z-facing

# ==================== Lighting and Rotation ====================
def get_camera_rotation(elev, azim):
    """Build rotation matrix for camera view."""
    e = np.radians(elev)
    a = np.radians(azim)
    
    Rz = np.array([[np.cos(a), -np.sin(a), 0],
                   [np.sin(a), np.cos(a), 0],
                   [0, 0, 1]])
    
    Re = np.array([[1, 0, 0],
                   [0, np.cos(e), -np.sin(e)],
                   [0, np.sin(e), np.cos(e)]])
    
    return Rz @ Re

def compute_lighting(face_normals, base_color, light_dir, light_rgb, ambient, intensity, elev, azim):
    """Apply directional lighting to the mesh."""
    R = get_camera_rotation(elev, azim)
    rotated_light = R @ np.array(light_dir)
    
    # Diffuse lighting
    cos_angle = np.dot(face_normals, rotated_light)
    diffuse = np.maximum(0, cos_angle)
    
    # Final color = ambient + diffuse
    factor = ambient + intensity * diffuse
    lit_color = base_color * (factor[:, np.newaxis] * np.array(light_rgb))
    
    return np.clip(lit_color, 0, 1)

def draw_mesh(ax, colors, title, elev, azim):
    """Render mesh on a given axis."""
    mesh_faces = mesh.vertices[mesh.faces]
    poly = Poly3DCollection(mesh_faces, facecolors=colors, linewidths=0)
    ax.add_collection(poly)
    ax.set_axis_on()
    ax.set_facecolor('white')
    ax.set_xlim(verts[:, 0].min(), verts[:, 0].max())
    ax.set_ylim(verts[:, 1].min(), verts[:, 1].max())
    ax.set_zlim(verts[:, 2].min(), verts[:, 2].max())
    ax.set_title(title, fontsize=10)
    ax.view_init(elev=elev, azim=azim)

# ==================== Parameters ====================
light_dirs = {
    "Right": [1,0,0],
    "Left": [-1,0,0],
    "Front": [0,1,0],
    "Back": [0,-1,0],
    "Top": [0,0,1],
    "Bottom": [0,0,-1]
}

light_colors = {
    "White": [1,1,1],
    "Warm": [1,0.92,0.85],
    "Cool": [0.85,0.9,1],
    "Red": [1,0.3,0.3],
    "Green": [0.3,1,0.3],
    "Blue": [0.3,0.3,1]
}

view_angles = {
    "Front": (15, -65),
    "Side": (15, 0),
    "Back": (15, 120),
    "Top": (-90, -60)
}

# Default light direction for color and view comparisons
default_light_dir = [0.5, 0.5, 1.0]

# ==================== Generate Figures ====================
# Figure 1: Different light directions
fig1 = plt.figure(figsize=(16, 9))
for idx, (name, ldir) in enumerate(light_dirs.items()):
    ax = fig1.add_subplot(2, 3, idx + 1, projection='3d')
    colors = compute_lighting(mesh.face_normals, face_colors, ldir, [1,1,1], 0.3, 0.8, -90, -60)
    draw_mesh(ax, colors, name, -90, -60)
plt.savefig('relighting_direction_comparison.png')

# Figure 2: Different light colors
fig2 = plt.figure(figsize=(15, 10))
for idx, (name, rgb) in enumerate(light_colors.items()):
    ax = fig2.add_subplot(2, 3, idx + 1, projection='3d')
    colors = compute_lighting(mesh.face_normals, face_colors, default_light_dir, rgb, 0.3, 0.8, -90, -60)
    draw_mesh(ax, colors, name, -90, -60)
plt.savefig('relighting_color_comparison.png')

# Figure 3: Different camera views
fig3 = plt.figure(figsize=(12, 10))
for idx, (name, (elev, azim)) in enumerate(view_angles.items()):
    ax = fig3.add_subplot(2, 2, idx + 1, projection='3d')
    colors = compute_lighting(mesh.face_normals, face_colors, default_light_dir, [1,1,1], 0.3, 0.8, elev, azim)
    draw_mesh(ax, colors, name, elev, azim)
plt.savefig('relighting_view_comparison.png')

plt.show()