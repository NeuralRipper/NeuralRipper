import { useRef, useEffect } from 'react';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

const StreamingTerminal = () => {
  const terminalRef = useRef<HTMLDivElement | null>(null);       // terminalRef.current, the <div> renders
  const terminalInstance = useRef<Terminal | null>(null);       // terminalInstance the actual Terminal object
  const inputBufferRef = useRef('');                            // temperoary storage of user input

  // Render terminal when component mounted
  useEffect(() => {
    const terminal = new Terminal({
        cursorBlink: true,
        fontSize: 15,
        theme: {
            background: '#0a0e1a',
            foreground: '#e1e5f0'
        }
    });

    if (terminalRef.current) {
        terminal.open(terminalRef.current);
        terminalInstance.current = terminal;
        terminal.write("Welcome to the [Neural Ripper]! I'm ur [Ripper Doc] choom!\r\n");
    }

    // handle input
    terminal.onData((data) => {
        const charCode = data.charCodeAt(0);

        if (charCode === 13) { // 13 is Enter, write the input and refresh buffer
            terminal.write('\r\nYou typed: ' + inputBufferRef.current + '\r\n> ')
            inputBufferRef.current = ''
        } else if (charCode === 127) {                      // 127 is backspace
            if (inputBufferRef.current.length > 0) {
                inputBufferRef.current = inputBufferRef.current.slice(0, -1)
                terminal.write('\b \b')
            } 
        } else if (charCode >= 32 && charCode <= 126) {     // normal characters
                inputBufferRef.current += data
                terminal.write(data);
        }
    })

    return () => {
        terminal.dispose();
    };
  }, []);

  return (
    <div className="bg-slate-900 p-3 rounded-lg">
      <div ref={terminalRef}></div>
    </div>
  );
};

export default StreamingTerminal;
