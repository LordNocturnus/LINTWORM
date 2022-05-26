from setuptools import setup, find_packages
from distutils.util import convert_path
import sys


# ver_path = convert_path('sim_common/version.py')
# with open(ver_path) as ver_file:
#     ns = {}
#     exec(ver_file.read(), ns)
#     version = ns['version']

setup(
    name='DRAGONS',
    version='0.0.1',
    description='Overarching framework for working with ODESSA',
    author='Delft Aerospace Rocket Engineering',
    author_email='felix@lagarden.de',
    # url='',

    install_requires=['gitpython',
                      'pyqt5',
                      "matplotlib",
                      "pandas",
                      "scipy"],

    packages=find_packages('.', exclude=["test"]),
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 1 - Pre-Alpha']
)