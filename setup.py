from setuptools import setup, find_packages

setup(
    name="loopertrx",
    version="0.1",
    packages=find_packages(),
    scripts=['loopertrx.py'],
    install_requires=['pyusb>=1.0.0'],

    author="Reiner Herrmann",
    author_email="reiner@reiner-h.de",
    license="GPLv2+",
)
