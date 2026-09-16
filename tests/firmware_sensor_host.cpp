#include <assert.h>
#include <stdint.h>
#include <string.h>

#include <algorithm>
#include <iostream>
#include <vector>

#include "SimTofSensor.h"

static unsigned long fakeMillis = 0;

unsigned long millis() { return fakeMillis; }
void delay(unsigned long milliseconds) { fakeMillis += milliseconds; }

void TwoWire::begin(int sda, int scl) {
  beginSda = sda;
  beginScl = scl;
}
void TwoWire::setClock(uint32_t frequency) { clock = frequency; }
void TwoWire::setTimeOut(uint16_t value) { timeout = value; }
void TwoWire::beginTransmission(uint8_t) { writeBuffer.clear(); }
size_t TwoWire::write(uint8_t byte) {
  writeBuffer.push_back(byte);
  return 1;
}
uint8_t TwoWire::endTransmission(bool) {
  if (nack) return 1;
  if (writeBuffer.size() == 2) {
    pointer = ((uint16_t)writeBuffer[0] << 8) | writeBuffer[1];
  }
  return 0;
}
size_t TwoWire::requestFrom(uint8_t, uint8_t count, uint8_t) {
  maxRequest = std::max(maxRequest, (size_t)count);
  readBuffer.clear();
  readIndex = 0;
  if (nack || pointer + count > deviceMemory.size()) return 0;
  readBuffer.insert(readBuffer.end(), deviceMemory.begin() + pointer,
                    deviceMemory.begin() + pointer + count);
  pointer += count;
  return count;
}
int TwoWire::available() { return (int)(readBuffer.size() - readIndex); }
int TwoWire::read() {
  return readIndex < readBuffer.size() ? readBuffer[readIndex++] : -1;
}

static void put16(std::vector<uint8_t> &data, size_t offset, uint16_t value) {
  data[offset] = value & 255;
  data[offset + 1] = value >> 8;
}

static void put32(std::vector<uint8_t> &data, size_t offset, uint32_t value) {
  for (int index = 0; index < 4; index++) {
    data[offset + index] = (value >> (8 * index)) & 255;
  }
}

static uint32_t crcUpdate(uint32_t crc, const uint8_t *bytes, size_t count) {
  while (count--) {
    crc ^= *bytes++;
    for (int bit = 0; bit < 8; bit++) {
      crc = (crc >> 1) ^ (0xedb88320u & -(int32_t)(crc & 1));
    }
  }
  return crc;
}

static std::vector<uint8_t> frame(uint32_t sequence) {
  std::vector<uint8_t> data(704, 0);
  memcpy(data.data(), "BFLD", 4);
  data[4] = 2;
  data[5] = 1;
  put16(data, 6, 64);
  put32(data, 8, sequence);
  put16(data, 24, 8);
  put16(data, 26, 8);
  put16(data, 28, 10);
  put16(data, 30, 3);
  put16(data, 58, 640);
  for (size_t index = 64; index < data.size(); index++) {
    data[index] = (uint8_t)(index * 17);
  }
  uint32_t crc = crcUpdate(0xffffffffu, data.data(), 60);
  crc = crcUpdate(crc, data.data() + 64, 640) ^ 0xffffffffu;
  put32(data, 60, crc);
  return data;
}

int main() {
  TwoWire wire;
  wire.deviceMemory = frame(7);
  SimTofSensor sensor(wire);
  assert(sensor.begin());
  assert(wire.beginSda == 21 && wire.beginScl == 22);
  assert(wire.clock == 400000 && wire.timeout == 100);

  uint8_t output[704] = {};
  size_t length = 0;
  TofFrameMetadata metadata = {};
  const char *reason = nullptr;
  assert(sensor.acquire(output, sizeof(output), length, metadata, reason));
  assert(reason == nullptr);
  assert(length == 704 && metadata.frameBytes == 704);
  assert(metadata.sequence == 7 && metadata.columns == 8 && metadata.rows == 8);
  assert(metadata.payloadBytes == 640);
  assert(memcmp(output, wire.deviceMemory.data(), length) == 0);
  assert(wire.maxRequest == 28);
  assert(strcmp(sensor.metadata().source, "simulation") == 0);

  reason = nullptr;
  assert(!sensor.acquire(output, 703, length, metadata, reason));
  assert(strcmp(reason, "frame_buffer_too_small") == 0 && length == 0);

  wire.deviceMemory = frame(8);
  wire.deviceMemory[100] ^= 1;
  reason = nullptr;
  assert(!sensor.acquire(output, sizeof(output), length, metadata, reason));
  assert(strcmp(reason, "crc_mismatch") == 0 && length == 0);

  wire.nack = true;
  reason = nullptr;
  assert(!sensor.acquire(output, sizeof(output), length, metadata, reason));
  assert(strcmp(reason, "i2c_nack") == 0 && length == 0);

  std::cout << "SimTofSensor host checks passed" << std::endl;
  return 0;
}
