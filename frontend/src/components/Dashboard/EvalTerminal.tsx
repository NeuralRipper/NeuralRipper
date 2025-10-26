import { useState, useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import { useEvalWebSocket } from '../../hooks/useEvalWebSocket';
import type { MetricsState, Benchmark, TerminalLine, TokenTracking } from '../../types/eval';
import { getPerformanceMetrics, calculateAccumulatedCost } from '../../utils/metrics';
import { renderProgressBar, getStatusDisplay } from '../../utils/benchmarks';

const EvalTerminal = () => {
  // State with proper types (reset to null/empty)
  const [metrics, setMetrics] = useState<MetricsState | null>(null);
  const [benchmarks] = useState<Benchmark[]>([
    { name: 'MMLU', progress: 0, current: 0, total: 14042, status: 'queued' },
    { name: 'HellaSwag', progress: 0, current: 0, total: 10042, status: 'queued' },
    { name: 'HumanEval', progress: 0, current: 0, total: 164, status: 'queued' },
    { name: 'TruthfulQA', progress: 0, current: 0, total: 817, status: 'queued' },
    { name: 'GSM8K', progress: 0, current: 0, total: 1319, status: 'queued' },
    { name: 'ARC', progress: 0, current: 0, total: 1172, status: 'queued' },
  ]);
  const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
    { type: 'system', text: '┌─ [NEURAL RIPPER] - AI Lab Terminal ───────────────────────────┐' },
    { type: 'system', text: '│ Model: qwen │ Provider: Modal │ Status: Ready              │' },
    { type: 'divider', text: '└────────────────────────────────────────────────────────────────┘' },
  ]);

  const [currentInput, setCurrentInput] = useState('');
  const [currentModel] = useState('qwen'); // Default model
  const [tokenTracking, setTokenTracking] = useState<TokenTracking>({
    startTime: null,
    firstTokenTime: null,
    tokenCount: 0,
    lastTokenTime: null,
  });

  const terminalEndRef = useRef<HTMLDivElement>(null);
  const responseTextRef = useRef<string>('');
  const processedMessagesCountRef = useRef<number>(0);
  const tokenTrackingRef = useRef<TokenTracking>(tokenTracking);

  // WebSocket connection
  const { sendMessage, messages, connectionStatus, isGenerating, clearMessages } = useEvalWebSocket();

  // Keep ref in sync with state
  useEffect(() => {
    tokenTrackingRef.current = tokenTracking;
  }, [tokenTracking]);

  // Auto-scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLines]);

  // Process WebSocket messages (only NEW messages)
  useEffect(() => {
    // Only process new messages that we haven't seen before
    const newMessages = messages.slice(processedMessagesCountRef.current);

    newMessages.forEach((msg) => {
      // Handle token
      if ('token' in msg) {
        const token = msg.token;
        responseTextRef.current += token;

        // Track first token time
        if (tokenTracking.firstTokenTime === null && tokenTracking.startTime !== null) {
          setTokenTracking(prev => ({
            ...prev,
            firstTokenTime: Date.now(),
          }));
        }

        // Increment token count
        setTokenTracking(prev => ({
          ...prev,
          tokenCount: prev.tokenCount + 1,
          lastTokenTime: Date.now(),
        }));

        // Update terminal with streaming text
        setTerminalLines(prev => {
          const newLines = [...prev];
          const lastLine = newLines[newLines.length - 1];

          if (lastLine?.type === 'response') {
            // Update existing response line
            newLines[newLines.length - 1] = {
              type: 'response',
              text: responseTextRef.current,
            };
          } else {
            // Create new response line
            newLines.push({
              type: 'response',
              text: responseTextRef.current,
            });
          }
          return newLines;
        });
      }

      // Handle completion
      if ('done' in msg && msg.done) {
        console.log('Generation completed - resetting state');
        setTerminalLines(prev => [...prev, { type: 'empty', text: '' }]);
        responseTextRef.current = ''; // Reset for next message

        // Reset token tracking for next generation
        setTokenTracking({
          startTime: null,
          firstTokenTime: null,
          tokenCount: 0,
          lastTokenTime: null,
        });

        // Clear messages to prevent memory leak
        clearMessages();
        processedMessagesCountRef.current = 0;
      }

      // Handle error
      if ('error' in msg) {
        setTerminalLines(prev => [
          ...prev,
          { type: 'error', text: `Error: ${msg.error}` },
          { type: 'empty', text: '' },
        ]);
        responseTextRef.current = '';

        // Reset token tracking on error
        setTokenTracking({
          startTime: null,
          firstTokenTime: null,
          tokenCount: 0,
          lastTokenTime: null,
        });

        // Clear messages on error
        clearMessages();
        processedMessagesCountRef.current = 0;
      }
    });

    // Update the count of processed messages
    processedMessagesCountRef.current = messages.length;
  }, [messages, clearMessages]);

  // Update metrics in real-time based on token tracking
  useEffect(() => {
    if (tokenTracking.startTime) {
      const interval = setInterval(() => {
        // Use ref to get latest values without restarting interval
        const tracking = tokenTrackingRef.current;

        if (tracking.tokenCount === 0) return; // Skip if no tokens yet

        const perfMetrics = getPerformanceMetrics(
          tracking.tokenCount,
          tracking.startTime!,
          tracking.firstTokenTime || 0
        );

        // Calculate total cost based on total token count (not incremental)
        const totalCost = calculateAccumulatedCost(
          0, // Start from 0
          tracking.tokenCount, // Total tokens so far
          currentModel
        );

        setMetrics({
          tokensPerSec: perfMetrics.tokensPerSec,
          ttft: perfMetrics.ttft,
          runtime: perfMetrics.runtime,
          cost: totalCost,
          gpuUtil: 0, // TODO: Get from backend
          temp: 0,    // TODO: Get from backend
          accuracy: 0, // TODO: Calculate from benchmarks
        });
      }, 500); // Update every 500ms

      return () => clearInterval(interval);
    }
  }, [tokenTracking.startTime, currentModel]);

  const handleSubmit = () => {
    if (!currentInput.trim() || isGenerating) return;

    // Add user prompt to terminal
    setTerminalLines(prev => [...prev, { type: 'prompt', text: `> ${currentInput}` }]);

    // Initialize token tracking
    setTokenTracking({
      startTime: Date.now(),
      firstTokenTime: null,
      tokenCount: 0,
      lastTokenTime: null,
    });

    // Send message to WebSocket
    sendMessage({
      model: currentModel,
      prompt: currentInput,
    });

    setCurrentInput('');
  };

  // Connection status color
  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400';
      case 'connecting': return 'text-yellow-400';
      case 'reconnecting': return 'text-orange-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="border border-cyan-500/30 bg-slate-900/50 mb-4 p-4">
          <div className="flex items-center gap-3">
            <Terminal className="text-cyan-400" size={28} />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 text-transparent bg-clip-text">
              NEURAL RIPPER
            </h1>
            <span className="ml-auto text-cyan-400 text-sm font-mono">LLM EVAL LAB v0.1</span>
            <span className={`text-xs font-mono ${getConnectionColor()}`}>
              [{connectionStatus.toUpperCase()}]
            </span>
          </div>
        </div>

        {/* Main Terminal */}
        <div className="border border-cyan-500/30 bg-slate-900/50 p-4">
          {/* Chat Area */}
          <div className="font-mono text-sm space-y-1 mb-4" style={{ height: '350px', overflowY: 'auto' }}>
            {terminalLines.map((line, i) => (
              <div key={i} className={
                line.type === 'system' ? 'text-gray-400' :
                line.type === 'prompt' ? 'text-yellow-400' :
                line.type === 'response' ? 'text-cyan-400' :
                line.type === 'divider' ? 'text-gray-600' :
                line.type === 'empty' ? 'h-2' : ''
              }>
                {line.text}
                {line.type === 'response' && isGenerating && i === terminalLines.length - 1 && (
                  <span className="animate-pulse">▊</span>
                )}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Live Metrics */}
          <div className="border-t border-cyan-500/30 pt-3 mb-3">
            <div className="font-mono text-sm">
            {/* Use span to combine multiple lines into same line applied with different className */}
              <div className="mb-1">    
                <span className="text-cyan-400">╔══════════════════════ </span>
                <span className="text-yellow-400">Live Model Performance</span>
                <span className="text-cyan-400"> ═══════════════════════╗</span>
              </div>

              <div className="text-cyan-400 text-center">
                Tokens/sec: <span className="text-yellow-400">{metrics?.tokensPerSec.toFixed(0) || '0'}</span> │
                TTFT: <span className="text-yellow-400">{metrics?.ttft.toFixed(0) || '0'}ms</span> │
                GPU Util: <span className="text-yellow-400">{metrics?.gpuUtil || '0'}%</span> │
                Cost: <span className="text-yellow-400">${metrics?.cost.toFixed(4) || '0.0000'}</span>
              </div>
              <div className="text-cyan-400 text-center">
                Accuracy: <span className="text-yellow-400">{metrics?.accuracy || '0'}%</span>    │
                Temp: <span className="text-yellow-400">{metrics?.temp || '0'}°C</span>  │
                Provider: <span className="text-yellow-400">Modal</span> │
                Runtime: <span className="text-yellow-400">{metrics?.runtime.toFixed(1) || '0.0'}m</span>
              </div>
              <div className="text-cyan-400">╚═════════════════════════════════════════════════════════════════════╝</div>
            </div>
          </div>

          {/* Benchmarks */}
          <div className="border-t border-cyan-500/30 pt-3 mb-3">
            <div className="font-mono text-sm">
              <div className="text-gray-400 mb-1">╔═ Evaluation Benchmarks [COMING SOON] ═══════════════════════════╗</div>
              {benchmarks.map((b, i) => (
                <div key={i} className="text-gray-500">
                  ║ [<span className="text-gray-600">IDLE</span>] {b.name.padEnd(11)}: {renderProgressBar(0)} <span className="text-gray-600">0.0%</span> ({b.total} samples)
                </div>
              ))}
              <div className="text-gray-400">╚═════════════════════════════════════════════════════════════════╝</div>
            </div>
          </div>

          {/* Input */}
          <div className="border-t border-cyan-500/30 pt-3 flex items-center gap-2">
            <span className="text-yellow-400 font-mono">{'>'}</span>
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              disabled={isGenerating}
              placeholder="Enter your prompt..."
              className="flex-1 bg-transparent text-yellow-400 font-mono outline-none disabled:opacity-50"
            />
            {isGenerating && (
              <span className="text-cyan-400 text-xs animate-pulse">GENERATING...</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvalTerminal;