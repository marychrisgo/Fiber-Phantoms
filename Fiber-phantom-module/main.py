import os
import numpy as np
import h5py
import json
import time 

from fiber_phantom.next_point_generator import NextPointGenerator
from fiber_phantom.defects import DefectGenerator
import fiber_phantom.generate_filaments as gf
import fiber_phantom.perform_ASTRA as tomo

def main():
    # Start the timer
    start_time = time.time()

    # Create the FiberDataset folder if it doesn't exist
    dataset_folder = "FiberDataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)

    # Load parameters from the JSON file
    with open("fiber_phantom/parameters.json", "r") as file:
        params = json.load(file)
    
    # Loop through volumes to generate and save
    for i in range(200, 200 + params["num_volumes"]):
        volume = np.zeros(params["volume_dimensions"], dtype=np.float32)
        random_seed = params["random_seed"] + i  # different seed for each volume
        np.random.seed(random_seed)

        # Generate filaments in the volume
        gf.generate_and_count_filaments(
            volume, 
            params["num_filaments"], 
            NextPointGenerator(mode=params["generator_mode"]), 
            DefectGenerator(defect_type=params["defect_type"], params=params["square_notch_params"]), #CHANGE THIS!!!
            params["pipe_radius"],
            params["min_length"],
            params["max_length"], 
            params["radius"]
        )

        # Save the volume in the FiberDataset folder
        volume_filename = os.path.join(dataset_folder, f"filaments_volume_{i}.nii")
        gf.save_as_nifti(volume, volume_filename)

        # If ASTRA reconstruction is enabled, perform it and save results
        if params["ASTRA_reconstruction"]:
            original_recon, noisy_recon = tomo.perform_tomography(
                volume,
                params["volume_dimensions"],
                params["num_angles"],
                params["geometry_type"],
                params["det_width_u"],
                params["det_width_v"],
                params["det_count_x"],
                params["det_count_y"],
                params["i0"],
                params["gamma"],
                params["algorithm"],
                params["show_plots"], 
                params["source_origin"],
                params["origin_det"]
            )

            # Save the reconstructions in the FiberDataset folder
            gf.save_as_nifti(original_recon, os.path.join(dataset_folder, f"original_reconstruction_{i}.nii"))
            gf.save_as_nifti(noisy_recon, os.path.join(dataset_folder, f"noisy_reconstruction_{i}.nii"))

        # Save volume and reconstructions data to HDF5 format in the FiberDataset folder
        hdf5_filename = os.path.join(dataset_folder, f"volume_and_reconstruction_{i}.hdf5")
        with h5py.File(hdf5_filename, "w") as h5f:
            for key, value in params.items():
                h5f.attrs[key] = str(value)
            h5f.attrs["random_seed"] = str(random_seed)

    # End the timer and print elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Total processing time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()
