telegram_callback = {
    "type": "object",
    "properties": {
        "message": {
            "type": "object",
            "properties": {
                "chat": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number"},
                        "type": {"enum": ["group", "private", "supergroup"]},
                        "title": {"type": "string"},
                        "username": {"type": "string"}
                    },
                    "required": ["id", "type"]
                },
                "text": {"type": "string"}
            },
            "required": ["chat", "text"]
        }
    },
    "required": ["message"]
}
