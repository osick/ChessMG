from os import path, environ, makedirs
import subprocess
import shutil

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext as _build_ext

from Cython.Build import cythonize
import numpy


working_directory   = path.abspath(path.dirname(__file__))
chessmg_dir           = "chessmg"
libcmg_dir          = path.join(chessmg_dir,'libcmg')
lib_dir             = path.join(working_directory, libcmg_dir)

long_description    = open(path.join(working_directory, 'README.md'), encoding='utf-8').read()

environ["CC"]       = "g++"
environ["CXX"]      = "g++"

# ---------------------------------------------------------------------------------------------------------------------------
# Function to build C++ libraries using a Makefile
def build_cpp_libraries(lib_dir):
    subprocess.check_call("make", cwd=lib_dir)

build_cpp_libraries(lib_dir)

extensions = [
    Extension(
        'chessmg.libchessmg',  # Fixed: was 'chessmglib', should be 'chessmg.libchessmg'
        sources=[path.join(chessmg_dir, 'libchessmg.pyx'),],
        include_dirs=[libcmg_dir, numpy.get_include()],  # Added numpy include
        libraries=['cmg', 'surge'],
        library_dirs=[libcmg_dir],
        extra_objects=[path.join(libcmg_dir,'libsurge.a'),path.join(libcmg_dir,'libcmg.a'),],
        extra_compile_args=['-std=c++20'],
        extra_link_args=[path.join(libcmg_dir,'libcmg.a'), path.join(libcmg_dir,'libsurge.a'),]
    )
]

setup(
    name                                = "chessmg",
    version                             = open('Version.txt').read().strip(),
    install_requires                    = open('requirements.txt').read().splitlines(),
    url                                 = 'https://github.com/osick/chessmg',
    author                              = 'Oliver Sick',
    author_email                        = 'oliver.sick@gmail.com',
    description                         = 'High-performance chess move generation and helpmate tablebase system',
    long_description                    = long_description,
    long_description_content_type       = 'text/markdown',
    python_requires                     = '>=3.8',
    classifiers                         = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Games/Entertainment :: Board Games',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: C++',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],

    packages                            = find_packages(),
    ext_modules                         = cythonize(extensions),
    package_data                        = {
        'chessmg': ['LICENCE', 'README.md'],
        'tablebase': ['README.md'],
    },
    include_package_data                = True,

    # Entry points for console scripts
    entry_points                        = {
        'console_scripts': [
            'cmgtb=tablebase.cli:main',
        ],
    },

    # Development dependencies
    extras_require                      = {
        'dev': [
            'pytest>=7.0',
            'black>=22.0',
            'mypy>=0.950',
            'pytest-cov>=3.0',
        ],
    },
)