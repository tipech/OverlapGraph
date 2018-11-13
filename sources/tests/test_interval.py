#!/usr/bin/env python
# Unit tests for ../shapes/interval.py

from dataclasses import asdict, astuple
from numpy import mean
from typing import List
from unittest import TestCase
from ..shapes.interval import Interval

class TestInterval(TestCase):

  test_intervals: List[Interval]
  overlaps: List[List[bool]]

  def setUp(self):
    self.test_intervals = []
    self.test_intervals.append(Interval(-10, 25))
    self.test_intervals.append(Interval(10.5, 45))
    self.test_intervals.append(Interval(-10.5, 45))
    self.test_intervals.append(Interval(10.5, -45))
    self.test_intervals.append(Interval(-10.5, -45))
    self.test_intervals.append(Interval(5, 5))
    self.test_intervals.append(Interval(5, 6))
    self.overlaps = [
      [True,  True,  True,  True,  False, True,  True],
      [True,  True,  True,  False, False, False, False],
      [True,  True,  True,  True,  False, True,  True],
      [True,  False, True,  True,  True,  True,  True],
      [False, False, False, True,  True,  False, False],
      [True,  False, True,  True,  False, True,  False],
      [True,  False, True,  True,  False, False, True]
    ]

  def test_create_interval(self):
    test_intervals = []
    test_intervals.append(Interval(10.5, 20))
    test_intervals.append(Interval(20, '10.5'))
    test_intervals.append(Interval(**{'lower': 10.5, 'upper': 20}))
    test_intervals.append(Interval(*('20', '10.5')))

    for interval in test_intervals:
      self.assertEqual(interval.lower, 10.5)
      self.assertEqual(interval.upper, 20)
      self.assertTrue(isinstance(interval.lower, float))
      self.assertTrue(isinstance(interval.upper, float))

  def test_interval_properties(self):
    for interval in self.test_intervals:
      #print(f'{interval}: length={interval.length} midpoint={interval.midpoint}')
      self.assertEqual(interval.length, interval.upper - interval.lower)
      self.assertEqual(interval.midpoint, mean([interval.lower, interval.upper]))

  def test_interval_conversion(self):
    for interval in self.test_intervals:
      #print(f'{interval}: dict={asdict(interval)}, tuple={astuple(interval)}')
      self.assertEqual(asdict(interval), {'lower': interval.lower, 'upper': interval.upper})
      self.assertEqual(astuple(interval), (interval.lower, interval.upper))

  def test_interval_contains(self):
    interval = Interval(-5, 15)
    self.assertTrue(interval.lower in interval)
    self.assertTrue(interval.upper in interval)
    self.assertTrue(interval.midpoint in interval)
    self.assertTrue((interval.lower + 0.1) in interval)
    self.assertTrue((interval.upper - 0.1) in interval)
    self.assertFalse(interval.contains(interval.lower, inc_lower = False))
    self.assertFalse(interval.contains(interval.upper, inc_upper = False))
    self.assertFalse((interval.lower - 0.1) in interval)
    self.assertFalse((interval.upper + 0.1) in interval)

  def test_interval_overlaps(self):
    for i, first in enumerate(self.test_intervals):
      for j, second in enumerate(self.test_intervals):
        #print(f'{first} and {second}: expect={self.overlaps[i][j]}, actual={first.overlaps(second)}')
        self.assertEqual(first.overlaps(second), self.overlaps[i][j])

  def test_interval_difference(self):
    for i, first in enumerate(self.test_intervals):
      for j, second in enumerate(self.test_intervals):
        difference = first.difference(second)
        if self.overlaps[i][j]:
          expected = first if first == second \
                           else Interval(max(first.lower, second.lower), 
                                         min(first.upper, second.upper))

          #print(f'{first} and {second}:')
          #print(f'  expect={expected}')
          #print(f'  actual={difference}')
          #print(f'  length={difference.length}')
          self.assertEqual(difference, expected)
        else:
          #print(f'{first} and {second}:')
          #print(f'  expect=None')
          #print(f'  actual={difference}')
          self.assertEqual(first.difference(second), None)
