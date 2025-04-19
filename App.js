import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');

  const lambdaEndpoint = 'https://pcb5eyhzc3332c4cv2ekxdxmpa0qjgts.lambda-url.us-east-1.on.aws/';

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    const newMessages = [...messages, { sender: 'user', text: userInput }];
    setMessages(newMessages);
    setUserInput('');

    try {
      const response = await fetch(lambdaEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_prompt: userInput,
          user_id: 'demo-user'
        })
      });

      const data = await response.json();
      setMessages([...newMessages, { sender: 'bot', text: data.ai_reply }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages([...newMessages, { sender: 'bot', text: 'Error contacting server.' }]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>{msg.text}</div>
        ))}
      </div>
      <div className="input-box">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
