import { useEffect, useState } from "react";

const Testws = () => {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [messages, setMessages] = useState<string[]>([]);
    const [inputValue, setInputValue] = useState("");

    useEffect(() => {
        const socket = new WebSocket('ws://localhost:8000/ws/eval');
        socket.onopen = () => console.log('Connected!');
        socket.onmessage = (e) => {
            console.log('Received:', e.data);
            setMessages(prev => [...prev, e.data]);
        };
        setWs(socket);
        return () => socket.close();
    }, []);

    const sendMessage = () => {
        if (ws && inputValue.trim()) {
            ws.send(JSON.stringify({
                type: "chat",
                content: inputValue
            }));
            setInputValue("");
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    };

    return (
        <div>
            <input 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type message..."
            />
            <button onClick={sendMessage}>Send Message</button>
            <div>
                {messages.map((msg, i) => <div key={i}>{msg}</div>)}
            </div>
        </div>
    );
}

export default Testws;