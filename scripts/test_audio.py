import sounddevice as sd

print("Testing WASAPI device 20 and 21:")
for dev in [20, 21]:
    try:
        s = sd.InputStream(device=dev, samplerate=48000, channels=2)
        s.start()
        s.stop()
        s.close()
        print(f"Device {dev}: SUCCESS")
    except Exception as e:
        print(f"Device {dev}: FAILED ({e})")
