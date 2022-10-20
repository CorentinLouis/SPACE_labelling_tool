from distutils.core import setup
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='space labelling tool',
    version='2.0.0',
    description='Interactive python tool designed to label radio emission features of interest in a temporal-spectral map',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CorentinLouis/SPACE_labelling_tool",
    authors=[
    "Corentin K. Louis, C. M. Jackman, S. W. Mangham, K. D. Smith, E. P. O'Dwyer, A. Empey, B. Cecconi, A. Boudouma, P. Zarka, S. Maloney"
    ],
    maintainer='Corentin Louis',
    maintainer_email='corentin.louis@dias.ie',
    packages=find_packages(),
    include_package_data=True,
    entry_points = {'console_scripts': ['spacelabel = spacelabel.__main__:main'],},
    install_requires=[
        'wheel',
        'scipy',
        'numpy',
        'matplotlib',
        'shapely',
        'scipy',
        'astropy',
        'h5py',
        'TFCat'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_require='>3.7',
    license='MIT',
)
