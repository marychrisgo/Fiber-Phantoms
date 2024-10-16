# Fiber-Phantoms

### Table of Contents

[Description](https://github.com/marychrisgo/Fiber-Phantoms#description)

[Installation](https://github.com/marychrisgo/Fiber-Phantoms#installation)

[Usage](https://github.com/marychrisgo/Fiber-Phantoms#usage)
- Directory Structure
- Description of Files
- How to run
- ASTRA documentation
- Defects
- Curve Intensity
- Pre-defined Parameters

[License](https://github.com/marychrisgo/Fiber-Phantoms#license)

## Description
*FibreSimulator* is a Python tool for generating uni-directional fiber phantoms and doing virtual X-ray scanning using the ASTRA Toolbox. Included in the repository are the source-code and the code manual/documentation. 

## Installation

### Prerequisites
Ensure you have Conda installed on your system. You can download and install Conda from [here](https://docs.conda.io/en/latest/miniconda.html).

### Steps
1. **Create and activate a new Conda environment:**
    ```sh
    conda create -n fiber_phantom python=3.10
    conda activate fiber_phantom
    ```

2. **Download the wheel file and install the [Fiber-Phantom package]([https://drive.google.com/file/d/1RDukIsBO8gBr5zlT2T6C49T0wjlQeKwY/view?usp=sharing](https://drive.google.com/file/d/1RDukIsBO8gBr5zlT2T6C49T0wjlQeKwY/view?usp=drive_link)):**
    ```sh
    pip install fiber_phantom-0.1.0-py3-none-any.whl
    ```

3. **Install ASTRA using Conda:**
    ```sh
    conda install -c astra-toolbox astra-toolbox
    ```


## Usage

* Directory Structure
```
Fiber-Phantoms
│   README.md
└───Fiber-phantom-module
    │   main.py
    │   requirements.txt
    │   setup.py
    └───fiber_phantom
        │   defects.py
        │   generate_filaments.py
        │   next_point_generator.py
        │   parameters.json
        └───perform_ASTRA.py

```
Description of files
- `defects.py` - contains classes of different macro-scale defects namely: hole, square notch, v-notch, double square notch, double v-notch, reduced
- `generate_filaments.py` - contains all function for generating a single fiber, includes the check before generating another point
- `next_point_generator.py` - contains classes for different fiber behaviour: straight, full-wave, half-wave, kinking, c-curve
- `perform_ASTRA.py` - contains the function for performing tomography to the volume.

| **Parameters**         | **Description**                                                                                                               |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| random_seed            | a fixed seed for randomization to ensure reproducibility: 36                                                                  |
| num_volumes            | number of volumes to generate: 1                                                                                               |
| volume_dimensions      | defines the dimensions of the volume in voxels: [256, 256, 256]                                                               |
| pipe_radius            | radius of the pipe/cylinder through which the filaments are generated, usually half of the x-dimension of the volume: 125 |
| num_filaments          | number of filaments to generate within the volume                                                                             |
| min_length, max_length | minimum and maximum lengths of the filaments: 80, 200                                                                         |
| radius_range           | range of the radius (follows a normal distribution)                                                                           |
| generator_mode         | either 'straight', 'kink_curve', 'c_curve', 'full_wave_curve', 'half_wave_curve'                                              |
| defect_type            | either 'hole', 'square_notch', 'double_square_notch', 'v_notch', 'double_v_notch', 'reduced', 'none'                          |
|                        |                                                                                                                               |
| ASTRA_reconstruction   | whether ASTRA toolbox will be used for reconstruction:'True' or 'False'                                                      |
| num_angles             | number of projection angles used for tomography                                                                               |
| geometry_type          | specifies the geometry of the beam: 'parallel3d' or 'cone'                                                                    |
| det_width_u            | distance between the center of two horizontally adjacent detector pixels                                                      |
| det_width_v            | distance between the centers of two vertically adjacent detector pixels                                                       |
| det_count_x            | number of detector rows in a single projection                                                                                |
| det_count_y            | number of detector columns in a single projection                                                                             |
| i0                     | Initial intensity of the X-ray beam used for simulation                                                                       |
| gamma                  | noise in the simulation                                                                                                       |
| algorithm              | reconstruction algorithm: 'FDK_CUDA', 'SIRT3D_CUDA'                                                                           |
| show_plots             | Enable or disable generation of plots for checking: 'True' or 'False'                                                         |
| source_original        | distance between  the source and the center of rotation                                                                       |
| origin_det             | distance between the center of rotation and detector array                                                                      |

* How to run
  There are two main files for running:
  - `main.py` - this script is the main running file
  - `parameters.json` - where the user sets the parameters both for the volume and scanning configurations

* ASTRA documentation
  - See [link](https://astra-toolbox.com/index.html)
* Defects
  1. **hole**
     - ![image](https://github.com/user-attachments/assets/b0b2030d-7ec0-49c9-9e52-1a302e7722a7)
     - In the `parameters.json` file, the following lines can be adjusted based on where you want to position the hole. For a volume of [256, 256, 256], the example below places the hole in the center, which is why the parameters are set as follows:
      ```
      "hole_params": [
        {
            "hole_center": [125, 125, 125],
            "hole_radius": 50
        }
      ]
      ```
  2. **square notch & double square notch**
     - ![image](https://github.com/user-attachments/assets/bace3b39-539a-4980-9d39-74279136d721)
     - The parameters set in `parameters.json` are for the square notch. For double square notch, it uses the same parameters but it is applied on the opposite side. 
      ```
      "square_notch_params": [
        {
            "square_notch_center": [125, 0], 
            "square_notch_wh": 50
        }
      ]
      ```
  3. **v-notch and  double v-notch**
     - ![image](https://github.com/user-attachments/assets/c04e1f89-3a7f-4c86-99c9-63f3b285d643)
     - The parameters are as follows:
    ```
    "v_notch_params": [
        {
            "v_notch_center": [125, 0], 
            "v_notch_height": 50, 
            "v_notch_width": 100
        }
    ]
    ```

  5. **reduced**
     - ![image](https://github.com/user-attachments/assets/3265d54b-5a62-4b82-a1cd-3ade959f1053)
     - 'reduced_slice_thickness' is the vertical length; 'reduced_radius' is the remaining raduis of the inner fibers
    ```
    "reduced_params": [
        {
            "reduced_center": [125, 125],
            "reduced_radius": 100,
            "reduced_slice_thickness": 25
        }
    ]
    ```

* Curve intensity
  - ![image](https://github.com/user-attachments/assets/bfd9e641-2d8d-4ea5-a96a-5d3f60e834c8)
  - The curve intesities are the following: c_curve, kink_curve, straight, full_wave_curve, half_wave_curve.
  - Currently, the curves are set for [256, 256, 256] volume. But if the user want to customize this with a bigger or smaller volume, see `next_point_generator.py`.
  - Each class is the desired curve and the "wave_center", "wave_amplitude", "wave_frequency" can be change in the initialization.
* Other samples
  - ![image](https://github.com/user-attachments/assets/4a1abf84-b6a6-4ca8-aebc-a83fa7429705)
  - The photo above exhibits the flexibility of the simulator to customize the volume. This volume is a c_curve with the curve_center outside of the volume dimension. Because of how it was parametrize, we technically see only half of the 'c_curve'.

    
* Pre-defined parameters
  - See `generate_filaments.py`
  - max_attempts : maximum attempt of the script in finding a fiber point that does not collide with another fiber point
  - num_voids: at the end of the generation of the volume, there are 100 small spheres generated along the resin. This small spheres in the resin mimics voids found in the sample.
  - cluster_centers: there are also pre-defined location of cluster_centers which are more prominent if you have spaced fibers


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

