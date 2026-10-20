import pyaudiowpatch as pyaudio
import numpy as np
import time

class TestCapture:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.blocks = []

    def start(self):
        wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        loopback_dev = None
        for dev in self.p.get_loopback_device_info_generator():
            if default_speakers["name"] in dev["name"]:
                loopback_dev = dev
                break
        if not loopback_dev:
            for dev in self.p.get_loopback_device_info_generator():
                loopback_dev = dev
                break

        print(f"Using Loopback Device: {loopback_dev['name']}")
        channels = loopback_dev["maxInputChannels"]
        native_rate = int(loopback_dev["defaultSampleRate"])
        target_rate = 16000

        def callback(in_data, frame_count, time_info, status):
            raw = np.frombuffer(in_data, dtype=np.float32)
            if channels > 1:
                mono = np.mean(raw.reshape(-1, channels), axis=1)
            else:
                mono = raw
            
            if native_rate != target_rate and len(mono) > 1:
                new_len = int(len(mono) * target_rate / native_rate)
                if new_len > 0:
                    x_orig = np.arange(len(mono))
                    x_new = np.linspace(0, len(mono) - 1, new_len)
                    mono = np.interp(x_new, x_orig, mono).astype(np.float32)
            
            mono_out = mono.reshape(-1, 1)
            self.blocks.append(mono_out.shape)
            return (in_data, pyaudio.paContinue)

        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=channels,
            rate=native_rate,
            input=True,
            input_device_index=loopback_dev["index"],
            stream_callback=callback,
            frames_per_buffer=1024
        )
        self.stream.start_stream()

    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.p.terminate()

tc = TestCapture()
print("Starting capture...")
tc.start()
time.sleep(2.0)
print(f"Blocks captured in 2s: {len(tc.blocks)}, sample shape: {tc.blocks[0] if tc.blocks else 'None'}")
tc.stop()
print("Stopped cleanly!")
