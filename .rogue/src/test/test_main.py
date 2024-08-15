import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from ..system import savefile
import rogue

class TestMain(unittest.TestCase):
	@mock.patch('src.system.savefile.Savefile')
	@mock.patch('src.ui.auto_ui')
	@mock.patch('src.game.Game')
	def should_run_new_game(self, mock_game, mock_ui, mock_savefile):
		mock_savefile.return_value.load.return_value = None
		rogue.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.update_vision.assert_not_called()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_called_once_with(mock.ANY)
		mock_game.return_value.save.assert_called_once()
	@mock.patch('src.game.load_game')
	@mock.patch('src.system.savefile.Savefile')
	@mock.patch('src.ui.auto_ui')
	@mock.patch('src.game.Game')
	def should_load_game(self, mock_game, mock_ui, mock_savefile, load_game):
		from ..system import savefile
		mock_savefile.return_value.load.return_value = savefile.Reader(iter([1]))
		rogue.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
	@mock.patch('src.game.load_game')
	@mock.patch('src.system.savefile.Savefile')
	@mock.patch('src.ui.auto_ui')
	@mock.patch('src.game.Game')
	def should_abandon_game(self, mock_game, mock_ui, mock_savefile, load_game):
		from ..system import savefile
		mock_savefile.return_value.load.return_value = savefile.Reader(iter([1]))
		mock_game.return_value.get_player.return_value.is_alive.return_value = False
		rogue.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_not_called()
		mock_savefile.return_value.unlink.assert_called_once_with()
