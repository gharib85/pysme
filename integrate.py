"""
.. py:module:: integrate.py
   :synopsis: Integrate stochastic master equations in vectorized form.
.. moduleauthor:: Jonathan Gross <jarthurgross@gmail.com>

"""

import numpy as np
from scipy.integrate import odeint
from pysme.system_builder import *
from pysme.sde import *
from math import sqrt

def b_dx_b(G2, k_T_G, G, k_T, rho):
    r'''Function to return the :math:`\left(\vec{b}(\vec{\rho})\cdot
    \vec{\nabla}_{\vec{\rho}}\right)\vec{b}(\vec{\rho})` term for Milstein
    integration.

    :param G2:          :math:`G^2`.
    :param k_T_G:       :math:`\vec{k}^TG`.
    :param G:           :math:`G`.
    :param k_T:         :math:`\vec{k}^T`.
    :param rho:         :math:`\rho`.
    :returns:           :math:`\left(\vec{b}(\vec{\rho})\cdot
                        \vec{\nabla}_{\vec{\rho}}\right)\vec{b}(\vec{\rho})`.

    '''
    k_rho_dot = np.dot(k_T, rho)
    return (np.dot(k_T_G, rho) + 2*k_rho_dot**2)*rho + \
            np.dot(G2 + 2*k_rho_dot*G, rho)

def b_dx_a(QG, k_T, Q, rho):
    r'''Function to return the :math:`\left(\vec{b}(\vec{\rho})\cdot
    \vec{\nabla}_{\vec{\rho}}\right)\vec{a}(\vec{\rho})` term for stochastic
    integration.

    :param QG:          :math:`QG`.
    :param k_T:         :math:`\vec{k}^T`.
    :param Q:           :math:`Q`.
    :param rho:         :math:`\rho`.
    :returns:           :math:`\left(\vec{b}(\vec{\rho})\cdot
                        \vec{\nabla}_{\vec{\rho}}\right)\vec{a}(\vec{\rho})`.

    '''
    return np.dot(QG + np.dot(k_T, rho)*Q, rho)

def a_dx_b(GQ, k_T, Q, k_T_Q, rho):
    r'''Function to return the :math:`\left(\vec{a}(\vec{\rho})\cdot
    \vec{\nabla}_{\vec{\rho}}\right)\vec{b}(\vec{\rho})` term for stochastic
    integration.

    :param GQ:          :math:`GQ`.
    :param k_T:         :math:`\vec{k}^T`.
    :param Q:           :math:`Q`.
    :param k_T_Q:       :math:`\vec{k}^TQ`.
    :param rho:         :math:`\rho`.
    :returns:           :math:`\left(\vec{a}(\vec{\rho})\cdot
                        \vec{\nabla}_{\vec{\rho}}\right)\vec{b}(\vec{\rho})`.

    '''
    return np.dot(GQ + np.dot(k_T, rho)*Q, rho) + np.dot(k_T_Q, rho)

def a_dx_a(Q2, rho):
    r'''Function to return the :math:`\left(\vec{a}(\vec{\rho})\cdot
    \vec{\nabla}_{\vec{\rho}}\right)\vec{a}(\vec{\rho})` term for stochastic
    integration.

    :param Q2:          :math:`Q^2`.
    :param rho:         :math:`\rho`.
    :returns:           :math:`\left(\vec{a}(\vec{\rho})\cdot
                        \vec{\nabla}_{\vec{\rho}}\right)\vec{a}(\vec{\rho})`.

    '''
    return np.dot(Q2, rho)

def b_dx_b_dx_b(G3, G2, G, k_T, k_T_G, k_T_G2, rho):
    r'''Function to return the :math:`\left(\vec{b}(\vec{\rho})\cdot
    \vec{\nabla}_{\vec{\rho}}\right)^2\vec{b}(\vec{\rho})` term for stochastic
    integration.

    :param G3:          :math:`G^3`.
    :param G2:          :math:`G^2`.
    :param G:           :math:`G`.
    :param k_T:         :math:`\vec{k}^T`.
    :param k_T_G:       :math:`\vec{k}^TG`.
    :param k_T_G2:      :math:`\vec{k}^TG^2`.
    :param rho:         :math:`\rho`.
    :returns:           :math:`\left(\vec{b}(\vec{\rho})\cdot
                        \vec{\nabla}_{\vec{\rho}}\right)^2\vec{b}(\vec{\rho})`.

    '''
    k_rho_dot = np.dot(k_T, rho)
    k_T_G_rho_dot = np.dot(k_T_G, rho)
    k_T_G2_rho_dot = np.dot(k_T_G2, rho)
    return (np.dot(G3 + 3*k_rho_dot*G2 + 3*(k_T_G_rho_dot + 2*k_rho_dot)*G,
                   rho) + (k_T_G2_rho_dot + 6*k_rho_dot*k_T_G_rho_dot +
                           6*k_rho_dot**3)*rho)

def uncond_vac_integrate(rho_0, c_op, basis, times):
    r"""Integrate an unconditional vacuum master equation.

    :param rho_0:   The initial state of the system
    :type rho_0:    numpy.array
    :param c_op:    The coupling operator
    :type c_op:     numpy.array
    :param basis:   The Hermitian basis to vectorize the operators in terms of
                    (with the component proportional to the identity in last
                    place)
    :type basis:    list(numpy.array)
    :param times:   A sequence of time points for which to solve for rho
    :type times:    list(real)
    :returns:       The components of the vecorized :math:`\rho` for all
                    specified times
    :rtype:         list(numpy.array)

    """

    rho_0_vec = [comp.real for comp in vectorize(rho_0, basis)]
    diff_mat = diffusion_op(c_op, basis[:-1])
    
    return odeint(lambda rho_vec, t: np.dot(diff_mat, rho_vec), rho_0_vec,
            times, Dfun=(lambda rho_vec, t: diff_mat))

def uncond_gauss_integrate(rho_0, c_op, M_sq, N, H, basis, times):
    r"""Integrate an unconditional Gaussian master equation.

    :param rho_0:   The initial state of the system
    :type rho_0:    numpy.array
    :param c_op:    The coupling operator
    :type c_op:     numpy.array
    :param M_sq:    The squeezing parameter
    :type M_sq:     complex
    :param N:       The thermal parameter
    :type N:        positive real
    :param H:       The plant Hamiltonian
    :type H:        numpy.array
    :param basis:   The Hermitian basis to vectorize the operators in terms of
                    (with the component proportional to the identity in last
                    place)
    :type basis:    list(numpy.array)
    :param times:   A sequence of time points for which to solve for rho
    :type times:    list(real)
    :returns:       The components of the vecorized :math:`\rho` for all
                    specified times
    :rtype:         list(numpy.array)

    """

    rho_0_vec = [comp.real for comp in vectorize(rho_0, basis)]
    diff_mat = (N + 1)*diffusion_op(c_op, basis[:-1]) + \
            N*diffusion_op(c_op.conj().T, basis[:-1]) + \
            double_comm_op(c_op, M_sq, basis[:-1]) + hamiltonian_op(H,
                    basis[:-1])
    
    return odeint(lambda rho_vec, t: np.dot(diff_mat, rho_vec), rho_0_vec,
            times, Dfun=(lambda rho_vec, t: diff_mat))

class Taylor_1_5_HomodyneIntegrator:
    r"""Integrator for the conditional Gaussian master equation that uses
    strong order 1.5 Taylor integration.

    """

    def __init__(self, c_op, M_sq, N, H, basis):
        r'''Constructor.

        :param c_op:    The coupling operator
        :type c_op:     numpy.array
        :param M_sq:    The squeezing parameter
        :type M_sq:     complex
        :param N:       The thermal parameter
        :type N:        positive real
        :param H:       The plant Hamiltonian
        :type H:        numpy.array
        :param basis:   The Hermitian basis to vectorize the operators in terms
                        of (with the component proportional to the identity in
                        last place)
        :type basis:    list(numpy.array)

        '''
        self.basis = basis
        self.Q = (N + 1)*diffusion_op(c_op, basis[:-1]) + \
                 N*diffusion_op(c_op.conj().T, basis[:-1]) + \
                 double_comm_op(c_op, M_sq, basis[:-1]) + \
                 hamiltonian_op(H, basis[:-1])
        self.G, self.k_T = weiner_op(((N + M_sq.conjugate() + 1)*c_op -
                                      (N + M_sq)*c_op.conj().T)/
                                     sqrt(2*(M_sq.real + N) + 1), basis[:-1])

        self.G2 = np.dot(self.G, self.G)
        self.G3 = np.dot(self.G2, self.G)
        self.Q2 = np.dot(self.Q, self.Q)
        self.QG = np.dot(self.Q, self.G)
        self.GQ = np.dot(self.G, self.Q)
        self.k_T_G = np.dot(self.k_T, self.G)
        self.k_T_G2 = np.dot(self.k_T, self.G2)
        self.k_T_Q = np.dot(self.k_T, self.Q)

    def a_fn(self, rho):
        return np.dot(self.Q, rho)

    def b_fn(self, rho):
        return np.dot(self.k_T, rho)*rho + np.dot(self.G, rho)

    def b_dx_b_fn(self, rho):
        return b_dx_b(self.G2, self.k_T_G, self.G, self.k_T, rho)

    def b_dx_a_fn(self, rho):
        return b_dx_a(self.QG, self.k_T, self.Q, rho)

    def a_dx_b_fn(self, rho):
        return a_dx_b(self.GQ, self.k_T, self.Q, self.k_T_Q, rho)

    def a_dx_a_fn(self, rho):
        return a_dx_a(self.Q2, rho)

    def b_dx_b_dx_b_fn(self, rho):
        return b_dx_b_dx_b(self.G3, self.G2, self.G, self.k_T, self.k_T_G,
                           self.k_T_G2, rho)

    def integrate(self, rho_0, times, U1s=None, U2s=None):
        r'''Integrate for a sequence of times with a given initial condition
        (and optionally specified white noise).

        :param rho_0:   The initial state of the system
        :type rho_0:    numpy.array
        :param times:   A sequence of time points for which to solve for rho
        :type times:    list(real)
        :param U1s:     Samples from a standard-normal distribution used to
                        construct Wiener increments :math:`\Delta W` for each
                        time interval. Multiple rows may be included for
                        independent trajectories.
        :type U1s:      numpy.array(N, len(times) - 1)
        :param U2s:     Samples from a standard-normal distribution used to
                        construct multiple-Ito increments :math:`\Delta Z` for
                        each time interval. Multiple rows may be included for
                        independent trajectories.
        :type U2s:      numpy.array(N, len(times) - 1)
        :returns:       The components of the vecorized :math:`\rho` for all
                        specified times
        :rtype:         list(numpy.array)

        '''
        rho_0_vec = np.array([[comp.real]
                              for comp in vectorize(rho_0, self.basis)])
        if U1s is None:
            U1s = np.random.randn(len(times) -1)
        if U2s is None:
            U2s = np.random.randn(len(times) -1)

        return time_ind_taylor_1_5(self.a_fn, self.b_fn, self.b_dx_b_fn,
                                   self.b_dx_a_fn, self.a_dx_b_fn,
                                   self.a_dx_a_fn, self.b_dx_b_dx_b_fn,
                                   rho_0_vec, times, U1s, U2s)

class MilsteinHomodyneIntegrator:
    r"""Integrator for the conditional Gaussian master equation that uses
    Milstein integration.

    """

    def __init__(self, c_op, M_sq, N, H, basis):
        r'''Constructor.

        :param c_op:    The coupling operator
        :type c_op:     numpy.array
        :param M_sq:    The squeezing parameter
        :type M_sq:     complex
        :param N:       The thermal parameter
        :type N:        positive real
        :param H:       The plant Hamiltonian
        :type H:        numpy.array
        :param basis:   The Hermitian basis to vectorize the operators in terms
                        of (with the component proportional to the identity in
                        last place)
        :type basis:    list(numpy.array)

        '''
        self.basis = basis
        self.Q = (N + 1)*diffusion_op(c_op, basis[:-1]) + \
                 N*diffusion_op(c_op.conj().T, basis[:-1]) + \
                 double_comm_op(c_op, M_sq, basis[:-1]) + \
                 hamiltonian_op(H, basis[:-1])
        self.G, self.k_T = weiner_op(((N + M_sq.conjugate() + 1)*c_op -
                                      (N + M_sq)*c_op.conj().T)/
                                     sqrt(2*(M_sq.real + N) + 1), basis[:-1])
        self.k_T_G = np.dot(self.k_T, self.G)
        self.G2 = np.dot(self.G, self.G)

    def a_fn(self, rho, t):
        return np.dot(self.Q, rho)

    def b_fn(self, rho, t):
        return np.dot(self.k_T, rho)*rho + np.dot(self.G, rho)

    def b_dx_b_fn(self, rho, t):
        return b_dx_b(self.G2, self.k_T_G, self.G, self.k_T, rho)

    def integrate(self, rho_0, times, U1s=None, U2s=None):
        r'''Integrate for a sequence of times with a given initial condition
        (and optionally specified white noise).

        :param rho_0:   The initial state of the system
        :type rho_0:    numpy.array
        :param times:   A sequence of time points for which to solve for rho
        :type times:    list(real)
        :param U1s:     Samples from a standard-normal distribution used to
                        construct Wiener increments :math:`\Delta W` for each
                        time interval. Multiple rows may be included for
                        independent trajectories.
        :type U1s:      numpy.array(len(times) - 1)
        :param U2s:     Unused, included to make the argument list uniform with
                        higher-order integrators.
        :type U2s:      numpy.array(len(times) - 1)
        :returns:       The components of the vecorized :math:`\rho` for all
                        specified times
        :rtype:         list(numpy.array)

        '''
        rho_0_vec = np.array([[comp.real]
                              for comp in vectorize(rho_0, self.basis)])
        if U1s is None:
            U1s = np.random.randn(len(times) -1)

        return milstein(self.a_fn, self.b_fn, self.b_dx_b_fn, rho_0_vec, times,
                        U1s)

class FaultyMilsteinHomodyneIntegrator(MilsteinHomodyneIntegrator):

    def integrate(self, rho_0, times, U1s=None, U2s=None):
        r'''Method included to test if grid convergence could identify an error
        I originally had in my Milstein integrator (missing a factor of 1/2 in
        front of the term that's added to the Euler scheme).

        '''
        rho_0_vec = np.array([[comp.real]
                              for comp in vectorize(rho_0, self.basis)])
        if U1s is None:
            U1s = np.random.randn(len(times) -1)

        return faulty_milstein(self.a_fn, self.b_fn, self.b_dx_b_fn, rho_0_vec,
                               times, U1s)
