// SPDX-License-Identifier: Apache-2.0

#include <stddef.h>

void* __cdecl memcpy(void* destination, const void* source, size_t count);
void* __cdecl memmove(void* destination, const void* source, size_t count);
void* __cdecl memset(void* destination, int value, size_t count);
const void* __stdcall __std_find_trivial_1(
    const void* first, const void* last, unsigned char value);
const void* __stdcall __std_find_trivial_2(
    const void* first, const void* last, unsigned short value);
void __cdecl __std_reverse_trivially_swappable_1(void* first, void* last);

static int bytes_equal(const unsigned char* actual, const unsigned char* expected, size_t count) {
  size_t index;
  for (index = 0; index < count; ++index) {
    if (actual[index] != expected[index]) {
      return 0;
    }
  }
  return 1;
}

int main(void) {
  unsigned char bytes[] = {0, 1, 2, 3, 4, 5};
  const unsigned char shifted_right[] = {0, 1, 0, 1, 2, 3};
  const unsigned char shifted_left[] = {0, 1, 2, 3, 2, 3};
  const unsigned char reversed[] = {3, 2, 1, 0};
  unsigned char copied[4] = {0, 0, 0, 0};
  unsigned char reverse_target[] = {0, 1, 2, 3};
  unsigned short words[] = {10, 20, 30, 40};

  if (memmove(bytes + 2, bytes, 4) != bytes + 2 ||
      !bytes_equal(bytes, shifted_right, sizeof(bytes))) {
    return 1;
  }
  if (memmove(bytes, bytes + 2, 4) != bytes ||
      !bytes_equal(bytes, shifted_left, sizeof(bytes))) {
    return 2;
  }
  if (memmove(bytes, bytes, 0) != bytes) {
    return 3;
  }
  if (memset(copied, 0xAB, sizeof(copied)) != copied || copied[3] != 0xAB) {
    return 4;
  }
  if (memcpy(copied, reversed, sizeof(copied)) != copied ||
      !bytes_equal(copied, reversed, sizeof(copied))) {
    return 5;
  }
  if (__std_find_trivial_1(copied, copied + 4, 2) != copied + 1 ||
      __std_find_trivial_1(copied, copied + 4, 9) != copied + 4) {
    return 6;
  }
  if (__std_find_trivial_2(words, words + 4, 30) != words + 2 ||
      __std_find_trivial_2(words, words + 4, 50) != words + 4) {
    return 7;
  }
  __std_reverse_trivially_swappable_1(reverse_target, reverse_target + 4);
  if (!bytes_equal(reverse_target, reversed, sizeof(reverse_target))) {
    return 8;
  }
  __std_reverse_trivially_swappable_1(reverse_target, reverse_target);
  return 0;
}
