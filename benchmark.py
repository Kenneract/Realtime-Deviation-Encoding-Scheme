"""
Author: Kennan (Kenneract)

Date: Jun.3.2023

Description: A rudimentary RDES demo implementation
			 benchmarking program.
"""

from rdes import RDESCompressor, RDESDecompressor
import random
import time


def ratioBenchmarkLinear():
	"""
	Benchmarks compression ratio.

	Tests by feeding data which changes by
	various constant amounts. Linear.
	"""
	## Configuration
	ROWS = 10000
	INCREMENTS = [2**x for x in range(4, 25)]
	## Print header

	print(f"\tCOMPRESSION RATIO TEST: LINEAR ({ROWS} rows)")
	print("Increment\tRDES1\tRDES2\tRDES3")

	## Create RDES classes
	comp1 = RDESCompressor(variant=1, numCols=1)
	comp2 = RDESCompressor(variant=2, numCols=1)
	comp3 = RDESCompressor(variant=3, numCols=1)
	## Run tests for each increment bracket
	for incr in INCREMENTS:
		## Initialize all
		comp1.reset()
		comp2.reset()
		comp3.reset()
		## Fill with data (increase then decrease)
		for i in range(ROWS//2):
			## Increase
			comp1.writeCompressedRow([incr])
			comp2.writeCompressedRow([incr])
			comp3.writeCompressedRow([incr])
			## Decrease
			comp1.writeCompressedRow([0])
			comp2.writeCompressedRow([0])
			comp3.writeCompressedRow([0])
		## Print results
		tabs = "\t\t" if len(str(incr))< 8 else "\t"
		print(f"{incr}{tabs}{comp1.getCompressionRatio():.3f}\t{comp2.getCompressionRatio():.3f}\t{comp3.getCompressionRatio():.3f}")

def ratioBenchmarkRandom():
	"""
	Benchmarks compression ratio.

	Tests by feeding data which changes at
	random, by at most various constants.
	Random.
	"""
	## Configuration
	ROWS = 10000
	MAX_VARS = INCREMENTS = [2**x for x in range(4, 25)]

	## Print header

	print(f"\tCOMPRESSION RATIO TEST: RANDOM ({ROWS} rows)")
	print("Max Increment\tRDES1\tRDES2\tRDES3")

	## Create RDES classes
	comp1 = RDESCompressor(variant=1, numCols=1)
	comp2 = RDESCompressor(variant=2, numCols=1)
	comp3 = RDESCompressor(variant=3, numCols=1)
	## Run tests for each max variation bracket
	for maxVar in MAX_VARS:
		## Initialize all
		comp1.reset()
		comp2.reset()
		comp3.reset()
		## Fill with data (increase then decrease)
		for i in range(ROWS):
			val = int(random.random()*maxVar)
			comp1.writeCompressedRow([val])
			comp2.writeCompressedRow([val])
			comp3.writeCompressedRow([val])

		## Print results
		tabs = "\t\t" if len(str(maxVar))< 8 else "\t"
		print(f"{maxVar}{tabs}{comp1.getCompressionRatio():.3f}\t{comp2.getCompressionRatio():.3f}\t{comp3.getCompressionRatio():.3f}")


def compressionBenchmarkLinear():
	"""
	Tests the compression and decompression time efficiency
	for all RDES variants. Does so with regularly changing
	data. Linear.

	Decompression values may be flawed as each RDES variant
	techincally has a different amount of input data (due to
	varying compression ratios)
	"""
	## Configuration
	ROWS = 500000
	INCREMENTS = [10**x for x in range(1, 9)]
	## Print header
	print(f"\tCOMPRESSION TIME TEST: LINEAR ({ROWS} rows)")
	print("Increment\tRDES1\t\tRDES2\t\tRDES3")

	## Create RDES classes
	comp1 = RDESCompressor(variant=1, numCols=1)
	comp2 = RDESCompressor(variant=2, numCols=1)
	comp3 = RDESCompressor(variant=3, numCols=1)
	deco1 = RDESDecompressor(variant=1, numCols=1)
	deco2 = RDESDecompressor(variant=2, numCols=1)
	deco3 = RDESDecompressor(variant=3, numCols=1)
	
	## Run tests for each increment bracket
	for incr in INCREMENTS:
		## Initialize all
		comp1.reset()
		comp2.reset()
		comp3.reset()
		## Fill with data (increase then decrease)
		rdes1CompStart = time.time()
		for i in range(ROWS//2):
			comp1.writeCompressedRow([incr])
			comp1.writeCompressedRow([0])
		rdes2CompStart = time.time()
		for i in range(ROWS//2):
			comp2.writeCompressedRow([incr])
			comp2.writeCompressedRow([0])
		rdes3CompStart = time.time()
		for i in range(ROWS//2):
			comp3.writeCompressedRow([incr])
			comp3.writeCompressedRow([0])
		rdes1DecompStart = time.time()
		deco1.decompress(comp1.getCompressedData())
		rdes2DecompStart = time.time()
		deco2.decompress(comp2.getCompressedData())
		rdes3DecompStart = time.time()
		deco3.decompress(comp3.getCompressedData())
		decompTestEnd = time.time()

		## Calculate times
		rdes1CompTime = (rdes2CompStart - rdes1CompStart) * 1000
		rdes2CompTime = (rdes3CompStart - rdes2CompStart) * 1000
		rdes3CompTime = (rdes1DecompStart - rdes3CompStart) * 1000

		rdes1DecompTime = (rdes2DecompStart - rdes1DecompStart) * 1000
		rdes2DecompTime = (rdes3DecompStart - rdes2DecompStart) * 1000
		rdes3DecompTime = (decompTestEnd - rdes3DecompStart) * 1000

		## Print results
		tabs = "\t\t" if len(str(incr))< 8 else "\t"
		print(f"{incr}{tabs}{rdes1CompTime:.0f}ms,{rdes1DecompTime:.0f}ms\t{rdes2CompTime:.0f}ms,{rdes2DecompTime:.0f}ms\t{rdes3CompTime:.0f}ms,{rdes3DecompTime:.0f}ms")


def compressionBenchmarkRandom():
	"""
	Tests the compression and decompression time efficiency
	for all RDES variants. Does so with randomly changing
	data. Random.

	Decompression values may be flawed as each RDES variant
	techincally has a different amount of input data (due to
	varying compression ratios)
	"""
	## Configuration
	ROWS = 500000
	MAX_VARS = [10**x for x in range(1, 9)]
	## Print header
	print(f"\tCOMPRESSION TIME TEST: RANDOM ({ROWS} rows)")
	print("Max Increment\tRDES1\t\tRDES2\t\tRDES3")

	## Create RDES classes
	comp1 = RDESCompressor(variant=1, numCols=1)
	comp2 = RDESCompressor(variant=2, numCols=1)
	comp3 = RDESCompressor(variant=3, numCols=1)
	deco1 = RDESDecompressor(variant=1, numCols=1)
	deco2 = RDESDecompressor(variant=2, numCols=1)
	deco3 = RDESDecompressor(variant=3, numCols=1)
	
	## Run tests for each increment bracket
	for maxVar in MAX_VARS:
		## Initialize all
		comp1.reset()
		comp2.reset()
		comp3.reset()
		## Generate data
		data = list([int(random.random()*maxVar) for i in range(ROWS)])

		## Fill with data
		rdes1CompStart = time.time()
		for val in data:
			comp1.writeCompressedRow([val])
		rdes2CompStart = time.time()
		for val in data:
			comp2.writeCompressedRow([val])
		rdes3CompStart = time.time()
		for val in data:
			comp3.writeCompressedRow([val])
		rdes1DecompStart = time.time()
		deco1.decompress(comp1.getCompressedData())
		rdes2DecompStart = time.time()
		deco2.decompress(comp2.getCompressedData())
		rdes3DecompStart = time.time()
		deco3.decompress(comp3.getCompressedData())
		decompTestEnd = time.time()

		## Calculate times
		rdes1CompTime = (rdes2CompStart - rdes1CompStart) * 1000
		rdes2CompTime = (rdes3CompStart - rdes2CompStart) * 1000
		rdes3CompTime = (rdes1DecompStart - rdes3CompStart) * 1000

		rdes1DecompTime = (rdes2DecompStart - rdes1DecompStart) * 1000
		rdes2DecompTime = (rdes3DecompStart - rdes2DecompStart) * 1000
		rdes3DecompTime = (decompTestEnd - rdes3DecompStart) * 1000

		## Print results
		tabs = "\t\t" if len(str(maxVar))< 8 else "\t"
		print(f"{maxVar}{tabs}{rdes1CompTime:.0f}ms,{rdes1DecompTime:.0f}ms\t{rdes2CompTime:.0f}ms,{rdes2DecompTime:.0f}ms\t{rdes3CompTime:.0f}ms,{rdes3DecompTime:.0f}ms")



ratioBenchmarkLinear()
print("\n")
ratioBenchmarkRandom()
print("\n")
compressionBenchmarkLinear()
print("\n")
compressionBenchmarkRandom()