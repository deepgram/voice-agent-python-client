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
