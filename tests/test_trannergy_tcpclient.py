from unittest.mock import MagicMock, patch

import pytest
from trannergy_tcpclient import TaskReadSerial


@pytest.fixture
def task_read_serial_instance():
  mock_trigger = MagicMock()
  mock_stopper = MagicMock()
  mock_telegram = MagicMock()
  return TaskReadSerial(trigger=mock_trigger, stopper=mock_stopper, telegram=mock_telegram)


def test_read_serial_sets_trigger_on_correct_serial(task_read_serial_instance):
  with patch('trannergy_tcpclient.cfg.INV_SERIAL', '1234567890123456'), \
      patch('trannergy_tcpclient.binascii.hexlify') as mock_hexlify, \
      patch.object(task_read_serial_instance, '_TaskReadSerial__sock') as mock_socket:
    mock_socket.recv.return_value = b'HeaderData1234567890123456MoreData'
    task_read_serial_instance._TaskReadSerial__counter = 0
    task_read_serial_instance._TaskReadSerial__trigger.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__stopper.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__telegram.clear.return_value = None

    mock_hexlify.return_value = b'hexrepresentation'

    task_read_serial_instance._TaskReadSerial__read_serial()

    assert task_read_serial_instance._TaskReadSerial__trigger.set.called
    assert task_read_serial_instance._TaskReadSerial__telegram.append.call_count == 2


def test_read_serial_does_not_set_trigger_on_incorrect_serial(task_read_serial_instance):
  with patch('trannergy_tcpclient.cfg.INV_SERIAL', '1234567890123456'), \
      patch.object(task_read_serial_instance, '_TaskReadSerial__sock') as mock_socket:
    mock_socket.recv.return_value = b'HeaderData0987654321098765MoreData'
    task_read_serial_instance._TaskReadSerial__trigger.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__stopper.is_set.side_effect = [False, True]

    task_read_serial_instance._TaskReadSerial__read_serial()

    assert not task_read_serial_instance._TaskReadSerial__trigger.set.called
    assert task_read_serial_instance._TaskReadSerial__telegram.append.call_count == 0


def test_read_serial_handles_invalid_encoding(task_read_serial_instance):
  with patch('trannergy_tcpclient.cfg.INV_SERIAL', '1234567890123456'), \
      patch.object(task_read_serial_instance, '_TaskReadSerial__sock') as mock_socket:
    mock_socket.recv.return_value = b'HeaderDataInvalidEncodingMoreData'
    task_read_serial_instance._TaskReadSerial__trigger.is_set.side_effect = [False, True]
    task_read_serial_instance._TaskReadSerial__stopper.is_set.side_effect = [False, True]

    task_read_serial_instance._TaskReadSerial__read_serial()

    assert not task_read_serial_instance._TaskReadSerial__trigger.set.called
    assert task_read_serial_instance._TaskReadSerial__telegram.append.call_count == 0
