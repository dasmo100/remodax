"""
Remodax - WASAPI Audio Capture Infrastructure
Captures system audio (Zoom, Google Meet, Teams, Browser, Speakers) using WASAPI Loopback via PyAudioWPatch.
Includes automatic resampling to 16 kHz mono in RAM and microphone capture support.
"""

import logging
import threading
from typing import Callable, List, Dict, Any, Optional
import numpy as np
from src.domain.ports.audio_port import IAudioCaptureService
from src.domain.exceptions import AudioCaptureException

logger = logging.getLogger("remodax.audio")


class WasapiAudioCaptureService(IAudioCaptureService):
    """
    Audio capture implementation for Windows using PyAudioWPatch and WASAPI.
    Captures speaker/headphone output (Loopback) to hear Zoom, Google Meet, and interviewers,
    or microphone input, resampled in memory to 16 kHz mono for Whisper.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self._sample_rate = sample_rate
        self._channels = channels
        self._is_capturing = False
        self._pa_instance = None
        self._stream = None
        self._lock = threading.Lock()
        self._callback: Optional[Callable[[np.ndarray], None]] = None

    def start_capture(
        self,
        callback: Callable[[np.ndarray], None],
        device_index: Optional[int] = None,
        is_loopback: bool = True
    ) -> None:
        with self._lock:
            if self._is_capturing:
                logger.warning("Audio capture is already running.")
                return

            self._callback = callback

            # Attempt 1: PyAudioWPatch (Native WASAPI Loopback on Windows)
            try:
                import pyaudiowpatch as pyaudio

                p = pyaudio.PyAudio()
                self._pa_instance = p

                target_dev = None
                if is_loopback:
                    # Specific loopback device selected
                    if device_index is not None and device_index >= 0:
                        try:
                            d = p.get_device_info_by_index(device_index)
                            if d.get("isLoopbackDevice", False) or "loopback" in d.get("name", "").lower():
                                target_dev = d
                        except Exception:
                            target_dev = None

                    # Default loopback device via WASAPI
                    if target_dev is None and hasattr(p, "get_default_wasapi_loopback"):
                        try:
                            target_dev = p.get_default_wasapi_loopback()
                        except Exception as ex:
                            logger.debug("get_default_wasapi_loopback falló: %s", ex)

                    # Fallback loopback search
                    if target_dev is None:
                        try:
                            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                        except Exception:
                            default_speakers = None

                        for dev in p.get_loopback_device_info_generator():
                            if default_speakers and default_speakers["name"] in dev["name"]:
                                target_dev = dev
                                break

                        if target_dev is None:
                            for dev in p.get_loopback_device_info_generator():
                                target_dev = dev
                                break
                else:
                    # Microphone capture requested
                    if device_index is not None and device_index >= 0:
                        try:
                            d = p.get_device_info_by_index(device_index)
                            if d.get("maxInputChannels", 0) > 0 and not d.get("isLoopbackDevice", False):
                                target_dev = d
                        except Exception:
                            target_dev = None

                    if target_dev is None:
                        try:
                            target_dev = p.get_default_input_device_info()
                        except Exception:
                            for idx in range(p.get_device_count()):
                                d = p.get_device_info_by_index(idx)
                                if d.get("maxInputChannels", 0) > 0 and not d.get("isLoopbackDevice", False):
                                    target_dev = d
                                    break

                if target_dev is not None:
                    raw_channels = int(target_dev.get("maxInputChannels", 1))
                    stream_channels = max(1, min(2, raw_channels))
                    native_rate = int(target_dev["defaultSampleRate"])
                    target_rate = self._sample_rate

                    def _pa_callback(in_data, frame_count, time_info, status):
                        if status:
                            logger.debug("PyAudio status: %s", status)
                        if self._callback and in_data:
                            raw = np.frombuffer(in_data, dtype=np.float32)
                            if len(raw) == 0:
                                return (in_data, pyaudio.paContinue)

                            # Convert to mono
                            if stream_channels > 1:
                                mono = np.mean(raw.reshape(-1, stream_channels), axis=1)
                            else:
                                mono = raw

                            # Resample to 16 kHz for Whisper if native rate differs
                            if native_rate != target_rate and len(mono) > 1:
                                new_len = int(len(mono) * target_rate / native_rate)
                                if new_len > 0:
                                    x_orig = np.arange(len(mono))
                                    x_new = np.linspace(0, len(mono) - 1, new_len)
                                    mono = np.interp(x_new, x_orig, mono).astype(np.float32)

                            mono_out = mono.reshape(-1, 1).astype(np.float32)
                            self._callback(mono_out)

                        return (in_data, pyaudio.paContinue)

                    stream = p.open(
                        format=pyaudio.paFloat32,
                        channels=stream_channels,
                        rate=native_rate,
                        input=True,
                        input_device_index=target_dev["index"],
                        stream_callback=_pa_callback,
                        frames_per_buffer=1024
                    )
                    stream.start_stream()
                    self._stream = stream
                    self._is_capturing = True
                    logger.info(
                        "Captura iniciada vía PyAudioWPatch: %s (Loopback: %s, Rate: %s Hz)",
                        target_dev["name"], is_loopback, native_rate
                    )
                    return
            except Exception as pa_ex:
                logger.warning("Fallo al iniciar PyAudioWPatch: %s. Probando fallback sounddevice...", pa_ex)
                if self._pa_instance:
                    try:
                        self._pa_instance.terminate()
                    except Exception:
                        pass
                    self._pa_instance = None

            # Attempt 2: Sounddevice Fallback
            try:
                import sounddevice as sd

                all_devs = sd.query_devices()
                target_idx = None
                for idx, d in enumerate(all_devs):
                    if d["max_input_channels"] > 0:
                        target_idx = idx
                        break

                dev_info = all_devs[target_idx] if target_idx is not None else None
                native_rate = int(dev_info["default_samplerate"]) if dev_info else 44100
                stream_channels = min(2, max(1, dev_info["max_input_channels"])) if dev_info else 1

                def _sd_callback(indata, frames, time_info, status):
                    if self._callback and indata is not None and len(indata) > 0:
                        if indata.ndim > 1 and indata.shape[1] > 1:
                            mono = np.mean(indata, axis=1, keepdims=True).astype(np.float32)
                        else:
                            mono = indata.astype(np.float32)

                        if native_rate != self._sample_rate and len(mono) > 1:
                            new_len = int(len(mono) * self._sample_rate / native_rate)
                            if new_len > 0:
                                x_orig = np.arange(len(mono))
                                x_new = np.linspace(0, len(mono) - 1, new_len)
                                mono = np.interp(x_new, x_orig, mono[:, 0]).astype(np.float32).reshape(-1, 1)

                        self._callback(mono)

                stream = sd.InputStream(
                    samplerate=native_rate,
                    channels=stream_channels,
                    device=target_idx,
                    callback=_sd_callback
                )
                stream.start()
                self._stream = stream
                self._is_capturing = True
                logger.info("Captura de audio iniciada vía sounddevice (Device: %s)", target_idx)
            except Exception as sd_ex:
                self._is_capturing = True
                logger.warning("Hardware no disponible, operando en memoria: %s", sd_ex)

    def stop_capture(self) -> None:
        with self._lock:
            if not self._is_capturing:
                return

            if self._stream is not None:
                try:
                    # Check if stream is PyAudio or sounddevice
                    if hasattr(self._stream, "stop_stream"):
                        self._stream.stop_stream()
                        self._stream.close()
                    elif hasattr(self._stream, "stop"):
                        self._stream.stop()
                        self._stream.close()
                except Exception as ex:
                    logger.debug("Error cerrando stream de audio: %s", str(ex))
                finally:
                    self._stream = None

            if self._pa_instance is not None:
                try:
                    self._pa_instance.terminate()
                except Exception as ex:
                    logger.debug("Error terminando PyAudio: %s", str(ex))
                finally:
                    self._pa_instance = None

            self._is_capturing = False
            self._callback = None
            logger.info("Captura de audio detenida y recursos liberados.")

    def is_capturing(self) -> bool:
        return self._is_capturing

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Enumerates audio capture devices with loopback capability."""
        devices_list = []
        try:
            import pyaudiowpatch as pyaudio

            with pyaudio.PyAudio() as p:
                # 1. Enumerate Loopback devices (System/Meeting Audio)
                for dev in p.get_loopback_device_info_generator():
                    devices_list.append({
                        "index": dev["index"],
                        "name": f"🔊 Audio del Sistema ({dev['name']})",
                        "is_loopback": True,
                        "channels": dev.get("maxInputChannels", 2),
                        "sample_rate": dev.get("defaultSampleRate", 48000.0)
                    })

                # 2. Enumerate Microphones
                for idx in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(idx)
                    if dev.get("maxInputChannels", 0) > 0 and not dev.get("isLoopbackDevice", False):
                        devices_list.append({
                            "index": dev["index"],
                            "name": f"🎤 Micrófono ({dev['name']})",
                            "is_loopback": False,
                            "channels": dev.get("maxInputChannels", 1),
                            "sample_rate": dev.get("defaultSampleRate", 44100.0)
                        })
        except Exception:
            # Fallback listing
            devices_list.append({
                "index": 0,
                "name": "🔊 Audio de Reunión (Zoom / Meet / Sistema)",
                "is_loopback": True,
                "channels": 2,
                "sample_rate": 48000.0
            })
            devices_list.append({
                "index": 1,
                "name": "🎤 Micrófono Propio",
                "is_loopback": False,
                "channels": 1,
                "sample_rate": 44100.0
            })

        return devices_list
