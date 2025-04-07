# Credit : https://gist.github.com/radarsat1/6f8b9b50d1ecd2546d8a765e8a144631
#
# A Python translation of the Brownian Surface function from
# http://www.mathworks.com/matlabcentral/fileexchange/38945-fractional-brownian-field-or-surface-generator
#
# More info, check https://en.wikipedia.org/wiki/Brownian_surface
#
# Example output: http://i.imgur.com/MKHxA6N.png

import numpy as np

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# embedding of covariance function on a [0,R]^2 grid


def rho(x, y, R, alpha):

    if alpha <= 1.5:
        # alpha=2*H, where H is the Hurst parameter
        beta = 0
        c2 = alpha/2
        c0 = 1-alpha/2
    else:
        # parameters ensure piecewise function twice differentiable
        beta = alpha*(2-alpha)/(3*R*(R**2-1))
        c2 = (alpha-beta*(R-1)**2*(R+2))/2
        c0 = beta*(R-1)**3+1-c2

    # create continuous isotropic function
    r = np.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)
    if r <= 1:
        out = c0-r**alpha+c2*r**2
    elif r <= R:
        out = beta*(R-r)**3/r
    else:
        out = 0

    return out, c0, c2

# The main control is the Hurst parameter: H should be between 0 and
# 1, where 0 is very noisy, and 1 is smoother.


def brownian_surface(N=1000, H=0.95):
    R = 2  # [0,R]^2 grid, may have to extract only [0,R/2]^2

    # size of grid is m*n; covariance matrix is m^2*n^2
    M = N

    # create grid for field
    tx = np.linspace(0, R, M)
    ty = np.linspace(0, R, N)
    rows = np.zeros((M, N))

    for i in range(N):
        for j in range(M):
            # rows of blocks of cov matrix
            rows[j, i] = rho([tx[i], ty[j]],
                             [tx[0], ty[0]],
                             R, 2*H)[0]

    BlkCirc_row = np.vstack(
        [np.hstack([rows, rows[:, -1:1:-1]]),
         np.hstack([rows[-1:1:-1, :], rows[-1:1:-1, -1:1:-1]])])

    # compute eigen-values
    lam = np.real(np.fft.fft2(BlkCirc_row))/(4*(M-1)*(N-1))
    lam = np.sqrt(lam)

    # generate field with covariance given by block circular matrix
    Z = np.vectorize(complex)(np.random.randn(2*(M-1), 2*(M-1)),
                              np.random.randn(2*(M-1), 2*(M-1)))
    F = np.fft.fft2(lam*Z)
    F = F[:M, :N]  # extract sub-block with desired covariance

    out, c0, c2 = rho([0, 0], [0, 0], R, 2*H)

    field1 = np.real(F)  # two independent fields
    field2 = np.imag(F)
    field1 = field1 - field1[0, 0]  # set field zero at origin
    field2 = field2 - field2[0, 0]  # set field zero at origin

    # make correction for embedding with a term c2*r^2
    field1 = field1 + np.kron(np.array([ty]).T * np.random.randn(),
                              np.array([tx]) * np.random.randn())*np.sqrt(2*c2)
    field2 = field2 + np.kron(np.array([ty]).T * np.random.randn(),
                              np.array([tx]) * np.random.randn())*np.sqrt(2*c2)
    X, Y = np.meshgrid(tx, ty)

    field1 = field1[:N//2, :M//2]
    field2 = field2[:N//2, :M//2]
    return field1
