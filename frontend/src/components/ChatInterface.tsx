/**
 * ChatInterface Component
 * 
 * Displays agent status messages, processing progress, clarification questions,
 * and allows user responses during pipeline execution.
 * 
 * Validates: Requirements 9.1, 9.2, 9.3
 */
import React, { useState, useRef, useEffect } from 'react';
import { WebSocketMessage, AgentStatus } from '../hooks/useWebSocket';

export interface ChatInterfaceProps {
  messages: WebSocketMessage[];
  agentStatuses: Record<string, AgentStatus>;
  isConnected: boolean;
  onSendMessage?: (message: string) => void;
}

/**
 * ChatInterface component for displaying real-time pipeline updates
 * 
 * Features:
 * - Display agent status messages with timestamps
 * - Show processing progress with visual indicators
 * - Display clarification questions
 * - Allow user to respond to clarifications
 * - Auto-scroll to latest messages
 * - Connection status indicator
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  agentStatuses,
  isConnected,
  onSendMessage
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  /**
   * Handle sending a message
   */
  const handleSend = () => {
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /**
   * Get status icon based on agent status
   */
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'started':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '⏸️';
    }
  };

  /**
   * Get status color based on agent status
   */
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'started':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  /**
   * Render a single message
   */
  const renderMessage = (message: WebSocketMessage, index: number) => {
    const timestamp = formatTimestamp(message.timestamp);

    switch (message.type) {
      case 'connected':
        return (
          <div key={index} className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <span className="text-green-600 mr-2">🔗</span>
              <span className="text-sm text-green-800">{message.message}</span>
              {timestamp && <span className="ml-auto text-xs text-green-600">{timestamp}</span>}
            </div>
          </div>
        );

      case 'status_update':
        const statusIcon = getStatusIcon(message.status || '');
        const statusColor = getStatusColor(message.status || '');
        return (
          <div key={index} className="mb-4 p-3 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="flex items-start">
              <span className="mr-2">{statusIcon}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">
                    {message.agent_name?.replace('_', ' ').toUpperCase()}
                  </span>
                  {timestamp && <span className="text-xs text-gray-500">{timestamp}</span>}
                </div>
                <div className={`text-sm ${statusColor} mt-1`}>
                  Status: {message.status}
                </div>
                {message.data?.execution_time && (
                  <div className="text-xs text-gray-600 mt-1">
                    Execution time: {message.data.execution_time.toFixed(2)}s
                  </div>
                )}
                {message.data?.summary && (
                  <div className="text-xs text-gray-700 mt-2 p-2 bg-gray-50 rounded">
                    {Object.entries(message.data.summary).map(([key, value]) => (
                      <div key={key}>
                        {key.replace(/_/g, ' ')}: {String(value)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'assertion':
        return (
          <div key={index} className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start">
              <span className="text-blue-600 mr-2">📝</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-900">New Assertion Generated</span>
                  {timestamp && <span className="text-xs text-blue-600">{timestamp}</span>}
                </div>
                {message.assertion && (
                  <pre className="text-xs text-gray-800 mt-2 p-2 bg-white rounded overflow-x-auto">
                    {message.assertion.assertion_code}
                  </pre>
                )}
              </div>
            </div>
          </div>
        );

      case 'error':
        return (
          <div key={index} className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <span className="text-red-600 mr-2">⚠️</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-red-900">Error</span>
                  {timestamp && <span className="text-xs text-red-600">{timestamp}</span>}
                </div>
                {message.agent_name && (
                  <div className="text-sm text-red-700 mt-1">
                    Agent: {message.agent_name}
                  </div>
                )}
                <div className="text-sm text-red-800 mt-2">
                  {message.error}
                </div>
              </div>
            </div>
          </div>
        );

      case 'clarification':
        return (
          <div key={index} className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start">
              <span className="text-yellow-600 mr-2">❓</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-yellow-900">Clarification Needed</span>
                  {timestamp && <span className="text-xs text-yellow-600">{timestamp}</span>}
                </div>
                <div className="text-sm text-yellow-800 mt-2">
                  {message.question}
                </div>
                {message.context && (
                  <div className="text-xs text-yellow-700 mt-2 p-2 bg-yellow-100 rounded">
                    Context: {JSON.stringify(message.context, null, 2)}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'completion':
        return (
          <div key={index} className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start">
              <span className="text-green-600 mr-2">🎉</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-green-900">Pipeline Completed</span>
                  {timestamp && <span className="text-xs text-green-600">{timestamp}</span>}
                </div>
                {message.result && (
                  <div className="text-sm text-green-800 mt-2">
                    Total execution time: {message.result.total_execution_time?.toFixed(2)}s
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header with connection status */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Pipeline Monitor</h2>
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Agent status indicators */}
      {Object.keys(agentStatuses).length > 0 && (
        <div className="p-4 bg-white border-b border-gray-200">
          <div className="flex flex-wrap gap-2">
            {Object.values(agentStatuses).map((agent) => (
              <div
                key={agent.name}
                className="flex items-center px-3 py-1 bg-gray-100 rounded-full text-sm"
              >
                <span className="mr-1">{getStatusIcon(agent.status)}</span>
                <span className={getStatusColor(agent.status)}>
                  {agent.name.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages container */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <p className="text-lg mb-2">No messages yet</p>
              <p className="text-sm">Pipeline updates will appear here</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => renderMessage(message, index))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area for responses */}
      {onSendMessage && (
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a response..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!isConnected}
            />
            <button
              onClick={handleSend}
              disabled={!isConnected || !inputValue.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
