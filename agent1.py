# agent1.py

from gemini import generate_response

class EventChatbotAgent:
    def __init__(self):
        self.system_prompt = """
        You are a smart and friendly AI assistant for a Student Event Management website.

        You can:
        - Explain events
        - Suggest events
        - Answer questions about categories
        - Help students decide what to join

        Keep responses:
        - Friendly
        - Short but helpful
        - Clear
        - Engaging

        Always speak like a helpful campus assistant.
        """

        # Conversation memory
        self.chat_history = []

    def chat(self, user_message: str):
        # Add user message to history
        self.chat_history.append(f"User: {user_message}")

        # Build full conversation context
        conversation = "\n".join(self.chat_history)

        prompt = f"""
        {self.system_prompt}

        Conversation so far:
        {conversation}

        Assistant:
        """

        response = generate_response(prompt)

        # Save assistant response in memory
        self.chat_history.append(f"Assistant: {response}")

        return response

    def reset_chat(self):
        self.chat_history = []