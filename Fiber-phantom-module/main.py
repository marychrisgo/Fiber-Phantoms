import numpy as np
import h5py
import json
import time 

from fiber_phantom.next_point_generator import NextPointGenerator
from fiber_phantom.defects import DefectGenerator
import fiber_phantom.generate_filaments as gf
import fiber_phantom.perform_ASTRA as tomo

def main():

    start_time = time.time()
    with open("fiber_phantom/parameters.json", "r") as file:
        params = json.load(file)
    
    for i in range(91, 91+params["num_volumes"]):
        volume = np.zeros(params["volume_dimensions"])
        random_seed = params["random_seed"] + i  # diff seed for each volume
        np.random.seed(random_seed) 

        gf.generate_and_count_filaments(
            volume, 
            params["num_filaments"], 
            NextPointGenerator(mode=params["generator_mode"]), 
            DefectGenerator(defect_type=params["defect_type"], params=params["reduced_params"]), # !!! params needs to be changed as well, improve this!!
            params["pipe_radius"],
            params["min_length"],
            params["max_length"]
            )

        volume_filename = f"filaments_volume_{i}.nii"
        gf.save_as_nifti(volume, volume_filename)

        # ############################################################
        # # Comment this out if you don't want the ASTRA reconstruction part

        # original_recon, noisy_recon = tomo.perform_tomography(
        #     volume, 
        #     params["volume_dimensions"], 
        #     params["num_angles"], 
        #     params["geometry_type"],
        #     params["det_width_u"], 
        #     params["det_width_v"], 
        #     params["det_count_x"],
        #     params["det_count_y"], 
        #     params["i0"], 
        #     params["gamma"], 
        #     params["algorithm"], 
        #     params["show_plots"]
        # )

        # gf.save_as_nifti(original_recon, f"original_reconstruction_{i}.nii")
        # gf.save_as_nifti(noisy_recon, f"noisy_reconstruction_{i}.nii")

        # ############################################################

        with h5py.File(f"volume_and_reconstruction_{i}.hdf5", "w") as h5f:
            for key, value in params.items():
                h5f.attrs[key] = str(value)
            h5f.attrs["random_seed"] = str(random_seed)

        end_time = time.time() 
        elapsed_time = end_time - start_time

        print(f"Total processing time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()