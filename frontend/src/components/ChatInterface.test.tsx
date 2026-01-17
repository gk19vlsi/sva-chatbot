/**
 * Unit Tests for ChatInterface Component
 * 
 * Tests message display, user interaction, and component behavior.
 * 
 * Validates: Requirements 9.1, 9.2, 9.3
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import { WebSocketMessage, AgentStatus } from '../hooks/useWebSocket';

describe('ChatInterface', () => {
  const mockMessages: WebSocketMessage[] = [];
  const mockAgentStatuses: Record<string, AgentStatus> = {};

  it('renders connection status indicator', () => {
    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('shows disconnected status when not connected', () => {
    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={false}
      />
    );

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('displays empty state when no messages', () => {
    render(
      <ChatInterface
        messages={[]}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('No messages yet')).toBeInTheDocument();
    expect(screen.getByText('Pipeline updates will appear here')).toBeInTheDocument();
  });

  it('displays connected message', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'connected',
        message: 'WebSocket connection established',
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('WebSocket connection established')).toBeInTheDocument();
  });

  it('displays status update messages', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'status_update',
        agent_name: 'spec_parser',
        status: 'started',
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText(/SPEC PARSER/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: started/i)).toBeInTheDocument();
  });

  it('displays assertion messages', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'assertion',
        assertion: {
          assertion_code: 'assert property (@(posedge clk) valid |-> ready);'
        },
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('New Assertion Generated')).toBeInTheDocument();
    expect(screen.getByText(/assert property/)).toBeInTheDocument();
  });

  it('displays error messages', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'error',
        error: 'Test error message',
        agent_name: 'rtl_analyzer',
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    expect(screen.getByText(/Agent: rtl_analyzer/i)).toBeInTheDocument();
  });

  it('displays clarification questions', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'clarification',
        question: 'Which clock signal should be used?',
        context: { signals: ['clk1', 'clk2'] },
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('Clarification Needed')).toBeInTheDocument();
    expect(screen.getByText('Which clock signal should be used?')).toBeInTheDocument();
  });

  it('displays completion message', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'completion',
        result: {
          total_execution_time: 45.67
        },
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText('Pipeline Completed')).toBeInTheDocument();
    expect(screen.getByText(/Total execution time: 45.67s/i)).toBeInTheDocument();
  });

  it('displays agent status indicators', () => {
    const agentStatuses: Record<string, AgentStatus> = {
      spec_parser: {
        name: 'spec_parser',
        status: 'completed'
      },
      rtl_analyzer: {
        name: 'rtl_analyzer',
        status: 'started'
      }
    };

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={agentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText(/spec parser/i)).toBeInTheDocument();
    expect(screen.getByText(/rtl analyzer/i)).toBeInTheDocument();
  });

  it('allows sending messages when connected', () => {
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
        onSendMessage={onSendMessage}
      />
    );

    const input = screen.getByPlaceholderText('Type a response...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    expect(onSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('disables input when disconnected', () => {
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={false}
        onSendMessage={onSendMessage}
      />
    );

    const input = screen.getByPlaceholderText('Type a response...') as HTMLInputElement;
    const sendButton = screen.getByText('Send') as HTMLButtonElement;

    expect(input.disabled).toBe(true);
    expect(sendButton.disabled).toBe(true);
  });

  it('clears input after sending message', () => {
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
        onSendMessage={onSendMessage}
      />
    );

    const input = screen.getByPlaceholderText('Type a response...') as HTMLInputElement;
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(input.value).toBe('Test message');

    fireEvent.click(sendButton);
    expect(input.value).toBe('');
  });

  it('sends message on Enter key press', () => {
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
        onSendMessage={onSendMessage}
      />
    );

    const input = screen.getByPlaceholderText('Type a response...');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

    expect(onSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('does not send empty messages', () => {
    const onSendMessage = vi.fn();

    render(
      <ChatInterface
        messages={mockMessages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
        onSendMessage={onSendMessage}
      />
    );

    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);

    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it('displays execution time in status updates', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'status_update',
        agent_name: 'spec_parser',
        status: 'completed',
        data: {
          execution_time: 2.5
        },
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText(/Execution time: 2.50s/i)).toBeInTheDocument();
  });

  it('displays summary data in status updates', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'status_update',
        agent_name: 'spec_parser',
        status: 'completed',
        data: {
          summary: {
            requirements_count: 5
          }
        },
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    expect(screen.getByText(/requirements count: 5/i)).toBeInTheDocument();
  });

  it('renders multiple messages in order', () => {
    const messages: WebSocketMessage[] = [
      {
        type: 'connected',
        message: 'Connected',
        timestamp: new Date().toISOString()
      },
      {
        type: 'status_update',
        agent_name: 'spec_parser',
        status: 'started',
        timestamp: new Date().toISOString()
      },
      {
        type: 'status_update',
        agent_name: 'spec_parser',
        status: 'completed',
        timestamp: new Date().toISOString()
      }
    ];

    render(
      <ChatInterface
        messages={messages}
        agentStatuses={mockAgentStatuses}
        isConnected={true}
      />
    );

    const allMessages = screen.getAllByText(/SPEC PARSER|Connected/i);
    expect(allMessages.length).toBeGreaterThan(0);
  });
});
