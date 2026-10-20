import sounddevice as sd
import numpy as np

def try_stream(is_loopback=True, device_index=None):
    all_devs = sd.query_devices()
    all_apis = sd.query_hostapis()
    
    target_idx = None
    if device_index is not None and 0 <= device_index < len(all_devs):
        if all_devs[device_index]['max_input_channels'] > 0:
            target_idx = device_index
            
    if target_idx is None and is_loopback:
        for idx, d in enumerate(all_devs):
            if d['max_input_channels'] > 0 and any(k in d['name'].lower() for k in ['mixed', 'loopback', 'stereo mix', 'mezcla']):
                target_idx = idx
                break
                
    if target_idx is None:
        def_idx = sd.default.device[0]
        if def_idx >= 0 and def_idx < len(all_devs) and all_devs[def_idx]['max_input_channels'] > 0:
            target_idx = def_idx
        else:
            for idx, d in enumerate(all_devs):
                if d['max_input_channels'] > 0:
                    target_idx = idx
                    break

    if target_idx is None:
        print("No input devices found on system.")
        return False
        
    dev = all_devs[target_idx]
    native_rate = int(dev['default_samplerate']) if dev['default_samplerate'] > 0 else 44100
    native_channels = min(2, max(1, dev['max_input_channels']))
    
    stream = None
    # Try preferred rates
    for sr in [16000, native_rate]:
        try:
            stream = sd.InputStream(device=target_idx, samplerate=sr, channels=native_channels, callback=lambda i, f, t, s: None)
            stream.start()
            print(f"Opened on dev {target_idx} ({dev['name']}) at {sr} Hz, {native_channels} ch")
            break
        except Exception as e:
            pass
            
    if stream is None:
        stream = sd.InputStream(callback=lambda i, f, t, s: None)
        stream.start()
        print("Opened default fallback stream")
        
    stream.stop()
    stream.close()
    return True

print("--- Testing Loopback request ---")
try_stream(is_loopback=True)
print("--- Testing Mic request ---")
try_stream(is_loopback=False)
