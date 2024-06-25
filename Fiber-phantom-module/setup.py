# setup.py

from setuptools import setup, find_packages

setup(
    name='fiber_phantom',
    version='0.1.0',
    description='A package for generating fiber phantoms with cylinder holes',
    author='MC, Daan, Joost',
    author_email='marychrismcr@liacs.leidenuniv.nl',
    packages=find_packages(include=['fiber_phantom', 'fiber_phantom.*']),
    install_requires=[
        'numpy==1.24.2',
        'h5py==3.8.0',
        'matplotlib==3.7.1',
        'nibabel==5.2.1',
        'scipy==1.13.1'
        # Add other dependencies here
    ],
    entry_points={
        'console_scripts': [
            'fiber_phantom=fiber_phantom.main:main',
        ],
    },
)
