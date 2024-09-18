import time
from openai.types.beta import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.run import Run
from openai.types.beta.threads.message import Message
import logging

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
    while run.status not in ["completed", "failed", "cancelled"]:
        time.sleep(1)  # Wait for 1 second before checking again
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        logging.debug(f"Run status: {run.status}")
    
    logging.debug(f"Run completed with status: {run.status}")
    
    if run.status != "completed":
        logging.error(f"Run failed with status: {run.status}")
        raise Exception(f"Assistant run failed with status: {run.status}")
    
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
