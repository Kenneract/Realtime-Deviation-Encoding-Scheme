"""
Author: Kennan (Kenneract)

Date: Jun.4.2023

Description: RDES2 embedded hardware example - reads compressed
			 data from embedded hardware (Arduino) and
			 decompresses it.
"""

# NOTE: You must move the "rdes.py" file to this directory
from rdes import RDESDecompressor
from time import sleep
import serial

"""
If you are testing this for yourself, make sure
to fill out the correct COM port & baud rate.
"""
COM_PORT = "COM4"
BAUD_RATE = 115200


def cleanPrintList(inpList, cols=8):
	"""
	Cleanly prints a list to
	the console.
	"""
	curInd = 0
	itemsOnLine = 0

	print("[", end="")
	while (curInd < len(inpList)):
		if (curInd == 0):
			print(f"{inpList[curInd]}", end="")
			itemsOnLine += 1
		elif (itemsOnLine < cols):
			print(f", {inpList[curInd]}", end="")
			itemsOnLine += 1
		else:
			print("")
			print(f" {inpList[curInd]}", end="")
			itemsOnLine = 1

		curInd += 1
	print("]")



# Connect 
device = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=.5)
if (device is None):
	print("Error connecting to device")
else:
	print("Connected")

# Wait for device to stabilize
sleep(2)

# Send byte to trigger response
device.write([0xFF])
print("Sent byte...")

# Wait a moment to ensure ready
sleep(0.5)

print("Reading response...")
# Read "original data" line from device
devOrigDataRaw = device.readline().decode("utf-8")
# 		(split into chunks)
devOrigData = devOrigDataRaw.split(":")[1].strip()
devOrigData = devOrigData.split(",")[0:-1]
#		(cast to int)
devOrigData = [int(x, 10) for x in devOrigData]


# Read "compressed bytes" line from device
devCompDataRaw = device.readline().decode("utf-8")
# 		(split into chunks)
devCompBytes = devCompDataRaw.split(":")[1].strip()
devCompBytes = devCompBytes.split(",")[0:-1]
#		(cast to int from hex)
devCompBytes = [int(x, 16) for x in devCompBytes]

# Read "original size" line from device
device.readline()
# Read "compression time (us)" line from device
devCompTime = device.readline().decode("utf-8")
#	(clean up)
devCompTime = devCompTime.split(":")[1].strip()

# Read "compressize size" line from device
device.readline()
# Read "done" line from device
device.readline()


# Attempt to uncompress data
#	Variant=2, 1 column
decomp = RDESDecompressor(variant=2, numCols=1, verbose=False)
decompData = decomp.decompress(devCompBytes)
# Convert to 1D array
decompData = [x[0] for x in decompData]


print("")
print("# RESULTS #")
print("\n(Device) Original Data:")
cleanPrintList(devOrigData)
print("\n(Device) Compressed Bytes:")
cleanPrintList(devCompBytes)
print("\n(Computer) Decompressed Data:")
cleanPrintList(decompData)
print("\n")
if (devOrigData==decompData):
	print("Compress + Decompress successful :)")
else:
	print("Compress + Decompress error - corruption found :(")
print()

print(f"Compression took {devCompTime}uS on device.")
origSize = len(decompData)*4
compSize = len(devCompBytes)
print(f"Compressed {origSize}B into {compSize}B")
print(f"Compression Ratio = {origSize/compSize:.2f} ({compSize/origSize:.1%})")