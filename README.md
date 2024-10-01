# voice-agent-python-client

This is a Python client for interacting with Deepgram's Voice Agent API.

## Instructions

1. Install the dependencies in `requirements.txt`. For example, on Ubuntu using a virtual environment:
    ```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. Set an environment variable with your Deepgram API key:
    ```
    export DEEPGRAM_API_KEY=<your-key-here>
    ```

3. Run the client:
    ```
    python3 client.py
    ```

4. Start talking into your mic. This client doesn't have echo cancellation; you'll want to use headphones so the agent doesn't hear itself and think it's user speech.
