#pragma once

#include <Wire.h>

#include "ITofSensor.h"

class SimTofSensor : public ITofSensor {
 public:
  explicit SimTofSensor(TwoWire &wire, uint8_t address = 0x42)
      : wire_(wire), address_(address), lastSequence_(0) {}

  bool begin() override;
  bool acquire(uint8_t *frame, size_t capacity, size_t &length,
               TofFrameMetadata &frameMetadata,
               const char *&reason) override;
  const TofSensorMetadata &metadata() const override;

 private:
  static const size_t HEADER_SIZE = 64;
  static const size_t MAX_FRAME = 64 + 8 * 8 * 10;

  bool readBlock(uint16_t address, uint8_t *out, size_t count);
  static uint16_t u16(const uint8_t *bytes);
  static uint32_t u32(const uint8_t *bytes);
  static uint32_t crcUpdate(uint32_t crc, const uint8_t *bytes, size_t count);

  TwoWire &wire_;
  uint8_t address_;
  uint32_t lastSequence_;
};
