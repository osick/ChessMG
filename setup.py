from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
from os import path, getcwd, environ

working_directory   = path.abspath(path.dirname(__file__))
long_description    = open(path.join(working_directory, 'README.md'), encoding='utf-8').read()
environ["CC"]       = "g++-13"
environ["CXX"]      = "g++-13"

extensions = [
    Extension(
        name          = "libpycmg", 
        sources       = [path.join(getcwd(),"src","libpycmg.pyx"), path.join(getcwd(),"src","libcmg.cpp")],
        language      = "c++",        
        include_dirs  = ["include"],  
        #library_dirs = [f"{working_directory}"],
        libraries     = ["cmg"],
        library_dirs  = ["."],
        extra_compile_args=["-std=c++20"]
    ),
]

setup(
    name="pycmg",
    version='0.0.1',
    url='https://github.com/osick/pycmg',
    author='Oliver Sick',
    author_email='oliver.sick@gmail.com',
    description='fast chess move generator for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    ext_modules=cythonize(extensions),
    install_requires=[],
)