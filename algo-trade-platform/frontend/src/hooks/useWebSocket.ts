import { useEffect, useRef, useState } from 'react';

interface WebSocketOptions {
  onOpen?: () => void;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export const useWebSocket = (url: string, options: WebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const {
    onOpen,
    onMessage,
    onError,
    onClose,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options;

  const connect = () => {
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.onerror = (event) => {
        setError('WebSocket connection error');
        onError?.(event);
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        onClose?.();
        
        // Attempt to reconnect
        if (reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
      
      wsRef.current = ws;
    } catch (err) {
      setError('Failed to create WebSocket connection');
      console.error('WebSocket connection error:', err);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  const sendMessage = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [url]);

  return {
    isConnected,
    error,
    sendMessage,
    disconnect
  };
};