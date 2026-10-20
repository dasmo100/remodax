import sounddevice as sd
import numpy as np
import time

wasapi_api = sd.query_hostapis()[2]
default_out = wasapi_api['default_output_device']
dev_info = sd.query_devices(default_out)

print(f"Testing WASAPI Loopback on Output Device {default_out}: {dev_info['name']}")
print(f"Channels: {dev_info['max_output_channels']}, Rate: {dev_info['default_samplerate']}")

recorded_blocks = []

def callback(indata, frames, time_info, status):
    if status:
        print(f"Status: {status}")
    vol = np.linalg.norm(indata)
    recorded_blocks.append(vol)

try:
    wasapi_settings = sd.WasapiSettings(loopback=True)
    stream = sd.InputStream(
        device=default_out,
        channels=int(dev_info['max_output_channels']),
        samplerate=int(dev_info['default_samplerate']),
        extra_settings=wasapi_settings,
        callback=callback
    )
    with stream:
        print("STREAM OPENED AND RUNNING SUCCESSFULLY!")
        time.sleep(1.0)
    print(f"Total blocks captured: {len(recorded_blocks)}")
    print("SUCCESS: WASAPI Loopback WORKS PERFECTLY!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"FAILED: {e}")
