#!/usr/bin/env python3
"""
Unit tests for logging utilities module.
"""

import os
import json
import logging
import tempfile
import pytest
from utils.logging_utils import JsonFormatter, setup_logging, add_scan_context

@pytest.mark.logging
@pytest.mark.unit
def test_json_formatter():
    """
    Test JSON log formatter with various log record scenarios.
    """
    formatter = JsonFormatter()
    
    # Create logger and record
    logger = logging.getLogger('test_logger')
    record = logger.makeRecord('test_logger', logging.INFO, None, None, 'Test message', None, None)
    record.custom_field = 'custom_value'
    
    # Format log record
    log_json = formatter.format(record)
    log_data = json.loads(log_json)
    
    # Validate JSON log structure
    assert 'timestamp' in log_data
    assert log_data['level'] == 'INFO'
    assert log_data['name'] == 'test_logger'
    assert log_data['message'] == 'Test message'
    assert log_data.get('custom_field') == 'custom_value'

@pytest.mark.logging
@pytest.mark.unit
def test_setup_logging_file_handler():
    """
    Test logging setup with file handler.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, 'test.log')
        config = {
            'LOG_FILE': log_file,
            'LOG_LEVEL': 'DEBUG',
            'LOG_JSON': False,
            'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
        
        logger = setup_logging(config, 'test_logger')
        logger.info("Test log message")
        
        # Verify log file was created
        assert os.path.exists(log_file)
        
        # Check log file contents
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "Test log message" in log_content

@pytest.mark.logging
@pytest.mark.unit
def test_setup_logging_console_handler():
    """
    Test logging setup with console handler.
    """
    config = {
        'LOG_CONSOLE': True,
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(levelname)s - %(message)s'
    }
    
    logger = setup_logging(config, 'console_logger')
    
    # Verify console handler was added
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)

@pytest.mark.logging
@pytest.mark.unit
def test_add_scan_context():
    """
    Test adding scan context to logger.
    """
    base_logger = logging.getLogger('base_logger')
    file_data = {
        'name': 'test_file.txt',
        'size': 1024,
        'md5': 'abc123',
        'zeek_uid': 'xyz789'
    }
    scan_result = {
        'rule_name': 'test_rule',
        'matched': True
    }
    
    logger_with_context = add_scan_context(base_logger, file_data, scan_result)
    
    # Verify context was added
    assert logger_with_context.extra == {
        'file_name': 'test_file.txt',
        'file_size': 1024,
        'file_md5': 'abc123',
        'file_zeek_uid': 'xyz789',
        'rule_name': 'test_rule',
        'matched': True
    }

@pytest.mark.logging
@pytest.mark.unit
def test_setup_logging_json():
    """
    Test logging setup with JSON formatting.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, 'test.json')
        config = {
            'LOG_FILE': log_file,
            'LOG_JSON': True,
            'LOG_LEVEL': 'INFO',
            'SUPPRESS_INIT_LOG': True  # Suppress initialization log
        }
        
        logger = setup_logging(config, 'json_logger')
        logger.info("JSON log test")
        
        # Verify log file was created
        assert os.path.exists(log_file)
        
        # Read and parse JSON log
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
            
            # Find the log line with the test message
            test_log = None
            for line in log_lines:
                log_data = json.loads(line)
                if log_data['message'] == 'JSON log test':
                    test_log = log_data
                    break
            
            assert test_log is not None, "Could not find test log message"
            assert 'timestamp' in test_log
            assert 'level' in test_log
            assert test_log['message'] == 'JSON log test'

@pytest.mark.logging
@pytest.mark.unit
def test_logging_exception_handling():
    """
    Test logging with exception data.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, 'exception.log')
        config = {
            'LOG_FILE': log_file,
            'LOG_JSON': True,
            'LOG_LEVEL': 'ERROR'
        }
        
        logger = setup_logging(config, 'exception_logger')
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            logger.exception("An error occurred")
        
        # Verify exception log contains necessary information
        with open(log_file, 'r') as f:
            log_line = f.read().strip()
            log_data = json.loads(log_line)
            
            assert 'exception' in log_data
            assert 'ValueError' in log_data['exception']
            assert 'Test exception' in log_data['exception']
