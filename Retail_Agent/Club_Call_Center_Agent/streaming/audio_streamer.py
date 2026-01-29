"""
Audio Streamer for Call Center Agent
Handles continuous microphone input and audio output using separate streams
"""
import asyncio
import pyaudio

from config.constants import (
    INPUT_SAMPLE_RATE,
    OUTPUT_SAMPLE_RATE,
    CHANNELS,
    AUDIO_FORMAT,
    CHUNK_SIZE
)
from utils.logging import debug_print
from utils.timing import time_it


class AudioStreamer:
    """Handles continuous microphone input and audio output using separate streams."""

    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.is_streaming = False
        self.loop = asyncio.get_event_loop()

        debug_print("AudioStreamer Initializing PyAudio...")
        self.p = time_it("AudioStreamerInitPyAudio", pyaudio.PyAudio)
        debug_print("AudioStreamer PyAudio initialized")

        debug_print("Opening input audio stream...")
        self.input_stream = time_it(
            "AudioStreamerOpenAudio",
            lambda: self.p.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=INPUT_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.input_callback,
            ),
        )
        debug_print("input audio stream opened")

        debug_print("Opening output audio stream...")
        self.output_stream = time_it(
            "AudioStreamerOpenAudio",
            lambda: self.p.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=OUTPUT_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
            ),
        )

        debug_print("output audio stream opened")

    def input_callback(self, in_data, frame_count, time_info, status):
        """Callback function that schedules audio processing in the asyncio event loop"""
        if self.is_streaming and in_data:
            asyncio.run_coroutine_threadsafe(
                self.process_input_audio(in_data), self.loop
            )
        return (None, pyaudio.paContinue)

    async def process_input_audio(self, audio_data):
        """Process a single audio chunk directly"""
        try:
            self.stream_manager.add_audio_chunk(audio_data)
        except Exception as e:
            if self.is_streaming:
                print(f"Error processing input audio: {e}")

    async def play_output_audio(self):
        """Play audio responses from Nova Sonic"""
        while self.is_streaming:
            try:
                if self.stream_manager.barge_in:
                    while not self.stream_manager.audio_output_queue.empty():
                        try:
                            self.stream_manager.audio_output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    self.stream_manager.barge_in = False
                    await asyncio.sleep(0.05)
                    continue

                audio_data = await asyncio.wait_for(
                    self.stream_manager.audio_output_queue.get(), timeout=0.1
                )

                if audio_data and self.is_streaming:
                    chunk_size = CHUNK_SIZE

                    for i in range(0, len(audio_data), chunk_size):
                        if not self.is_streaming:
                            break

                        end = min(i + chunk_size, len(audio_data))
                        chunk = audio_data[i:end]

                        def write_chunk(data):
                            return self.output_stream.write(data)

                        await asyncio.get_event_loop().run_in_executor(
                            None, write_chunk, chunk
                        )

                        await asyncio.sleep(0.001)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.is_streaming:
                    print(f"Error playing output audio: {str(e)}")
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(0.05)

    async def start_streaming(self):
        """Start streaming audio."""
        if self.is_streaming:
            return

        print("Starting audio streaming. Speak into your microphone...")
        print("Press Enter to stop streaming...")

        from utils.timing import time_it_async
        await time_it_async(
            "send_audio_content_start_event",
            lambda: self.stream_manager.send_audio_content_start_event(),
        )

        self.is_streaming = True

        if not self.input_stream.is_active():
            self.input_stream.start_stream()

        self.output_task = asyncio.create_task(self.play_output_audio())

        await asyncio.get_event_loop().run_in_executor(None, input)

        await self.stop_streaming()

    async def stop_streaming(self):
        """Stop streaming audio."""
        if not self.is_streaming:
            return

        self.is_streaming = False

        tasks = []
        if hasattr(self, "input_task") and not self.input_task.done():
            tasks.append(self.input_task)
        if hasattr(self, "output_task") and not self.output_task.done():
            tasks.append(self.output_task)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if self.input_stream:
            if self.input_stream.is_active():
                self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            if self.output_stream.is_active():
                self.output_stream.stop_stream()
            self.output_stream.close()
        if self.p:
            self.p.terminate()

        await self.stream_manager.close()
