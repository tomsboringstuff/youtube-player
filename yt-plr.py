import random
import os
import sys
import time
import pyautogui
import subprocess
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from screeninfo import get_monitors
from pynput import keyboard as kb
import tempfile  # for handling temporary files
import logging  # for logging
import argparse  # for command-line arguments

# Function to read video URLs from a file
def read_video_urls_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            video_urls = [line.strip() for line in file]
        return video_urls
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        exit(1)

# Configure command-line argument parsing
parser = argparse.ArgumentParser(description="YouTube Player")
parser.add_argument("-s", "--silent", action="store_true", help="Silence all output")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("-n", "--nonrandom", action="store_true", help="Make playlist non-random (NOT WORKING IN THIS VERSION)")
parser.add_argument("-a", "--autoplay", action="store_true", help="Make playlist autoplay the next item (NOT WORKING IN THIS VERSION)")
parser.add_argument("-f", "--file", help="Use a custom URL pool. Must have a new URL on each line. No playlists. SOMETIMES WORKS IN TESTING")

# Add a separate argument for the playlist URL
parser.add_argument("playlist_url", nargs="?", default="https://www.youtube.com/playlist?list=PL-D2eb2vBV7LzsXkzeinc7v1eZ-22AaCs",
                    help="YouTube playlist URL (default: %(default)s)")

# Parse command-line arguments
args = parser.parse_args()

# Configure logging based on verbosity
if args.silent:
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
elif args.verbose:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

if args.nonrandom:
    logging.info("TESTING")
else:
    logging.info("NONTESTING")

logging.info(f"Using playlist URL: {args.playlist_url}")

# Check if the playlist URL contains the word "list"
if "list" not in args.playlist_url:
    # If it doesn't contain "list," use the URL as-is
    video_urls = [args.playlist_url]
    logging.info(f"Using custom URL: {args.playlist_url}")
elif args.file:
    # Use the file provided by the -f flag
    video_urls = read_video_urls_from_file(args.file)
else:
    # If it contains "list," proceed with the yt-dlp part
    # yt-dlp command to parse YouTube URLs
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "-i",
            "--print-to-file",
            "url",
            tmp.name,  # use the temporary file's name
            args.playlist_url
        ]

        # Log the creation of the temporary file
        logging.info(f"Temporary file created: {tmp.name} This is where the URLs are stored :)")

        # Run the command, capture the output, and filter it
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        finished_present = any("Finished" in line for line in stdout.splitlines() + stderr.splitlines())
        if finished_present:
            logging.info("YouTube URLs parsed. Loading a random video.")

        # Check for a non-zero exit status and ignore it
        if process.returncode != 0:
            logging.warning(f"yt-dlp command exited with code {process.returncode}")

        # Read URLs from the temporary file
        with open(tmp.name, "r") as source:
            video_urls = [line.strip() for line in source]

# Select a random video URL from the list
random_url = random.choice(video_urls)

# JavaScript function to parse YouTube video ID from a URL
youtube_parser_js = """
function youtube_parser(url){
    var regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    var match = url.match(regExp);
    return (match&&match[7].length==11)? match[7] : false;
}
"""

# Configure the WebDriver for Firefox
firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--start-maximized")  # Start Firefox maximized

# Create the Firefox WebDriver instance
driver = webdriver.Firefox(options=firefox_options)

# Get the screen resolutions of all monitors
monitors = get_monitors()

# If there's a second monitor, use its position; otherwise, use the primary monitor's position
monitor_to_use = monitors[1] if len(monitors) > 1 else monitors[0]
driver.set_window_position(monitor_to_use.x, monitor_to_use.y)

# Execute the JavaScript function to extract the video ID from the URL
video_id = driver.execute_script(youtube_parser_js + f"return youtube_parser('{random_url}');")

if not video_id:
    print("Failed to parse YouTube video ID from the URL.")
    driver.quit()
    exit()

# Construct the modified URL with the new endpoint
modified_url_vididinject = f"https://www.youtube.com/embed/{video_id}"
modified_url = f"{modified_url_vididinject}?autoplay=0&showinfo=0&controls=0"

# Navigate to a blank page
driver.get("about:blank")

# Inject custom HTML & CSS for an animated preloader
preloader_html_css = """
document.body.innerHTML = '<div class="preloader">Loading...</div>';
document.body.style.backgroundColor = "black";
document.body.style.display = "flex";
document.body.style.justifyContent = "center";
document.body.style.alignItems = "center";
document.body.style.height = "100vh";
document.querySelector('.preloader').style.fontSize = '2em';
document.querySelector('.preloader').style.color = 'white';
document.querySelector('.preloader').style.animation = 'fadeInOut 1.5s infinite';

// Adding keyframes for animation
var styleSheet = document.createElement("style")
styleSheet.type = "text/css"
styleSheet.innerText = '@keyframes fadeInOut { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }'
document.head.appendChild(styleSheet)
"""

driver.execute_script(preloader_html_css)

# Wait for 2 seconds to show the animated preloader
time.sleep(2)

# Navigate to the actual video URL
driver.get(modified_url)

# Wait for 0.5 seconds
time.sleep(0.5)

try:
    # Find the button element by its class name
    play_button = driver.find_element_by_class_name('ytp-large-play-button')
    
    # Create an ActionChains object and move to the button, then click on it
    actions = ActionChains(driver)
    actions.move_to_element(play_button).click().perform()
    # Press 'f' to enter fullscreen mode
    pyautogui.press('F')
    
except Exception as e:
    print(f"Video is not allowed to be embedded. Trying to play on YouTube.")
    pyautogui.press('tab')
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('F')

# Function to close the browser window and exit the script
def close_browser():
    driver.quit()  # Close the WebDriver instance
    exit()  # Exit the script

# Function to handle the "X" key press
def on_key_release(key):
    if key == kb.Key.esc:
        close_browser()
    elif key == kb.KeyCode.from_char('x'):
        close_browser()

# Create a keyboard listener
listener = kb.Listener(on_release=on_key_release)

# Start the keyboard listener
listener.start()

# Keep the script running
listener.join()

# Remove the temporary file after its use
try:
    os.remove(tmp.name)
    logging.info(f"Temporary file deleted: {tmp.name}")
except Exception as e:
    logging.error(f"No temp file needed as direct URL was supplied. No clean-up :)")
