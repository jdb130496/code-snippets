# hwrng

Direct RDSEED hardware RNG for x86_64.

Bypasses the OS entropy pool entirely and reads raw thermal-noise entropy
straight from the CPU via the `RDSEED` instruction — no CSPRNG, no
conditioning, no OS-level mixing. Intended for callers who specifically
want hardware-sourced entropy rather than a general-purpose random
number generator.

## Requirements

- Python 3.14+
- x86_64 CPU with RDSEED support (Intel Broadwell 2014+, AMD Zen+)
- 64-bit only — 32-bit builds are rejected at compile time

## Install

```bash
pip install hwrng
```

Building from source on Windows, Linux, macOS, or MSYS2 — see
[BUILDING.md](BUILDING.md) for full platform-specific instructions,
including the MSYS2/UCRT64 setup.

## Usage

```python
import hwrng

if hwrng.has_rdseed():
    data = hwrng.rdseed_raw_bytes(32)   # 32 bytes of raw hardware entropy
    print(data.hex())
```

## API

### `has_rdseed() -> bool`

Returns `True` if the current CPU supports the `RDSEED` instruction.
Call this before `rdseed_raw_bytes()` on unknown hardware.

### `rdseed_raw_bytes(n_bytes, max_retries=100) -> bytes`

Generates `n_bytes` of raw hardware entropy.

- `n_bytes` — positive multiple of 8, maximum 1 MB
- `max_retries` — per-word retry limit (Intel recommends ≥ 10)
- Output is native little-endian byte order

Raises `RuntimeError` if the CPU lacks RDSEED support, or if entropy is
exhausted after `max_retries` attempts per word.

## A Note on AMD Zen 5

Zen 5 CPUs have a known issue where `RDSEED` can report success with a
returned value of `0` when the entropy pool is exhausted. This library
mitigates the issue by treating a zero result as a failed attempt and
retrying — a genuine all-zero 64-bit value has probability `1 / 2^64`,
so this does not meaningfully bias output. A `UserWarning` is raised at
import time on affected hardware; updating CPU microcode (Oct 2025 fix)
resolves the underlying issue.

## Why Not Just Use `os.urandom()`?

`os.urandom()` is almost always the right choice for application-level
randomness — it goes through the OS CSPRNG, which is well-tested,
properly mixed, and fast. `hwrng` exists for the narrower case where you
specifically need unconditioned hardware entropy itself, rather than a
general-purpose secure random source.

## License

See [LICENSE](LICENSE).
