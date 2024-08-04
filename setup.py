from os import path, environ, makedirs
import subprocess
import shutil

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext as _build_ext

from Cython.Build import cythonize


working_directory   = path.abspath(path.dirname(__file__))
pycmg_dir           = "pycmg"
libcmg_dir          = path.join(pycmg_dir,'libcmg')
lib_dir             = path.join(working_directory, libcmg_dir)

long_description    = open(path.join(working_directory, 'README.md'), encoding='utf-8').read()

environ["CC"]       = "g++-13"
environ["CXX"]      = "g++-13"

# ---------------------------------------------------------------------------------------------------------------------------
# Function to build C++ libraries using a Makefile
def build_cpp_libraries(lib_dir):
    subprocess.check_call("make", cwd=lib_dir)

build_cpp_libraries(lib_dir)

extensions = [
    Extension(
        'pycmg',
        sources=[path.join(pycmg_dir, 'libpycmg.pyx'),],
        include_dirs=[libcmg_dir],
        libraries=['cmg', 'surge'],
        library_dirs=[libcmg_dir],
        extra_objects=[path.join(libcmg_dir,'libsurge.a'),path.join(libcmg_dir,'libcmg.a'),],
        extra_compile_args=['-std=c++20'],
        extra_link_args=[path.join(libcmg_dir,'libcmg.a'), path.join(libcmg_dir,'libsurge.a'),]
    )
]

setup(
    name                                = "pycmg",
    version                             = open('Version.txt').read(),
    install_requires                    = open('requirements.txt').read().splitlines(),
    url                                 = 'https://github.com/osick/pycmg',
    author                              = 'Oliver Sick',
    author_email                        = 'oliver.sick@gmail.com',
    description                         = 'Fast chess move generator library for python',
    long_description                    = long_description,
    long_description_content_type       = 'text/markdown',
    python_requires                     = '>=3.6',
    classifiers                         = [
    'Programming Language :: Python :: 3',
    'Programming Language :: C++',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Topic :: Games/Entertainment :: Board Games',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    packages                            = [], #find_packages(), #
    ext_modules                         = cythonize(extensions),
    package_data                        = {'pycmg': ['LICENCE','README.md',path.join(pycmg_dir,'test.py')],},
    include_package_data                = True,
)