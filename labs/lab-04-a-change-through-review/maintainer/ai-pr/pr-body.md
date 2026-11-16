## Summary

This PR claims slot `uio[7]` for a **heartbeat** block: a slow square wave that toggles every
256 clock cycles, so you can see on a scope or an LED that the design is alive.

## Changes

- `src/slot_uio7.v`: an 8-bit counter that flips `beat` each time it wraps, driven out on `uio_out[7]`.
- `test/test_uio7.py`: a cocotb test that checks the reset value and the heartbeat over 512 cycles.
- `info.yaml`: names `uio[7]` as the heartbeat output.
- `docs/info.md`: fills in the `uio[7]` row.

## Testing

All 16 tests pass locally with Icarus Verilog and cocotb 2.0.1.

## Notes

The heartbeat period is fixed at 512 cycles (51.2 µs at the sandbox's 10 MHz clock), which is
too fast to see on an LED; a follow-up could add a prescaler.

Generated with an AI coding tool, for IC102-D Lab 04 (Part 5). It contains problems on purpose.
