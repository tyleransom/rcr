"""
TEST_EP.PY: Unit tests for estimate_parameter()
"""
import sys

import numpy as np
import pytest

sys.path.append("./")
sys.path.append("../")
from rcr import estimate_parameter, thetastar, lambdastar, \
    simplify_moments, read_data


@pytest.fixture
def moment_vector():
    (n_moments, n_lambda, external_big_number, moment_vector,
        lambda_range) = read_data("testin1.txt")
    return moment_vector


def vary(moment_vector):
    sm = simplify_moments(moment_vector)
    return sm[0]


# Test with simple data
def test_ep_basic():
    mv1 = np.array([0, 0, 0, 1, 0.5, 0.5, 1, 0.5, 1.0])
    ep_true = np.array([1., 0, 0, 0, 0, 0, 0, 1, 0, 0])
    ep = estimate_parameter(vary, mv1)
    assert ep == pytest.approx(ep_true)


# Test with real data
def test_ep_realdata(moment_vector):
    ep_true = np.zeros(len(moment_vector)+1)
    ep_true[0] = 542.53831290783
    ep_true[7] = -102.89924396
    ep_true[42] = 1.0
    ep = estimate_parameter(vary, moment_vector)
    assert ep == pytest.approx(ep_true)


# Special cases


# When the function is nan or inf, derivative is zeros
def test_ep_inf():
    mv = np.array([0, 0, 0, 1, 0.5, 0, 1, 0.5, 1])
    ep = estimate_parameter(lambdastar, mv)
    assert ep[0] == np.inf and all(ep[1:] == 0.)


def test_ep_nan():
    mv = np.array([0, 0, 0, 1, 0.5, 0, 1, 0.5, 1])
    ep = estimate_parameter(thetastar, mv)
    assert np.isnan(ep[0]) and all(ep[1:] == 0.)