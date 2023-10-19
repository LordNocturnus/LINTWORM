from setuptools import setup, find_packages

setup(
    name='LINTWORM',
    version='1.0.0',
    description='A python parser for checking the state of documentation',
    author='Delft Aerospace Rocket Engineering',
    author_email='felix@lagarden.de',
    # url='',

    install_requires=["pandas"],

    packages=find_packages('.', exclude=["test"]),
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 1 - Pre-Alpha']
)