cimport numpy as np

cdef extern from 'write_geogrid.h':
    int write_geogrid(
        float* rarray,
        int nx,
        int ny,
        int nz,
        int isigned,
        int endian,
        float scalefactor,
        int wordsize
    )

def write_2d_array(np.ndarray[float, ndim=2, mode='c'] topo_array not None):
    cdef int nz = 1
    cdef int isigned = 1
    cdef int endian = 0
    cdef float scalefactor = 1.0
    cdef int wordsize = 2
    write_geogrid(
        <float*> np.PyArray_DATA(topo_array),
        topo_array.shape[0],
        topo_array.shape[1],
        nz,
        isigned,
        endian,
        scalefactor,
        wordsize
    )
