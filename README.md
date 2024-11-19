# Train Countdown Timer

This project is a Python-based countdown timer for train departures in Melbourne Australia, designed to run on a Raspberry Pi with an e-ink display. The timer fetches live train schedule data from the PTV (Public Transport Victoria) API and displays the time remaining until the next train departs.
<img src="Timer.gif" alt="Running Timer" width="400" height="300">

## Features

- **Real-time Train Schedules**: Retrieves and updates train schedules via the PTV API.
- **Clear E-ink Display**: Displays departure time in hours and minutes, ideal for low-power usage.
- **Automated Updates**: Refreshes the countdown periodically without heavy screen flicker.
- **Robust Operation**: Automatically retries failed API requests to handle occasional connection issues.

## Requirements

- **Hardware**:
  - Raspberry Pi (tested on Pi Zero WH)
  - Waveshare 2.13-inch Touch E-Paper Display

- **Software**:
  - Python 3
  - [Requests](https://docs.python-requests.org/en/master/)
  - [Pillow](https://pillow.readthedocs.io/)

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/Chojins/Train-Countdown-Timer.git
    cd Train-Countdown-Timer
    ```

2. **Install Required Libraries**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure the PTV API**:
   - Set up a PTV developer account and obtain your `devid` and `signature`.
   - Update these credentials in `train_countdown.py`.

4. **Configure System Service (Optional)**:
   - To run the script as a background service, copy the provided `train_countdown.service` to `/etc/systemd/system/`.
   - Enable and start the service:
     ```bash
     sudo systemctl enable train_countdown.service
     sudo systemctl start train_countdown.service
     ```

## Usage
Start the service manuallY
```bash
sudo systemctl start train_countdown.service
```
monitor the system service with
```bash
journalctl -u train_countdown.service -f
```
