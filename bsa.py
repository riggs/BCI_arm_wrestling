#TODO add output of all calculated components

from numpy.matlib import *
from numpy.core.umath import square
from scipy.linalg import eig


def bsa(data,modeleqs):
    """
    this function uses the algorithm from Dr. Bretthorst's lecture notes to calculate how
    well a model represents the data. Said wellness as reported as a non-normalized
    probability. Normalizing that probability is "possible". You probably don't need to,
    and certainly don't want to.

    The data is an Nx1 matrix of numbers. The model is an NxM matrix of numbers.
    The model is these M Nx1 matrices scaled in some way and added together. The
    algorithm calculates what way of doing so accounts for the largest amount of the
    signal.

    See 
    http://bayes.wustl.edu/glb/bib.html
    for further information. You want "Bayesian Spectrum Analysis and Parameter Estimation"
    from 1988.

    :param data: Nx1 matrix
    :param modeleqs: NxM matrix
    :return:
    """
    #whose clever idea was it to use shape for what is clearly size
    (_,N) = data.shape
    (M,Np) = modeleqs.shape
    
    #assert Np == N or something
    
    d = data-mean(data)
    dbarsq = mean(square(d))
    
    G = modeleqs
    B = ones((1,M))# 1xM (or Mx1?)
    m = M
    g = zeros((m,m))
    modelfunc = zeros((1,N))
    for it in range(0,m-1):
        for jt in range(0,m-1):
            #1xN * Nx1 = scalar
            g[it,jt] = G[it,:] * G[jt,:].T
    
        modelfunc = modelfunc + B[0,it]*G[it,:]
    
    #learn the numpy runes
    #evec is eigenvectors of g
    #eval is eigenvalues of g
    eval,evec = eig(g)
    #diagonal of that array
    #pretty sure it is Mx1
    evalarr = diag(eval)
    
    H = zeros((m,N))  # matrix of zeros, size mxN
    for j in range(0,m-1):
        for k in range(0,m-1):
            H[j,:] = H[j,:] + evec[k,j]*G[k,:]
        H[j,:] = H[j,:]/sqrt(evalarr[0,j])
    
    #B*evec' = 1xM * MxM => 1xM
    #sqrt(evalarr) * that = Mx1*1xM => MxM
    #then take diagonal of that, giving
    A = diag(sqrt(evalarr)*(B*evec.T).T).T
    
    Ap = zeros(B.shape)
    for j in range(0,m-1):
        Ap[0,j] = H[j,:] * modelfunc.T
    
    h = zeros((1,m))
    for j in range(0,m-1):
        #1xN*(1xN)' = scalar
        h[0,j] = H[j,:]*d.T
    
    hbarsq = sum(square(h))/m
    #fun fact, it doesn't matter what base this log is to :D
    #except for practical considerations like 1.01 is a bad base
    logp_w = (m-N)/2 * log10((1- (m*hbarsq)/(N*dbarsq)))
    #the best fit with these model functions is h*H
    logprob = logp_w
    return logprob
