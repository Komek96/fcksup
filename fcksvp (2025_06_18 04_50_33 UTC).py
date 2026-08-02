import trimesh
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Global variable to track processing state
processing_thread = None

def browse_directory(entry_widget):
    """Open file dialog to select a directory."""
    directory = filedialog.askdirectory()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, directory)

def compare_file_size(cleaned_file, reference_dir):
    """Compares the cleaned file's size to a reference file."""
    if not os.path.exists(reference_dir):
        return False  

    reference_file = os.path.join(reference_dir, os.path.basename(cleaned_file))
    if not os.path.exists(reference_file):
        return False  

    cleaned_size = os.path.getsize(cleaned_file)
    reference_size = os.path.getsize(reference_file)

    size_difference = abs(cleaned_size - reference_size) / reference_size
    return size_difference < 0.10  # Allow up to 10% difference


    """Loads and visualizes the STL file, highlighting detected supports."""
    mesh = trimesh.load_mesh(stl_path)
    components = mesh.split(only_watertight=False)  

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')

    for comp in components:
        bbox = comp.bounds  
        bbox_dims = bbox[1] - bbox[0]  
        min_dimension = min(bbox_dims)  

        color = 'red' if min_dimension < thickness_threshold and comp.volume < 1000 else 'gray'

        poly3d = [[comp.vertices[vert] for vert in face] for face in comp.faces]
        ax.add_collection3d(Poly3DCollection(poly3d, facecolors=color, linewidths=0.5, edgecolors='k', alpha=0.6))

    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.set_zlabel("Z Axis")
    ax.set_title("Support Detection Preview (Red = Supports)")

    plt.show()

def is_likely_support(component, thickness_threshold=2.0):
    """Detects if a component is a support based on absolute thickness."""
    bbox = component.bounds  
    bbox_dims = bbox[1] - bbox[0]  
    min_dimension = min(bbox_dims)  

    return min_dimension < thickness_threshold and component.volume < 1000

def has_large_overhang(component, angle_threshold=40):
    """Detects if a component has steep overhangs."""
    normals = component.face_normals  
    vertical_normals = normals[:, 2]  

    steep_faces = (vertical_normals < np.cos(np.radians(angle_threshold)))  
    return np.sum(steep_faces) / len(steep_faces) > 0.3  

def is_definite_base(component, base_threshold, volume_threshold):
    """Detects if a component is definitely a base."""
    bbox = component.bounds  
    min_z = bbox[0, 2]  
    max_z = bbox[1, 2]  

    is_low = min_z < base_threshold  
    is_flat = (max_z - min_z) < 1.5  
    is_small = component.volume < volume_threshold * 2  

    return is_low and is_flat and is_small  

def remove_supports_and_base(stl_path, output_dir, reference_dir, needs_review_dir, log_text):
    """Removes supports and base, then verifies the cleaned file."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(needs_review_dir, exist_ok=True)  

    file_name = os.path.basename(stl_path).replace(".stl", "_cleaned.stl")
    output_path = os.path.join(output_dir, file_name)

    try:
        mesh = trimesh.load_mesh(stl_path)
        components = mesh.split(only_watertight=False)  

        if len(components) <= 1:
            log_text.insert(tk.END, f"[INFO] No separate supports detected for: {file_name}. Saving original file.\n")
            mesh.export(output_path)
            return

        component_volumes = [comp.volume for comp in components]
        volume_threshold = max(component_volumes) * 0.15  
        face_threshold = max(len(comp.faces) for comp in components) * 0.15  

        while True:
            cleaned_components = [
                comp for comp in components
                if (comp.volume > volume_threshold or len(comp.faces) > face_threshold)
                and not is_likely_support(comp)
                and not has_large_overhang(comp)
            ]

            cleaned_components.sort(key=lambda comp: comp.volume, reverse=True)
            final_components = cleaned_components[:4] if len(cleaned_components) > 4 else cleaned_components

            cleaned_mesh = trimesh.util.concatenate(final_components)
            cleaned_mesh.export(output_path)

            if compare_file_size(output_path, reference_dir):
                log_text.insert(tk.END, f"✅ File size correct. Final version saved: {output_path}\n")
                break  # Stop retrying if file size is correct

            log_text.insert(tk.END, f"⚠️ [WARNING] File size incorrect. Retrying with adjusted settings...\n")
            volume_threshold *= 0.95  
            base_threshold += 0.1  

    except Exception as e:
        log_text.insert(tk.END, f"❌ Error processing {file_name}: {e}\n")

def process_directory(input_dir, output_dir, reference_dir, needs_review_dir, log_text, progress_bar, start_button):
    """Processes all STL files in a directory and updates the progress bar."""
    global processing_thread

    if processing_thread and processing_thread.is_alive():
        messagebox.showwarning("Warning", "Processing is already running. Please wait.")
        return

    if not os.path.isdir(input_dir):
        messagebox.showerror("Error", f"The input directory '{input_dir}' does not exist.")
        return

    stl_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".stl")]

    if not stl_files:
        messagebox.showwarning("Warning", f"No STL files found in: {input_dir}")
        return

    log_text.insert(tk.END, f"🔍 Found {len(stl_files)} STL files. Processing...\n")

    progress_bar["value"] = 0
    progress_bar["maximum"] = len(stl_files)

    start_button.config(state=tk.DISABLED)

    def process_files():
        global processing_thread
        for index, stl_file in enumerate(stl_files):
            input_path = os.path.join(input_dir, stl_file)
            remove_supports_and_base(input_path, output_dir, reference_dir, needs_review_dir, log_text)

            root.after(100, lambda i=index+1: progress_bar.config(value=i))

        log_text.insert(tk.END, f"🎉 Batch processing complete. Cleaned files are in: {output_dir}\n")
        messagebox.showinfo("Complete", "Batch processing completed successfully!")

        start_button.config(state=tk.NORMAL)
        processing_thread = None

    processing_thread = threading.Thread(target=process_files, daemon=True)
    processing_thread.start()
# GUI Setup
root = tk.Tk()
root.title("STL Support Remover")
root.geometry("700x500")
root.resizable(False, False)

tk.Label(root, text="Input Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_directory(input_entry)).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_directory(output_entry)).grid(row=1, column=2, padx=5, pady=5)

tk.Label(root, text="Reference Directory (for verification):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
reference_entry = tk.Entry(root, width=50)
reference_entry.grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_directory(reference_entry)).grid(row=2, column=2, padx=5, pady=5)

tk.Label(root, text="Needs Review Directory:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
review_entry = tk.Entry(root, width=50)
review_entry.grid(row=3, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_directory(review_entry)).grid(row=3, column=2, padx=5, pady=5)

# Start Button
start_button = tk.Button(
    root, text="Start Processing", bg="green", fg="white", font=("Arial", 12, "bold"),
    command=lambda: process_directory(
        input_entry.get(), output_entry.get(), reference_entry.get(),
        review_entry.get(), log_text, progress_bar, start_button
    )
)
start_button.grid(row=4, column=1, pady=10)

# Progress Bar
progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

# Log Output Box
log_text = scrolledtext.ScrolledText(root, height=10, width=80)
log_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

# Start the GUI
root.mainloop()
