import { useState, useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

const EvalTerminal = () => {
  const [metrics, setMetrics] = useState({
    tokensPerSec: 847,
    ttft: 23,
    gpuUtil: 94,
    cost: 0.12,
    accuracy: 87.3,
    temp: 72,
    runtime: 8
  });
  
  const [benchmarks, setBenchmarks] = useState([
    { name: 'MMLU', progress: 87, current: 1847, total: 2122, status: 'done' },
    { name: 'HellaSwag', progress: 52, current: 1104, total: 2122, status: 'running' },
    { name: 'HumanEval', progress: 0, current: 0, total: 164, status: 'queued' },
    { name: 'TruthfulQA', progress: 0, current: 0, total: 817, status: 'queued' },
    { name: 'GSM8K', progress: 0, current: 0, total: 1319, status: 'queued' },
    { name: 'ARC', progress: 0, current: 0, total: 1172, status: 'queued' }
  ]);
  
  const [terminalLines, setTerminalLines] = useState([
    { type: 'system', text: '┌─ [NEURAL RIPPER] - AI Lab Terminal ───────────────────────────┐' },
    { type: 'system', text: '│ Model: llama-3.1-8b │ Provider: RunPod │ Status: Ready      │' },
    { type: 'divider', text: '└────────────────────────────────────────────────────────────────┘' },
  ]);
  
  const [currentInput, setCurrentInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const terminalEndRef = useRef(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLines]);

  // Simulate benchmark progress
  useEffect(() => {
    const interval = setInterval(() => {
      setBenchmarks(prev => prev.map(b => {
        if (b.status === 'running' && b.progress < 100) {
          const newProgress = Math.min(100, b.progress + Math.random() * 3);
          const newCurrent = Math.floor((newProgress / 100) * b.total);
          return { ...b, progress: newProgress, current: newCurrent };
        }
        return b;
      }));
      
      setMetrics(prev => ({
        ...prev,
        tokensPerSec: 820 + Math.random() * 60,
        cost: prev.cost + 0.001
      }));
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = () => {
    if (!currentInput.trim() || isGenerating) return;

    setTerminalLines(prev => [...prev, 
      { type: 'prompt', text: `> ${currentInput}` }
    ]);
    
    setIsGenerating(true);
    setCurrentInput('');

    const response = "Quantum computing leverages quantum mechanical phenomena like superposition and entanglement to process information in ways that classical computers cannot. Unlike classical bits that exist in either 0 or 1, qubits can exist in superposition of both states simultaneously.";
    
    let tokens = response.split(' ');
    let currentText = '';
    let tokenCount = 0;
    
    const streamInterval = setInterval(() => {
      if (tokenCount < tokens.length) {
        currentText += (tokenCount > 0 ? ' ' : '') + tokens[tokenCount];
        tokenCount++;
        
        setTerminalLines(prev => {
          const newLines = [...prev];
          const lastLine = newLines[newLines.length - 1];
          
          if (lastLine?.type === 'response') {
            newLines[newLines.length - 1] = { type: 'response', text: `🤖 ${currentText}` };
          } else {
            newLines.push({ type: 'response', text: `🤖 ${currentText}` });
          }
          return newLines;
        });
        
      } else {
        clearInterval(streamInterval);
        setIsGenerating(false);
        setTerminalLines(prev => [...prev, { type: 'empty', text: '' }]);
      }
    }, 80);
  };

  const renderProgressBar = (progress) => {
    const filled = Math.floor(progress / 5);
    const empty = 20 - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="border border-cyan-500/30 bg-slate-900/50 mb-4 p-4">
          <div className="flex items-center gap-3">
            <Terminal className="text-cyan-400" size={28} />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 text-transparent bg-clip-text">
              NEURAL RIPPER[In Construction, Coming Soon...]
            </h1>
            <span className="ml-auto text-cyan-400 text-sm font-mono">LLM EVAL LAB v0.0</span>
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
              <div className="text-gray-400 mb-1">╔═ Live Model Performance ═══════════════════════════════════════════╗</div>
              <div className="text-cyan-400">
                ║ Tokens/sec: <span className="text-yellow-400">{metrics.tokensPerSec.toFixed(0)}</span> ⚡ │ 
                TTFT: <span className="text-yellow-400">{metrics.ttft}ms</span> │ 
                GPU Util: <span className="text-yellow-400">{metrics.gpuUtil}%</span> │ 
                Cost: <span className="text-yellow-400">${metrics.cost.toFixed(2)}</span> 💰║
              </div>
              <div className="text-cyan-400">
                ║ Accuracy: <span className="text-yellow-400">{metrics.accuracy}%</span>    │ 
                Temp: <span className="text-yellow-400">{metrics.temp}°C</span>  │ 
                Provider: <span className="text-yellow-400">RunPod</span> │ 
                Runtime: <span className="text-yellow-400">{metrics.runtime}m</span>║
              </div>
              <div className="text-gray-400">╚═════════════════════════════════════════════════════════════════════╝</div>
            </div>
          </div>

          {/* Benchmarks */}
          <div className="border-t border-cyan-500/30 pt-3 mb-3">
            <div className="font-mono text-sm">
              <div className="text-gray-400 mb-1">╔═ Benchmark Results (Live) ═════════════════════════════════════════╗</div>
              {benchmarks.map((b, i) => (
                <div key={i} className="text-cyan-400">
                  ║ [<span className={
                    b.status === 'done' ? 'text-green-400' :
                    b.status === 'running' ? 'text-yellow-400' :
                    'text-gray-500'
                  }>{b.status === 'done' ? 'DONE' : b.status === 'running' ? 'RUN ' : 'WAIT'}</span>] {b.name.padEnd(11)}: {renderProgressBar(b.progress)} <span className="text-yellow-400">{b.progress.toFixed(1)}%</span> {b.status === 'done' || b.status === 'running' ? `(${b.current}/${b.total})` : 'queued'.padEnd(13)}      ║
                </div>
              ))}
              <div className="text-gray-400">╚═════════════════════════════════════════════════════════════════════╝</div>
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