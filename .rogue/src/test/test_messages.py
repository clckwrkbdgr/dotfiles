from .. import messages
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'

class TestEvents(unittest.TestCase):
	def should_str_events(self):
		self.assertEqual(str(messages.DiscoverEvent('@')), 'Discovered @')
		self.assertEqual(str(messages.AttackEvent('@', 'M')), '@ attacks M')
		self.assertEqual(str(messages.HealthEvent('@', -10)), '@ -10 hp')
		self.assertEqual(str(messages.HealthEvent('@', +10)), '@ +10 hp')
		self.assertEqual(str(messages.DeathEvent('@')), '@ dies')
		self.assertEqual(str(messages.MoveEvent('@', 'POS')), '@ moves to POS')
		self.assertEqual(str(messages.DescendEvent('@')), '@ descends')
		self.assertEqual(str(messages.BumpEvent('@', 'POS')), '@ bumps into POS')
		self.assertEqual(str(messages.GrabItemEvent('@', '!')), '@ grabs !')
		self.assertEqual(str(messages.ConsumeItemEvent('@', '!')), '@ consumes !')
		self.assertEqual(str(messages.DropItemEvent('@', '!')), '@ drops !')
