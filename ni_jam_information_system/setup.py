from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='NI-Jam-Information-System',
    packages=['ni_jam_information_system'],
    include_package_data=True,
    install_requires=[
        requirements,
    ],
)