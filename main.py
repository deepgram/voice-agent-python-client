from websockets.exceptions import ConnectionClosedOK
import asyncio
import json
import websockets
import pyaudio
import os
import argparse
import logging
from agent_config import AGENT_SETTINGS
# for multilingual demo:
# from agent_config import MULTILINGUAL_AGENT_SETTINGS as AGENT_SETTINGS
from agent_functions import FUNCTION_MAP
from speaker import Speaker

logger = logging.getLogger("__name__")


def configure_logger(loglevel):
    debugdict = dict(
        DEBUG=logging.DEBUG,
        INFO=logging.INFO,
        WARNING=logging.WARNING,
        ERROR=logging.ERROR,
    )
    logger.setLevel(debugdict[loglevel])
    formatter = logging.Formatter("%(levelname)-8s %(asctime)s %(name)-12s %(message)s")
    streamhandle = logging.StreamHandler()
    streamhandle.setFormatter(formatter)
    logger.addHandler(streamhandle)


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
FRAMES_PER_BUFFER = 1024


def _handle_task_result(task):
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation should not be logged as an error.
    except Exception:  # pylint: disable=broad-except
        logger.error("Exception raised by task = %r", task)


async def start_stream(mic_stream, uri):
    """Run websocket connection to stream audio file to uri.

    Parameters
    ----------
    mic_stream: pyaudio.Stream object
    uri: string
        The full destination with request parameters baked in
    """
    extra_headers = {"Authorization": f"Token {os.environ.get('DEEPGRAM_API_KEY')}"}
    logger.debug(uri)
    try:
        async with websockets.connect(uri, extra_headers=extra_headers) as ws:
            # see https://websockets.readthedocs.io/en/stable/reference/client.html#websockets.client.WebSocketClientProtocol
            shared_data = {"endstream": False, "agent_ready": False}

            async def sender(mic_stream, ws, shared):
                """Send audio through websocket."""

                # Start out by sending the settings
                await ws.send(json.dumps(AGENT_SETTINGS))
                while True:
                    piece = mic_stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

                    if not shared_data.get("agent_ready", False):
                        await asyncio.sleep(0.1)  # wait a little
                        continue  # Discard audio until agent is ready

                    if shared_data["endstream"]:
                        piece = b""  # This will close the connection
                        logger.debug("Sending close frame")
                        await ws.send(piece)
                        break
                    elif len(piece) == 0:
                        logger.debug(f"Piece is empty.")
                        continue

                    try:
                        await ws.send(piece)
                    except ConnectionClosedOK:
                        break

                    await asyncio.sleep(0.01)

            # This example function will handle responses.
            async def receiver(ws, shared):
                speaker = Speaker(
                    AGENT_SETTINGS.get("audio", {})
                    .get("output", {})
                    .get("sample_rate", 16000)
                )
                with speaker:
                    async for msg in ws:
                        try:
                            # Deserialize the JSON message.
                            if type(msg) is bytes:
                                await speaker.play(msg)
                            else:
                                msg = json.loads(msg)
                                msg_type = msg.get("type", "unknown")
                                if msg_type == "Welcome":
                                    logger.info(
                                        f"Welcome received. Request id: {msg.get('request_id', '')}"
                                    )
                                elif msg_type == "SettingsApplied":
                                    logger.info(
                                        f"Settings applied, starting to stream microphone"
                                    )
                                    shared_data["agent_ready"] = True
                                elif msg_type == "PromptUpdated":
                                    logger.info(f"Prompt Updated")
                                elif msg_type == "SpeakUpdated":
                                    logger.info(f"Speak Updated")
                                elif msg_type == "ConversationText":
                                    logger.info(
                                        f"Conversation text received.  Role: {msg.get('role')}. Content: {msg.get('content')}"
                                    )
                                elif msg_type == "UserStartedSpeaking":
                                    logger.info(
                                        f"User started speaking.  Stopping speaker"
                                    )
                                    speaker.stop()
                                elif msg_type == "Agent Thinking":
                                    logger.info(
                                        f"Agent thinking.  Content: {msg.get('content')}"
                                    )
                                elif msg_type == "FunctionCallRequest":
                                    logger.info(f"Agent making function call.  {msg}")
                                    for function_obj in msg.get("functions", []):
                                        id = function_obj.get("id")
                                        name = function_obj.get("name")
                                        func = FUNCTION_MAP.get(name)
                                        if name == "end_story":
                                            await ws.close()
                                            break
                                        elif func is not None:
                                            try:
                                                kwargs = json.loads(
                                                    function_obj.get("arguments", "{}")
                                                )
                                                logger.debug(f"Function args: {kwargs}")
                                                funcresponse = func(**kwargs)
                                            except Exception as e:
                                                logger.error(
                                                    f"Error calling function {function_obj}!"
                                                )
                                                funcresponse = (
                                                    "Function could not be called"
                                                )
                                        else:
                                            funcresponse = (
                                                "Function could not be called"
                                            )

                                        response = {
                                            "type": "FunctionCallResponse",
                                            "id": id,
                                            "name": name,
                                            "content": funcresponse,
                                        }
                                        logger.debug(f"Function response: {response}")
                                        await ws.send(json.dumps(response))
                                elif msg_type == "FunctionCallResponse":
                                    logger.info(f"Function call response.  {msg}")
                                elif msg_type == "AgentStartedSpeaking":
                                    logger.info(f"Agent started speaking")
                                elif msg_type == "AgentAudioDone":
                                    logger.info(f"Agent audio done")
                                elif msg_type == "Error":
                                    logger.info(
                                        f"Received error from Voice Agent: {msg}"
                                    )
                                elif msg_type == "Warning":
                                    logger.info(
                                        f"Received warning from Voice Agent: {msg}"
                                    )
                                else:
                                    logger.info(f"Unhandled message type: {msg}")

                        except Exception as e:
                            # The above get will fail on final metadata response
                            logger.error(f"Caught exception on {msg}, {e}")

            loop = asyncio.get_event_loop()
            sendertask = loop.create_task(sender(mic_stream, ws, shared_data))
            receivertask = loop.create_task(receiver(ws, shared_data))
            sendertask.add_done_callback(_handle_task_result)
            receivertask.add_done_callback(_handle_task_result)
            await asyncio.wait([sendertask, receivertask], timeout=None)
    except Exception as e:
        logger.error(f"Caught exception: {e}")
        logger.debug(f"Exception: {e}")
        logger.debug(f"Dir: {dir(e)}")
        logger.debug(f"Headers: {e.headers}")


def run_voiceagent(mic_stream, uri):
    logger_prefix = ""
    asyncio.run(start_stream(mic_stream, uri))


if __name__ == "__main__":

    parser = argparse.ArgumentParser("microphone")
    parser.add_argument(
        "url",
        help="The URL to hit",
        type=str,
        nargs="?",
        default="wss://agent.deepgram.com/v1/agent/converse",
    )
    parser.add_argument(
        "--loglevel",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR)",
        type=str,
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    configure_logger(args.loglevel)
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

    try:
        run_voiceagent(stream, args.url)
    except Exception as e:
        logger.error(f"Found exception {e}")
    finally:
        stream.close()
