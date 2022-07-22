from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name='SPACE Labelling',
    version='2.0',
    description='Radio measurement labelling utility',
    author='Corentin Louis',
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
        'tfcat @ git+https://gitlab.obspm.fr/maser/catalogues/tfcat.git'
    ]
)
