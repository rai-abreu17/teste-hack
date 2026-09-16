#include "SimTofSensor.h"

#include <string.h>

namespace {
const TofSensorMetadata SENSOR_METADATA = {
    "ToF Mock, perfil VL53L5CX 8x8, I2C PROPRIO 0x42",
    "simulation",
    "bench-vl53-30cm-v3",
    "simulation_monotonic",
};
}

uint16_t SimTofSensor::u16(const uint8_t *bytes) {
  return bytes[0] | ((uint16_t)bytes[1] << 8);
}

uint32_t SimTofSensor::u32(const uint8_t *bytes) {
  return bytes[0] | ((uint32_t)bytes[1] << 8) |
         ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

uint32_t SimTofSensor::crcUpdate(uint32_t crc, const uint8_t *bytes,
                                 size_t count) {
  while (count--) {
    crc ^= *bytes++;
    for (int bit = 0; bit < 8; bit++) {
      crc = (crc >> 1) ^ (0xedb88320u & -(int32_t)(crc & 1));
    }
  }
  return crc;
}

bool SimTofSensor::begin() {
  wire_.begin(21, 22);
  wire_.setClock(400000);
  wire_.setTimeOut(100);
  return true;
}

// Independent bounded transactions: two address bytes, then at most 28 bytes.
bool SimTofSensor::readBlock(uint16_t address, uint8_t *out, size_t count) {
  while (count) {
    size_t blockSize = min(count, (size_t)28);
    wire_.beginTransmission(address_);
    wire_.write(address >> 8);
    wire_.write(address & 255);
    if (wire_.endTransmission(false) != 0) return false;
    if (wire_.requestFrom(address_, (uint8_t)blockSize, (uint8_t)true) !=
        blockSize) {
      while (wire_.available()) wire_.read();
      return false;
    }
    for (size_t index = 0; index < blockSize; index++) {
      out[index] = (uint8_t)wire_.read();
    }
    address += blockSize;
    out += blockSize;
    count -= blockSize;
    delay(0);
  }
  return true;
}

// The sensor simulator acquires a frozen geometric scene for each command.
bool SimTofSensor::acquire(uint8_t *frame, size_t capacity, size_t &length,
                           TofFrameMetadata &frameMetadata,
                           const char *&reason) {
  length = 0;
  reason = "i2c_nack";
  if (capacity < MAX_FRAME) {
    reason = "frame_buffer_too_small";
    return false;
  }

  wire_.beginTransmission(address_);
  wire_.write(0xff);
  wire_.write(0xff);
  wire_.write(0xa1);
  if (wire_.endTransmission() != 0) return false;

  unsigned long start = millis();
  bool ready = false;
  while (millis() - start < 2500) {
    delay(20);
    if (!readBlock(0, frame, HEADER_SIZE)) return false;
    if (!memcmp(frame, "BFLD", 4) && frame[4] == 2 && frame[5] == 1 &&
        u32(frame + 8) != lastSequence_) {
      ready = true;
      break;
    }
  }
  if (!ready) {
    reason = "scan_timeout_or_frozen";
    return false;
  }

  uint16_t columns = u16(frame + 24);
  uint16_t rows = u16(frame + 26);
  uint16_t payloadBytes = u16(frame + 58);
  length = HEADER_SIZE + payloadBytes;
  if (u16(frame + 6) != 64 || u16(frame + 28) != 10 ||
      u16(frame + 30) != 3 || columns != 8 || rows != 8 ||
      (uint32_t)columns * rows * 10 != payloadBytes ||
      length > capacity || length > MAX_FRAME) {
    length = 0;
    reason = "invalid_header";
    return false;
  }
  if (!readBlock(HEADER_SIZE, frame + HEADER_SIZE, payloadBytes)) {
    length = 0;
    reason = "incomplete_i2c_read";
    return false;
  }

  uint8_t finalHeader[HEADER_SIZE];
  if (!readBlock(0, finalHeader, HEADER_SIZE) ||
      memcmp(finalHeader, frame, HEADER_SIZE)) {
    length = 0;
    reason = "mixed_frames";
    return false;
  }

  uint32_t crc = crcUpdate(0xffffffffu, frame, 60);
  crc = crcUpdate(crc, frame + HEADER_SIZE, payloadBytes) ^ 0xffffffffu;
  if (crc != u32(frame + 60)) {
    length = 0;
    reason = "crc_mismatch";
    return false;
  }

  lastSequence_ = u32(frame + 8);
  frameMetadata.sequence = lastSequence_;
  frameMetadata.columns = columns;
  frameMetadata.rows = rows;
  frameMetadata.payloadBytes = payloadBytes;
  frameMetadata.frameBytes = length;
  reason = nullptr;
  return true;
}

const TofSensorMetadata &SimTofSensor::metadata() const {
  return SENSOR_METADATA;
}
