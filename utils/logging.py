import logging
import os
from datetime import datetime

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('Logs'):
        os.makedirs('Logs')
    
    # Set up logging configuration
    log_file = os.path.join('Logs', f'zwaif_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    return logging.getLogger(name)

# Don't call setup_logging here to avoid circular imports 