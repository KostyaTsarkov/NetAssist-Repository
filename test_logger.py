import logging
import os

from src.logger import Logger


def test_logger_init():
    # Проверяем, что файл с логами создается
    log_file = 'test.log'
    logger = Logger(log_file)
    assert os.path.exists(log_file)
    os.remove(log_file)

def test_logger_log_info(caplog):
    # Проверяем, что сообщение уровня info записывается в лог
    log_file = 'test.log'
    logger = Logger(log_file)
    message = 'info message'
    logger.log_info(message)
    assert message in caplog.text

def test_logger_log_warning(caplog):
    # Проверяем, что сообщение уровня warning записывается в лог
    log_file = 'test.log'
    logger = Logger(log_file)
    message = 'warning message'
    logger.log_warning(message)
    assert message in caplog.text

def test_logger_log_error(caplog):
    # Проверяем, что сообщение уровня error записывается в лог
    log_file = 'test.log'
    logger = Logger(log_file)
    message = 'error message'
    logger.log_error(message)
    assert message in caplog.text
