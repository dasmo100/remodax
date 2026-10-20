import sounddevice as sd

print("--- HOST APIS ---")
for idx, api in enumerate(sd.query_hostapis()):
    print(f"API {idx}: {api['name']} | default_in: {api['default_input_device']} | default_out: {api['default_output_device']}")

print("\n--- DEVICES ---")
apis = sd.query_hostapis()
for idx, dev in enumerate(sd.query_devices()):
    api_name = apis[dev['hostapi']]['name']
    print(f"Dev {idx:2d} | API: {api_name:20s} | In: {dev['max_input_channels']} | Out: {dev['max_output_channels']} | Rate: {dev['default_samplerate']} | Name: {dev['name']}")
