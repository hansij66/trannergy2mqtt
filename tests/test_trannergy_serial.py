from unittest.mock import MagicMock, patch

import pytest
from trannergy_serial import TaskReadSerial


@pytest.fixture
def task_read_serial_instance():
  trigger = MagicMock()
  stopper = MagicMock()
  telegram = MagicMock()
  return TaskReadSerial(trigger, stopper, telegram)


def test_read_serial_sets_trigger_and_adds_telegram_entries(task_read_serial_instance):
  with patch('trannergy_serial.binascii.hexlify') as mock_hexlify, \
      patch.object(task_read_serial_instance, '_TaskReadSerial__sock') as mock_socket:
    mock_socket.recv.return_value = b'HeaderData1234567890123456MoreData'
    task_read_serial_instance._TaskReadSerial__stopper.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__trigger.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__telegram.clear.return_value = None
    mock_hexlify.return_value = b'hexrepresentation'

    task_read_serial_instance._TaskReadSerial__read_serial()

    assert task_read_serial_instance._TaskReadSerial__trigger.set.called
    assert len(task_read_serial_instance._TaskReadSerial__telegram.append.mock_calls) == 2


def test_task_stops_on_exception(task_read_serial_instance):
  with patch('trannergy_serial.socket.socket') as mock_socket:
    mock_socket.side_effect = Exception("Socket error")
    with pytest.raises(ValueError, match="Cannot open socks port"):
      task_read_serial_instance.__init__(
        task_read_serial_instance._TaskReadSerial__trigger,
        task_read_serial_instance._TaskReadSerial__stopper,
        task_read_serial_instance._TaskReadSerial__telegram
      )


def test_socket_accept_raises_exception(task_read_serial_instance):
  with patch.object(task_read_serial_instance, '_TaskReadSerial__sock') as mock_socket:
    mock_socket.accept.side_effect = Exception("Accept error")
    task_read_serial_instance._TaskReadSerial__stopper.is_set.side_effect = [False, True]

    task_read_serial_instance.run()

    task_read_serial_instance._TaskReadSerial__stopper.set.assert_called()
    assert mock_socket.close.called
