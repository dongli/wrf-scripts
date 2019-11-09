from distutils.core import setup, Extension
from Cython.Distutils import build_ext

setup(
	cmdclass={'build_ext': build_ext},
	ext_modules=[Extension("write_geogrid", ["write_geogrid.pyx"])]
)
