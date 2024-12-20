let currentThreadId = null;
let currentAssistantId = null;
let currentAssistantName = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');

    const assistantSelect = document.getElementById('assistant-select');
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const startButton = document.getElementById('start-button');
    const calculateBtn = document.getElementById('calculateBtn');
    const results = document.getElementById('results');
    const smsSimulatorBtn = document.getElementById('sms-simulator-btn');
    const revenueCalculatorBtn = document.getElementById('revenue-calculator-btn');
    const smsSimulator = document.getElementById('sms-simulator');
    const revenueCalculator = document.getElementById('revenue-calculator');

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

    assistantSelect.addEventListener('change', (event) => {
        currentAssistantId = event.target.value;
        currentAssistantName = event.target.options[event.target.selectedIndex].text;
        if (currentAssistantId) {
            chatContainer.innerHTML = '';
            createNewThread();
            startButton.disabled = false;
        } else {
            startButton.disabled = true;
        }
    });

    startButton.addEventListener('click', () => {
        console.log('Start button clicked');
        if (currentAssistantId) {
            console.log('Current assistant ID:', currentAssistantId);
            startButton.disabled = true;
            addMessageToChat('system', `You are now chatting with ${currentAssistantName}`);
            sendMessage('START');
        } else {
            console.log('No assistant selected');
            alert('Please select an assistant first.');
        }
    });

    sendButton.addEventListener('click', () => sendMessage());

    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    smsSimulatorBtn.addEventListener('click', () => {
        smsSimulator.style.display = 'block';
        revenueCalculator.style.display = 'none';
        smsSimulatorBtn.classList.add('active');
        revenueCalculatorBtn.classList.remove('active');
    });

    revenueCalculatorBtn.addEventListener('click', () => {
        smsSimulator.style.display = 'none';
        revenueCalculator.style.display = 'block';
        revenueCalculatorBtn.classList.add('active');
        smsSimulatorBtn.classList.remove('active');
    });

    calculateBtn.addEventListener('click', calculateRevenue);

    function createNewThread() {
        fetch('/create_thread', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                currentThreadId = data.thread_id;
                console.log('New thread created:', currentThreadId);
            });
    }

    function sendMessage(message = null) {
        console.log('sendMessage called with message:', message);
        const messageToSend = message || messageInput.value.trim();
        console.log('messageToSend:', messageToSend);
        console.log('currentThreadId:', currentThreadId);
        console.log('currentAssistantId:', currentAssistantId);
        if (messageToSend && currentThreadId && currentAssistantId) {
            if (messageToSend !== 'START') {
                addMessageToChat('user', messageToSend);
            }
            if (!message) {
                messageInput.value = '';
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;

            console.log('Sending message:', messageToSend);
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    thread_id: currentThreadId,
                    message: messageToSend,
                    assistant_id: currentAssistantId
                }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Received data from server:', data);
                if (data.error) {
                    console.error('Error:', data.error);
                    addMessageToChat('system', 'Error: ' + data.error);
                } else {
                    const lastMessage = data.message;
                    console.log('Last message:', lastMessage);
                    if (lastMessage && lastMessage.role === 'assistant') {
                        console.log('Adding assistant message to chat:', lastMessage.content);
                        addMessageToChat('assistant', lastMessage.content);
                    } else {
                        console.log('No assistant message found in the response');
                    }
                }
                chatContainer.scrollTop = chatContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error:', error);
                addMessageToChat('system', 'Error: Unable to send message');
            });
        } else {
            console.log('Message not sent. Check values:', { messageToSend, currentThreadId, currentAssistantId });
        }
        messageInput.focus();
    }

    function addMessageToChat(role, content) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${role}-message`);
        
        if (role === 'assistant') {
            const formattedContent = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
            messageElement.innerHTML = formattedContent;
        } else if (role === 'user') {
            messageElement.textContent = `You: ${content}`;
        } else {
            messageElement.textContent = content;
        }
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function calculateRevenue(event) {
        event.preventDefault();
        console.log('Calculate button clicked');

        const numLeads = parseFloat(document.getElementById('numLeads').value);
        const leadAge = document.getElementById('leadAge').value;
        const closeRate = parseFloat(document.getElementById('closeRate').value) / 100;
        const avgRevenue = parseFloat(document.getElementById('avgRevenue').value);

        console.log('Parsed input values:', { numLeads, leadAge, closeRate, avgRevenue });

        if (isNaN(numLeads) || isNaN(closeRate) || isNaN(avgRevenue)) {
            console.error('Invalid input values detected');
            alert('Please enter valid numbers for all fields.');
            return;
        }

        let appointmentRate;
        switch (leadAge) {
            case 'less7':
                appointmentRate = 0.3;
                break;
            case '7to30':
                appointmentRate = 0.2;
                break;
            case '30to90':
                appointmentRate = 0.1;
                break;
            case 'more90':
                appointmentRate = 0.05;
                break;
            default:
                appointmentRate = 0.1;
        }

        console.log('Appointment rate:', appointmentRate);

        const appointmentsScheduled = Math.round(numLeads * appointmentRate);
        const potentialRevenue = appointmentsScheduled * closeRate * avgRevenue;

        console.log('Calculated values:', { appointmentsScheduled, potentialRevenue });

        document.getElementById('appointmentsScheduled').textContent = `Appointments Scheduled: ${appointmentsScheduled.toLocaleString()}`;
        document.getElementById('potentialRevenue').textContent = `Potential Revenue: $${potentialRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        results.style.display = 'block';
    }
});
