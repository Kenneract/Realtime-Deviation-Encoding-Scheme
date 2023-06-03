"""
Author: Kennan (Kenneract)

Date: Jun.2.2023

Description: A small collection of functions for working with bits & bytes.
"""


def byte(val):
	"""
	A quick function to cast the given value
	to a byte (8 bits).
	"""
	return (val & 0xFF)


def checkBit(inByte, position):
	"""
	Returns the state (1=True, 0=False) of the
	given bit in a byte.

	MSB							LSB
	B8	B7	B6	B5	B4	B3	B2	B1
	"""
	maskVal = 2**(position-1)
	return (inByte & maskVal)>0

def byte2Str(inByte):
	"""
	Returns a string-representation
	of a given byte.
	"""
	return format(inByte, '#010b')
