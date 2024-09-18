let currentThreadId = null;
let currentAssistantId = null;
let currentAssistantName = null;

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
        currentAssistantName = event.target.options[event.target.selectedIndex].text;
        if (currentAssistantId) {
            chatContainer.innerHTML = ''; // Clear previous messages only when a new assistant is selected
            createNewThread();
            addMessageToChat('system', `You are now chatting with ${currentAssistantName}`);
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
                if (data.error) {
                    console.error('Error:', data.error);
                    addMessageToChat('system', 'Error: ' + data.error);
                } else {
                    const assistantMessages = data.messages.filter(msg => msg.role === 'assistant');
                    if (assistantMessages.length > 0) {
                        const latestMessage = assistantMessages[assistantMessages.length - 1];
                        addMessageToChat('assistant', latestMessage.content, true);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessageToChat('system', 'Error: Unable to send message');
            });
        }
    }

    function addMessageToChat(role, content, isReplacement = false) {
        if (isReplacement) {
            const existingAssistantMessages = chatContainer.querySelectorAll('.assistant-message');
            existingAssistantMessages.forEach(msg => msg.remove());
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${role}-message`);
        
        if (role === 'assistant') {
            messageElement.textContent = `${currentAssistantName}: ${content}`;
        } else {
            messageElement.textContent = content;
        }
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
