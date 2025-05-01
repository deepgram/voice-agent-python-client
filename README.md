# voice-agent-python-client

This is a Python client for interacting with Deepgram's Voice Agent API.

## Instructions

1. Set an environment variable with your Deepgram API key:
    ```
    export DEEPGRAM_API_KEY=<your-key-here>
    ```

2. Install the dependencies in `requirements.txt`. For example, on Ubuntu using a virtual environment:
    ```
    python3 -m venv venv
    source venv/bin/activate
    pip install .
    ```
    Or if using `uv` you can jump right in with `uv run main.py`

3. Run the client:
    ```
    python3 main.py
    # or
    uv run main.py
    ```
    If you want to see additional logging information:
    ```
    uv run main.py --loglevel DEBUG
    ```

4. Start talking into your mic. This client doesn't have echo cancellation; you'll want to use headphones so the agent doesn't hear itself and think it's user speech.

If you say "goodbye" or ask the voice agent to exit, it will close the stream.
