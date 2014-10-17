from numpy.matlib import *


def pkalman(x, Ns=64, Fs=None, t=None, sigma=None, lda=0.01, m0=None, v0=None, sparse=False, n_block=1000,
            n_overlap=100, n_bs=None, smoothing=False):
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
    
    if Fs is not None:
        Fs = matrix(Fs)
        if Fs.size is not 1:
            Ftp = []
            Fs = squeeze(Fs)
        else:
            Ftp = Fs
            spc = Ftp/Ns
            Fs = matrix(arange(0+spc,Ftp-spc + 1,spc))
    else:
        Fs = 6
        spc = Fs/2 / Ns
        Fs = matrix(arange(0+spc,Fs/2 - spc + 1, spc)).T

    if t is None:
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
    m, vtar = kalman_est(x, t, Fs, Ns, smoothing, n_block, n_overlap, sigma, lda, m0, v0, sparse)

    ds = Fs.size

    amp = zeros((ds, n))
    print(amp.shape)
    for j in range(0,ds):
        rowwd = matrix(hstack((j, j+ds)))
        #print(j)
        #print(rowwd)
        #print(sqrt(square(m[j, :]) + square(m[j+ds, :])))
        amp[j,:] = sqrt(square(m[j, :]) + square(m[j+ds, :]));
    
    amp = vstack((abs(m[-1, :]), amp))
    phs = zeros((ds, n))
    for j in range(0,ds):
        rowwd = hstack((j, j+ds))
        phs[j, :] = arctan2(m[j, :], m[j+ds, :])  # TODO check this is the right form of atan

    phs = vstack((zeros((1, n)), phs))

    return amp, phs, vtar, Fs, t


def kalman_est(x, t, Fs, Ns, smoothing, n_block, n_overlap, sigma, lda, m0, v0, sparse):
    """
    port of Yuan Qi's spectrum estimation MATLAB code to python

    args:
    x           (xR,xC) matrix
    t           (tR,tC) matrix
    Fs          (Fs_R,1) matrix or scalar
    Ns          (NsR,NsC) matrix
    smoothing   boolean
    n_block     ?
    n_overlap   ?
    sigma       ?
    lda         scalar. could it be a matrix? (lda_R,lda_C)
    m0          (m0_R,m0_C) matrix
    v0          (v0_R,v0_C) matrix
    sparse      boolean
    """
    #ensure x is (N,1) matrix
    x.flatten(1)
    t = array(t)  # is this okay?
    n = x.size
    tau = 2*pi
    (m0_len, _) = m0.shape
    m = zeros((m0_len, n))
    #print(Fs.shape)
    #print(t.shape)
    #print(t[0].shape)
    matrix(sin(tau*Fs*t[0]))
    matrix(cos(tau*Fs*t[0]))
    matrix(1)
    C = hstack((matrix(sin(tau*Fs*t[0])), matrix(cos(tau*Fs*t[0])), matrix(1)))
    # C = (Fs_R,3)
    v0C = v0 * C.T  # v0C = (v0_R,C_R) matrix = (v0_R,v0_C) * (C_C,C_R)
    #v0_C = C_C
    k1 = v0C * (C*v0C + lda).I  # (v0_R,C_R) * ((C_R,C_C)*(v0_R,C_R))
    # (v0_R,C_R) * (C_R,C_R)
    # C_C = v0_R
    # lda_R = lda_C = C_R or lda is scalar
    #k1 = (v0_R,C_R)
    vt = v0 - k1*v0C.T
    m[:, 0] = m0 + k1*(x[0] - C*m0)

    vtar = []
    if smoothing:
        vtar = []
        n_block = min(n, n_block)
        #TODO not sure about these sizes here
        vtar = [zeros((v0.shape[0], v0.shape[1])) for _ in range(0, n_block+1)]
        ptar = [zeros((v0.shape[0], v0.shape[1])) for _ in range(0, n_block-1+1)]
        vtar[0][:, :] = vt

    mdi = 1
    for i in range(1,n):
        inttp = t[i]-t[i-1]
        sigma_t = sigma*inttp
        pt = vt + sigma_t  # TODO check this line

        C = hstack((matrix(sin(tau*Fs*t[i])), matrix(cos(tau*Fs*t[i])), matrix(1)))
        ptC = pt*C.T
        kt = ptC * (1./(C * ptC + lda))
        vtp = pt - kt*(C*pt)
        mtp = m[:, i-1] + kt*(x[i] - C*m[:, i-1])

        """
        if sparse and mod(i, 100) == 0 and i > 50:
            #not clear what this is. don't call this function with sparse.
            m[:, i], vt = obs4(mtp, vtp, v0);
        else:
            m[:, i] = mtp
            vt = vtp
        """
        m[:, i] = mtp
        vt = vtp

        if smoothing:
            mdi += 1
            if mdi == 0:
                ptar[n_block-1][:, :] = pt
                vtar[n_block][:, :] = vt
            elif mdi == 1:
                vtar[0][:, :] = vt
            elif mdi >= 2:
                vtar[mdi][:, :] = vt
                ptar[mdi-1][:, :] = pt

            if (mdi == n_block) or (i == n):
                ind = i+1 - arange(n_block, 0, -1)
                for j in range(mdi-2, -1, -1):
                    jt = vtar[j][:, :] * (ptar[j][:, :]).I
                    m[:, ind[j]] = m[:, ind[j]] + jt * (m[:, ind[j]+1] - m[:, ind[j]])
                    vtar[j][:, :] = vtar[j][:, :] + jt * (vtar[j+1][:, :] - ptar[j][:, :])*jt.T

                vtar[0][:, :] = vtar[n_block - n_overlap + 1][:,:]
                for g in range(1, n_overlap):
                    vtar[g][:, :] = vtar[n_block - n_overlap+g][:, :]
                    ptar[g-1][:, :] = ptar[n_block - n_overlap + g - 1][:,:]

                mdi = n_overlap

    return m, vtar
