# A test that catches Lab 03's planted bug. Add it to test/test.py, after the other tests.


@cocotb.test()
async def test_load(dut):
    await start(dut)
    dut.uio_in.value = 0x5A
    dut.ui_in.value = LOAD
    await cycles(dut, 1)
    assert dut.uo_out.value == 0x5A, f"after LOAD with uio_in = 0x5A, uo_out is {dut.uo_out.value}, expected 0x5A"
