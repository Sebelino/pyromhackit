# findscript

Usage:

```bash
$ python3 findscript.py "PLAYER" mario.nes
{
  "start": 10,
  "end": 16,
}
```

Or:

```python
import findscript

a, b = findscript.load("mario.nes").find("PLAYER")
assert (a, b) == (10, 16)
```