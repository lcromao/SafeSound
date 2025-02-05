import os
import subprocess
import sys
import webbrowser
import time
import signal
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/safesound_debug.log')),
        logging.StreamHandler()
    ]
)

def signal_handler(signum, frame):
    logging.info("Received signal to terminate. Cleaning up...")
    sys.exit(0)

def wait_for_streamlit(port=8501, timeout=30):
    """Wait for Streamlit to be ready"""
    import http.client
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            conn = http.client.HTTPConnection(f"localhost:{port}")
            conn.request("GET", "/_stcore/health")
            response = conn.getresponse()
            if response.status == 200:
                return True
        except:
            time.sleep(1)
    return False

if __name__ == '__main__':
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Get the directory containing our script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logging.info(f"Current directory: {current_dir}")
        
        # Log Python executable and environment
        logging.info(f"Python executable: {sys.executable}")
        logging.info(f"Python version: {sys.version}")
        
        # Set up the command to run streamlit
        streamlit_script = os.path.join(current_dir, "safesound.py")
        logging.info(f"Streamlit script path: {streamlit_script}")
        
        streamlit_cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            streamlit_script,
            "--server.address=localhost",
            "--server.port=8501",
            "--browser.serverAddress=localhost",
            "--server.headless=true",
            "--theme.base=light"
        ]
        
        logging.info("Starting Streamlit process...")
        process = subprocess.Popen(streamlit_cmd)
        
        # Wait for Streamlit to be ready
        logging.info("Waiting for Streamlit server to be ready...")
        if wait_for_streamlit():
            # Open browser after a short delay
            time.sleep(2)
            webbrowser.open('http://localhost:8501')
            logging.info("Browser opened")
            
            # Keep the app running
            process.wait()
        else:
            logging.error("Streamlit server failed to start")
            process.terminate()
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}", exc_info=True)
        sys.exit(1)