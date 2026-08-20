// SPDX-License-Identifier: Apache-2.0
// Baseline-only scalar implementations of the exact ABI entry points that
// otherwise retain runtime-dispatched AVX code from the static MSVC libraries.

#include <stddef.h>
#include <stdint.h>

__declspec(noinline) void* __cdecl memcpy(
    void* destination, const void* source, size_t count) {
  unsigned char* output = (unsigned char*)destination;
  const unsigned char* input = (const unsigned char*)source;
  size_t index;
  for (index = 0; index < count; ++index) {
    output[index] = input[index];
  }
  return destination;
}

__declspec(noinline) void* __cdecl memmove(
    void* destination, const void* source, size_t count) {
  unsigned char* output = (unsigned char*)destination;
  const unsigned char* input = (const unsigned char*)source;
  size_t index;
  if ((uintptr_t)output < (uintptr_t)input) {
    for (index = 0; index < count; ++index) {
      output[index] = input[index];
    }
  } else {
    for (index = count; index != 0; --index) {
      output[index - 1] = input[index - 1];
    }
  }
  return destination;
}

__declspec(noinline) void* __cdecl memset(void* destination, int value, size_t count) {
  unsigned char* output = (unsigned char*)destination;
  size_t index;
  for (index = 0; index < count; ++index) {
    output[index] = (unsigned char)value;
  }
  return destination;
}

__declspec(noinline) const void* __stdcall __std_find_trivial_1(
    const void* first, const void* last, unsigned char value) {
  const unsigned char* current = (const unsigned char*)first;
  const unsigned char* end = (const unsigned char*)last;
  while (current != end) {
    if (*current == value) {
      return current;
    }
    ++current;
  }
  return last;
}

__declspec(noinline) const void* __stdcall __std_find_trivial_2(
    const void* first, const void* last, unsigned short value) {
  const unsigned short* current = (const unsigned short*)first;
  const unsigned short* end = (const unsigned short*)last;
  while (current != end) {
    if (*current == value) {
      return current;
    }
    ++current;
  }
  return last;
}

__declspec(noinline) void __cdecl __std_reverse_trivially_swappable_1(
    void* first, void* last) {
  unsigned char* left = (unsigned char*)first;
  unsigned char* right = (unsigned char*)last;
  while (left != right && left != --right) {
    unsigned char temporary = *left;
    *left = *right;
    *right = temporary;
    ++left;
  }
}
