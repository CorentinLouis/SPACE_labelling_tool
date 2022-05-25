from distutils.core import setup

setup(
    name='SPACE Labelling',
    version='2.0',
    description='Radio measurement labelling utility',
    author='Aaron Empey',
    maintainer='Corentin Louis',
    maintainer_email='corentin.louis@dias.ie',
    data_files=[
        ('config', ['config/*.json'])
    ],
    packages=['spacelabel'],
    scripts=['space_label.py'],
    install_requires=[
        'wheel',
        'scipy',
        'numpy',
        'matplotlib',
        'shapely',
        'scipy',
        'astropy',
        'h5py',
        'tfcat @ git+https://gitlab.obspm.fr/maser/catalogues/tfcat.git@b99296190e4ac047ef01fdb3e5deabb1e5651443'
    ]
)
