import pyaudio
import asyncio
import websockets
import os
import json
import threading
import janus
import queue
import sys

VOICE_AGENT_URL = "wss://agent.deepgram.com/agent"
PROMPT = "You are a helpful assistant. Responses should be short and direct."
VOICE = "aura-asteria-en"

USER_AUDIO_SAMPLE_RATE = 16000
USER_AUDIO_SECS_PER_CHUNK = 0.05
USER_AUDIO_SAMPLES_PER_CHUNK = round(USER_AUDIO_SAMPLE_RATE * USER_AUDIO_SECS_PER_CHUNK)

AGENT_AUDIO_SAMPLE_RATE = 16000
AGENT_AUDIO_BYTES_PER_SEC = 2 * AGENT_AUDIO_SAMPLE_RATE

SETTINGS = {
    "type": "SettingsConfiguration",
    "audio": {
        "input": {
            "encoding": "linear16",
            "sample_rate": USER_AUDIO_SAMPLE_RATE,
        },
        "output": {
            "encoding": "linear16",
            "sample_rate": AGENT_AUDIO_SAMPLE_RATE,
            "container": "none",
        },
    },
    "agent": {
        "listen": {"model": "nova-2"},
        "think": {
            "provider": {"type": "open_ai"},
            "model": "gpt-4o-mini",
            "instructions": PROMPT,
        },
        "speak": {"model": VOICE},
    },
}

mic_audio_queue = asyncio.Queue()


def callback(input_data, frame_count, time_info, status_flag):
    mic_audio_queue.put_nowait(input_data)
    return (input_data, pyaudio.paContinue)


async def run():
    dg_api_key = os.environ.get("DEEPGRAM_API_KEY")
    if dg_api_key is None:
        print("DEEPGRAM_API_KEY env var not present")
        return

    async with websockets.connect(
        VOICE_AGENT_URL,
        extra_headers={"Authorization": f"Token {dg_api_key}"},
    ) as ws:

        async def microphone():
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=USER_AUDIO_SAMPLE_RATE,
                input=True,
                frames_per_buffer=USER_AUDIO_SAMPLES_PER_CHUNK,
                stream_callback=callback,
            )

            stream.start_stream()

            while stream.is_active():
                await asyncio.sleep(0.1)

            stream.stop_stream()
            stream.close()

        async def sender(ws):
            await ws.send(json.dumps(SETTINGS))

            try:
                while True:
                    data = await mic_audio_queue.get()
                    await ws.send(data)

            except Exception as e:
                print("Error while sending: " + str(e))
                raise

        async def receiver(ws):
            try:
                speaker = Speaker()
                with speaker:
                    async for message in ws:
                        if type(message) is str:
                            print(message)

                            if json.loads(message)["type"] == "UserStartedSpeaking":
                                speaker.stop()

                        elif type(message) is bytes:
                            await speaker.play(message)

            except Exception as e:
                print(e)

        await asyncio.wait(
            [
                asyncio.ensure_future(microphone()),
                asyncio.ensure_future(sender(ws)),
                asyncio.ensure_future(receiver(ws)),
            ]
        )


def main():
    asyncio.get_event_loop().run_until_complete(run())


def _play(audio_out, stream, stop):
    while not stop.is_set():
        try:
            # Janus sync queue mimics the API of queue.Queue, and async queue mimics the API of
            # asyncio.Queue. So for this line check these docs:
            # https://docs.python.org/3/library/queue.html#queue.Queue.get.
            #
            # The timeout of 0.05 is to prevent this line from going into an uninterruptible wait,
            # which can interfere with shutting down the program on some systems.
            data = audio_out.sync_q.get(True, 0.05)

            # In PyAudio's "blocking mode," the `write` function will block until playback is
            # finished. This is why we can stop playback very quickly by simply stopping this loop;
            # there is never more than 1 chunk of audio awaiting playback inside PyAudio.
            # Read more: https://people.csail.mit.edu/hubert/pyaudio/docs/#example-blocking-mode-audio-i-o
            stream.write(data)

        except queue.Empty:
            pass


class Speaker:
    def __init__(self):
        self._queue = None
        self._stream = None
        self._thread = None
        self._stop = None

    def __enter__(self):
        audio = pyaudio.PyAudio()
        self._stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AGENT_AUDIO_SAMPLE_RATE,
            input=False,
            output=True,
        )
        self._queue = janus.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=_play, args=(self._queue, self._stream, self._stop), daemon=True
        )
        self._thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop.set()
        self._thread.join()
        self._stream.close()
        self._stream = None
        self._queue = None
        self._thread = None
        self._stop = None

    async def play(self, data):
        return await self._queue.async_q.put(data)

    def stop(self):
        if self._queue and self._queue.async_q:
            while not self._queue.async_q.empty():
                try:
                    self._queue.async_q.get_nowait()
                except janus.QueueEmpty:
                    break


if __name__ == "__main__":
    sys.exit(main() or 0)
