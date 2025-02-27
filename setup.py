from setuptools import setup, find_packages, Command

PKG_NAME = "src"
VERSION = "1.0.0"

def _read_install_requires():
    with open('requirements.txt') as file:
        requirements = file.read().splitlines()
        
    return [
        str(requirement) for requirement in requirements
    ]

class CleanEggInfo(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import os
        import shutil
        #Remove egg-info directory
        if os.path.exists(os.path.join(PKG_NAME, f'{PKG_NAME}.egg-info')):
            shutil.rmtree(os.path.join(PKG_NAME, f'{PKG_NAME}.egg-info'))
        
        if os.path.exists(f'{PKG_NAME}.egg-info'):
            shutil.rmtree(f'{PKG_NAME}.egg-info')

setup(
    name=PKG_NAME,
    version=VERSION,
    author=f"Davide Stenner",
    description="Package for fanta scraping",
    packages=find_packages(PKG_NAME),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=_read_install_requires(),
    python_requires="==3.13.*",
    cmdclass={'clean': CleanEggInfo}
)
