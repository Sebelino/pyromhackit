# findscript

Usage:

```bash
$ python3 findscript.py "PLAYER" mario.nes
{
  "start": 40904,
  "end": 40910,
  "offset": 201
}
```

Or:

```python
from findscript import findscript

result = findscript.load("mario.nes").find("PLAYER")
assert result.start == 40904
assert result.end == 40910
assert result.offset == 55
```