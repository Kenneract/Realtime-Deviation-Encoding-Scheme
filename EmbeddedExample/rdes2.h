// rdes2.h
#ifndef rdes2_h
#define rdes2_h
#include <Arduino.h>

class RDES2Comp {
  public:
    RDES2Comp(uint8_t numCols, uint16_t originRefreshInt, uint8_t storage[]);
    ~RDES2Comp(); // Destructor
    bool writeRow(uint32_t rowData[]);
    uint32_t unsignify(int32_t value);
    uint32_t getSize();
    
  private:
    const uint16_t LVL_2_MAX = 8191;    //2^13-1
    const uint32_t LVL_3_MAX = 2097151; //2^21-1

    void writeByte(uint8_t in);
    void writeUint32(uint32_t in);
    
    uint8_t _numCols;
    uint16_t _originRefreshInt;
    uint16_t _rowsSinceRaw;
    bool _initialized;
    uint32_t _storagePos;
    uint32_t *_lastValsPntr;
    uint8_t *_storagePntr;
};

#endif
