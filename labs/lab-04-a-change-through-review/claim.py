#!/usr/bin/env python3
"""Lab 04: put a ready-made block into one slot of your clone of the cohort sandbox.

    python3 claim.py --list
    python3 claim.py BLOCK PIN [REPO_DIR] [--by YOUR_GITHUB_USERNAME]

PIN is uo0 to uo7 or uio0 to uio7 (uo[3] works too). It writes two files and nothing else:
src/slot_<pin>.v with the block, and test/test_<pin>.py with a starter test. The starter test
checks only two input values, on purpose: deciding what else it should check is part of the
review. You edit info.yaml and docs/info.md yourself (Part 2).

You can also write a block of your own instead: copy the shape of src/slot_<pin>.v, keep the
port list, and drive `out` (and, for a uio pin, `oe`) from `in`, `clk` and `rst_n`.
"""
import os
import re
import subprocess
import sys

# name: (what it does, Verilog body, signals it leaves unused, test cases or None, test body)
# A combinational block's test checks two (ui_in, expected) pairs. A clocked block's test is
# written out in full.
BLOCKS = {
    "parity": ("1 when an odd number of the eight ui_in pins are 1",
               "  assign out = ^in;", "clk, rst_n", [(0x00, 0), (0x01, 1)], None),
    "majority": ("1 when at least two of ui_in[2:0] are 1",
                 "  assign out = (in[0] & in[1]) | (in[1] & in[2]) | (in[0] & in[2]);",
                 "clk, rst_n, in[7:3]", [(0b000, 0), (0b011, 1)], None),
    "over-100": ("1 when ui_in, read as a number from 0 to 255, is more than 100",
                 "  assign out = (in > 8'd100);", "clk, rst_n", [(0, 0), (200, 1)], None),
    "all-ones": ("1 when all eight ui_in pins are 1",
                 "  assign out = &in;", "clk, rst_n", [(0x00, 0), (0xFF, 1)], None),
    "nibbles-equal": ("1 when ui_in[7:4] equals ui_in[3:0]",
                      "  assign out = (in[7:4] == in[3:0]);", "clk, rst_n",
                      [(0x00, 1), (0x12, 0)], None),
    "one-hot": ("1 when exactly one ui_in pin is 1",
                "  assign out = (in != 8'd0) && ((in & (in - 8'd1)) == 8'd0);", "clk, rst_n",
                [(0x01, 1), (0x03, 0)], None),
    "blink": ("toggles every 128 clock cycles, while ui_in[0] is 1",
              """  reg [6:0] count;
  reg       state;

  always @(posedge clk) begin
    if (!rst_n) begin
      count <= 7'd0;
      state <= 1'b0;
    end else if (in[0]) begin
      count <= count + 7'd1;
      if (count == 7'd127)
        state <= ~state;
    end
  end

  assign out = state;""", "in[7:1]", None,
              """    await start(dut)
    assert pin(dut, "{pin}") == 0, "{pin} should be 0 after reset"
    dut.ui_in.value = 0x01
    await settle(dut, 128)
    assert pin(dut, "{pin}") == 1, f"after 128 cycles with ui_in[0] = 1, {pin} is {{pin(dut, '{pin}')}}, expected 1\""""),
    "toggle": ("changes state each time ui_in[0] goes from 0 to 1",
               """  reg last;
  reg state;

  always @(posedge clk) begin
    if (!rst_n) begin
      last  <= 1'b0;
      state <= 1'b0;
    end else begin
      last <= in[0];
      if (in[0] && !last)
        state <= ~state;
    end
  end

  assign out = state;""", "in[7:1]", None,
               """    await start(dut)
    assert pin(dut, "{pin}") == 0, "{pin} should be 0 after reset"
    dut.ui_in.value = 0x01
    await settle(dut, 2)
    assert pin(dut, "{pin}") == 1, f"after one rising edge on ui_in[0], {pin} is {{pin(dut, '{pin}')}}, expected 1\""""),
}

HEADER = """/*
 * Copyright (c) 2026 UofT ASIC Team
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
"""


def die(msg):
    print(f"claim.py: {msg}", file=sys.stderr)
    sys.exit(2)


def slot_v(slot, block, by):
    what, body, unused, _, _ = BLOCKS[block]
    p = f"{slot[:-1]}[{slot[-1]}]"
    uio = slot.startswith("uio")
    ports = ["    input  wire       clk,", "    input  wire       rst_n,",
             "    input  wire [7:0] in,     // ui_in, shared by every slot"]
    if uio:
        ports += [f"    output wire       out,    // drives uio_out[{slot[-1]}]",
                  f"    output wire       oe      // uio_oe[{slot[-1]}]: 1 makes the pin an output"]
    else:
        ports += [f"    output wire       out     // drives {p}"]
    lines = [HEADER, f"// Slot {p}: {block}, claimed by {by}.", f"// {what[0].upper() + what[1:]}.",
             f"module slot_{slot} (", *ports, ");", "", body]
    if uio:
        lines += ["  assign oe  = 1'b1;   // this block drives the pin, so it's an output"]
    lines += ["", f"  wire _unused = &{{{unused}, 1'b0}};", "", "endmodule", ""]
    return "\n".join(lines)


def test_py(slot, block, by):
    what, _, _, cases, body = BLOCKS[block]
    p = f"{slot[:-1]}[{slot[-1]}]"
    uio = slot.startswith("uio")
    imports = "is_output, pin, settle, start" if uio else "pin, settle, start"
    t = [f"# Slot {p}: {block}, claimed by {by}.", f"# The block: {what}.", "",
         "import cocotb", f"from sandbox import {imports}", "", "",
         "@cocotb.test()", f"async def test_{slot}_{block.replace('-', '_')}(dut):"]
    if cases:
        pairs = ", ".join(f"({v:#04x}, {e})" for v, e in cases)
        t += ["    await start(dut)",
              f"    for value, expected in [{pairs}]:",
              "        dut.ui_in.value = value", "        await settle(dut)",
              f'        got = pin(dut, "{p}")',
              f'        assert got == expected, f"{block}: ui_in = {{value:#04x}} gives {p} = {{got}}, expected {{expected}}"']
    else:
        t += body.format(pin=p).splitlines()
    if uio:
        t.append(f'    assert is_output(dut, "{p}"), "{p} should be an output (uio_oe[{slot[-1]}] = 1)"')
    return "\n".join(t) + "\n"


def main(argv):
    by = None
    if "--by" in argv:
        i = argv.index("--by")
        by = argv[i + 1] if i + 1 < len(argv) else die("--by needs your GitHub username")
        argv = argv[:i] + argv[i + 2:]
    if argv[:1] == ["--list"]:
        for name, (what, *_rest) in BLOCKS.items():
            print(f"{name:<14} {what}")
        return
    if len(argv) not in (2, 3):
        die("usage: python3 claim.py BLOCK PIN [REPO_DIR] [--by YOUR_GITHUB_USERNAME]")
    block, raw = argv[0], argv[1]
    if block not in BLOCKS:
        die(f"no block called {block}; python3 claim.py --list shows them")
    m = re.fullmatch(r"(uio|uo)\[?([0-7])\]?", raw)
    if not m:
        die(f"PIN is uo0 to uo7 or uio0 to uio7, not {raw}")
    slot = m.group(1) + m.group(2)
    repo = subprocess.run(["git", "-C", argv[2] if len(argv) == 3 else ".", "rev-parse",
                           "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    src = os.path.join(repo, "src", f"slot_{slot}.v")
    if not repo or not os.path.exists(src):
        die("run this in your clone of the cohort sandbox, or give its folder")
    if not any(l.startswith("// Slot") and "unclaimed" in l for l in open(src).read().splitlines()[:12]):
        die(f"src/slot_{slot}.v isn't unclaimed in your branch; pick another pin")
    if by is None:
        url = subprocess.run(["git", "-C", repo, "config", "user.name"], capture_output=True,
                             text=True).stdout.strip()
        by = url or "a student"
    open(src, "w").write(slot_v(slot, block, by))
    open(os.path.join(repo, "test", f"test_{slot}.py"), "w").write(test_py(slot, block, by))
    p = f"{slot[:-1]}[{slot[-1]}]"
    print(f"Wrote src/slot_{slot}.v and test/test_{slot}.py ({block} on {p}).")
    print(f"Now edit by hand: the line `{p}: \"\"` in info.yaml, and the `{p}` row of the table in "
          "docs/info.md.")


if __name__ == "__main__":
    main(sys.argv[1:])
