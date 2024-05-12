from pathlib import Path
from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'PySysLoadBench benchmarks functions for system load'
LONG_DESCRIPTION = 'PySysLoadBench benchmarks functions for system load including CPU and RAM utilization as well as timing'

# Setting up
setup(
        name="sysloadbench", 
        version=VERSION,
        author="Jan Hochstrasser",
        author_email="janhochstrasser@gmx.ch",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['numpy', 'psutil', 'py-cpuinfo', 'pathos', 'prettytable'],
        
        keywords=['python', 'benchmarking', 'system'],
        classifiers= [
            'Programming Language :: Python :: 3',
            'Operating System :: Linux'
        ]
)