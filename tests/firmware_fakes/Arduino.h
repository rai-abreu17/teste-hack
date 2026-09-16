#pragma once

#include <stddef.h>
#include <stdint.h>

unsigned long millis();
void delay(unsigned long milliseconds);

template <typename T>
T min(T left, T right) {
  return left < right ? left : right;
}
