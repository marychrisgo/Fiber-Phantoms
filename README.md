# Fiber-Phantoms

### Table of Contents

[Description](https://github.com/marychrisgo/Fiber-Phantoms#description)

[Installation](https://github.com/marychrisgo/Fiber-Phantoms#installation)

[Usage](https://github.com/marychrisgo/Fiber-Phantoms#usage)

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


* How to run
  There are two main files for running:
  - `main.py` - this script is the main running file
  - `parameters.json` - where the user sets the parameters both for the volume and scanning configurations
  - Detail
* ASTRA documentation
* Defects
* Curve intensity
* Pre-defined parameters 

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

2. **Download the wheel file and install the Fiber-Phantom package: (email marychrismcr@liacs.leidenuniv.nl**
    ```sh
    pip install fiber_phantom-0.1.0-py3-none-any.whl
    ```

3. **Install ASTRA using Conda:**
    ```sh
    conda install -c astra-toolbox astra-toolbox
    ```


## Usage

1. **Run the main.py (This script is a sample script of how to use fiber_phantom). In the same folder, parameters.json should also be present:**
    ```sh
    python main.py
    ```

This will execute the script and generate the fiber phantoms as specified in your configuration.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

