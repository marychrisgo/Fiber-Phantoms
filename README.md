# Fiber-Phantoms

## Description
Fiber-Phantoms is a Python package for generating fiber phantoms and doing virtual X-ray scanning using the ASTRA Toolbox. This package facilitates the creation and manipulation of complex phantom structures for use in various scientific and engineering applications.

## Installation

### Prerequisites
Ensure you have Conda installed on your system. You can download and install Conda from [here](https://docs.conda.io/en/latest/miniconda.html).

### Steps
1. **Create and activate a new Conda environment:**
    ```sh
    conda create -n astra_env python=3.10
    conda activate astra_env
    ```

2. **Download the wheel file and install the Fiber-Phantom package:**
    ```sh
    pip install fiber_phantom-0.1.0-py3-none-any.whl
    ```

3. **Install ASTRA using Conda:**
    ```sh
    conda install numpy==1.24.2 matplotlib==3.7.1 scipy==1.10.1 nibabel==5.0.0 h5py==3.8.0
    conda install -c astra-toolbox astra-toolbox
    ```

4. **Install additional Python packages using pip: (only if the whl file did not successfully install these packages**
    ```sh
    pip install matplotlib
    pip install nibabel
    ```

## Usage

1. **Run the main script (main.py). In the same folder, parameters.json should also be present:**
    ```sh
    python main.py
    ```

This will execute the script and generate the fiber phantoms as specified in your configuration.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

