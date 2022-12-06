from clckwrkbdgr import unittest
import clckwrkbdgr.net

PING_SAMPLE_OUTPUT = b"""\
PING 192.168.0.1 (192.168.0.1) 56(84) bytes of data.
64 bytes from 192.168.0.1: icmp_seq=1 ttl=64 time=2.15 ms
64 bytes from 192.168.0.1: icmp_seq=2 ttl=64 time=1.92 ms
64 bytes from 192.168.0.1: icmp_seq=3 ttl=64 time=10.0 ms
64 bytes from 192.168.0.1: icmp_seq=4 ttl=64 time=3.42 ms

--- 192.168.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3002ms
rtt min/avg/max/mdev = 1.924/4.396/10.080/3.330 ms
"""

class MockPing(clckwrkbdgr.net.Ping):
	DROP_PATTERNS = clckwrkbdgr.net.LinuxPing.DROP_PATTERNS
	def run(self):
		self.rc = 0
		self.output = PING_SAMPLE_OUTPUT

class TestPing(unittest.TestCase):
	def should_clear_ping_output(self):
		ping = MockPing('hostname')
		ping.run()

		expected = [False, True, True, True, True, False, False, True, True]
		expected = [line for clear, line in zip(expected, PING_SAMPLE_OUTPUT.decode().splitlines()) if clear]
		self.assertEqual(list(ping.iter_output()), expected)

