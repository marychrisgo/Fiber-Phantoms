import argparse
import json
import os
import random
import time

import h5py
import numpy as np

from fiber_phantom.next_point_generator import NextPointGenerator
from fiber_phantom.defects import DefectGenerator
import fiber_phantom.generate_filaments as gf

DEFAULT_PARAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")

# Which block of parameters.json each defect type reads its settings from
DEFECT_PARAMS_KEY = {
    "hole": "hole_params",
    "square_notch": "square_notch_params",
    "double_square_notch": "square_notch_params",
    "v_notch": "v_notch_params",
    "double_v_notch": "v_notch_params",
    "reduced": "reduced_params",
    "none": None,
}


def build_defect_generator(params):
    defect_type = params["defect_type"]
    if defect_type not in DEFECT_PARAMS_KEY:
        raise ValueError(f"Unknown defect_type '{defect_type}'. Choose one of: {', '.join(DEFECT_PARAMS_KEY)}")
    key = DEFECT_PARAMS_KEY[defect_type]
    defect_params = params.get(key, []) if key else []
    return DefectGenerator(defect_type=defect_type, params=defect_params)


def build_point_generator(params):
    mode = params["generator_mode"]
    if mode == "straight":
        # the straight generator needs to know the volume size
        return NextPointGenerator(mode=mode, volume_shape=params["volume_dimensions"])
    return NextPointGenerator(mode=mode)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate fiber phantoms and (optionally) simulate X-ray scans with ASTRA.")
    parser.add_argument("-p", "--params", default=DEFAULT_PARAMS_FILE,
                        help="path to the parameters JSON file (default: fiber_phantom/parameters.json)")
    parser.add_argument("-o", "--output", default="FiberDataset",
                        help="folder where the generated files are saved (default: ./FiberDataset)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    start_time = time.time()

    with open(args.params, "r") as file:
        params = json.load(file)

    if params["ASTRA_reconstruction"]:
        # imported only when needed, so phantoms can be generated without ASTRA/GPU
        import fiber_phantom.perform_ASTRA as tomo

    dataset_folder = args.output
    os.makedirs(dataset_folder, exist_ok=True)
    print(f"Using parameters from: {args.params}")
    print(f"Saving results to: {os.path.abspath(dataset_folder)}")

    for i in range(200, 200 + params["num_volumes"]):
        volume = np.zeros(params["volume_dimensions"], dtype=np.float32)
        random_seed = params["random_seed"] + i  # different seed for each volume
        np.random.seed(random_seed)
        random.seed(random_seed)  # fiber placement also uses Python's random module

        gf.generate_and_count_filaments(
            volume,
            params["num_filaments"],
            build_point_generator(params),
            build_defect_generator(params),
            params["pipe_radius"],
            params["min_length"],
            params["max_length"],
            params["radius_range"],
            params["bias"],
            preferred_direction=params.get("preferred_direction", [1, 0, 0]),
        )

        volume_filename = os.path.join(dataset_folder, f"filaments_volume_{i}.nii")
        gf.save_as_nifti(volume, volume_filename)

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
                params["algorithm"],
                params["show_plots"],
                params["source_origin"],
                params["origin_det"]
            )

            gf.save_as_nifti(original_recon, os.path.join(dataset_folder, f"original_reconstruction_{i}.nii"))
            gf.save_as_nifti(noisy_recon, os.path.join(dataset_folder, f"noisy_reconstruction_{i}.nii"))

        # Save the parameters used for this volume as HDF5 attributes
        hdf5_filename = os.path.join(dataset_folder, f"volume_and_reconstruction_{i}.hdf5")
        with h5py.File(hdf5_filename, "w") as h5f:
            for key, value in params.items():
                h5f.attrs[key] = str(value)
            h5f.attrs["random_seed"] = str(random_seed)

    elapsed_time = time.time() - start_time
    print(f"Total processing time: {elapsed_time} seconds")


if __name__ == "__main__":
    main()
