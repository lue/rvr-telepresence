# based on sphero-sdk-raspberrypi-python/projects/keyboard_control/

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import asyncio

from helper_keyboard_input import KeyboardHelper
from sphero_sdk import SerialAsyncDal
from sphero_sdk import SpheroRvrAsync

# Socket io
import time
import socketio
sio = socketio.Client()


# initialize global variables
key_helper = KeyboardHelper()
current_key_code = -1
driving_keys = [119, 97, 115, 100, 32]
speed = 0
heading = 0
flags = 0

heading_update = 0
shift_update = 0

loop = asyncio.get_event_loop()
rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)

# Function catching socket.io events
@sio.on('doc')
def on_message(data):
    global speed
    global heading_update
    global shift_update
    
    print(data['message'])
    instruction = data['message'][0]
    param = int(data['message'][1:])
    if instruction == 'r':
        speed = 0
        heading_update = param
    
    if instruction == 'l':
        speed = 0
        heading_update = -param
    
    if instruction == 'f':
        speed = 0
        shift_update = param
     
    sio.emit('doc', {'message': 'done'})


sio.connect('http://instinctive-capable-pony.glitch.me')
sio.emit('doc', {'message': 'connected'})


def keycode_callback(keycode):
    global current_key_code
    current_key_code = keycode
    print("Key code updated: ", str(current_key_code))


async def main():
    """
    Runs the main control loop for this demo.  Uses the KeyboardHelper class to read a keypress from the terminal.
    W - Go forward.  Press multiple times to increase speed.
    A - Decrease heading by -10 degrees with each key press.
    S - Go reverse. Press multiple times to increase speed.
    D - Increase heading by +10 degrees with each key press.
    Spacebar - Reset speed and flags to 0. RVR will coast to a stop
    """
    global current_key_code
    global speed
    global heading
    global heading_update
    global flags
    global shift_update

    await rvr.wake()

    await rvr.reset_yaw()

    while True:
        
        print("heading", heading)
        
        if heading_update != 0:
            heading += heading_update
            heading_update = 0

        # check the speed value, and wrap as necessary.
        if speed > 255:
            speed = 255
        elif speed < -255:
            speed = -255

        # check the heading value, and wrap as necessary.
        if heading > 359:
            heading = heading - 359
        elif heading < 0:
            heading = 359 + heading

        # reset the key code every loop
        current_key_code = -1

        # issue the driving command
        await rvr.drive_with_heading(speed, heading, flags)
        
        if shift_update != 0:
            await rvr.drive_with_heading(32, heading, flags)
            await asyncio.sleep(1)
            await rvr.drive_with_heading(0, heading, flags)
            shift_update=0

        # sleep the infinite loop for a 10th of a second to avoid flooding the serial port.
        await asyncio.sleep(0.1)


def run_loop():
    global loop
    global key_helper
    key_helper.set_callback(keycode_callback)
    loop.run_until_complete(
        asyncio.gather(
            main()
        )
    )


if __name__ == "__main__":
    loop.run_in_executor(None, key_helper.get_key_continuous)
    try:
        run_loop()
    except KeyboardInterrupt:
        print("Keyboard Interrupt...")
        key_helper.end_get_key_continuous()
    finally:
        print("Press any key to exit.")
        exit(1)
