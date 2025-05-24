""" Simple logging"""
import logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Create a logger instance
logger = logging.getLogger(__name__)