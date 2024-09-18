let currentThreadId = null;
let currentAssistantId = null;

document.addEventListener('DOMContentLoaded', () => {
    const assistantSelect = document.getElementById('assistant-select');
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // Fetch assistants and populate the dropdown
    fetch('/get_assistants')
        .then(response => response.json())
        .then(assistants => {
            assistantSelect.innerHTML = '<option value="">Select an assistant</option>';
            assistants.forEach(assistant => {
                const option = document.createElement('option');
                option.value = assistant.id;
                option.textContent = assistant.name;
                assistantSelect.appendChild(option);
            });
        });

    // Handle assistant selection
    assistantSelect.addEventListener('change', (event) => {
        currentAssistantId = event.target.value;
        if (currentAssistantId) {
            chatContainer.innerHTML = ''; // Clear previous messages
            createNewThread();
        }
    });

    // Handle send button click
    sendButton.addEventListener('click', sendMessage);

    // Handle enter key press in message input
    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    function createNewThread() {
        fetch('/create_thread', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                currentThreadId = data.thread_id;
            });
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && currentThreadId && currentAssistantId) {
            addMessageToChat('user', message);
            messageInput.value = '';

            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    thread_id: currentThreadId,
                    message: message,
                    assistant_id: currentAssistantId
                }),
            })
            .then(response => response.json())
            .then(data => {
                data.messages.forEach(msg => {
                    if (msg.role !== 'user') {
                        addMessageToChat('assistant', msg.content[0].text.value);
                    }
                });
            });
        }
    }

    function addMessageToChat(role, content) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${role}-message`);
        messageElement.textContent = content;
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
