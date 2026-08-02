import trimesh
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

def remove_supports(stl_path, output_dir, log_text):
    """Removes support structures from an STL file."""
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    file_name = os.path.basename(stl_path).replace(".stl", "_cleaned.stl")
    output_path = os.path.join(output_dir, file_name)

    try:
        mesh = trimesh.load_mesh(stl_path)

        # Identify connected components
        components = mesh.split(only_watertight=False)  # Split into separate parts

        if len(components) <= 1:
            log_text.insert(tk.END, f"[INFO] No separate supports detected for: {file_name}. Saving original file.\n")
            mesh.export(output_path)
        else:
            # Keep only the largest component (assumed to be the model)
            largest_component = max(components, key=lambda comp: len(comp.faces))
            largest_component.export(output_path)
            log_text.insert(tk.END, f"✅ Cleaned file saved: {output_path}\n")

    except Exception as e:
        log_text.insert(tk.END, f"❌ Error processing {file_name}: {e}\n")

def process_directory(input_dir, output_dir, log_text, progress_bar):
    """Processes all STL files in a directory and updates the progress bar."""
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

    for index, stl_file in enumerate(stl_files):
        input_path = os.path.join(input_dir, stl_file)
        remove_supports(input_path, output_dir, log_text)

        # Update progress bar
        progress_bar["value"] = index + 1
        root.update_idletasks()  # Refresh GUI

    log_text.insert(tk.END, f"🎉 Batch processing complete. Cleaned files are in: {output_dir}\n")
    messagebox.showinfo("Complete", "Batch processing completed successfully!")

def browse_input_dir(entry_widget):
    """Open file dialog to select input directory."""
    directory = filedialog.askdirectory()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, directory)

def browse_output_dir(entry_widget):
    """Open file dialog to select output directory."""
    directory = filedialog.askdirectory()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, directory)

def start_processing(input_entry, output_entry, log_text, progress_bar):
    """Start the batch process."""
    input_dir = input_entry.get().strip()
    output_dir = output_entry.get().strip()

    if not input_dir or not output_dir:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return

    log_text.delete(1.0, tk.END)  # Clear previous logs
    process_directory(input_dir, output_dir, log_text, progress_bar)

# GUI Setup
root = tk.Tk()
root.title("STL Support Remover")
root.geometry("600x450")
root.resizable(False, False)

# Input Directory Selection
tk.Label(root, text="Input Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_input_dir(input_entry)).grid(row=0, column=2, padx=5, pady=5)

# Output Directory Selection
tk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_output_dir(output_entry)).grid(row=1, column=2, padx=5, pady=5)

# Start Button
tk.Button(root, text="Start Processing", command=lambda: start_processing(input_entry, output_entry, log_text, progress_bar), 
          bg="green", fg="white", font=("Arial", 12, "bold")).grid(row=2, column=1, pady=10)

# Progress Bar
progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

# Log Output Box
log_text = scrolledtext.ScrolledText(root, height=10, width=70)
log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

# Run the GUI
root.mainloop()
