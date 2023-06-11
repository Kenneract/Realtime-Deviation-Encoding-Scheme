"""
Author: Kennan (Kenneract)

Date: Jun.2.2023

Description: RDES demo implementation (all 3 variants). Designed for
			 easy testing and debugging; a much more efficient / focused
			 implementation is absolutely possible.
"""

from byteTools import byte, checkBit, byte2Str


class RDESCompressor():
	"""
	A demo RDES compressor class for UNSIGNED 31-bit values.
	Use RDESCompressor.unsignify() to store signed values.

	Supports RDES variants: RDES1, RDES2, RDES3

	Designed to handle data in table-form. Each "column"
	is treated as an independent sequence.

	Can accept a sequence of integers and
	produce a compressed array of data in real-time.

	NOTE: The decompressor must have matching column & signify settings,
	or else decompressed data will be corrupted!
	"""

	def __init__(self, variant:int=3, numCols:int=3, verbose:bool=False, originRefreshInterval:int=0):
		# The RDES variant
		self.__variant = variant
		# Number of columns in the virtual table
		self.__numCols = numCols
		# After how many rows should a raw value be written regardless
		# (prevents mass corruption)
		self.__originRefreshInterval = originRefreshInterval
		# If debug data should be printed to the console
		self.__verbose = verbose

		# Compressed data cache
		self.__compressed = bytearray()
		# How many concurrent rows of offsets have been written
		self.__rowsSinceRaw = 0
		# If the first row of data has been processed
		self.__initialized = False
		# The most recently stored values (not offsets)
		self.__lastVals = []		
		# Number of rows that have been processed
		self.__rowsCompressed = 0


	def getUncompressedSize(self):
		"""
		Returns the size of all the uncompressed data
		that has been processed, in bytes
		"""
		# values = rows * cols
		# uint32 = 4 bytes
		return self.__rowsCompressed * self.__numCols * 4


	def getCompressedSize(self):
		"""
		Returns the size of the compressed data in the cache,
		in bytes
		"""
		return len(self.__compressed)


	def getCompressionRatio(self):
		"""
		Returns the current compression ratio of
		the cached compressed data
		"""
		return self.getUncompressedSize() / self.getCompressedSize()


	def reset(self):
		"""
		Clears the internal cache of compressed data;
		effectively clears the virtual table.
		"""
		if self.__verbose: print("RDESComp: Reset")
		self.__compressed = bytearray()
		self.__rowsSinceRaw = 0
		self.__initialized = False
		self.__rowsCompressed = 0


	def unsignify(self, inp):
		"""
		Converts a signed long to an unsigned long so
		it may be compressed by RDES.

		Max values are -1,073,741,823 to +1,073,741,823.

		Can be decoded using resignify()
		"""
		return inp + ((2**30)-1)//2


	def getCompressedData(self):
		"""
		Returns the current cache of compressed data.

		Returns: bytearray
		"""
		return self.__compressed


	def __writeUint32(self, value):
		"""
		Writes a 31-bit value directly to the compressed cache.

		Sets the 32nd bit (MSB) to 0, denoting a uint32.
		"""
		b1 = value>>24 & 0b01111111 #Set Bit8=0
		b2 = byte( value>>16 )
		b3 = byte( value>>8 )
		b4 = byte( value )

		self.__compressed.append(b1) #MSB
		self.__compressed.append(b2)
		self.__compressed.append(b3)
		self.__compressed.append(b4) #LSB


	def __write3Bytes(self, b1, b2, b3):
		"""
		Writes 3 bytes directly to the compressed cache.

		Inputs MUST be bytes (8 bits)
		"""
		self.__compressed.append(b1) #MSB
		self.__compressed.append(b2)
		self.__compressed.append(b3) #LSB


	def __write2Bytes(self, b1, b2):
		"""
		Writes 2 bytes directly to the compressed cache

		Inputs MUST be bytes (8 bits)
		"""
		self.__compressed.append(b1) #MSB
		self.__compressed.append(b2) #LSB


	def __write1Byte(self, b1):
		"""
		Writes 1 byte directly to the compressed cache

		Inputs MUST be bytes (8 bits)
		"""
		self.__compressed.append(b1) #MSB


	def writeCompressedRow(self, data:list):
		"""
		Compresses the given data and writes it to the internal
		virtual table as a new row.

		Requires a list of data, each element being its own column.
		"""
		## Note new row
		self.__rowsCompressed += 1

		## Write unmodified data is it is the first row
		if (not self.__initialized):
			self.__lastVals = data
			for val in data:
				self.__writeUint32(val)
			self.__initialized = True
			if self.__verbose: print("RDESComp: Initialized")
			return

		## Write unmodified data if origin refresh interval met
		if (self.__originRefreshInterval > 0 and self.__rowsSinceRaw >= self.__originRefreshInterval):
			self.__lastVals = data
			self.__rowsSinceRaw = 0
			for val in data:
				self.__writeUint32(val)
			if self.__verbose: print("RDESComp: Origin Refresh")
			return

		## Hand-off to specific RDES variant algorithm
		if (self.__variant == 1):
			self.__compressRowRDES1(data)
		elif (self.__variant == 2):
			self.__compressRowRDES2(data)
		else:
			self.__compressRowRDES3(data)

		## Clean up
		self.__rowsSinceRaw += 1
		if self.__verbose: print("RDESComp: Row compressed")


	def __compressRowRDES3(self, data:list):
		"""
		RDES3. Compresses the given data and writes it to 
		the internal virtual table as a new row.

		Requires a list of data, each element being its own column.
		"""

		LVL_1_MAX = (2**5)-1 # Lvl1 = 5 bits
		LVL_2_MAX = (2**12)-1 # Lvl2 = 12 bits
		LVL_3_MAX = (2**20)-1 # Lvl3 = 20 bits

		## Loop over each column in this row
		for i in range(self.__numCols):
			newVal = data[i]
			lastVal = self.__lastVals[i]
			if self.__verbose: print(f"RDES3: Compressing column {i}: {lastVal} -> {newVal}")
			## Determine if adding or subtracting
			add = (newVal >= lastVal)
			## Determine offset
			offset = abs(lastVal - newVal)
			
			## Determine how many bytes needed for storage
			lvl = 4
			if (offset <= LVL_1_MAX): lvl=1
			elif (offset <= LVL_2_MAX): lvl=2
			elif (offset <= LVL_3_MAX): lvl=3
			
			## Check if compression can help
			if (lvl == 4):
				self.__writeUint32( newVal )
				if self.__verbose: print(f"\tWriting uncompressed 4 bytes")
			else:
				if self.__verbose: print(f"\tOffset = {offset} = {byte2Str(offset)} (add={add})")
				## Generate compressed bytes
				if (lvl == 1):
					# Compute 1 compressed bytes
					
					byte1 = 0b11000000 | offset #captures D05 to D01
					
					if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
					byte1 = byte1 & 0b11011111 # Set Bit6 to 0 (size=1)

					# Write
					self.__write1Byte(byte1)
					if self.__verbose: print(f"\tWriting 1 compressed byte")

				if (lvl == 2):
					# Compute 2 compressed bytes
					
					byte1 = 0b11110000 | offset>>8 #captures D13 to D09
					byte2 = 0b11111111 & offset #captures D08 to D01
					
					if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
					byte1 = byte1 & 0b11101111 # Set Bit5 to 0 (size=2)

					# Write
					self.__write2Bytes(byte1, byte2)
					if self.__verbose: print(f"\tWriting 2 compressed bytes")

				elif (lvl == 3):
					# Compute 3 compressed bytes
					byte1 = 0b11110000 | offset>>16 #captures D20 to D17
					byte2 = 0b11111111 & offset>>8 #captures D16 to D09
					byte3 = 0b11111111 & offset #captures D08 to D01

					if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
					# Write
					self.__write3Bytes(byte1, byte2, byte3)
					if self.__verbose: print(f"\tWriting 3 compressed bytes")

			## Record new value
			self.__lastVals[i] = newVal


	def __compressRowRDES2(self, data:list):
		"""
		RDES2. Compresses the given data and writes it to 
		the internal virtual table as a new row.

		Requires a list of data, each element being its own column.
		"""

		LVL_2_MAX = (2**13)-1 # Lvl2 = 13 bits
		LVL_3_MAX = (2**21)-1 # Lvl3 = 21 bits

		## Loop over each column in this row
		for i in range(self.__numCols):
			newVal = data[i]
			lastVal = self.__lastVals[i]
			if self.__verbose: print(f"RDES2: Compressing column {i}: {lastVal} -> {newVal}")
			## Determine if adding or subtracting
			add = (newVal >= lastVal)
			## Determine offset
			offset = abs(lastVal - newVal)
			
			## Determine how many bytes needed for storage
			lvl = 4
			if (offset <= LVL_2_MAX): lvl=2
			elif (offset <= LVL_3_MAX): lvl=3
			
			## Check if compression can help
			if (lvl == 4):
				self.__writeUint32( newVal )
				if self.__verbose: print(f"\tWriting uncompressed 4 bytes")
			else:
				if self.__verbose: print(f"\tOffset = {offset} = {byte2Str(offset)} (add={add})")
				## Generate compressed bytes
				if (lvl == 2):
					# Compute 2 compressed bytes
					
					byte1 = 0b11100000 | offset>>8 #captures D13 to D09
					byte2 = 0b11111111 & offset #captures D08 to D01
					
					if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
					byte1 = byte1 & 0b11011111 # Set Bit6 to 0 (size=2)

					# Write
					self.__write2Bytes(byte1, byte2)
					if self.__verbose: print(f"\tWriting 2 compressed bytes")
				
				elif (lvl == 3):
					# Compute 3 compressed bytes
					byte1 = 0b11100000 | offset>>16 #captures D21 to D17
					byte2 = 0b11111111 & offset>>8 #captures D16 to D09
					byte3 = 0b11111111 & offset #captures D08 to D01

					if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
					# Write
					self.__write3Bytes(byte1, byte2, byte3)
					if self.__verbose: print(f"\tWriting 3 compressed bytes")
				
			## Record new value
			self.__lastVals[i] = newVal


	def __compressRowRDES1(self, data:list):
		"""
		RDES1. Compresses the given data and writes it to 
		the internal virtual table as a new row.

		Requires a list of data, each element being its own column.
		"""

		LVL_3_MAX = (2**22)-1 # Lvl3 = 22 bits

		## Loop over each column in this row
		for i in range(self.__numCols):
			newVal = data[i]
			lastVal = self.__lastVals[i]
			if self.__verbose: print(f"RDES1: Compressing column {i}: {lastVal} -> {newVal}")
			## Determine if adding or subtracting
			add = (newVal >= lastVal)
			## Determine offset
			offset = abs(lastVal - newVal)
			
			## Determine how many bytes needed for storage
			lvl = 4
			if (offset <= LVL_3_MAX): lvl=3

			## Check if compression can help
			if (lvl == 4):
				self.__writeUint32( newVal )
				if self.__verbose: print(f"\tWriting uncompressed 4 bytes")
			else:
				if self.__verbose: print(f"\tOffset = {offset} = {byte2Str(offset)} (add={add})")
				## Generate 3 compressed bytes
	
				byte1 = 0b11000000 | offset>>16 #captures D22 to D17
				byte2 = 0b11111111 & offset>>8 #captures D16 to D09
				byte3 = 0b11111111 & offset #captures D08 to D01

				if (not add): byte1 = byte1 & 0b10111111 # Set Bit7 to 0 (subtracting)
				# Write
				self.__write3Bytes(byte1, byte2, byte3)
				if self.__verbose: print(f"\tWriting 3 compressed bytes")

			## Record new value
			self.__lastVals[i] = newVal



class RDESDecompressor():
	"""
	A demo RDES decompressor class for UNSIGNED 31-bit values.
	Use RDESDecompressor.resignify() to recover signed values,
	or provide the column indexes (start=0) to have them
	automatically re-signed.

	Supports RDES variants: RDES1, RDES2, RDES3

	Requires the entire compressed dataset to function.

	Data is assumed to be a table; decompression results in an array, with
	each entry having a list of column values for that given row.

	NOTE: The decompressor must have matching column & signify settings,
	or else decompressed data will be corrupted!
	"""

	def __init__(self, variant:int=1, numCols:int=3, verbose:bool=False, signedCols=[]):
		# The RDES variant
		self.__variant = variant
		# Number of columns in the virtual table
		self.__numCols = numCols
		# If debug data should be printed to the console
		self.__verbose = verbose
		# Index of columns that contain signed data
		self.__signedCols = signedCols

		# Current column waiting for a value
		self.__curCol = 0
		# The most recent decoded values for each column
		self.__lastDecodedVals = [0]*self.__numCols
		# A copy of the most recent set of decompressed data
		self.__lastDecompressed = []
		# The size of the last compressed input (bytes)
		self.__lastCompressedSize = 0


	def getUncompressedSize(self):
		"""
		Returns the size of the most recent uncompressed
		data, in bytes.
		"""
		# values = rows * cols
		# uint32 = 4 bytes
		return len(self.__lastDecompressed) * self.__numCols * 4


	def getCompressedSize(self):
		"""
		Returns the size of the most recently provided
		compressed data, in bytes.
		"""
		return self.__lastCompressedSize


	def getCompressionRatio(self):
		"""
		Returns the compression ratio of the last
		decompressed data.
		"""
		return self.getUncompressedSize() / self.getCompressedSize()


	def resignify(self, inp):
		"""
		Converts an encoded signed value (unsigned) to a
		signed value.

		Undoes the encoding of unsignify()
		"""
		return inp - ((2**30)-1)//2


	def __rdes1ExtractByte(self, byte1):
		"""
		Extracts the value data from the most-significant
		byte of an RDES1-encoded offset value (eliminates
		flag bits).
		"""
		# 6 value bits
		return byte1 & 0b00111111


	def __rdes2ExtractByte(self, byte1):
		"""
		Extracts the value data from the most-significant
		byte of an RDES2-encoded offset value (eliminates
		flag bits).
		"""
		# 5 value bits
		return byte1 & 0b00011111


	def __rdes3ExtractByte(self, byte1):
		"""
		Extracts the value data from the most-significant
		byte of an RDES3-encoded offset value (eliminates
		flag bits).
		"""
		if (checkBit(byte1, 6) == 1):
			# 2 or 3 bytes; 4 value bits
			return byte1 & 0b00001111
		else:
			# 1 byte; 5 value bits
			return byte1 & 0b00011111


	def decompress(self, bytes):
		"""
		Decompresses the provided data and returns the original data.

		In format of list of lists, with each sub-list representing a row.
		"""
		## Make temp variables
		decodedRows = []
		curRowVals = [0]*self.__numCols
		## Cache size
		self.__lastCompressedSize = len(bytes)

		## Iterate until all bytes have been handled
		i = 0
		while (i < len(bytes)):
			byte1 = bytes[i]
			if self.__verbose: print(f"RDESDeco: Processing byte #{i+1}; {byte2Str(byte1)}")

			## Decode next value
			if (checkBit(byte1, 8) == 1): # Offset value found - decode
				## Determine origin of offset
				refVal = self.__lastDecodedVals[self.__curCol]

				## Determine number of bytes offset is
				if (self.__variant == 1):
					# 3
					size = 3
				elif (self.__variant == 2):
					# 2 or 3
					size = 3 if checkBit(byte1, 6) else 2
				else:
					# 1, 2, or 3
					size = 1
					if (checkBit(byte1, 6) == 1):
						size = 3 if checkBit(byte1, 5) else 2

				## Decode offset value
				if (size == 1):
					# Acquire MSB / offset
					offset = self.__rdes3ExtractByte(byte1)
				elif (size == 2):
					# Acquire MSB
					if (self.__variant == 2):
						b1 = self.__rdes2ExtractByte(byte1)
					else:
						b1 = self.__rdes3ExtractByte(byte1)
					# Calculate offset
					b2 = bytes[i+1]
					offset = (b1<<8) + b2
				else: #size=3
					# Acquire MSB
					if (self.__variant == 3):
						b1 = self.__rdes3ExtractByte(byte1)
					elif (self.__variant == 2):
						b1 = self.__rdes2ExtractByte(byte1)
					else:
						b1 = self.__rdes1ExtractByte(byte1)
					# Calculate offset
					b2 = bytes[i+1]
					b3 = bytes[i+2]
					offset = (b1<<16) + (b2<<8) + b3
				i += size #move cursor forward

				## Determine offset sign
				add = checkBit(byte1, 7) #B07; 1=add, 0=sub
				if (not add): offset *= -1

				## Calculate value
				decodedVal = refVal + offset

				if self.__verbose: print(f"\tDecoded offset = {offset}, size={size}B -> {refVal} + {offset} = {decodedVal}")

			else: # Raw uint32 found - decode
				## Isolate bytes
				b1 = byte1
				b2 = bytes[i+1]
				b3 = bytes[i+2]
				b4 = bytes[i+3]
				i += 4
				decodedVal = (b1<<24) + (b2<<16) + (b3<<8) + b4

			## Ensure sign is corrected for output
			storedVal = decodedVal # The actual value that is stored (before re-signifying)
			if (self.__curCol in self.__signedCols):
				decodedVal = self.resignify(decodedVal)

			if self.__verbose: print(f"\tDecoded raw value = {decodedVal}")

			## Value decoded; store in row
			curRowVals[self.__curCol] = decodedVal
			self.__lastDecodedVals[self.__curCol] = storedVal #need stored value, not resignified one
			self.__curCol += 1

			## Move to next row if done
			if (self.__curCol == self.__numCols):
				self.__curCol = 0
				decodedRows.append(curRowVals)
				curRowVals = [0]*self.__numCols

		## Return decompressed data
		self.__lastDecompressed = decodedRows
		return decodedRows


## Demo
if __name__ == "__main__":

	import random

	# RDES variant
	VARIANT = 1
	# The range of demo data values
	VALUE_RANGE = 10000000
	# The number of rows to test
	ROWS = 10

	## Print conditions
	print("")
	print(f"Using RDES{VARIANT} - Compress & Decompress test.")
	print(f"Testing 2 columns, N={ROWS} rows.")
	print(f"Values have a range of {VALUE_RANGE}.")


	## Create RDES compressor/decompressor
	comp = RDESCompressor(variant=VARIANT, numCols=2, originRefreshInterval=50, verbose=False)
	deco = RDESDecompressor(variant=VARIANT, numCols=2, verbose=False, signedCols=[1])
	
	## Compress demo data
	inputData = []
	for i in range(ROWS):

		unsignedVal = int(random.random()*VALUE_RANGE)
		signedVal = int(random.random()*VALUE_RANGE//2)-VALUE_RANGE

		inputData.append( [ unsignedVal, signedVal ] )
		comp.writeCompressedRow( [ unsignedVal, comp.unsignify(signedVal) ] )

	## Decompress data
	compressedData = comp.getCompressedData()
	uncompressedData = deco.decompress(compressedData)

	## Print data
	#print("Original Data:")
	#print(inputData)
	#print("Decompressed Data:")
	#print(uncompressedData)

	## Print stats
	if (inputData == uncompressedData):
		print("Data compressed & decompressed successfully.")
	else:
		print("!! Data was NOT compressed/decompressed successfully.")	
	print(f"Compressed {comp.getUncompressedSize()}B of data into {comp.getCompressedSize()}B")
	print(f"Compression ratio = {comp.getCompressionRatio():.2f} ({1/comp.getCompressionRatio():.1%})")


	## Interactive Demo
	print("")
	print(f"Interactive demo: feed data into RDES{VARIANT} in real-time.")
	comp2 = RDESCompressor(variant=VARIANT, numCols=1, originRefreshInterval=0, verbose=True)
	deco2 = RDESDecompressor(variant=VARIANT, numCols=1, verbose=True)

	while True:
		print("")
		val = int(input("Enter unsigned integer: "))
		comp2.writeCompressedRow([val])
		compressed = comp2.getCompressedData()
		print("Compressed Bytes:")
		print(", ".join(format(b, '#010b') for b in compressed))
		decompressed = deco2.decompress(compressed)
		print("Decompressed Values:")
		print(decompressed)
		print(f"{comp2.getUncompressedSize()}B In / {comp2.getCompressedSize()}B Out -> {comp2.getCompressionRatio():.2f} compression ratio")