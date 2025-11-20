"""
Logging configuration for the Grant Compliance Automation system.
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str, log_file: str | None = None, level=logging.INFO):
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional log file path
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_file_path(agent_name: str) -> str:
    """
    Generate a log file path for an agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Log file path
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    log_dir = os.path.join(os.getcwd(), 'logs')
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    return os.path.join(log_dir, f'{agent_name}_{timestamp}.log')
