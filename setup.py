import os, subprocess
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

if(os.uname().sysname == "Darwin"):
    project_dir = os.path.dirname(os.path.realpath(__file__))
    mac_setup_script = os.path.join(project_dir, "scripts", "osx_check.sh")
    subprocess.check_call(mac_setup_script)
    print("################################################")
    print("OSX Installation Notice")
    print("################################################")
    print("In order to fully complete the installation, run 'sudo scripts/osx_post_install.sh'")
