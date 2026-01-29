"""
Audio Streamer
Manages audio input/output with PyAudio for the banking voice agent
"""
import asyncio
import pyaudio
from config.constants import *
from utils.logging import debug_print


class AudioStreamer:
    """Manages audio input/output with PyAudio"""

    def __init__(self, stream_manager):
        """
        Initialize audio streamer

        Args:
            stream_manager: BedrockStreamManager instance for sending/receiving audio
        """
        self.stream_manager = stream_manager
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.running = False

    def start(self):
        """Start audio streams"""
        self.running = True

        # Input stream (microphone)
        self.input_stream = self.audio.open(
            format=AUDIO_FORMAT,
            channels=CHANNELS,
            rate=INPUT_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._input_callback,
        )

        # Output stream (speakers)
        self.output_stream = self.audio.open(
            format=AUDIO_FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        self.input_stream.start_stream()
        print("\n🏦  Banking Agent Ready - Start speaking...")
        print("Press Ctrl+C to exit\n")

    def _input_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio input"""
        if self.running:
            asyncio.create_task(self.stream_manager.send_audio_chunk(in_data))
        return (None, pyaudio.paContinue)

    async def play_output(self):
        """Play audio output from queue"""
        while self.running:
            try:
                audio_data = await asyncio.wait_for(
                    self.stream_manager.output_queue.get(), timeout=0.1
                )
                self.output_stream.write(audio_data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                debug_print(f"Output error: {e}")

    def stop(self):
        """Stop audio streams"""
        self.running = False
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.close()
        self.audio.terminate()
