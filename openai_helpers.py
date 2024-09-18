from openai.types.beta import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.run import Run
from openai.types.beta.threads.message import Message

def get_assistants(client):
    assistants = client.beta.assistants.list(order="desc", limit=20)
    return [{"id": assistant.id, "name": assistant.name} for assistant in assistants.data]

def create_thread(client) -> Thread:
    return client.beta.threads.create()

def add_message_to_thread(client, thread_id: str, message: str) -> Message:
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

def run_assistant(client, thread_id: str, assistant_id: str) -> Run:
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    # Wait for the run to complete
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    return run

def get_messages(client, thread_id: str):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return [
        {
            "role": message.role,
            "content": message.content[0].text.value if message.content else ""
        }
        for message in reversed(messages.data)  # Reverse the order here
    ]
