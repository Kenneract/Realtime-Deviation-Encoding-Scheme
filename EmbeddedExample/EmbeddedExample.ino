/*
 * Author: Kennan (Kenneract)
 * Date: Jun.4.2023
 * Hardware: Arduino Uno (almost anything should work)
 * Purpose: RDES2 embedded hardware example - generates and
 *          compresses sensor data & sends it over Serial.
 */

#include "rdes2.h"

// 30 randomly generated values
const uint8_t NUM_POINTS = 30;
uint32_t demoData[NUM_POINTS] = {285533, 193350, 1081386, 34374, 324614,
                                389492, 905632, 443793, 788159, 1048330,
                                786238, 22080, 885333, 894020, 817373,
                                1065044, 971604, 384440, 921268, 1069838,
                                388778, 855554, 519304, 972012, 664337,
                                805038, 430018, 222068, 773489, 579342};

// Allocate 500 bytes for storage
uint8_t storage[500];

// Create compressor object
// (1 column, no refresh period)
RDES2Comp comp = RDES2Comp(1, 0, storage);

void setup() {
  // Wait for serial
  Serial.begin(115200);
  // Wait for a byte before starting
  while (!Serial.available()) {}

  // Print original data
  Serial.print(F("Orignial Data: "));
  for (uint32_t i=0; i<NUM_POINTS; i++) {
    Serial.print(demoData[i]);
    Serial.print(F(", "));
  }//for

  // Compress data
  uint32_t compStart = micros();
  for (uint32_t i=0; i<NUM_POINTS; i++) {
    uint32_t vals[] = {demoData[i]};
    comp.writeRow( vals );
  }//for
  uint32_t compEnd = micros();

  Serial.println(F(""));

  // Print compressed data
  Serial.print(F("Compressed Data: "));
  for (int i=0; i<comp.getSize(); i++) {
    Serial.print(F("0x"));
    Serial.print(storage[i], HEX);
    Serial.print(F(", "));
  }//for

  Serial.println(F(""));

  // Print stats
  uint16_t origSize = sizeof(demoData);
  uint16_t compSize = comp.getSize();
  uint16_t compTime = compEnd - compStart;
  
  Serial.print(F("Orig Size: "));
  Serial.println(origSize);
  Serial.print(F("Comp Time: "));
  Serial.println(compTime);
  Serial.print(F("Comp Size: "));
  Serial.println(compSize);

  Serial.println(F("Done"));

}//setup()

void loop() {}
