"""
TEST_SM.PY: Unit tests for simplify_moments()
"""
import sys

import numpy as np
import pytest

sys.path.append("./")
sys.path.append("../")
from rcr import simplify_moments, \
    read_data  # pylint: disable=wrong-import-position


@pytest.fixture
def moment_vector():
    """get moment vector from test data"""
    mv = read_data("testing/testin1.txt")[3]
    return mv


# Basic functionality
def test_sm_basic():
    """get simple moments from simple test data"""
    mv = np.array([0, 0, 0, 1, 0.5, 0.5, 1, 0.5, 1.0])
    true_sm = np.array([1, 1, .5, .25, .25, .25])
    sm = simplify_moments(mv)
    assert sm == pytest.approx(true_sm)
    assert sm[5] == (np.sign(sm[5]) * np.sqrt(sm[3] * sm[4]))


def test_sm_realdata(moment_vector):
    """get simple moments from real test data"""
    true_sm = np.array([5.42538313e+02, 2.05839484e-01,
                        1.07467966e+00, 4.47643916e+01,
                        1.34931719e-03, 1.10235301e-02])
    sm = simplify_moments(moment_vector)
    assert sm == pytest.approx(true_sm)
    assert sm[5] <= (np.sign(sm[5]) * np.sqrt(sm[3] * sm[4]))


def random_mv():
    """generate random data for tests"""
    exyz = np.random.randn(3)
    vxyz = abs(np.random.randn(3))
    corxyz = np.random.uniform(-1, 1, 3)
    ex = exyz[0]
    ey = exyz[1]
    ez = exyz[2]
    vx = vxyz[0]
    vy = vxyz[1]
    vz = vxyz[2]
    cxy = corxyz[0] * np.sqrt(vx * vy)
    cxz = corxyz[1] * np.sqrt(vx * vz)
    cyz = corxyz[2] * np.sqrt(vy * vz)
    exx = vx + ex ** 2
    eyy = vy + ey ** 2
    ezz = vz + ez ** 2
    exy = cxy + ex * ey
    exz = cxz + ex * ez
    eyz = cyz + ey * ez
    vyhat = (cxy ** 2) / vx
    vzhat = (cxz ** 2) / vx
    covhat = cxy * cxz / vx
    mvi = np.array([ex, ey, ez, exx, exy, exz, eyy, eyz, ezz])
    smi = np.array([vy, vz, cyz, vyhat, vzhat, covhat])
    return mvi, smi


def test_sm_randomdata():
    """get simple moments from random test data"""
    for _ in range(10):
        mvi, true_smi = random_mv()
        smi = simplify_moments(mvi)
        assert smi == pytest.approx(true_smi)
        assert smi[5] == (np.sign(smi[5]) * np.sqrt(smi[3] * smi[4]))


# Special cases
def test_sm_wronglen():
    """raise exception if wrong length"""
    mv = np.zeros(8)
    try:
        simplify_moments(mv)
    except AssertionError:
        pass
    else:
        raise AssertionError("simplify_moments has accepted invalid input")


def test_sm_allzeros():
    """return mix of zeros and NaN if input is all zeros"""
    mv = np.zeros(9)
    true_sm = np.array([0, 0, 0, np.nan, np.nan, np.nan])
    sm = simplify_moments(mv)
    assert sm == pytest.approx(true_sm, nan_ok=True)


def test_sm_integer():
    """handle integer data"""
    mv1 = np.array([0, 0, 0, 2, 1, 1, 2, 1, 2])
    true_sm1 = np.array([2, 2, 1, .5, .5, .5])
    sm1 = simplify_moments(mv1)
    assert sm1 == pytest.approx(true_sm1)
    assert sm1[5] == (np.sign(sm1[5]) * np.sqrt(sm1[3] * sm1[4]))


def test_sm_varx0():
    """return NaN if var(x)=0"""
    mv = np.array([0, 0, 0, 0, 0.5, 0.5, 1, 0.5, 1.0])
    true_sm = np.array([1, 1, 0.5, np.nan, np.nan, np.nan])
    sm = simplify_moments(mv)
    assert sm == pytest.approx(true_sm, nan_ok=True)


def test_sm_varxneg():
    """return numeric values if var(x)<0"""
    mv0 = np.array([0, 0, 0, -1, 0.5, 0.5, 1, 0.5, 1.0])
    sm0 = simplify_moments(mv0)
    assert all(np.isfinite(sm0))


def test_sm_varyneg():
    """return numeric values if var(y) <= 0"""
    mv0 = np.array([0, 0, 0, 1, 0.5, 0.5, 0, 0.5, 1.0])
    sm0 = simplify_moments(mv0)
    assert all(np.isfinite(sm0))
    mv0 = np.array([0, 0, 0, 1, 0.5, 0.5, -1, 0.5, 1.0])
    sm0 = simplify_moments(mv0)
    assert all(np.isfinite(sm0))


def test_sm_varzneg():
    """return numeric values if var(z) < 0"""
    mv0 = np.array([0, 0, 0, 1, 0.5, 0.5, 1, 0.5, 0])
    sm0 = simplify_moments(mv0)
    assert all(np.isfinite(sm0))
    mv0 = np.array([0, 0, 0, 1, 0.5, 0.5, 1, 0.5, -1])
    sm0 = simplify_moments(mv0)
    assert all(np.isfinite(sm0))
