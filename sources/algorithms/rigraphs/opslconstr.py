#!/usr/bin/env python

"""
Regional Intersection Graph (RIG) Construction by One-pass Sweepline Algorithm

This script implements the OpslConstr (or one-pass sweepline RIG construction
algorithm). This algorithm builds an undirected, weighted (labelled)
graph of all the pair-wise intersections or overlapping regions between a
collection of regions with the same dimensionality.
"""

from networkx import Graph

from sources.algorithms.sweepln.opsweepln import SweeplnAlg, SweeplnRT
from sources.datastructs.datasets.regionset import RegionSet
from sources.datastructs.shapes.region import Region, RegionPair


class OpslConstr(SweeplnAlg, SweeplnRT):
  """
  Implementation of regional intersection graph construction based on a 
  one-pass sweepline algorithm. This algorithm builds an undirected, 
  weighted graph of all the pair-wise intersections or overlapping
  regions within a RegionSet. Inherits from: SweeplnAlg and SweeplnRT.

  Properties:         graph
  Overridden Methods:
    Special Methods:  __init__
    SweeplnAlg:
      Methods:        oninit, addoverlap, onfinalize
  """
  graph: Graph

  def __init__(self, regionset: RegionSet):
    """
    Initialize the intersection graph construction
    by sweepline algorithm with the given RegionSet.

    :param regionset:
    """
    SweeplnAlg.__init__(self)
    SweeplnRT.__init__(self, regionset)
    SweeplnRT.put(self, self)

  def oninit(self, dimension: int):
    """
    Initialize the evaluation of the RegionSet in the SweeplnRT
    with the given dimensions. Create a new intersection Graph and
    populate it with nodes for each Region. This method extends
    the superclass implementation.

    :param dimension:
    """
    SweeplnAlg.oninit(self, dimension)

    self.graph = Graph()

    for region in self.regionset:
      self.graph.add_node(region.id, region=region)

  def addoverlap(self, regionpair: RegionPair):
    """
    Add the given pair of Regions to the intersection graph as an edge.
    The intersection Region is added to the edge as an data attribute.
    This method overrides in superclass implementation.

    :param regionpair:
    """
    self.graph.add_edge(regionpair[0].id, regionpair[1].id, \
                        intersect = regionpair[0].intersect(regionpair[1]))

  def onfinalize(self) -> Graph:
    """
    When the evaluation is complete, this method is invoked.
    Returns the newly constructed intersection Graph.
    This method extends the superclass implementation.
    """
    SweeplnAlg.onfinalize(self)

    return self.graph