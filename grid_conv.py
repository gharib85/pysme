'''Functions for testing convergence rates using grid convergence

'''

import numpy as np
from pysme.integrate import *
from joblib import Parallel, delayed

def l1_norm(vec):
    return np.sum(np.abs(vec))

def double_increments(times, U1s, U2s=None):
    r'''Take a list of times (assumed to be evenly spaced) and standard-normal
    random variables used to define the Ito integrals on the intervals and
    return the equivalent lists for doubled time intervals. The new
    standard-normal random variables are defined in terms of the old ones by

    .. math:

       \begin{align}
       \tilde{U}_{1,n}&=\frac{U_{1,n}+U_{1,n+1}}{\sqrt{2}} \\
       \tilde{U}_{2,n}&=\frac{\sqrt{3}}{2}\frac{U_{1,n}-U_{1,n+1}}{\sqrt{2}}
                        +\frac{1}{2}\frac{U_{2,n}+U_{2,n+1}}{\sqrt{2}}
       \end{align}

    :param times:   List of evenly spaced times defining an even number of
                    time intervals.
    :type times:    numpy.array
    :param U1s:     Samples from a standard-normal distribution used to
                    construct Wiener increments :math:`\Delta W` for each time
                    interval. Multiple rows may be included for independent
                    trajectories.
    :type U1s:      numpy.array(N, len(times) - 1)
    :param U2s:     Samples from a standard-normal distribution used to
                    construct multiple-Ito increments :math:`\Delta Z` for each
                    time interval. Multiple rows may be included for independent
                    trajectories.
    :type U2s:      numpy.array(N, len(times) - 1)
    :returns:       Times sampled at half the frequency and the modified
                    standard-normal-random-variable samples for the new
                    intervals. If ``U2s=None``, only new U1s are returned.
    :rtype:         (numpy.array(len(times)//2 + 1),
                     numpy.array(len(times)//2)[, numpy.array(len(times)//2]))

    '''

    new_times = times[::2]
    even_U1s = U1s[::2]
    odd_U1s = U1s[1::2]
    new_U1s = (even_U1s + odd_U1s)/np.sqrt(2)

    if U2s is None:
        return new_times, new_U1s
    else:
        even_U2s = U2s[::2]
        odd_U2s = U2s[1::2]
        new_U2s = (np.sqrt(3)*(even_U1s - odd_U1s) +
                   even_U2s + odd_U2s)/(2*np.sqrt(2))
        return new_times, new_U1s, new_U2s

def calc_rate(integrator, rho_0, times, U1s=None, U2s=None):
    '''Calculate the convergence rate for some integrator.

    :param integrator:  An Integrator object.
    :param rho_0:           The initial state of the system
    :type rho_0:            numpy.array
    :param times:       Sequence of times (assumed to be evenly spaced, defining
                        a number of increments divisible by 4).
    :param U1s:         Samples from a standard-normal distribution used to
                        construct Wiener increments :math:`\Delta W` for each
                        time interval. If not provided will be generated by the
                        function.
    :type U1s:          numpy.array(len(times) - 1)
    :param U2s:         Samples from a standard-normal distribution used to
                        construct multiple-Ito increments :math:`\Delta Z` for
                        each time interval. If not provided will be generated by
                        the function.
    :type U2s:          numpy.array(len(times) - 1)
    :returns:           The convergence rate as a power of :math:`\Delta t`.
    :rtype:             float

    '''
    increments = len(times) - 1
    if U1s is None:
        U1s = np.random.randn(increments)
    if U2s is None:
        U2s = np.random.randn(increments)

    # Calculate times and random variables for the double and quadruple
    # intervals
    times_2, U1s_2, U2s_2 = double_increments(times, U1s, U2s)
    times_4, U1s_4, U2s_4 = double_increments(times_2, U1s_2, U2s_2)

    rhos = integrator.integrate(rho_0, times, U1s, U2s)
    rhos_2 = integrator.integrate(rho_0, times_2, U1s_2, U2s_2)
    rhos_4 = integrator.integrate(rho_0, times_4, U1s_4, U2s_4)
    rate = (np.log(l1_norm(rhos_4[-1] - rhos_2[-1])) -
            np.log(l1_norm(rhos_2[-1] - rhos[-1])))/np.log(2)

    return rate

def strong_grid_convergence(integrator, rho_0, times, U1s_arr=None,
                            U2s_arr=None, trajectories=256, n_jobs=1):
    r'''Calculate the strong convergence rate for an integrator.

    :param integrator:      Function to prepare arguments for the integrator.
    :type integrator:       Integrator object with method ``integrate``.
    :param rho_0:           The initial state of the system
    :type rho_0:            numpy.array
    :param times:           A sequence of time points for which to solve for rho
    :type times:            list(real)
    :param U1s_arr:         Samples from a standard-normal distribution used to
                            construct Wiener increments :math:`\Delta W` for
                            each time interval for each trajectory.
    :type U1s_arr:          numpy.array(trajectories, len(times) - 1)
    :param U2s_arr:         Samples from a standard-normal distribution used to
                            construct multiple-Ito increments :math:`\Delta Z`
                            for each time interval for each trajectory.
    :type U2s_arr:          numpy.array(trajectories, len(times) - 1)
    :param trajectories:    Number of trajectories to calculate the convergence
                            for (ignored if U1s_arr and U2s_arr are supplied).
    :type trajectories:     int
    :param n_jobs:          Number of parallel jobs (used by
                            ``joblib.Parallel``)
    :type n_jobs:           int
    :returns:               List of convergence rates.

    '''

    increments = len(times) - 1
    if U1s_arr is None:
        U1s_arr = np.random.randn(trajectories, increments)
    if U2s_arr is None:
        U2s_arr = np.random.randn(trajectories, increments)

    rates = Parallel(n_jobs=n_jobs)(delayed(calc_rate)(integrator, rho_0, times,
                                                       U1s, U2s)
                                    for U1s, U2s in zip(U1s_arr, U2s_arr))

    return rates
