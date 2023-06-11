// rdes2.cpp
#include "rdes2.h"

// Constructor
RDES2Comp::RDES2Comp(uint8_t numCols, uint16_t originRefreshInt, uint8_t storage[]) {

  _numCols = numCols;
  _originRefreshInt = originRefreshInt;
  _storagePntr = storage;
  _storagePos = 0;
  _rowsSinceRaw = 0;

  _initialized = false;
  _lastValsPntr = new uint32_t[numCols];

}//RDES2Comp()

// Destructor
RDES2Comp::~RDES2Comp() {
    delete[] _lastValsPntr;
}//~RDES2Comp()

// Applies offset to make signed
// int into unsigned int
uint32_t RDES2Comp::unsignify(int32_t value) {
  // apply offset of ((2^30)-1)//2
  return (uint32_t)(value + 536870911U);
}//unsignify()

// Returns the number of compressed
// bytes in the storage array.
uint32_t RDES2Comp::getSize() {
  return _storagePos;
}//getSize()

// Writes the given byte into the
// storage array
void RDES2Comp::writeByte(uint8_t in) {
  _storagePntr[_storagePos] = in;
  _storagePos++;
}//writeByte

// Writes the given uint32_t into the
// storage array (adjusts MSB = 0)
void RDES2Comp::writeUint32(uint32_t in) {

  // Set Bit8 = 0
  uint8_t byte1 = 0b01111111 & ( in >> 24 );
  uint8_t byte2 = in >> 16;
  uint8_t byte3 = in >> 8;
  uint8_t byte4 = in;
  // Write
  writeByte(byte1);
  writeByte(byte2);
  writeByte(byte3);
  writeByte(byte4);
  
}//writeUint32()

// Compresses and saves the given row
// of data to the storage array
bool RDES2Comp::writeRow(uint32_t rowData[]) {

  // Check if should write raw values
  bool refreshOrigin = (_originRefreshInt > 0) && (_rowsSinceRaw >= _originRefreshInt);
  if (!_initialized || refreshOrigin) {
    // Pass through all columns
    for (int col=0; col<_numCols; col++) {
      _lastValsPntr[col] = rowData[col];
      writeUint32(rowData[col]);
    }//for
    // Write complete
    _rowsSinceRaw = 0;
    _initialized = true;
    return true;
  }//if

  // Iterate over all columns
  for (int col=0; col<_numCols; col++) {
    uint32_t lastVal = _lastValsPntr[col];
    uint32_t curVal = rowData[col];

    // Determine sign of offset
    bool signAdd = (curVal >= lastVal);
    // Determine magnitude of offset
    uint32_t offset = 0;
    if (signAdd) { offset = curVal-lastVal; }
    else { offset = lastVal-curVal; }

    // Determine how many bytes compression will yield
    uint8_t lvl = 4;
    if (offset <= LVL_2_MAX) { lvl=2; }
    else if (offset <= LVL_3_MAX) { lvl=3; }

    // Compress value to bytes
    switch (lvl) {
      case 2: {
        // Compress to 2 bytes
        // Bit8 = 1 (offset)
        uint8_t byte1 = 0b11100000 | (offset >> 8);  // Captures D13 to D09
        uint8_t byte2 = offset; // Captures D08 to D01
        // Bit7 = add (0 = subtract)
        if (!signAdd) {byte1 = byte1 & 0b10111111;}
        // Bit6 = size (0 = 2Byte)
        byte1 = byte1 & 0b11011111;
        // Write bytes
        writeByte(byte1);
        writeByte(byte2);
        break;
      }//case2
      
      case 3: {
        // Compress to 3 bytes
        // Bit8 = 1 (offset)
        uint8_t byte1 = 0b11100000 | (offset >> 16); // Captures D21 to D17
        uint8_t byte2 = (offset >> 8); // Captures D16 to D09
        uint8_t byte3 = offset; // Captures D08 to D01
        // Bit7 = add (0 = subtract)
        if (!signAdd) {byte1 = byte1 & 0b10111111;}
        // Bit6 = size (1 = 3Byte, already set)
        // Write bytes
        writeByte(byte1);
        writeByte(byte2);
        writeByte(byte3);
        break;
      }//case3
      
      default: {
        // Store uncompressed value
        writeUint32(rowData[col]);
        break;
      }//case4
    }//switch
    
    // Store new value for this column
    _lastValsPntr[col] = rowData[col];
  }//for
  return true;
}//writeRow()
