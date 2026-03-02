import { useState, useEffect, useRef } from 'react';
import type {
  WSMessageSend,
  WSMessageReceive,
  ConnectionStatus
} from '../types/eval';

const WS_URL = 'ws://localhost:8000/ws/eval';

interface UseEvalWebSocketReturn {
  sendMessage: (message: WSMessageSend) => void;
  messages: WSMessageReceive[];
  connectionStatus: ConnectionStatus;
  isGenerating: boolean;
  clearMessages: () => void;
}

export const useEvalWebSocket = (): UseEvalWebSocketReturn => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [isGenerating, setIsGenerating] = useState(false);
  const [messages, setMessages] = useState<WSMessageReceive[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  // Connect to WebSocket on mount
  useEffect(() => {
    console.log('Connecting to WebSocket...');
    setConnectionStatus('connecting');

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessageReceive = JSON.parse(event.data);
        console.log('Received message:', data);

        // Add message to array
        setMessages(prev => [...prev, data]);

        // Update generating status
        if ('done' in data && data.done) {
          console.log('Done signal received - setting isGenerating to false');
          setIsGenerating(false);
        }
        if ('error' in data) {
          console.log('Error received - setting isGenerating to false');
          setIsGenerating(false);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setMessages(prev => [...prev, { error: 'Failed to parse message from server' }]);
        setIsGenerating(false);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
      setMessages(prev => [...prev, { error: 'WebSocket connection error' }]);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
      setIsGenerating(false);
    };

    wsRef.current = ws;

    // Cleanup on unmount
    return () => {
      console.log('Closing WebSocket connection');
      ws.close();
      wsRef.current = null;
    };
  }, []); // Empty array = run once on mount

  // Send message to WebSocket
  const sendMessage = (message: WSMessageSend) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      setMessages(prev => [...prev, { error: 'Not connected to server' }]);
      return;
    }

    try {
      console.log('Sending message:', message, '- setting isGenerating to true');
      wsRef.current.send(JSON.stringify(message));
      setIsGenerating(true);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, { error: 'Failed to send message to server' }]);
    }
  };

  // Clear messages (useful for resetting terminal)
  const clearMessages = () => {
    setMessages([]);
  };

  return {
    sendMessage,
    messages,
    connectionStatus,
    isGenerating,
    clearMessages,
  };
};
