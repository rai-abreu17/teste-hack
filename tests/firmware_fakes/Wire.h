#pragma once

#include <stddef.h>
#include <stdint.h>

#include <vector>

class TwoWire {
 public:
  void begin(int sda, int scl);
  void setClock(uint32_t frequency);
  void setTimeOut(uint16_t timeout);
  void beginTransmission(uint8_t address);
  size_t write(uint8_t byte);
  uint8_t endTransmission(bool stop = true);
  size_t requestFrom(uint8_t address, uint8_t count, uint8_t stop);
  int available();
  int read();

  std::vector<uint8_t> deviceMemory;
  std::vector<uint8_t> writeBuffer;
  std::vector<uint8_t> readBuffer;
  size_t readIndex = 0;
  uint16_t pointer = 0;
  bool nack = false;
  size_t maxRequest = 0;
  int beginSda = -1;
  int beginScl = -1;
  uint32_t clock = 0;
  uint16_t timeout = 0;
};
