#!/usr/bin/env python

transliter = dict()
for i in range(2**8):
    for j in range(2**8):
        transliter[bytes([i, j])] = "."

for i in range(2**8):
    for j in range(ord('z')-ord('a')+1):
        transliter[bytes([i, j+0x01])] = chr(ord('a')+j)

for i in range(2**8):
    for j in range(ord('z')-ord('a')+1):
        transliter[bytes([i, j+0xe0])] = chr(ord('A')+j)

for i in range(2**8):
    transliter[bytes([i, 0])] = " "
