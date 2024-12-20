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
    logging.debug(f"Created run: {run.id}")
    
    while run.status not in ["completed", "failed", "cancelled"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        logging.debug(f"Run status: {run.status}")
        
        if run.status == "requires_action":
            logging.debug(f"Run requires action: {run.required_action}")
            # Handle required actions here if needed
    
    logging.debug(f"Run completed with status: {run.status}")
    
    if run.status != "completed":
        logging.error(f"Run failed with status: {run.status}")
        raise Exception(f"Assistant run failed with status: {run.status}")
    
    # Add this check to ensure new messages are available
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    if not messages.data or messages.data[0].role != "assistant":
        logging.error("No new assistant message found after run completion")
        raise Exception("No new assistant message found after run completion")
    
    return run

def get_messages(client, thread_id: str):
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=10)
    logging.debug(f"Retrieved {len(messages.data)} messages from thread {thread_id}")
    
    formatted_messages = []
    seen_contents = set()
    
    for message in messages.data:
        content = message.content[0].text.value if message.content else ""
        if content not in seen_contents:
            formatted_messages.append({
                "role": message.role,
                "content": content
            })
            seen_contents.add(content)
    
    logging.debug(f"Formatted messages: {formatted_messages}")
    return formatted_messages
