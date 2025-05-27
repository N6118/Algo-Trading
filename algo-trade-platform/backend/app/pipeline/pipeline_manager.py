import sys
import os
import time
import logging
import threading
import schedule
import requests
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the necessary modules
from backend.app.data.streamdata import run_ibkr, run_flask

# Set up logging configuration
log_directory = os.path.join(project_root, "logs")
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create a log filename with timestamp
log_filename = os.path.join(log_directory, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("pipeline_manager")

class PipelineManager:
    def __init__(self, config=None):
        """Initialize the pipeline manager with configuration."""
        self.config = config or {}
        self.stream_thread = None
        self.flask_thread = None
        self.running = False
        
        # Default schedule settings
        self.schedule_settings = self.config.get('schedule', {
            'init_process': {
                'run_on_start': True,
                'interval_hours': 24,  # Run once a day
                'time': '00:00'  # At midnight
            },
            'update_process': {
                'run_on_start': True,
                'interval_minutes': 15  # Run every 15 minutes
            }
        })
        
        logger.info("Pipeline Manager initialized")
    
    def start_data_collection(self):
        """Start the data collection threads."""
        logger.info("Starting data collection...")
        
        # Start IBKR data collection thread
        self.stream_thread = threading.Thread(target=run_ibkr, daemon=True)
        self.stream_thread.start()
        logger.info("IBKR data collection thread started")
        
        # Start Flask API server thread for streamdata
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        logger.info("Streamdata Flask API server thread started")
        
        # Start attempt.py Flask server
        # We don't need to start this as a thread since it's already configured to run as a separate service
        # The pipeline will make HTTP requests to it
        logger.info("Will connect to strategy Flask server at http://localhost:5001")
    
    def run_init_process(self):
        """Run the initialization process by calling the Flask route."""
        logger.info("Running initialization process...")
        try:
            # Call the InitProcess Flask route via HTTP request
            response = requests.get('http://localhost:5001/')
            if response.status_code == 200:
                logger.info(f"Initialization process completed successfully")
                return response.text
            else:
                logger.error(f"Initialization process failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error in initialization process: {str(e)}")
            return None
    
    def run_update_process(self):
        """Run the update process by calling the Flask route."""
        logger.info("Running update process...")
        try:
            # Since there's no specific update route, we'll call the main route
            # which runs the InitProcess function in attempt.py
            response = requests.get('http://localhost:5001/')
            if response.status_code == 200:
                logger.info(f"Update process completed successfully")
                return response.text
            else:
                logger.error(f"Update process failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error in update process: {str(e)}")
            return None
    
    def setup_schedule(self):
        """Set up the schedule for running processes."""
        logger.info("Setting up schedule...")
        
        # Schedule InitProcess
        init_settings = self.schedule_settings.get('init_process', {})
        if init_settings.get('time'):
            schedule.every().day.at(init_settings.get('time')).do(self.run_init_process)
            logger.info(f"Scheduled InitProcess to run daily at {init_settings.get('time')}")
        elif init_settings.get('interval_hours'):
            schedule.every(init_settings.get('interval_hours')).hours.do(self.run_init_process)
            logger.info(f"Scheduled InitProcess to run every {init_settings.get('interval_hours')} hours")
        
        # Schedule UpdateProcess
        update_settings = self.schedule_settings.get('update_process', {})
        if update_settings.get('interval_minutes'):
            schedule.every(update_settings.get('interval_minutes')).minutes.do(self.run_update_process)
            logger.info(f"Scheduled UpdateProcess to run every {update_settings.get('interval_minutes')} minutes")
        
        # Run processes on start if configured
        if init_settings.get('run_on_start', False):
            logger.info("Running InitProcess on start")
            self.run_init_process()
        
        if update_settings.get('run_on_start', False):
            logger.info("Running UpdateProcess on start")
            self.run_update_process()
    
    def start(self):
        """Start the pipeline."""
        logger.info("Starting pipeline...")
        self.running = True
        
        # Start data collection
        self.start_data_collection()
        
        # Set up scheduled tasks
        self.setup_schedule()
        
        # Main loop to run scheduled tasks
        logger.info("Pipeline started, running scheduled tasks...")
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the pipeline."""
        logger.info("Stopping pipeline...")
        self.running = False
        
        # Clean up resources if needed
        logger.info("Pipeline stopped")

def load_config():
    """Load configuration from file."""
    config_path = os.getenv('PIPELINE_CONFIG_PATH', 'config/pipeline_config.json')
    try:
        import json
        with open(config_path, 'r') as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config from {config_path}: {str(e)}")
        logger.warning("Using default configuration")
        return {}

if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Create and start the pipeline
    pipeline = PipelineManager(config)
    pipeline.start()
