import { useRef, useEffect, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

const LLMEvalTerminal = () => {
    const terminalRef = useRef<HTMLDivElement | null>(null);
    const terminalInstance = useRef<Terminal | null>(null);
    const inputBufferRef = useRef('');
    const isGeneratingRef = useRef(false);
    const wsRef = useRef<WebSocket | null>(null);
    const [wsConnected, setWsConnected] = useState(false);

    useEffect(() => {
        // Initialize terminal
        const terminal = new Terminal({
            cursorBlink: true,
            fontSize: 15,
            theme: {
                background: '#0a0e1a',
                foreground: '#a855f7',
                cursor: '#fef08a',
            }
        });

        if (terminalRef.current) {
            terminal.open(terminalRef.current);
            terminalInstance.current = terminal;
            terminal.write("Welcome to [Neural Ripper] LLM Eval Lab!\r\n");
            terminal.write("Connecting to evaluation backend...\r\n");
        }

        // Handle input
        terminal.onData((data) => {
            const charCode = data.charCodeAt(0);

            if (charCode === 13) { // Enter
                handlePromptSubmission();
            } else if (charCode === 127) { // Backspace
                if (inputBufferRef.current.length > 0) {
                    inputBufferRef.current = inputBufferRef.current.slice(0, -1);
                    terminal.write('\b \b');
                }
            } else if (charCode >= 32 && charCode <= 126) { // Normal characters
                inputBufferRef.current += data;
                terminal.write(`${yellow}${data}\x1b[0m`);
            }
        });

        // Initialize WebSocket
        initializeWebSocket();

        return () => {
            terminal.dispose();
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const initializeWebSocket = () => {
        const ws = new WebSocket('ws://localhost:8000/ws/eval');
        wsRef.current = ws;

        ws.onopen = () => {
            setWsConnected(true);
            const terminal = terminalInstance.current;
            if (terminal) {
                terminal.write(`${cyan}✓ Connected to backend\r\n`);
                terminal.write(`${yellow}> `);
            }
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const terminal = terminalInstance.current;
            if (!terminal) return;

            switch (data.type) {
                case 'response_chunk':
                    terminal.write(`${cyan}${data.chunk}`);
                    break;
                case 'response_complete':
                    isGeneratingRef.current = false;
                    terminal.write(`\r\n${yellow}> `);
                    break;
                case 'error':
                    terminal.write(`\r\n${red}Error: ${data.message}\r\n`);
                    isGeneratingRef.current = false;
                    terminal.write(`${yellow}> `);
                    break;
                case 'status':
                    terminal.write(`\r\n${cyan}[${data.message}]\r\n`);
                    break;
            }
        };

        ws.onclose = () => {
            setWsConnected(false);
            const terminal = terminalInstance.current;
            if (terminal) {
                terminal.write(`\r\n${red}✗ Connection lost. Reconnecting...\r\n`);
            }
            setTimeout(initializeWebSocket, 3000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    };

    const handlePromptSubmission = () => {
        const terminal = terminalInstance.current;
        if (!terminal || !inputBufferRef.current.trim() || isGeneratingRef.current) {
            return;
        }

        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            terminal.write(`\r\n${red}Not connected to backend\r\n`);
            terminal.write(`${yellow}> `);
            return;
        }

        isGeneratingRef.current = true;
        const prompt = inputBufferRef.current;
        inputBufferRef.current = '';

        terminal.write(`\r\n${cyan}🤖 `);

        // Send prompt via WebSocket
        wsRef.current.send(JSON.stringify({
            type: "chat",
            content: prompt
        }));
    };

    const yellow = '\x1b[38;2;254;240;138m';
    const cyan = '\x1b[38;2;34;211;238m';
    const red = '\x1b[38;2;239;68;68m';

    return (
        <div className="bg-slate-900 p-3 rounded-lg">
            <div ref={terminalRef} className="min-h-[400px]"></div>
            <div className="mt-2 flex justify-between text-xs text-gray-400">
                <span>Status: {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</span>
                <span>Backend: Prime Intellect</span>
            </div>
        </div>
    );
};

export default LLMEvalTerminal;