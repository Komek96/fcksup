import trimesh
import numpy as np
import os
import keyboard  # For detecting Esc key

def remove_supports(stl_path, output_dir):
    """Removes support structures from an STL file."""
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Extract filename and set output path
    file_name = os.path.basename(stl_path).replace(".stl", "_cleaned.stl")
    output_path = os.path.join(output_dir, file_name)

    # Load the STL model
    mesh = trimesh.load_mesh(stl_path)

    # Identify connected components
    components = mesh.split(only_watertight=False)  # Split into separate pieces

    if len(components) <= 1:
        print(f"[INFO] No separate supports detected for: {file_name}. Saving original file.")
        mesh.export(output_path)
        return

    # Find the largest component (assumed to be the main model)
    largest_component = max(components, key=lambda comp: len(comp.faces))

    # Save the cleaned STL file
    largest_component.export(output_path)
    print(f"✅ Cleaned file saved: {output_path}")

def process_directory(input_dir, output_dir):
    """Processes all STL files in a directory."""
    if not os.path.isdir(input_dir):
        print(f"❌ Error: The input directory '{input_dir}' does not exist.")
        return

    stl_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".stl")]

    if not stl_files:
        print(f"⚠️ No STL files found in: {input_dir}")
        return

    print(f"🔍 Found {len(stl_files)} STL files. Processing...")

    for stl_file in stl_files:
        input_path = os.path.join(input_dir, stl_file)
        remove_supports(input_path, output_dir)

    print(f"🎉 Batch processing complete. Cleaned files are in: {output_dir}")

# Main loop to allow repeated batch processing
while True:
    input_directory = input("\nEnter the path to the directory containing STL files: ").strip().strip('"')
    output_directory = input("Enter the output directory: ").strip().strip('"')

    process_directory(input_directory, output_directory)

    # Ask if the user wants to process another batch
    print("\nWould you like to process another batch?")
    print("Press [Enter] to continue or [Esc] to exit.")

    while True:
        if keyboard.is_pressed("enter"):
            print("🔄 Restarting batch process...\n")
            break  # Restart the loop
        elif keyboard.is_pressed("esc"):
            print("🚪 Exiting program. Goodbye!")
            exit()  # Exit the program
