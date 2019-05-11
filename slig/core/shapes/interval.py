#!/usr/bin/env python

"""
Interval Data Class

Implements the Interval class, a data class that defines lower and upper
bounding values for an interval. Are the building blocks for representing
multi-dimensional regions and computing for overlap between those regions.
Provides methods for determining if there is an overlap between two intervals
and what the intersection interval between the two intervals is.


Classes:
- Interval
"""

from collections import abc
from dataclasses import asdict, astuple, dataclass
from functools import reduce
from numbers import Number, Real
from typing import Any, Callable, Dict, List, Tuple, Union

from numpy import floor

from sources.abstract import IOable


@dataclass(order = True)
class Interval(IOable, abc.Container, abc.Hashable):
  """
  The lower and upper bounding values for an interval.

  Building block for representing multi-dimensional regions and computing
  for overlap between those regions. Provides methods for determining if there
  is an overlap between two intervals and what the intersection length between
  the two intervals is.

  Extends:
    IOable
    abc.Container
    abc.Hashable

  Attributes:
    lower, upper:
      The lower and upper bounding values.
  """
  lower: float
  upper: float

  def __init__(self, lower: Number, upper: Number):
    """
    Initialize a new Interval, with the lower and upper bounding values.
    Converts input values to floating point numbers, and assigns
    the float value to the lower and upper fields. If lower is greater
    than upper, swaps the lower and upper values.

    Args:
      lower, upper:
        the lower and upper bounding values.
    """
    self.assign(float(lower), float(upper))


  ### Properties: Getters

  @property
  def _instance_invariant(self) -> bool:
    """
    Invariant:
    - lower, upper must Real or float values
    - lower <= upper

    Returns:
      True: If instance invariant holds
      False: Otherwise.
    """
    return all([isinstance(self.lower, Real),
                isinstance(self.upper, Real),
                self.lower <= self.upper])


  @property
  def length(self) -> float:
    """
    Compute the length of this Interval.

    Returns:
      The distance between the lower and
      upper bounding values.
    """
    return abs(self.upper - self.lower)


  @property
  def midpoint(self) -> float:
    """
    Compute the midpoint between the lower and upper bounds
    of this Interval.

    Returns:
      The value equal distance between the lower and
      upper bounding values.
    """
    return (self.lower + self.upper) / 2


  ### Methods: Assignment

  def __setattr__(self, name, value):
    """
    Called when an attribute assignment is attempted. This is called instead
    of the normal mechanism. name is the attribute name, value is the value
    to be assigned to it.

    Ensures that the lower and upper bounding values satisfy the object
    invariant: lower <= upper, the lower and upper bounding values cannot be
    modified directly after this Interval is initialized. If the lower or upper
    bounding values are attempted to be set, raises an exception. This
    effectively prevents this Interval from being mutated into an invalid state.
    To mutate this Interval, call the assign() method with both lower and
    upper bounding values instead.

    Args:
      name:   The attribute name
      value:  The value to be assigned to it.

    Raises:
      Exception: Attempt to be set lower or upper
    """
    if name == 'lower' or name == 'upper':
      raise Exception(f'Cannot set immutable "{name}" attribute')

    object.__setattr__(self, name, value)


  def assign(self, lower: Real, upper: Real):
    """
    Assign the lower and upper bounding values of this Interval.
    Converts input values to floating point numbers, and assigns
    the float value to the lower and upper fields. If lower is greater
    than upper, swaps the lower and upper values.

    Args:
      lower, upper:
        the lower and upper bounding values.
    """
    assert isinstance(lower, Real)
    assert isinstance(upper, Real)

    if lower > upper:
      object.__setattr__(self, 'lower', float(upper))
      object.__setattr__(self, 'upper', float(lower))
    else:
      object.__setattr__(self, 'lower', float(lower))
      object.__setattr__(self, 'upper', float(upper))


  ### Methods: Hash

  def __hash__(self) -> str:
    """
    Return the hash value for this object.
    Two objects that compare equal must also have the same hash value,
    but the reverse is not necessarily true.

    Returns:
      The hash value for this object.
    """
    return hash(astuple(self))


  ### Methods: Clone

  def __copy__(self) -> 'Interval':
    """
    Create a shallow copy of this Interval and return it.

    Returns:
      The newly created Interval copy.
    """
    return Interval(*astuple(self))


  def copy(self) -> 'Interval':
    """
    Alias for self.__copy__()
    """
    return self.__copy__()


  ### Methods: Queries

  def contains(self, value: float, inc_lower = True, inc_upper = True) -> bool:
    """
    Determine if the value lies between the lower and upper bounding values.

    Args:
      value:
        The value to test if it lies within
        this Interval's bounds.
      inc_lower, inc_upper:
        Boolean flag for whether or not to include or
        to exclude the lower or upper bounding values
        of this Interval. If inc_lower is True, includes
        the lower bounding value, otherwise excludes it.
        Likewise, if inc_upper is True, includes the
        upper bounding value, otherwise excludes it.

    Returns:
      True:   If values lies between the lower and
              upper bounding values.
      False:  Otherwise.
    """
    assert self._instance_invariant

    gte_lower = self.lower <= value if inc_lower else self.lower < value
    lte_upper = self.upper >= value if inc_upper else self.upper > value

    return gte_lower and lte_upper


  def encloses(self, that: 'Interval', inc_lower = True, inc_upper = True) -> bool:
    """
    Determine if the Interval lies entirely within this Interval.

    Args:
      that:
        The other Interval to test if it lies
        entirely within this Interval's bounds.
      inc_lower, inc_upper:
        Boolean flag for whether or not to include or
        to exclude the lower or upper bounding values
        of this Interval. If inc_lower is True, includes
        the lower bounding value, otherwise excludes it.
        Likewise, if inc_upper is True, includes the
        upper bounding value, otherwise excludes it.

    Returns:
      True:   If other Interval lies entirely within
              this Interval's bounds.
      False:  Otherwise.
    """
    assert isinstance(that, Interval)

    return all([self.length >= that.length,
                self.contains(that.lower, inc_lower, inc_upper),
                self.contains(that.upper, inc_lower, inc_upper)])


  def __contains__(self, value: Union[float, 'Interval']) -> bool:
    """
    Determine if the value or Interval lies entirely between this Interval's
    lower and upper bounding values, inclusively. Return True if value or
    Interval is entirely within this Interval, otherwise False.

    Is syntactic sugar for:
      value in self

    Overload Method that wraps:
      self.contains when value is a float value, and
      self.encloses when value is an Interval

    Args:
      value:
        The value to test if it lies within this Interval's
        bounds, or the other Interval to test if it lies
        entirely within this Interval's bounds.

    Returns:
      True:   If the value or other Interval lies entirely
              within this Interval's bounds.
      False:  Otherwise.
    """
    if isinstance(value, Interval):
      return self.encloses(value)
    else:
      return self.contains(value)

  def is_intersecting(self, that: 'Interval', inc_bounds = False) -> bool:
    """
    Determine if the given Interval overlaps with this Interval.
    If the intervals are exactly adjacent (one's lower is equal other's upper),
    then if they intersect or not is decided by inc_bounds flag.
    To be overlapping, one Interval must contain the other's lower or upper
    bounding value. Return True if given Interval overlaps with this Interval,
    otherwise False.

    Args:
      that:
        The other Interval to test if it overlaps
        with this Interval.
      inc_bounds:
        If intervals considered intersecting when
        lower/upper bounds are exactly equal
        (zero-length intersection)

    Returns:
      True:   If that Interval overlaps with this Interval
      False:  Otherwise.

    Examples:

      Overlapping:
      - |<---- Interval A ---->|
        |<---- Interval B ---->|
      - |<---- Interval A ---->|
            |<- Interval B ->|
      -    |<- Interval A ->|
        |<---- Interval B ---->|
      - |<- Interval A ->|
              |<- Interval B ->|
      -       |<- Interval A ->|
        |<- Interval B ->|

      Not overlapping:
      - |<- Interval A ->|   |<- Interval B ->|
      - |<- Interval B ->|   |<- Interval A ->|

      Conditionally overlapping:
      - |<- Interval A ->||<- Interval B ->|
      - |<- Interval B ->||<- Interval A ->|
    """
    assert isinstance(that, Interval)
    assert self._instance_invariant
    assert that._instance_invariant

    if self == that:
      return True

    if inc_bounds:
      return self.upper >= that.lower and that.upper >= self.lower

    return self.upper > that.lower and that.upper > self.lower


  ### Methods: Generators

  def get_intersection(self, that: 'Interval', inc_bounds = False) -> Union['Interval', None]:
    """
    Compute the overlapping Interval between this Interval and that Interval.
    If the intervals are exactly adjacent (one's lower is equal other's upper),
    then if they intersect or not is decided by inc_bounds flag.
    Return the overlapping Interval or None if the Intervals do not overlap.

    Args:
      that:
        The other Interval which this Interval is to compute
        the overlapping Interval with.
      inc_bounds:
        If intervals considered intersecting when
        lower/upper bounds are exactly equal
        (zero-length intersection)

    Returns:
      The overlapping Interval: If the Intervals overlap.
      None: If the Intervals do not overlap.

    Examples:

      Intersects:
      - |<---- Interval A ---->|
        |<---- Interval B ---->|
        |<---- ########## ---->|
      - |<---- Interval A ---->|
            |<- Interval B ->|
            |<- ########## ->|
      -    |<- Interval A ->|
        |<---- Interval B ---->|
            |<- ######### ->|
      - |<- Interval A ->|
              |<- Interval B ->|
              |<- #### ->|
      -       |<- Interval A ->|
        |<- Interval B ->|
              |<- #### ->|
    """
    assert isinstance(that, Interval)
    assert self._instance_invariant
    assert that._instance_invariant

    if not self.is_intersecting(that, inc_bounds):
      return None

    return Interval(max(self.lower, that.lower),
                    min(self.upper, that.upper))


  def get_union(self, that: 'Interval') -> 'Interval':
    """
    Compute the Interval that encloses both this Interval and that Interval.
    Return the enclosing Interval.

    Args:
      that:
        The other Interval which this Interval is to compute
        the encloseing Interval with.

    Returns:
      The enclosing Interval.

    Examples:

      Unions:
      - |<- Interval A ->|        |<- A ->||<- B ->|
        |<- Interval B ->|        |<- B ->||<- A ->|
        |<- ########## ->|        |<- ########## ->|
      - |<--- Interval A --->|        |<- Interval A ->|
            |<- Interval B ->|    |<--- Interval B --->|
        |<- ############## ->|    |<- ############## ->|
      - |<- Interval A ->|        |<- Interval A ->|
            |<- Interval B ->|    |<- Interval B ->|
        |<- ############## ->|    |<- ############## ->|
      - |<- A ->|    |<- B ->|    |<- B ->|    |<- A ->|
        |<- ############## ->|    |<- ############## ->|
    """
    assert isinstance(that, Interval)
    assert self._instance_invariant
    assert that._instance_invariant

    return Interval(min(self.lower, that.lower),
                    max(self.upper, that.upper))

  ### Class Methods: Generators

  @classmethod
  def from_intersection(cls, intervals: List['Interval']) -> Union['Interval', None]:
    """
    Construct a new Interval from the intersection of the given list of
    Intervals. If not all the Intervals intersect, return None, otherwise
    return the Interval that intersects with all of the given Intervals.

    Args:
      intervals:
        List of Intervals to compute the intersecting
        Interval amongst.

    Returns:
      Interval that intersects with all given Intervals.
      None: If not all the Intervals intersect.
    """
    assert isinstance(intervals, List) and len(intervals) > 1
    assert all([isinstance(interval, Interval) for interval in intervals])

    def intersect(a: Interval, b: Interval) -> Interval:
      assert a != None and b != None
      assert a.overlaps(b)
      return a.get_intersection(b)

    try:
      return reduce(intersect, intervals)
    except AssertionError:
      return None


  @classmethod
  def from_union(cls, intervals: List['Interval']) -> 'Interval':
    """
    Construct a new Interval from the union of the given list of Intervals.
    Return the Interval that encloses all of the given Intervals.

    Args:
      intervals:
        List of Intervals to compute the union
        Interval amongst.

    Returns:
      Interval that encloses all of the given Intervals.
    """
    assert isinstance(intervals, List) and len(intervals) > 1
    assert all([isinstance(interval, Interval) for interval in intervals])

    return reduce(lambda a, b: a.get_union(b), intervals)


  ### Class Methods: (De)serialization

  @classmethod
  def to_object(cls, object: 'Interval', format: str = 'json', **kwargs) -> Any:
    """
    Generates an object (dict, list, or tuple) from the given Interval object
    that can be converted or serialized as the specified data format: 'json'.
    Additional arguments passed via kwargs are used to customize and tweak the
    object generation process.

    Args:
      object: The Interval convert to an object (dict, list, tuple).
      format: The targetted output format type.
      kwargs: Additional arguments or options to customize and
              tweak the object generation process.

    kwargs:
      compact:
        Boolean flag for whether or not the data representation
        of the output JSON is a compact, abbreviated representation or
        the full data representation with all fields.

    Returns:
      The generated object.
    """
    assert isinstance(object, Interval)

    if 'compact' in kwargs and kwargs['compact']:
      return astuple(object)
    else:
      return asdict(object)

  @classmethod
  def from_object(cls, object: Any) -> 'Interval':
    """
    Construct a new Interval from the conversion of the given object.
    The object may be a Dict, List or Tuple. If it is a Dict contains fields:
    lower and upper bounding values. If it is a List or Tuple contains two
    values, first for the lower bound and second for the upper bound. Returns
    the new Interval.

    Args:
      object:
        The object (dict, tuple, list) to be converted
        into a new Interval instance.

    Returns:
      The newly constructed Interval.
    """
    if isinstance(object, Dict):
      assert 'lower' in object and isinstance(object['lower'], (Real, str))
      assert 'upper' in object and isinstance(object['upper'], (Real, str))
      return Interval(**object)
    else:
      assert isinstance(object, (List, Tuple)) and len(object) == 2
      assert all([isinstance(item, (Real, str)) for item in object])
      return Interval(*object)
