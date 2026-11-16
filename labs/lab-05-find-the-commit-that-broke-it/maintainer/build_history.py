#!/usr/bin/env python3
"""Build Lab 05's prepared history and write it to data/history.bundle.

Students never run this; they clone the bundle. It exists so the history can be rebuilt or
changed, and so anyone can see exactly what each commit does.

    python3 build_history.py [--template DIR] [--out PATH] [--keep DIR]

--template is a checkout of TinyTapeout/ttsky-verilog-template at TEMPLATE_COMMIT; without it
the script fetches that commit from GitHub. The history is the template's files followed by a
small project, a PWM dimmer, written over 41 commits by three made-up teammates. Every commit is
rendered from a `state` dict: each step changes a few keys, the files are written from the whole
state, and the step is committed with a fixed author, committer and date. Git names a commit by
a hash of its tree, parents, message, names, emails and dates, so the same inputs give the same
hashes on any machine, and the lab writeup can quote them.

Three commits don't compile, for reasons unrelated to the bug (a half-written file, a file left
out of PROJECT_SOURCES, a half-written case statement), and one commit, a "tidy-up" of the PWM
comparator, makes `phase < duty` into `phase <= duty`, which turns the LED on for one step in
every period even at duty 0. TAG marks a commit whose workflows the made-up team saw green.

After changing anything here, rebuild, run maintainer/verify.sh, and update the hashes and
outputs quoted in docs/labs/lab-05-find-the-commit-that-broke-it-overview.md and in check.py.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

TEMPLATE_REPO = "https://github.com/TinyTapeout/ttsky-verilog-template"
TEMPLATE_COMMIT = "a42e6662fab316e93b4e26399e21d41664a460b7"
TAG = "v1.0"

AVERY = ("Avery Lee", "avery.lee@example.com")
JORDAN = ("Jordan Park", "jordan.park@example.com")
SAM = ("Sam Rivera", "sam.rivera@example.com")

LICENSE_HEADER = """/*
 * Copyright (c) 2026 The PWM dimmer team
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
"""

SEG_TABLE = [
    ("0", "0111111"), ("1", "0000110"), ("2", "1011011"), ("3", "1001111"),
    ("4", "1100110"), ("5", "1101101"), ("6", "1111101"), ("7", "0000111"),
    ("8", "1111111"), ("9", "1101111"), ("A", "1110111"), ("B", "1111100"),
    ("C", "0111001"), ("D", "1011110"), ("E", "1111001"),
]


# ---------------------------------------------------------------------------------------------
# Files, rendered from the state.

def info_yaml(s, base):
    y = base
    if s["filled"]:
        y = y.replace('title:        ""', 'title:        "PWM dimmer"')
        y = y.replace('author:       ""', 'author:       "Avery Lee, Jordan Park, Sam Rivera"')
        desc = s["description"]
        y = y.replace('description:  ""', f'description:  "{desc}"')
        y = y.replace("clock_hz:     0 ", "clock_hz:     10000000 ")
        y = y.replace('tiles: "1x1"', 'tiles: "1x2"')
    if s["top"] != "tt_um_example":
        y = y.replace('top_module:  "tt_um_example"', f'top_module:  "{s["top"]}"')
    y = y.replace('    - "project.v"\n', "".join(f'    - "{f}"\n' for f in sources(s, yaml=True)))
    pins = {}
    if s["filled"]:
        for i in range(8):
            pins[f"ui[{i}]"] = f"brightness[{i}]"
        pins["uo[7]"] = "LED"
    if s["seg_pins"]:
        for i, seg in enumerate("abcdefg"):
            pins[f"uo[{i}]"] = f"segment {seg}"
    if s["uio0_pin"]:
        pins["uio[0]"] = "fade mode"
    if s["presets"] == "done" and s["preset_pins"]:
        pins["uio[1]"] = "preset[0]"
        pins["uio[2]"] = "preset[1]"
    for k, v in pins.items():
        y = y.replace(f'  {k}: ""', f'  {k}: "{v}"')
    return y


def sources(s, yaml=False):
    out = ["project.v"]
    if s["prescaler"]:
        out.append("prescaler.v")
    if s["pwm"]:
        out.append("pwm.v")
    if s["seg"]:
        out.append("seg7.v")
    if s["seg_split"] and (yaml or s["seg_split_in_makefile"]):
        out.append("seg7_table.v")
    if s["fade"]:
        out.append("fade.v")
    return out


def test_makefile(s, base):
    return base.replace("PROJECT_SOURCES = project.v", "PROJECT_SOURCES = " + " ".join(sources(s)))


def tb_v(s, base):
    return base.replace("  tt_um_example user_project (", f"  {s['top']} user_project (")


def project_v(s, base):
    if not s["pwm_wired"]:
        return base.replace("module tt_um_example (", f"module {s['top']} (")
    step = "step" if s["step_name"] else "tick"
    lines = [LICENSE_HEADER, f"module {s['top']} ("]
    lines += [
        "    input  wire [7:0] ui_in,    // Dedicated inputs",
        "    output wire [7:0] uo_out,   // Dedicated outputs",
        "    input  wire [7:0] uio_in,   // IOs: Input path",
        "    output wire [7:0] uio_out,  // IOs: Output path",
        "    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)",
        "    input  wire       ena,      // always 1 when the design is powered, so you can ignore it",
        "    input  wire       clk,      // clock",
        "    input  wire       rst_n     // reset_n - low to reset",
        ");",
        "",
        "  // ui_in is the brightness, 0 (off) to 255, and uo_out[7] drives the LED.",
    ]
    if s["seg_wired"]:
        lines.append("  // uo_out[6:0] show the brightness's top hex digit on a seven-segment display.")
    if s["fade_wired"]:
        lines.append("  // With uio_in[0] high, the LED fades up and down by itself and ui_in is ignored.")
    if s["presets"]:
        lines.append("  // uio_in[2:1] pick a preset brightness: 1 is 16, 2 is 64, 3 is 255; 0 means none.")
    lines += ["", f"  wire       {step};", "  wire       led;"]
    if s["seg_wired"]:
        lines.append("  wire [6:0] segments;")
    if s["fade_wired"]:
        lines.append("  wire [7:0] level;")
    if s["presets"]:
        lines += ["  reg  [7:0] duty;", "", "  always @(*) begin", "    case (uio_in[2:1])",
                  "      2'd1: duty = 8'd16;", "      2'd2: duty = 8'd64;"]
        if s["presets"] == "wip":
            lines += ["      2'd3: duty = 8'd255", "    endcase", "  end"]
        else:
            lines += ["      2'd3: duty = 8'd255;",
                      "      default: duty = uio_in[0] ? level : ui_in;" if s["fade_wired"]
                      else "      default: duty = ui_in;",
                      "    endcase", "  end"]
    elif s["fade_wired"]:
        lines.append("  wire [7:0] duty = uio_in[0] ? level : ui_in;")
    else:
        lines.append("  wire [7:0] duty = ui_in;")
    lines += [
        "",
        f"  prescaler #(.DIV(4)) u_prescaler (.clk(clk), .rst_n(rst_n), .tick({step}));"
        if s["prescaler_param"] else
        f"  prescaler u_prescaler (.clk(clk), .rst_n(rst_n), .tick({step}));",
        f"  pwm       u_pwm       (.clk(clk), .rst_n(rst_n), .step({step}), .duty(duty), .out(led));",
    ]
    if s["fade_wired"]:
        lines.append(f"  fade      u_fade      (.clk(clk), .rst_n(rst_n), .step({step}), .level(level));")
    if s["seg_wired"]:
        lines.append("  seg7      u_seg7      (.digit(duty[7:4]), .segments(segments));")
    lines.append("")
    lines.append("  assign uo_out  = {led, segments};" if s["seg_wired"]
                 else "  assign uo_out  = {led, 7'b0};")
    lines += ["  assign uio_out = 8'd0;", "  assign uio_oe  = 8'd0;", "",
              "  // List all unused inputs to prevent warnings"]
    unused = "uio_in[7:3]" if s["presets"] else ("uio_in[7:1]" if s["fade_wired"] else "uio_in")
    lines += [f"  wire _unused = &{{ena, {unused}, 1'b0}};", "", "endmodule", ""]
    return "\n".join(lines)


def prescaler_v(s):
    head = LICENSE_HEADER + "\n"
    if s["prescaler_param"]:
        return head + """// Divides the clock: tick is high for one clock cycle in every DIV.
module prescaler #(
    parameter DIV = 4
) (
    input  wire clk,
    input  wire rst_n,
    output wire tick
);

  reg [7:0] n;

  always @(posedge clk) begin
    if (!rst_n || tick)
      n <= 8'd0;
    else
      n <= n + 8'd1;
  end

  assign tick = (n == DIV - 1);

endmodule
"""
    return head + """// Divides the clock by 4: tick is high for one clock cycle in every four.
module prescaler (
    input  wire clk,
    input  wire rst_n,
    output wire tick
);

  reg [1:0] n;

  always @(posedge clk) begin
    if (!rst_n)
      n <= 2'd0;
    else
      n <= n + 2'd1;
  end

  assign tick = (n == 2'd3);

endmodule
"""


def pwm_v(s):
    if s["pwm_tidy"]:
        doc = """// An 8-bit PWM. Each step moves the phase on by one, so a period is 256 steps long, and out is
// on for duty steps of each period."""
        compare = """  // On for duty steps of each period.
  assign out = (phase <= duty);"""
    else:
        doc = """// An 8-bit PWM. Each step advances the phase by one, so a period is 256 steps, and out is high
// for the first duty steps of each period: duty 0 is always off, and 255 is on for 255 of 256."""
        compare = """  // High while the phase is below the duty.
  assign out = (phase < duty);"""
    return LICENSE_HEADER + "\n" + doc + """
module pwm (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       step,
    input  wire [7:0] duty,
    output wire       out
);

  reg [7:0] phase;

  always @(posedge clk) begin
    if (!rst_n)
      phase <= 8'd0;
    else if (step)
      phase <= phase + 8'd1;
  end

""" + compare + """

endmodule
"""


def seg_case(indent):
    rows = [f"{indent}4'h{d}: segments = 7'b{bits};" for d, bits in SEG_TABLE]
    rows.append(f"{indent}default: segments = 7'b1110001;  // F")
    return "\n".join(rows)


def seg7_v(s):
    doc = "// Hex digit to seven segments, active high: segments[6:0] = {g, f, e, d, c, b, a}."
    if s["seg_split"]:
        return LICENSE_HEADER + "\n" + doc + """
// The table itself is in seg7_table.v.
module seg7 (
    input  wire [3:0] digit,
    output wire [6:0] segments
);

  seg7_table u_table (.digit(digit), .segments(segments));

endmodule
"""
    return LICENSE_HEADER + "\n" + doc + """
module seg7 (
    input  wire [3:0] digit,
    output reg  [6:0] segments
);

  always @(*) begin
    case (digit)
""" + seg_case("      ") + """
    endcase
  end

endmodule
"""


def seg7_table_v(s):
    doc = ("// Seven-segment patterns, active high: segments[6:0] = {g, f, e, d, c, b, a}."
           if s["seg_tidy"] else
           "// The seven-segment table, active high: segments[6:0] = {g, f, e, d, c, b, a}.")
    return LICENSE_HEADER + "\n" + doc + """
module seg7_table (
    input  wire [3:0] digit,
    output reg  [6:0] segments
);

  always @(*) begin
    case (digit)
""" + seg_case("      ") + """
    endcase
  end

endmodule
"""


def fade_v(s):
    body = LICENSE_HEADER + """
// Fade mode: on each step, level moves one count towards 255, then back down to 0, and so on.
module fade (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       step,
    output reg  [7:0] level
);

  reg rising;

  always @(posedge clk) begin
    if (!rst_n) begin
      level  <= 8'd0;
      rising <= 1'b1;
    end else if (step) begin
      if (rising) begin
        if (level == 8'hFF) rising <= 1'b0;
        else level <= level + 8'd1;
      end else begin
        if (level == 8'h00) rising <= 1'b1;
        else level <= level - 8'd1;
      end
"""
    if s["fade"] == "wip":
        return body + """
endmodule
"""
    return body + """    end
  end

endmodule
"""


def test_py(s):
    t = ['# SPDX-FileCopyrightText: 2026 The PWM dimmer team',
         '# SPDX-License-Identifier: Apache-2.0', '',
         'import cocotb', 'from cocotb.clock import Clock',
         'from cocotb.triggers import ClockCycles, FallingEdge', '',
         'DIV = 4               # the prescaler divides the clock by 4',
         'PERIOD = 256 * DIV    # clock cycles in one PWM period']
    if s["test_seg"]:
        t += ['', '# segments[6:0] = {g, f, e, d, c, b, a} for the digits 0 to F',
              'DIGITS = [' + ", ".join(f"0b{b}" for _, b in SEG_TABLE[:8]) + ',',
              '          ' + ", ".join(f"0b{b}" for _, b in SEG_TABLE[8:]) + ', 0b1110001]']
    period = 100 if s["test_clock"] == 100 else 10
    t += ['', '',
          'async def start(dut, duty=0, mode=0):',
          f'    """Start a {"10 MHz" if period == 100 else "100 kHz"} clock and reset the design, '
          'with ui_in = duty and uio_in = mode."""',
          f'    cocotb.start_soon(Clock(dut.clk, {period if period == 100 else 10}, '
          f'unit="{"ns" if period == 100 else "us"}").start())',
          '    dut.ena.value = 1', '    dut.ui_in.value = duty', '    dut.uio_in.value = mode',
          '    dut.rst_n.value = 0', '    await ClockCycles(dut.clk, 5)', '    dut.rst_n.value = 1',
          '    await FallingEdge(dut.clk)', '', '',
          'def led(dut):', '    return (int(dut.uo_out.value) >> 7) & 1', '', '',
          'async def on_cycles(dut, cycles):',
          '    """Count the cycles the LED is on, sampling on each falling edge."""',
          '    n = 0', '    for _ in range(cycles):', '        n += led(dut)',
          '        await FallingEdge(dut.clk)', '    return n', '', '']
    pin = "the LED (uo_out[7])" if s["test_pin_names"] else "the LED"
    t += ['@cocotb.test()', 'async def test_duty_0_is_off(dut):', '    await start(dut, duty=0)',
          '    n = await on_cycles(dut, 2 * PERIOD)',
          f'    assert n == 0, f"with duty 0 {pin} was on for {{n}} of {{2 * PERIOD}} cycles, expected 0"',
          '', '',
          '@cocotb.test()', 'async def test_duty_64_is_a_quarter(dut):', '    await start(dut, duty=64)',
          '    n = await on_cycles(dut, PERIOD)',
          f'    assert n == 64 * DIV, f"with duty 64 {pin} was on for {{n}} of {{PERIOD}} cycles, expected {{64 * DIV}}"',
          '', '',
          '@cocotb.test()', 'async def test_duty_255(dut):', '    await start(dut, duty=255)',
          '    n = await on_cycles(dut, PERIOD)',
          f'    assert n == 255 * DIV, f"with duty 255 {pin} was on for {{n}} of {{PERIOD}} cycles, expected {{255 * DIV}}"']
    if s["test_seg"]:
        t += ['', '', '@cocotb.test()', 'async def test_segments_show_the_top_digit(dut):',
              '    await start(dut)', '    for digit in range(16):',
              '        dut.ui_in.value = digit << 4', '        await FallingEdge(dut.clk)',
              '        segments = int(dut.uo_out.value) & 0x7F',
              '        assert segments == DIGITS[digit], f"digit {digit:X}: segments {segments:07b}, expected {DIGITS[digit]:07b}"']
    if s["test_fade"]:
        steps = 100 if s["test_fade_long"] else 72
        digit = steps >> 4
        t += ['', '', '@cocotb.test()', 'async def test_fade_rises(dut):',
              '    await start(dut, duty=0, mode=0b001)',
              f'    await ClockCycles(dut.clk, {steps} * DIV, rising=False)',
              '    segments = int(dut.uo_out.value) & 0x7F',
              f'    assert segments == DIGITS[{digit}], f"after {steps} steps of fade mode the display shows {{segments:07b}}, expected {{DIGITS[{digit}]:07b}} ({digit})"']
    if s["test_presets"]:
        t += ['', '', '@cocotb.test()', 'async def test_presets(dut):', '    await start(dut, duty=0)',
              '    for preset, duty in [(1, 16), (2, 64), (3, 255)]:',
              '        dut.uio_in.value = preset << 1', '        await FallingEdge(dut.clk)',
              '        segments = int(dut.uo_out.value) & 0x7F',
              '        assert segments == DIGITS[duty >> 4], f"preset {preset}: segments {segments:07b}, expected {DIGITS[duty >> 4]:07b}"']
    if s["test_uio"]:
        t += ['', '', '@cocotb.test()', 'async def test_uio_pins_are_inputs(dut):', '    await start(dut)',
              '    assert dut.uio_oe.value == 0, f"uio_oe is {dut.uio_oe.value}, expected all inputs (0)"']
    return "\n".join(t) + "\n"


def info_md(s, base):
    if not s["filled"]:
        return base
    works = ["The design is an LED dimmer. A prescaler divides the clock by four, and an 8-bit PWM",
             "turns the LED on `uo_out[7]` on for `ui_in` of every 256 steps, so `ui_in` sets the",
             "brightness from 0 (off) to 255."]
    if s["doc_seg"]:
        works += ["", "The top hex digit of the brightness is shown on a seven-segment display on",
                  "`uo_out[6:0]` (segments a to g)."]
    if s["doc_fade"]:
        works += ["", "With `uio_in[0]` high the LED fades up and down by itself, one count per step, and",
                  "`ui_in` is ignored."]
    if s["doc_pins"]:
        works += ["", "| Pin | Use |", "|---|---|", "| `ui_in[7:0]` | Brightness |",
                  "| `uo_out[7]` | LED |", "| `uo_out[6:0]` | Seven-segment display |",
                  "| `uio_in[0]` | Fade mode |"]
        if s["presets"] == "done":
            works.append("| `uio_in[2:1]` | Preset brightness |")
    test = ["Set `ui_in` and watch the LED."]
    if s["doc_test"]:
        test = ["Connect an LED to `uo_out[7]` and set `ui_in` to the brightness you want; the",
                "display shows its top hex digit. Set `uio_in[0]` to watch the LED fade."]
    hw = "List external hardware used in your project (e.g. PMOD, LED display, etc), if any"
    if s["doc_hw"]:
        hw = "An LED with a resistor on `uo_out[7]`, and a common-cathode seven-segment display on `uo_out[6:0]`."
    return (base.replace("Explain how your project works", "\n".join(works))
                .replace("Explain how to use your project", "\n".join(test))
                .replace("List external hardware used in your project (e.g. PMOD, LED display, etc), if any", hw))


def readme(s, base):
    if not s["readme"]:
        return base
    return base.replace("# Tiny Tapeout Verilog Project Template",
                        "# PWM dimmer\n\nAn LED dimmer for Tiny Tapeout, with a seven-segment brightness display and a fade mode.\n\n## About the template")


def render(s, base):
    files = {
        "info.yaml": info_yaml(s, base["info.yaml"]),
        "test/Makefile": test_makefile(s, base["test/Makefile"]),
        "test/tb.v": tb_v(s, base["test/tb.v"]),
        "src/project.v": project_v(s, base["src/project.v"]),
        "docs/info.md": info_md(s, base["docs/info.md"]),
        "README.md": readme(s, base["README.md"]),
        "test/test.py": test_py(s) if s["tests"] else base["test/test.py"],
    }
    if s["prescaler"]:
        files["src/prescaler.v"] = prescaler_v(s)
    if s["pwm"]:
        files["src/pwm.v"] = pwm_v(s)
    if s["seg"]:
        files["src/seg7.v"] = seg7_v(s)
    if s["seg_split"]:
        files["src/seg7_table.v"] = seg7_table_v(s)
    if s["fade"]:
        files["src/fade.v"] = fade_v(s)
    return files


# ---------------------------------------------------------------------------------------------
# The history: (author, date, message, state changes). Dates are Eastern Time.

START = dict(filled=False, description="An LED dimmer", top="tt_um_example", prescaler=False,
             prescaler_param=False, pwm=False, pwm_wired=False, pwm_tidy=False, seg=False,
             seg_wired=False, seg_pins=False, seg_split=False, seg_split_in_makefile=False,
             seg_tidy=False, fade=False, fade_wired=False, uio0_pin=False, presets=False,
             preset_pins=False, step_name=False, tests=False, test_seg=False, test_fade=False,
             test_fade_long=False, test_presets=False, test_uio=False, test_clock=10,
             test_pin_names=False, doc_seg=False, doc_fade=False, doc_pins=False, doc_test=False,
             doc_hw=False, readme=False)

STEPS = [
    (AVERY, "2026-09-28T19:12:00-04:00", "Fill in info.yaml and the datasheet", dict(filled=True)),
    (AVERY, "2026-09-28T19:40:00-04:00", "Rename the top module to tt_um_ic102_dimmer", dict(top="tt_um_ic102_dimmer")),
    (JORDAN, "2026-09-30T20:05:00-04:00", "Add a prescaler that divides the clock by 4", dict(prescaler=True)),
    (JORDAN, "2026-09-30T21:30:00-04:00", "Add an 8-bit PWM", dict(pwm=True)),
    (JORDAN, "2026-10-01T18:22:00-04:00", "Drive the LED on uo_out[7] from the PWM, with the duty on ui_in", dict(pwm_wired=True)),
    (SAM, "2026-10-02T15:10:00-04:00", "test: replace the adder test with three PWM tests", dict(tests=True)),
    (SAM, "2026-10-02T16:45:00-04:00", "README: say what the project is", dict(readme=True)),
    (AVERY, "2026-10-03T11:30:00-04:00", "docs: say how the dimmer works", dict(description="A PWM LED dimmer")),
    (JORDAN, "2026-10-05T19:00:00-04:00", "Add a hex to seven-segment decoder", dict(seg=True)),
    (JORDAN, "2026-10-05T19:35:00-04:00", "Show the brightness's top digit on uo_out[6:0]", dict(seg_wired=True)),
    (SAM, "2026-10-06T14:20:00-04:00", "test: check all sixteen digits on the display", dict(test_seg=True)),
    (AVERY, "2026-10-07T10:15:00-04:00", "info.yaml: pinout for the display", dict(seg_pins=True, doc_seg=True)),
    (JORDAN, "2026-10-09T22:40:00-04:00", "WIP: start a fade mode", dict(fade="wip")),
    (JORDAN, "2026-10-10T12:05:00-04:00", "fade: finish the module", dict(fade="done")),
    (JORDAN, "2026-10-10T12:50:00-04:00", "Wire fade mode to uio_in[0]", dict(fade_wired=True)),
    (SAM, "2026-10-11T16:00:00-04:00", "test: fade mode raises the brightness", dict(test_fade=True)),
    (AVERY, "2026-10-12T09:30:00-04:00", "docs: describe fade mode", dict(doc_fade=True, uio0_pin=True)),
    (JORDAN, "2026-10-14T18:10:00-04:00", "prescaler: make the divide ratio a parameter", dict(prescaler_param=True)),
    (SAM, "2026-10-15T20:25:00-04:00", "Move the seven-segment table into seg7_table.v", dict(seg_split=True)),
    (SAM, "2026-10-15T21:02:00-04:00", "test/Makefile: add seg7_table.v to PROJECT_SOURCES", dict(seg_split_in_makefile=True)),
    (JORDAN, "2026-10-16T19:30:00-04:00", "WIP: preset brightness levels on uio_in[2:1]", dict(presets="wip")),
    (JORDAN, "2026-10-17T08:55:00-04:00", "presets: finish the case statement", dict(presets="done")),
    (JORDAN, "2026-10-17T13:00:00-04:00", "Rename tick to step in the top level", dict(step_name=True)),
    (AVERY, "2026-10-18T10:45:00-04:00", "docs: add a pin table", dict(doc_pins=True)),
    (SAM, "2026-10-21T17:40:00-04:00", "test: the three presets", dict(test_presets=True)),
    (AVERY, "2026-10-22T11:10:00-04:00", "info.yaml: describe uio[1] and uio[2]", dict(preset_pins=True)),
    (SAM, "2026-10-23T15:35:00-04:00", "test: run the testbench clock at 10 MHz, to match clock_hz", dict(test_clock=100)),
    (JORDAN, "2026-10-25T20:15:00-04:00", "pwm: tidy up the comparator and its comments", dict(pwm_tidy=True)),
    (AVERY, "2026-10-26T10:00:00-04:00", "docs: say how to test it", dict(doc_test=True)),
    (SAM, "2026-10-27T18:30:00-04:00", "test: check that every uio pin is an input", dict(test_uio=True)),
    (JORDAN, "2026-10-28T21:05:00-04:00", "seg7_table: reword the comment", dict(seg_tidy=True)),
    (AVERY, "2026-10-30T09:20:00-04:00", "docs: list the external hardware", dict(doc_hw=True)),
    (SAM, "2026-11-01T14:45:00-05:00", "test: run fade mode for 100 steps", dict(test_fade_long=True)),
    (AVERY, "2026-11-02T10:30:00-05:00", "info.yaml: a longer description", dict(description="A PWM LED dimmer with a seven-segment display and a fade mode")),
    (SAM, "2026-11-03T16:20:00-05:00", "test: name the LED's pin in failure messages", dict(test_pin_names=True)),
]


def run(cmd, cwd, env=None):
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", help="a checkout of the template at TEMPLATE_COMMIT")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "..", "data", "history.bundle"))
    ap.add_argument("--keep", help="also leave the built repository in this folder")
    a = ap.parse_args()

    work = tempfile.mkdtemp(prefix="ic102-lab05-")
    tpl = a.template
    if not tpl:
        tpl = os.path.join(work, "template")
        run(["git", "init", "-q", tpl], work)
        run(["git", "fetch", "-q", "--depth", "1", TEMPLATE_REPO, TEMPLATE_COMMIT], tpl)
        run(["git", "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"], tpl)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tpl, capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != TEMPLATE_COMMIT:
        sys.exit(f"the template checkout is at {head}, not {TEMPLATE_COMMIT}")

    repo = os.path.join(work, "dimmer")
    os.makedirs(repo)
    run(["git", "init", "-q", "-b", "main"], repo)
    # Copy the template's tracked files with their modes, as "Use this template" would.
    files = subprocess.run(["git", "ls-files", "-s"], cwd=tpl, capture_output=True, text=True,
                           check=True).stdout.splitlines()
    for line in files:
        meta, path = line.split("\t", 1)
        mode = meta.split()[0]
        dst = os.path.join(repo, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(tpl, path), dst)
        os.chmod(dst, 0o755 if mode == "100755" else 0o644)
    base = {p: open(os.path.join(repo, p)).read() for p in
            ["info.yaml", "test/Makefile", "test/tb.v", "src/project.v", "docs/info.md",
             "README.md", "test/test.py"]}

    def commit(author, date, message):
        env = dict(os.environ, GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1],
                   GIT_COMMITTER_NAME=author[0], GIT_COMMITTER_EMAIL=author[1],
                   GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date, TZ="UTC")
        run(["git", "add", "-A"], repo)
        run(["git", "-c", "core.fileMode=true", "-c", "commit.gpgsign=false", "commit", "-q",
             "--allow-empty", "-m", message], repo, env)

    commit(AVERY, "2026-09-28T18:55:00-04:00", "Initial commit")
    state = dict(START)
    for author, date, message, change in STEPS:
        state.update(change)
        old = set(subprocess.run(["git", "ls-files", "src"], cwd=repo, capture_output=True,
                                 text=True, check=True).stdout.split())
        new = render(state, base)
        # Remove only the Verilog files a step drops. The template's src/config.json stays in
        # every commit: without it the gds job stops at "Could not file configuration file
        # src/config.{json}", which is what the first build of this history did on GitHub.
        for path in old - set(new):
            if path.endswith(".v"):
                os.remove(os.path.join(repo, path))
        for path, text in new.items():
            with open(os.path.join(repo, path), "w", newline="\n") as fh:
                fh.write(text)
        commit(author, date, message)
        if message == "docs: say how the dimmer works":
            env = dict(os.environ, GIT_COMMITTER_NAME=AVERY[0], GIT_COMMITTER_EMAIL=AVERY[1],
                       GIT_COMMITTER_DATE="2026-10-04T12:00:00-04:00")
            run(["git", "tag", "-a", TAG, "-m", "First version with every workflow green"], repo, env)

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["git", "bundle", "create", "-q", out, "HEAD", "main", TAG], repo)
    print(f"wrote {out}")
    print(subprocess.run(["git", "log", "--oneline", "--decorate"], cwd=repo, capture_output=True,
                         text=True).stdout)
    if a.keep:
        shutil.rmtree(a.keep, ignore_errors=True)
        shutil.copytree(repo, a.keep, symlinks=True)
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
