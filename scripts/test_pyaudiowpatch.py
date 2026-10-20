import pyaudiowpatch as pyaudio
import time
import numpy as np

with pyaudio.PyAudio() as p:
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        print("WASAPI host api:", wasapi_info)
    except OSError:
        print("WASAPI not available")
        exit(1)

    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    print("Default speakers (output device):", default_speakers["name"])

    # Find matching loopback device
    loopback_dev = None
    for dev in p.get_loopback_device_info_generator():
        print(f"Loopback device found: Index {dev['index']} - {dev['name']}")
        if default_speakers["name"] in dev["name"]:
            loopback_dev = dev
            break
    if not loopback_dev:
        # Fallback to first loopback device
        for dev in p.get_loopback_device_info_generator():
            loopback_dev = dev
            break

    if not loopback_dev:
        print("No loopback device found!")
        exit(1)

    print(f"\nTarget Loopback Device: {loopback_dev['name']} (Index {loopback_dev['index']})")
    print(f"Channels: {loopback_dev['maxInputChannels']}, Rate: {int(loopback_dev['defaultSampleRate'])}")

    blocks_captured = []
    def callback(in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        blocks_captured.append(len(audio_data))
        return (in_data, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paFloat32,
        channels=loopback_dev["maxInputChannels"],
        rate=int(loopback_dev["defaultSampleRate"]),
        input=True,
        input_device_index=loopback_dev["index"],
        stream_callback=callback
    )

    with stream:
        print("Loopback stream OPENED and RECORDING successfully!")
        time.sleep(1.0)

    print(f"SUCCESS! Captured {len(blocks_captured)} blocks of system audio (Zoom/Meet/interviewer speaker output).")
