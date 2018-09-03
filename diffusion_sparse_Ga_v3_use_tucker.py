from __future__ import division

import numpy as np
from numpy.linalg import norm
from scipy.linalg import svd
import sys
from ffthompy import Timer, Struct
from ffthompy.materials import Material
from ffthompy.tensors import matrix2tensor
from ffthompy.sparse.materials_tucker import SparseMaterial
from ffthompy.sparse.homogenisation import homog_Ga_full_potential
from ffthompy.sparse.homogenisation_tucker import homog_sparse

debug=0
full=0
# PARAMETERS ##############################################################
dim=2
N=15
pars=Struct(dim=dim, # number of dimensions (works for 2D and 3D)
            N=dim*(N,), # number of voxels (assumed equal for all directions)
            Y=np.ones(dim),
            Amax=10., # material contrast
            maxiter=5,
            tol=None,
            rank=5,
            solver={'tol':1e-4}
            )

pars_sparse=pars.copy()
if dim == 2:
    pars_sparse.update(Struct(N=dim*(15*N,),))
elif dim == 3 and N==45:
    pars_sparse.update(Struct(N=dim*(N,),))
elif dim == 3 and N==15:
    pars_sparse.update(Struct(N=dim*(3*N,),))

# auxiliary operator
Nbar = lambda N: 2*np.array(N)-1

# PROBLEM DEFINITION ######################################################
mat_conf={'inclusions': ['square', 'otherwise'],
          'positions': [0.*np.ones(dim), ''],
          'params': [0.6*np.ones(dim), ''], # size of sides
          'vals': [10*np.eye(dim), 1.*np.eye(dim)],
          'Y': np.ones(dim),
          'P': pars.N,
          'order': 0, }

mat=Material(mat_conf)
mats=SparseMaterial(mat_conf)

# Agani=matrix2tensor(mat.get_A_GaNi(N, primaldual='primal'))
# Aganis=mats.get_A_GaNi(N, primaldual='primal', k=2)
# print(np.linalg.norm(Agani.val[0, 0]-Aganis.full()))

Aga=matrix2tensor(mat.get_A_Ga(Nbar(pars.N), primaldual='primal'))
Agas=mats.get_A_Ga(Nbar(pars_sparse.N), primaldual='primal', order=0, k=2)

if debug:
    mat_conf.update(dict(P=pars_sparse.N))
    mat3=Material(mat_conf)
    mats3=SparseMaterial(mat_conf)

    Aga3=matrix2tensor(mat3.get_A_Ga(Nbar(pars_sparse.N), primaldual='primal'))
    Agas3=mats3.get_A_Ga(Nbar(pars_sparse.N), primaldual='primal', order=0, k=2)

    print(Aga)
    print(Agas)
    print(Aga3)
    print(np.linalg.norm(Agas.full()-Aga3[0,0]))
    print(np.linalg.norm(Agas.full()-Agas3.full()))

    print('end')
    sys.exit()

if np.array_equal(pars.N, pars_sparse.N): # assert
    print(np.linalg.norm(Aga.val[0, 0]-Agas.full()))

if full:
    print('\n== Full solution with potential by CG ===========')
    resP=homog_Ga_full_potential(Aga, pars)
    print('homogenised properties (component 11) = {}'.format(resP.AH))

print('\n== SPARSE Richardson solver with preconditioner =======================')
resS=homog_sparse(Agas, pars_sparse)
print('homogenised properties (component 11) = {}'.format(resS.AH))

print(resS.Fu)
print('iterations={}'.format(resS.solver['kit']))
if np.array_equal(pars.N, pars_sparse.N):
    print('norm(dif)={}'.format(np.linalg.norm(resP.Fu.val-resS.Fu.full())))
print('norm(resP)={}'.format(resS.solver['norm_res']))
print('memory efficiency = {0}/{1} = {2}'.format(resS.Fu.size, resP.Fu.val.size, resS.Fu.size/resP.Fu.val.size))

print('END')