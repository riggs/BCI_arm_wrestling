#generate N elements of a sine signal with 0-mean and unit variance normal noise
#the model equations for searching for a sinusoid are cos(kt) and sin(kt)

from numpy.matlib import *
from bsa import bsa


N = 1000
T = 10
time = mat(linspace(-T, T, N))
param = .2
noise = randn((1, N))

signalsin = sin(param*time)
signalcos = cos(param*time)

data = noise+signalsin+signalcos

param_cands = linspace(.1, .3, 51)
p_params = zeros((1, 51))
for cand in range(0, 51):
    param = param_cands[cand]
    signalsin = sin(param*time)
    signalcos = cos(param*time)
    model = vstack((signalsin, signalcos))
    p_params[0, cand] = bsa(data, model)
#logp = bsa(data,model)
