"""Sounddevice stream and ring buffer for real-time audio capture."""

import threading

import numpy as np
import sounddevice as sd

from clamtuna.constants import BUFFER_SIZE, RING_BUFFER_SIZE, SAMPLE_RATE


class RingBuffer:
    """Thread-safe ring buffer for audio samples."""

    def __init__(self, size: int = RING_BUFFER_SIZE):
        self.buffer = np.zeros(size, dtype=np.float32)
        self.size = size
        self.write_pos = 0
        self._lock = threading.Lock()

    def write(self, data: np.ndarray) -> None:
        n = len(data)
        with self._lock:
            if self.write_pos + n <= self.size:
                self.buffer[self.write_pos : self.write_pos + n] = data
            else:
                first = self.size - self.write_pos
                self.buffer[self.write_pos :] = data[:first]
                self.buffer[: n - first] = data[first:]
            self.write_pos = (self.write_pos + n) % self.size

    def read(self, n: int) -> np.ndarray:
        """Read the most recent n samples."""
        with self._lock:
            n = min(n, self.size)
            start = (self.write_pos - n) % self.size
            if start + n <= self.size:
                return self.buffer[start : start + n].copy()
            else:
                first = self.size - start
                return np.concatenate([self.buffer[start:], self.buffer[: n - first]])


class AudioStream:
    """Manages sounddevice input stream feeding a ring buffer."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, block_size: int = BUFFER_SIZE):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.ring_buffer = RingBuffer()
        self.stream: sd.InputStream | None = None
        self.is_running = False

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            pass  # silently ignore xruns
        self.ring_buffer.write(indata[:, 0])

    def start(self) -> None:
        if self.is_running:
            return
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self.stream.start()
        self.is_running = True

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_running = False

    def get_samples(self, n: int = BUFFER_SIZE) -> np.ndarray:
        return self.ring_buffer.read(n)
