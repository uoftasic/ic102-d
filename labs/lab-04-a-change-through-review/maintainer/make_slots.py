#!/usr/bin/env python3
"""Write the sandbox's sixteen unclaimed slots, the top module that wires them to the pins, the
test Makefile and the slot tests.

    python3 make_slots.py [SANDBOX_DIR]

Run it only to regenerate ../sandbox/ from scratch (for example after changing the slot
interface). It overwrites src/project.v, src/slot_*.v, test/Makefile, test/sandbox.py and
test/test_*.py. info.yaml, docs/info.md and the rest are written by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "sandbox")
TOP = "tt_um_uoftasic_ic102_sandbox"
SLOTS = [f"uo{i}" for i in range(8)] + [f"uio{i}" for i in range(8)]

HEADER = """/*
 * Copyright (c) 2026 UofT ASIC Team
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
"""


def pin(slot):
    return f"{slot[:-1]}[{slot[-1]}]"


def slot_v(slot):
    uio = slot.startswith("uio")
    ports = ["    input  wire       clk,", "    input  wire       rst_n,",
             "    input  wire [7:0] in,     // ui_in, shared by every slot",
             "    output wire       out" + ("," if uio else "     // drives " + pin(slot))]
    if uio:
        ports[-1] += "     // drives uio_out" + slot[-1:].join("[]")
        ports.append("    output wire       oe       // uio_oe" + slot[-1:].join("[]") +
                     ": 1 makes the pin an output, 0 an input")
    body = ["  // Unclaimed: drive 0" + (" and leave the pin an input." if uio else "."),
            "  assign out = 1'b0;"]
    if uio:
        body.append("  assign oe  = 1'b0;")
    body += ["", "  wire _unused = &{clk, rst_n, in, 1'b0};"]
    return (HEADER + f"\n// Slot {pin(slot)}: unclaimed. CONTRIBUTING.md says how to claim it.\n"
            f"module slot_{slot} (\n" + "\n".join(ports) + "\n);\n\n" + "\n".join(body) +
            "\n\nendmodule\n")


def project_v():
    lines = [HEADER, "// The IC102-D cohort sandbox. Each output pin, uo[0] to uo[7] and uio[0] to uio[7],",
             "// is driven by its own slot module in src/slot_<pin>.v, and every slot can read all",
             "// eight ui_in pins. The slots are claimed one pull request at a time; see CONTRIBUTING.md.",
             f"module {TOP} (",
             "    input  wire [7:0] ui_in,    // Dedicated inputs",
             "    output wire [7:0] uo_out,   // Dedicated outputs",
             "    input  wire [7:0] uio_in,   // IOs: Input path",
             "    output wire [7:0] uio_out,  // IOs: Output path",
             "    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)",
             "    input  wire       ena,      // always 1 when the design is powered, so you can ignore it",
             "    input  wire       clk,      // clock",
             "    input  wire       rst_n     // reset_n - low to reset",
             ");", ""]
    for i in range(8):
        lines.append(f"  slot_uo{i}  s_uo{i}  (.clk(clk), .rst_n(rst_n), .in(ui_in), .out(uo_out[{i}]));")
    lines.append("")
    for i in range(8):
        lines.append(f"  slot_uio{i} s_uio{i} (.clk(clk), .rst_n(rst_n), .in(ui_in), "
                     f".out(uio_out[{i}]), .oe(uio_oe[{i}]));")
    lines += ["", "  // The slots read only ui_in.", "  wire _unused = &{ena, uio_in, 1'b0};", "",
              "endmodule", ""]
    return "\n".join(lines)


def makefile():
    srcs = " ".join(["project.v"] + [f"slot_{s}.v" for s in SLOTS])
    mods = ",".join(f"test_{s}" for s in SLOTS)
    return f"""# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info
#
# Changed from Tiny Tapeout's template only in PROJECT_SOURCES and COCOTB_TEST_MODULES, which
# already list every slot, so claiming a slot doesn't change this file.

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = {srcs}

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# One test module per slot, test/test_<pin>.py:
COCOTB_TEST_MODULES = {mods}

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
"""


SANDBOX_PY = '''# SPDX-FileCopyrightText: 2026 UofT ASIC Team
# SPDX-License-Identifier: Apache-2.0
"""Helpers every slot test uses. They read and drive only the top-level pins, because the
gl_test job runs the same tests on the gate-level netlist, where the slots' own names are gone."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge


async def start(dut):
    """Start a 10 MHz clock (clock_hz in info.yaml), reset the design, and return on a falling
    edge with ui_in = 0. Change inputs and read outputs on falling edges, half a clock period
    away from the rising edges where the flip-flops change."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)


async def settle(dut, cycles=1):
    """Let `cycles` rising edges go by and return on the falling edge after the last one."""
    for _ in range(cycles):
        await FallingEdge(dut.clk)


def pin(dut, name):
    """The value, 0 or 1, of one output pin: pin(dut, "uo[3]") or pin(dut, "uio[5]")."""
    bus, n = name.rstrip("]").split("[")
    signal = {"uo": dut.uo_out, "uio": dut.uio_out}[bus]
    return (int(signal.value) >> int(n)) & 1


def is_output(dut, name):
    """Whether a uio pin is set as an output (its uio_oe bit is 1)."""
    n = int(name.rstrip("]").split("[")[1])
    return (int(dut.uio_oe.value) >> n) & 1
'''


def test_py(slot):
    p = pin(slot)
    t = [f"# Slot {p}: unclaimed. Whoever claims {p} replaces this test with one for their block.",
         "", "import cocotb", "from sandbox import pin, settle, start", "",
         "", "@cocotb.test()", f"async def test_{slot}_unclaimed(dut):", "    await start(dut)",
         "    for value in (0x00, 0xFF):", "        dut.ui_in.value = value",
         "        await settle(dut)",
         f'        assert pin(dut, "{p}") == 0, f"unclaimed {p} is {{pin(dut, \'{p}\')}} with ui_in = {{value:#04x}}, expected 0"']
    if slot.startswith("uio"):
        t[3] = "from sandbox import is_output, pin, settle, start"
        t.append(f'    assert not is_output(dut, "{p}"), "unclaimed {p} should be an input"')
    return "\n".join(t) + "\n"


def main():
    w = lambda path, text: open(os.path.join(OUT, path), "w").write(text)
    w("src/project.v", project_v())
    for s in SLOTS:
        w(f"src/slot_{s}.v", slot_v(s))
        w(f"test/test_{s}.py", test_py(s))
    w("test/Makefile", makefile())
    w("test/sandbox.py", SANDBOX_PY)
    print(f"wrote {len(SLOTS)} slots and their tests in {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
