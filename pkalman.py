from numpy.matlib import *
from kalman_est import kalman_est


def pkalman(x, Ns=64, Fs=None, t=None, sigma=None, lda=0.01, m0=None, v0=None, sparse=False, n_block=1000, n_overlap=100, n_bs=None, smoothing=False, disp = False, fig_sz = None, color = None, log_scale = False, ts = None, tp = None, te = None, axis = None, XTICK = None,YTICK = None,FontSize = None):
    """
    port of Yuan Qi's pkalman spectrum estimation code.
    
    t's default value is more complicated
    
    output: (amp, phs, vtar, freqs)
        amp: extimated frequency amplitudes from time 1 to n
        phs: estimated frequency phases from time 1 to n
        vtar: the variances from last block's smoothing. empty matrix if smoothing not performed
        freqs: array of frequencies used.
    """
    
    x.flatten(1)
    n = x.size
    
    #PARSE_PAR replaced with python named args
    if Fs is not None:
        Fs = matrix(Fs)
        if Fs.size is not 1:
            Ftp = []
            Fs = squeeze(Fs)
        else:
            Ftp = Fs
            spc = Ftp/Ns
            #Fs = (0+spc):spc:(Ftp-spc)
            Fs = matrix(arange(0+spc,Ftp-spc + 1,spc))
    else:
        Fs = 6
        spc = Fs/2 / Ns
        #Fs = (0+spc):spc:(Fs/2 - spc)
        Fs = matrix(arange(0+spc,Fs/2 - spc + 1, spc)).T

    if t is None:
        #t = (1:n)/(Ftp*2)
        t = array(range(1, n+1)/(Ftp*2))[0, :]

    if n_bs is None:
        n_bs = 2*Fs.size + 1  # row vector, so size is the number we want
    
    if sigma is None:
        sigma = 1*10*eye(n_bs)  # ensure this is the right function
        
    if m0 is None:
        m0 = ones((n_bs, 1))
    
    if v0 is None:
        v0 = 100*eye(n_bs)

    #do the real calc
    m, vtar =  kalman_est(x, t, Fs, Ns, smoothing, n_block, n_overlap, sigma, lda, m0, v0, sparse);
    
    
    ds = Fs.size

    amp = zeros((ds, n))
    print(amp.shape)
    for j in range(0,ds):
        rowwd = matrix(hstack((j, j+ds)))
        #print(j)
        #print(rowwd)
        #print(sqrt(square(m[j, :]) + square(m[j+ds, :])))
        #amp[j, :] = sqrt(sum(square(m[rowwd, :])))
        amp[j,:] = sqrt(square(m[j, :]) + square(m[j+ds, :]));
    
    amp = vstack((abs(m[-1, :]), amp))
    phs = zeros((ds, n))
    for j in range(0,ds):
        rowwd = hstack((j, j+ds))
        phs[j, :] = arctan2(m[j, :], m[j+ds, :])  # TODO check this is the right form of atan

    phs = vstack((zeros((1, n)), phs))

    #if nargout == 0 | disp_flg == 1:
    #    disp_spec(amp, t, Fs, varargin{:})

    return amp, phs, vtar, Fs, t
     