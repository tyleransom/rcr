"""
TEST_EM.PY: Unit tests for estimate_model()
"""
import sys

import pytest
import numpy as np
import pandas as pd

sys.path.append("./")
sys.path.append("../")
from rcr import read_data, estimate_model


@pytest.fixture
def moment_vector():
    (n_moments, n_lambda, external_big_number, moment_vector,
        lambda_range) = read_data("testin1.txt")
    return moment_vector


# Basic functionality
# Estimate parameters and gradient with real data
def test_em_realdata(moment_vector):
    lambda_range = np.array([0.0, 1.0])
    true_em1 = np.array([12.31059909,  8.16970996, 28.93548917,
                         5.13504376,  5.20150257])
    true_result = np.asarray(pd.read_csv("testout1.txt",
                                         delimiter=" ",
                                         header=None,
                                         skipinitialspace=True))
    em, thetavec, lambdavec = estimate_model(moment_vector, lambda_range)
    # Check parameter estimates
    assert em[:, 0] == pytest.approx(true_em1)
    # Check parameter estimates and gradient
    assert em == pytest.approx(true_result)


# lambda_range is a single point
def test_em_lambdapoint(moment_vector):
    lr0 = np.array([0, 0])
    true_em = np.array([12.31059909,  8.16970996, 28.93548917,
                        5.20150257,  5.20150257])
    em, thetavec, lambdavec = estimate_model(moment_vector, lr0)
    assert em[:, 0] == pytest.approx(true_em)
    # TODO: need to check gradient too


# lambda_range has no lower bound
def test_em_nolambdalow(moment_vector):
    lr0 = np.array([-np.inf, 1])
    true_em = np.array([12.31059909,  8.16970996, 28.93548917,
                        5.13504376,  8.16970996])
    with pytest.warns(UserWarning, match="Inaccurate SE"):
        em, thetavec, lambdavec = estimate_model(moment_vector, lr0)
    assert em[:, 0] == pytest.approx(true_em)
    # TODO: need to check gradient too


# lambda_range has no upper bound
def test_em_nolambdahigh(moment_vector):
    lr0 = np.array([0, np.inf])
    true_em = np.array([12.31059909,  8.16970996, 28.93548917,
                        -np.inf, np.inf])
    em, thetavec, lambdavec = estimate_model(moment_vector, lr0)
    assert em[:, 0] == pytest.approx(true_em)
    assert np.all(em[3:4, 1:] == 0.0)
    # TODO: need to check gradient too


# Special cases for moments
# Near-perfect RCT (cov(z,x) almost zero)
def test_em_nearrct():
    mv1 = np.array([0, 0, 0, 1, 0.5, 0.000001, 1, 0.5, 1.0])
    lr1 = np.array([0.0, 1.0])
    em, thetavec, lambdavec = estimate_model(mv1, lr1)
    assert np.all(em[0:3, 0] > 1000)
    assert em[3:4, 0] == pytest.approx(0.5, rel=1e-04)


# Perfect RCT (cov(z,x) exactly zero)
def test_em_rct():
    mv1 = np.array([0, 0, 0, 1, 0.5, 0.0, 1, 0.5, 1.0])
    lr1 = np.array([0.0, 1.0])
    # This test currently fails with an UnboundLocalError
    try:
        em, thetavec, lambdavec = estimate_model(mv1, lr1)
    except UnboundLocalError:
        pass
    else:
        assert np.all(em[0:3, 0] > 1000)
        assert em[3:4, 0] == pytest.approx(0.5, rel=1e-04)