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
        install_requires=['numpy>=1.26.0', 'psutil==5.9.8', 'py-cpuinfo==9.0.0', 'prettytable'],
        
        keywords=['python', 'benchmarking', 'system'],
        classifiers= [
            'Programming Language :: Python :: 3',
            'Operating System :: Linux'
        ]
)