/**
 * WebSocket Connection Manager Hook
 *
 * Provides WebSocket connection with auto-reconnect, message handling,
 * and state management for real-time pipeline updates.
 *
 * Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
 */
import { useEffect, useRef, useState, useCallback } from "react";

export interface WebSocketMessage {
  type:
    | "connected"
    | "status_update"
    | "assertion"
    | "error"
    | "clarification"
    | "completion"
    | "pong";
  timestamp?: string;
  agent_name?: string;
  status?: string;
  data?: any;
  assertion?: any;
  error?: string;
  question?: string;
  context?: any;
  result?: any;
  project_id?: string;
  message?: string;
}

export interface AgentStatus {
  name: string;
  status: "idle" | "started" | "completed" | "failed";
  executionTime?: number;
  summary?: any;
}

export interface UseWebSocketOptions {
  projectId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onStatusUpdate?: (agentName: string, status: string, data?: any) => void;
  onAssertion?: (assertion: any) => void;
  onError?: (error: string, agentName?: string) => void;
  onClarification?: (question: string, context?: any) => void;
  onCompletion?: (result: any) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  messages: WebSocketMessage[];
  agentStatuses: Record<string, AgentStatus>;
  sendMessage: (message: any) => void;
  clearMessages: () => void;
  reconnect: () => void;
}

/**
 * Custom hook for managing WebSocket connection to backend pipeline
 *
 * Features:
 * - Automatic connection on mount
 * - Auto-reconnect with exponential backoff
 * - Message type routing
 * - Agent status tracking
 * - Ping/pong heartbeat
 *
 * @param options WebSocket configuration options
 * @returns WebSocket state and control functions
 */
export const useWebSocket = (
  options: UseWebSocketOptions
): UseWebSocketReturn => {
  const {
    projectId,
    onMessage,
    onStatusUpdate,
    onAssertion,
    onError,
    onClarification,
    onCompletion,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<
    Record<string, AgentStatus>
  >({});

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Send a message through the WebSocket connection
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected. Message not sent:", message);
    }
  }, []);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // Add to messages list
        setMessages((prev) => [...prev, message]);

        // Call generic message handler
        if (onMessage) {
          onMessage(message);
        }

        // Route message based on type
        switch (message.type) {
          case "connected":
            console.log("WebSocket connected:", message.message);
            break;

          case "status_update":
            if (message.agent_name && message.status) {
              // Update agent status
              setAgentStatuses((prev) => ({
                ...prev,
                [message.agent_name!]: {
                  name: message.agent_name!,
                  status: message.status as any,
                  executionTime: message.data?.execution_time,
                  summary: message.data?.summary,
                },
              }));

              // Call status update handler
              if (onStatusUpdate) {
                onStatusUpdate(
                  message.agent_name,
                  message.status,
                  message.data
                );
              }
            }
            break;

          case "assertion":
            if (message.assertion && onAssertion) {
              onAssertion(message.assertion);
            }
            break;

          case "error":
            if (message.error && onError) {
              onError(message.error, message.agent_name);
            }
            break;

          case "clarification":
            if (message.question && onClarification) {
              onClarification(message.question, message.context);
            }
            break;

          case "completion":
            if (message.result && onCompletion) {
              onCompletion(message.result);
            }
            break;

          case "pong":
            // Heartbeat response received
            break;

          default:
            console.warn("Unknown message type:", message.type);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    },
    [
      onMessage,
      onStatusUpdate,
      onAssertion,
      onError,
      onClarification,
      onCompletion,
    ]
  );

  /**
   * Start ping/pong heartbeat
   */
  const startHeartbeat = useCallback(() => {
    // Clear existing interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    // Send ping every 30 seconds
    pingIntervalRef.current = setInterval(() => {
      sendMessage({ type: "ping" });
    }, 30000);
  }, [sendMessage]);

  /**
   * Stop ping/pong heartbeat
   */
  const stopHeartbeat = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Determine WebSocket URL based on current location
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.hostname;
      const port = import.meta.env.VITE_API_PORT || "8000";
      const wsUrl = `${protocol}//${host}:${port}/ws/generation/${projectId}`;

      console.log("Connecting to WebSocket:", wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        setIsConnected(false);
        stopHeartbeat();

        // Attempt to reconnect if enabled
        if (
          autoReconnect &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          const delay = Math.min(
            reconnectInterval * Math.pow(2, reconnectAttemptsRef.current),
            30000 // Max 30 seconds
          );

          console.log(
            `Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket connection:", error);
    }
  }, [
    projectId,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    handleMessage,
    startHeartbeat,
    stopHeartbeat,
  ]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Stop heartbeat
    stopHeartbeat();

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, [stopHeartbeat]);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect, disconnect]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    messages,
    agentStatuses,
    sendMessage,
    clearMessages,
    reconnect,
  };
};
