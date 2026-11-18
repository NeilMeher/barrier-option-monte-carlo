from dataclasses import replace
from math import exp
import unittest

import numpy as np

from study import Contract, continuous, discrete_quadrature, integral_check, samples


class BarrierTests(unittest.TestCase):
    def test_immediate_knockout(self):
        c = replace(Contract(), barrier=100)
        self.assertEqual(continuous(c), 0)
        self.assertEqual(samples(c, np.ones((3, 2)), "bridge").sum(), 0)

    def test_analytic_and_integral(self):
        for barrier in (70, 95, 99):
            c = replace(Contract(), barrier=barrier)
            self.assertAlmostEqual(continuous(c), integral_check(c), places=6)

    def test_distant_barrier(self):
        self.assertAlmostEqual(continuous(replace(Contract(), barrier=1)), 11.3484768251, places=6)

    def test_discount(self):
        c = Contract(rate=.06, vol=(.12)**.5)
        self.assertAlmostEqual(samples(c, np.zeros((1, 2)), "vanilla")[0], 0)
        c = replace(c, strike=90)
        self.assertAlmostEqual(samples(c, np.zeros((1, 2)), "vanilla")[0], 10 * exp(-.06))

    def test_parity_and_pathwise_order(self):
        c = Contract()
        z = np.random.default_rng(41).normal(size=(500, 12))
        bridge = samples(c, z, "bridge")
        np.testing.assert_allclose(bridge + samples(c, z, "knock_in"), samples(c, z, "vanilla"))
        self.assertTrue(np.all(bridge <= samples(c, z, "grid")))

    def test_discrete_and_continuous_are_distinct(self):
        c = Contract()
        fine = discrete_quadrature(c, 16, 1200)
        self.assertGreater(fine, continuous(c))
        self.assertLess(abs(fine - discrete_quadrature(c, 16, 600)), .002)
