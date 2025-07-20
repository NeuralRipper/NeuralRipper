import React, { useRef, useEffect } from 'react';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

const StreamingTerminal = () => {
  const terminalRef = useRef(null);

  useEffect(() => {
    const terminal = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      theme: {
        background: '#0a0e1a',
        foreground: '#e1e5f0'
      }
    });

    terminal.open(terminalRef.current);
    terminal.write('Hello Terminal!\r\n');

    return () => {
      terminal.dispose();
    };
  }, []);

  return (
    <div className="h-96 w-full bg-slate-900 p-4 rounded-lg">
      <div ref={terminalRef}></div>
    </div>
  );
};

export default StreamingTerminal;