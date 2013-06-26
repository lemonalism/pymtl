#=========================================================================
# Bits.py
#=========================================================================
# Module containing the Bits class.

from SignalValue import SignalValue

# NOTE: circular imports between Bits and helpers, using 'import helpers'
#       instead of 'from helpers import' ensures pydoc still works
import helpers
import operator

#-------------------------------------------------------------------------
# Bits
#-------------------------------------------------------------------------
# Class emulating limited precision values of a set bitwidth.
class Bits( SignalValue ):

  #-----------------------------------------------------------------------
  # __init__
  #-----------------------------------------------------------------------
  def __init__( self, nbits, value = 0, trunc = False ):

    # Disallow value = Bits()
    assert isinstance( value, (int, long) )
    # Make sure width is non-zero and that we have space for the value
    assert nbits > 0

    # Set the nbits and bitmask (_mask) attributes
    self.nbits = nbits
    self._max  =  2**nbits - 1
    self._min  = -2**nbits
    self._mask = ( 1 << self.nbits ) - 1

    if not trunc:
      #assert nbits >= helpers.get_nbits( value )
      assert self._min <= value <= self._max

    # Convert negative values into unsigned ints and store them
    value_uint = value if ( value >= 0 ) else ( ~(-value) + 1 )
    self._uint = value_uint & self._mask

  #-----------------------------------------------------------------------
  # uint
  #-----------------------------------------------------------------------
  # Return the unsigned integer representation of the bits.
  def uint( self ):
    return self._uint

  #-----------------------------------------------------------------------
  # uint
  #-----------------------------------------------------------------------
  # Return the integer representation of the bits.
  def int( self ):
    if ( self[ self.nbits - 1] ):
      twos_complement = ~self + 1
      return -twos_complement._uint
    else:
      return self._uint

  #-----------------------------------------------------------------------
  # write
  #-----------------------------------------------------------------------
  # Implementing abstract write method defined by SignalValue.
  def write( self, value ):
    # TODO... performance impact of this? A way to get around this?
    if isinstance( value, Bits ):
      value = value._uint
    #assert self.nbits >= helpers.get_nbits( value )
    assert self._min <= value <= self._max
    self._uint = (value & self._mask)

  #-----------------------------------------------------------------------
  # bit_length
  #-----------------------------------------------------------------------
  # Implement bit_length method provided by the int built-in. Simplifies
  # the implementation of get_nbits().
  def bit_length( self ):
    return self._uint.bit_length()

  #-----------------------------------------------------------------------
  # Print Methods
  #-----------------------------------------------------------------------

  def __repr__(self):
    return "Bits(w={0},v={1})".format(self.nbits, self._uint)

  def __str__(self):
    num_chars = (((self.nbits-1)/4)+1)
    str = "{:x}".format(self._uint).zfill(num_chars)
    return str[-num_chars:len(str)]

  def bin_str(self):
    str = "{:b}".format(self._uint).zfill(self.nbits)
    return str

  #------------------------------------------------------------------------
  # Descriptor Object Methods
  #------------------------------------------------------------------------
  # http://www.rafekettler.com/magicmethods.html#descriptor
  # Doesn't work :(
  # http://stackoverflow.com/a/1004254

  #def __get__(self, instance, owner ):
  #  return self._uint

  #def __set__(self, instance, value ):
  #  print "HERE"
  #  self._uint = ( value & self._mask )

  #------------------------------------------------------------------------
  # __getitem__
  #------------------------------------------------------------------------
  # Read a subset of bits in the Bits object.
  def __getitem__( self, addr ):

    # TODO: clean up this logic!

    if isinstance( addr, slice ):
      start = addr.start
      stop = addr.stop
      # special case open-ended ranges [:], [N:], and [:N]
      if start is None and stop is None:
        return Bits( self.nbits, self._uint )
      elif start is None:
        start = 0
      elif stop is None:
        stop = self.nbits
      # Make sure our ranges are sane
      assert 0 <= start < stop <= self.nbits
      nbits = stop - start
      mask  = (1 << nbits) - 1
      return Bits( nbits, (self._uint & (mask << start)) >> start )
    else:
      assert 0 <= addr < self.nbits
      return Bits( 1, (self._uint & (1 << addr)) >> addr )

  #------------------------------------------------------------------------
  # write_slice
  #------------------------------------------------------------------------
  # Write a subset of bits in the Bits object.
  # Need to do it this way because it's impossible for __setitem__ to be
  # overridden per-instance after the fact!
  # http://stackoverflow.com/questions/11687653/method-overriding-by-monkey-patching
  def write_slice( self, addr, value ):

    # TODO: clean up this logic!

    if isinstance( value, Bits ):
      value = value._uint

    if isinstance( addr, slice ):
      start = addr.start
      stop = addr.stop
      # special case open-ended ranges [:], [N:], and [:N]
      if start is None and stop is None:
        #assert self.nbits >= helpers.get_nbits( value )
        assert self._min <= value <= self._max
        self._uint = value
        return
      elif start is None:
        start = 0
      elif stop is None:
        stop = self.nbits
      # Make sure our ranges are sane
      assert 0 <= start < stop <= self.nbits
      nbits = stop - start
      # This assert fires if the value you are trying to store is wider
      # than the bitwidth of the slice you are writing to!
      #assert nbits >= helpers.get_nbits( value )
      assert self._min <= value <= self._max
      # Clear the bits we want to set
      ones  = (1 << nbits) - 1
      mask = ~(ones << start)
      cleared_val = self._uint & mask
      # Set the bits, anding with ones to ensure negative value assign
      # works that way you would expect. TODO: performance impact?
      self._uint = cleared_val | ((value & ones) << start)
    else:
      assert 0 <= addr < self.nbits
      assert 0 <= value <= 1
      # Clear the bits we want to set
      mask = ~(1 << addr)
      cleared_val = self._uint & mask
      # Set the bits
      self._uint = cleared_val | (value << addr)

  #------------------------------------------------------------------------
  # Arithmetic Operators
  #------------------------------------------------------------------------
  # For now, let's make the width equal to the max of the widths of the
  # two operands. These semantics match Verilog:
  # http://www1.pldworld.com/@xilinx/html/technote/TOOL/MANUAL/21i_doc/data/fndtn/ver/ver4_4.htm

  # TODO: reflected operands?
  def __invert__( self ):
    return Bits( self.nbits, ~self._uint, trunc=True )

  def __add__( self, other ):
    if not isinstance( other, Bits ):
      #other = Bits( helpers.get_nbits( other ), other )
      other = Bits( self.nbits, other )
    return Bits( max( self.nbits, other.nbits ),
                 operator.add( self._uint, other._uint), trunc=True )

  def __sub__( self, other ):
    if not isinstance( other, Bits ):
      #other = Bits( helpers.get_nbits( other ), other )
      other = Bits( self.nbits, other )
    return Bits( max( self.nbits, other.nbits ),
                 operator.sub( self._uint, other._uint), trunc=True )

  # TODO: what about multiplying Bits object with an object of other type
  # where the bitwidth of the other type is larger than the bitwidth of the
  # Bits object? ( applies to every other operator as well.... )
  def __mul__( self, other ):
    if isinstance( other, int ):
      return Bits( 2*self.nbits, operator.mul( self._uint, other ) )
    else:
      assert self.nbits == other.nbits
      return Bits( 2*self.nbits, operator.mul( self._uint, other._uint ) )

  def __radd__( self, other ):
    return self.__add__( other )

  def __rsub__( self, other ):
    return Bits( helpers.get_nbits( other ), other ) - self

  def __rmul__( self, other ):
    return self.__mul__( other )

  # TODO: implement these?
  #def __floordiv__(self, other)
  #def __mod__(self, other)
  #def __divmod__(self, other)
  #def __pow__(self, other[, modulo])

  #------------------------------------------------------------------------
  # Shift Operators
  #------------------------------------------------------------------------

  def __lshift__( self, other ):
    if isinstance( other, int ):
      # If the shift amount is greater than the width, just return 0
      if other >= self.nbits: return Bits( self.nbits, 0 )
      #return Bits( self.nbits, self._uint << other, trunc=True )
      return Bits( self.nbits, operator.lshift( self._uint, other), trunc=True )
    else:
      # If the shift amount is greater than the width, just return 0
      if other._uint >= self.nbits: return Bits( self.nbits, 0 )
      #return Bits( self.nbits, self._uint << other._uint, trunc=True )
      return Bits( self.nbits, operator.lshift( self._uint, other._uint), trunc=True )

  def __rshift__( self, other ):
    if isinstance( other, int ):
      #assert other <= self.nbits
      #return Bits( self.nbits, self._uint >> other )
      return Bits( self.nbits, operator.rshift( self._uint, other ) )
    else:
      #assert other.uint <= self.nbits
      #return Bits( self.nbits, self._uint >> other._uint )
      return Bits( self.nbits, operator.rshift( self._uint, other._uint ) )

  # TODO: Not implementing reflective operators because its not clear
  #       how to determine width of other object in case of lshift
  #def __rlshift__(self, other):
  #  return self.__lshift__( other )
  #def __rrshift__(self, other):
  #  return self.__rshift__( other )

  #------------------------------------------------------------------------
  # Bitwise Operators
  #------------------------------------------------------------------------

  def __and__( self, other ):
    #if isinstance( other, Bits ):
    #  other = other._uint
    #assert other >= 0
    #return Bits( max( self.nbits, helpers.get_nbits( other ) ),
    #             self._uint & other)
    if isinstance( other, int ):
      other = Bits( self.nbits, other )
    assert other >= 0
    return Bits( max( self.nbits, other.nbits ),
                 operator.and_( self._uint, other._uint ) )
                 #self._uint & other._uint )

  def __xor__( self, other ):
    #if isinstance( other, Bits ):
    #  other = other._uint
    #assert other >= 0
    #return Bits( max( self.nbits, helpers.get_nbits( other ) ),
    #             self._uint ^ other)
    if isinstance( other, int ):
      other = Bits( self.nbits, other )
    assert other >= 0
    return Bits( max( self.nbits, other.nbits ),
                 operator.xor( self._uint, other._uint ) )
                 #self._uint ^ other._uint )

  def __or__( self, other ):
    #if isinstance( other, Bits ):
    #  other = other._uint
    #assert other >= 0
    #return Bits( max( self.nbits, helpers.get_nbits( other ) ),
    #             self._uint | other)
    if isinstance( other, int ):
      other = Bits( self.nbits, other )
    assert other >= 0
    return Bits( max( self.nbits, other.nbits ),
                 operator.or_( self._uint, other._uint ) )
                 #self._uint | other._uint )

  def __rand__( self, other ):
    return self.__and__( other )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __ror__( self, other ):
    return self.__or__( other )

  #------------------------------------------------------------------------
  # Comparison Operators
  #------------------------------------------------------------------------

  def __nonzero__(self):
    return self._uint != 0

  def __eq__(self,other):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint == other
    return operator.eq( self._uint, other )

  def __ne__(self,other):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint != other
    return operator.ne( self._uint, other )

  def __lt__(self,other):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint < other
    return operator.lt( self._uint, other )

  def __le__( self,other ):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint <= other
    return operator.le( self._uint, other )

  def __gt__( self, other ):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint > other
    return operator.gt( self._uint, other )

  def __ge__( self, other ):
    if isinstance( other, Bits ):
      assert self.nbits == other.nbits
      other = other._uint
    assert other >= 0   # TODO: allow comparison with negative numbers?
    #return self._uint >= other
    return operator.ge( self._uint, other )

  #------------------------------------------------------------------------
  # Extension
  #------------------------------------------------------------------------
  # TODO: make abstract method in SignalValue, or implement differently?

  def _zext( self, new_width ):
    return Bits( new_width, self._uint )

  def _sext( self, new_width ):
    return Bits( new_width, self.int() )
