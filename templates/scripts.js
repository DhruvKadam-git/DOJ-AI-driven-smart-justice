// JavaScript to handle chat form submission and interaction with the Flask backend
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent the default form submission

        const userMessage = messageInput.value.trim(); // Get the user's message
        if (userMessage) {
            // Create and append user message element
            const userMessageElement = document.createElement('div');
            userMessageElement.className = 'message user';
            userMessageElement.textContent = userMessage;
            messagesContainer.appendChild(userMessageElement);

            // Clear input field
            messageInput.value = '';

            // Scroll to the bottom to show the latest message
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Send message to Flask backend
            try {
                const response = await fetch('/chat', {  // Ensure this URL matches your Flask route
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: userMessage })
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok.');
                }

                const data = await response.json();
                const botMessageElement = document.createElement('div');
                botMessageElement.className = 'message bot';
                botMessageElement.textContent = data.response || 'No response from bot.';
                messagesContainer.appendChild(botMessageElement);

                // Scroll to the bottom to show the latest message
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } catch (error) {
                console.error('Error fetching response:', error);
                const errorMessageElement = document.createElement('div');
                errorMessageElement.className = 'message bot';
                errorMessageElement.textContent = 'Sorry, there was an error processing your request.';
                messagesContainer.appendChild(errorMessageElement);
                
                // Scroll to the bottom to show the latest message
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
    });
});
