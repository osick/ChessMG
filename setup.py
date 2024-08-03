from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
from os import path, getcwd, environ

working_directory   = path.abspath(path.dirname(__file__))
long_description    = open(path.join(working_directory, 'README.md'), encoding='utf-8').read()
environ["CC"]       = "g++-13"
environ["CXX"]      = "g++-13"

extensions = [
    Extension(
        name          = "libsurge", 
        sources       = [path.join(getcwd(),"src","libsurge.cpp")],
        language      = "c++",        
        include_dirs  = ["include"],  
        libraries     = ["surge"],
        library_dirs  = ["."],
        extra_compile_args=["-std=c++20"]
    ),    
    Extension(
        name          = "libcmg", 
        sources       = [path.join(getcwd(),"src","libcmg.cpp")],
        language      = "c++",        
        include_dirs  = ["include"],  
        libraries     = ["cmg"],
        library_dirs  = ["."],
        extra_compile_args=["-std=c++20"]
    ),
    Extension(
        name          = "pycmg", 
        sources       = [path.join(getcwd(),"src","libpycmg.pyx"), path.join(getcwd(),"src","libcmg.cpp")],
        language      = "c++",        
        include_dirs  = ["include"],  
        #library_dirs = [f"{working_directory}"],
        libraries     = [],
        library_dirs  = ["."],
        extra_compile_args=["-std=c++20"]
    ),
]

setup(
    name            = "pycmg",
    version         = '0.0.1',
    url             = 'https://github.com/osick/pycmg',
    author          = 'Oliver Sick',
    author_email    = 'oliver.sick@gmail.com',
    description     = 'fast chess move generator for python',
    long_description= long_description,
    long_description_content_type= 'text/markdown',
    packages        = find_packages(),
    ext_modules     = cythonize(extensions),
    python_requires = '>=3.6',
    install_requires= open('requirements.txt').read().splitlines(),
    classifiers     = [
        'Programming Language :: Python :: 3',
        'Programming Language :: C++',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Games/Entertainment :: Board Games',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)