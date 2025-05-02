import os

AGENT_SETTINGS = {
    "type": "Settings",
    "audio": {
        "input": {"encoding": "linear16", "sample_rate": 44100},
        "output": {
            "encoding": "linear16",
            "sample_rate": 16000,
        },
    },
    "agent": {
        "listen": {"provider": {"model": "nova-3", "type": "deepgram"}},
        "think": {
            "provider": {"model": "gpt-4o-mini", "type": "open_ai"},
            "prompt": "Your name is Sarah and you are a story teller who creates new stories given a specific theme",
            "functions": [
                {
                    "name": "pick_author",
                    "description": "Pick a new author to imitate. Use this function when a user asks for a new author",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "author": {
                                "type": "string",
                                "description": "The name of an author or storywriter that can be imitated",
                            }
                        },
                        "required": ["author"],
                    },
                },
                {
                    "name": "end_story",
                    "description": "End the story or conversation",
                    "parameters": {
                    },
                },
            ],
        },
        "speak": {"provider": {"type": "deepgram", "model": "aura-2-thalia-en"}},
        "greeting": "Hello.  My name is Sarah, would you like to hear a story?",
    },
}

MULTILINGUAL_AGENT_SETTINGS = {
    "type": "Settings",
    "audio": {
        "input": {"encoding": "linear16", "sample_rate": 44100},
        "output": {
            "encoding": "linear16",
            "sample_rate": 16000,
        },
    },
    "agent": {
        "listen": {"provider": {"model": "nova-3", "type": "deepgram"}},
        "language": "multi",
        "think": {
            "provider": {"model": "gpt-4o-mini", "type": "open_ai"},
            "prompt": "Your name is Sarah and you are a story teller who creates new stories given a specific theme",
            "functions": [
                {
                    "name": "pick_author",
                    "description": "Pick a new author to imitate. Use this function when a user asks for a new author",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "author": {
                                "type": "string",
                                "description": "The name of an author or storywriter that can be imitated",
                            }
                        },
                        "required": ["author"],
                    },
                },
                {
                    "name": "end_story",
                    "description": "End the story or conversation",
                    "parameters": {},
                },
            ],
        },
        "speak": {
            "provider": {"type": "eleven_labs", "model_id": "eleven_flash_v2_5"},
            "endpoint": {
                "url": "https://api.elevenlabs.io/v1/text-to-speech/bIHbv24MWmeRgasZH58o",
                "headers": {"xi-api-key": os.environ.get("ELEVENLABS_API_KEY")},
            },
        },
        "greeting": "Hello.  My name is Sarah, would you like to hear a story?",
    },
}
