from distutils.core import setup

setup(
    name='SPACE Labelling',
    version='1.0',
    description='Radio measurement labelling utility',
    author='Aaron Empey',
    maintainer='Corentin Louis',
    maintainer_email='corentin.louis@dias.ie ',
    data_files=[('config', ['config/*.json'])],
    scripts=['space_label.py'],
    install_requires=[
        'scipy', 'numpy', 'matplotlib', 'shapely'
    ]
)
