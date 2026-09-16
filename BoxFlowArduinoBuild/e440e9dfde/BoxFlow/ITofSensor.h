#pragma once

#include <Arduino.h>

struct TofSensorMetadata {
  const char *name;
  const char *source;
  const char *geometryId;
  const char *acquisitionClock;
};

struct TofFrameMetadata {
  uint32_t sequence;
  uint16_t columns;
  uint16_t rows;
  uint16_t payloadBytes;
  size_t frameBytes;
};

// Sensor drivers return the original binary scan. Volume reconstruction remains
// on the receiver, so switching drivers cannot silently change that algorithm.
class ITofSensor {
 public:
  virtual ~ITofSensor() {}
  virtual bool begin() = 0;
  virtual bool acquire(uint8_t *frame, size_t capacity, size_t &length,
                       TofFrameMetadata &frameMetadata,
                       const char *&reason) = 0;
  virtual const TofSensorMetadata &metadata() const = 0;
};
