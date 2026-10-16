"""Small Renode Monitor adapter. Time advances only through RunFor commands."""

import re
import tempfile
from pathlib import Path

import pexpect


PROMPT = re.compile(r"\((?:monitor|machine-0)\) ")
VALUE = re.compile(r"0x[0-9A-Fa-f]{8}")
GPIO_ODR = 0x40020C14
IRQ_COUNT = 0x20000000


class RenodeSession:
    def __init__(self, renode_bin: Path, platform: Path, firmware: Path, raw_log: Path):
        self.renode_bin = renode_bin
        self.platform = platform
        self.firmware = firmware
        self.raw_log = raw_log
        self.elapsed_ns = 0
        self.trace = []
        self.child = None
        self.log_file = None
        self.tempdir = None

    def __enter__(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="phase0-renode-")
        config = str(Path(self.tempdir.name) / "renode.cfg")
        self.raw_log.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = self.raw_log.open("w", encoding="utf-8")
        self.child = pexpect.spawn(
            str(self.renode_bin),
            ["--plain", "--disable-gui", "--hide-log", "--console", "-P", "-1", "--config", config],
            encoding="utf-8",
            codec_errors="replace",
            timeout=45,
            echo=False,
        )
        self.child.delaybeforesend = 0.01
        self.child.logfile_read = self.log_file
        self.child.expect(PROMPT)
        self.command("mach create")
        self.command(f"machine LoadPlatformDescription @{self.platform}")
        self.command(f"sysbus LoadELF @{self.firmware}")
        self.command('emulation SetGlobalQuantum "0.000001"')
        if self.read_gpio() & (1 << 12):
            raise RuntimeError("LED output high before firmware starts")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.child is not None and self.child.isalive():
                self.child.sendline("quit")
                try:
                    self.child.expect(pexpect.EOF, timeout=5)
                except pexpect.TIMEOUT:
                    self.child.terminate(force=True)
                self.child.close()
        finally:
            if self.log_file is not None:
                self.log_file.close()
            if self.tempdir is not None:
                self.tempdir.cleanup()

    def command(self, command: str) -> str:
        self.child.sendline(command)
        self.child.expect(PROMPT)
        output = self.child.before.replace("\r", "\n")
        if "[ERROR]" in output or "There was an error executing command" in output or "Bad parameters" in output:
            raise RuntimeError(f"Renode command failed: {command}\n{output}")
        return output

    def read_word(self, address: int) -> int:
        output = self.command(f"sysbus ReadDoubleWord 0x{address:08X}")
        values = [line.strip() for line in output.splitlines() if VALUE.fullmatch(line.strip())]
        if len(values) != 1:
            raise RuntimeError(f"Cannot parse register read at 0x{address:08X}: {output!r}")
        return int(values[0], 16)

    def read_gpio(self) -> int:
        return self.read_word(GPIO_ODR)

    def observe_gpio(self) -> int:
        value = self.read_gpio()
        self.trace.append({"virtual_ns": self.elapsed_ns, "gpio_odr": value})
        return value

    def run_for_ns(self, interval_ns: int):
        if interval_ns <= 0:
            raise ValueError("virtual-time step must be positive")
        seconds = f"{interval_ns // 1_000_000_000}.{interval_ns % 1_000_000_000:09d}"
        self.command(f'emulation RunFor "{seconds}"')
        self.elapsed_ns += interval_ns

    def restart_same_binary(self):
        self.command("machine Reset")
        self.command(f"sysbus LoadELF @{self.firmware}")
        self.elapsed_ns = 0
        self.trace = []
        if self.read_gpio() & (1 << 12):
            raise RuntimeError("LED output remained high after machine reset")
