# Fiber-Phantoms

## Description
Fiber-Phantoms is a Python package for generating fiber phantoms and doing virtual X-ray scanning using the ASTRA Toolbox. This package facilitates the creation and manipulation of complex phantom structures for use in various scientific and engineering applications.

## Installation

### Prerequisites
Ensure you have Conda installed on your system. You can download and install Conda from [here](https://docs.conda.io/en/latest/miniconda.html).

### Steps
1. **Create and activate a new Conda environment:**
    ```sh
    conda create -n fiber_phantom python=3.10
    conda activate astra_env
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

