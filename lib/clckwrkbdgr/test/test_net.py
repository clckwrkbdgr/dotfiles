from clckwrkbdgr import unittest
import clckwrkbdgr.net

PING_SAMPLE_OUTPUT = [
		(False, "PING 192.168.0.1 (192.168.0.1) 56(84) bytes of data."),
		(True, "64 bytes from 192.168.0.1: icmp_seq=1 ttl=64 time=2.15 ms"),
		(True, "64 bytes from 192.168.0.1: icmp_seq=2 ttl=64 time=1.92 ms"),
		(True, "64 bytes from 192.168.0.1: icmp_seq=3 ttl=64 time=10.0 ms"),
		(True, "64 bytes from 192.168.0.1: icmp_seq=4 ttl=64 time=3.42 ms"),
		(False, ""),
		(False, "--- 192.168.0.1 ping statistics ---"),
		(True, "4 packets transmitted, 4 received, 0% packet loss, time 3002ms"),
		(True, "rtt min/avg/max/mdev = 1.924/4.396/10.080/3.330 ms"),
		]

class TestPing(unittest.TestCase):
	def should_clear_ping_output(self):
		actual = clckwrkbdgr.net._clear_ping_output(line for _, line in PING_SAMPLE_OUTPUT)
		expected = [line for clear, line in PING_SAMPLE_OUTPUT if clear]
		self.assertEqual(list(actual), expected)

