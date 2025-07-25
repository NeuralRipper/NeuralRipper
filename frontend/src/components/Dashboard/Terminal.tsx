import { useRef, useEffect } from 'react';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

const StreamingTerminal = () => {
    const terminalRef = useRef<HTMLDivElement | null>(null);        // terminalRef.current, the <div> renders
    const terminalInstance = useRef<Terminal | null>(null);         // terminalInstance the actual Terminal object
    const inputBufferRef = useRef('');                              // temperoary storage of user input
    const isGeneratingRef = useRef(false);                          // Track if we are currently generating

    // Render terminal when component mounted
    useEffect(() => {
        const terminal = new Terminal({
            cursorBlink: true,
            fontSize: 15,
            theme: {
                background: '#0a0e1a',
                foreground: '#a855f7',    // main text color, refering to official docs
                cursor: '#fef08a',        // https://tailwindcss.com/docs/colors
            }
        });

        if (terminalRef.current) {
            terminal.open(terminalRef.current);
            terminalInstance.current = terminal;
            terminal.write("Welcome to the [Neural Ripper] Choom! I'm ur [Ripper Doc]!\r\n");
            terminal.write(`${yellow}>`)
        }

        // Handle input, use RGB codes to handle color diff for input/output
        terminal.onData((data) => {
            const charCode = data.charCodeAt(0);

            if (charCode === 13) { // 13 is Enter, call handler to get stream from backend
                handlePromptSubmission();
            } else if (charCode === 127) {                      // 127 is backspace
                if (inputBufferRef.current.length > 0) {
                    inputBufferRef.current = inputBufferRef.current.slice(0, -1)
                    terminal.write('\b \b')
                } 
            } else if (charCode >= 32 && charCode <= 126) {     // normal characters
                    inputBufferRef.current += data
                    terminal.write(`${yellow}` + data + '\x1b[0m');
            }
        })

        return () => {
            terminal.dispose();
        };
    }, []);

    const yellow = '\x1b[38;2;254;240;138m';
    const cyan = '\x1b[38;2;34;211;238m';

    // Handle prompt submission
    const handlePromptSubmission = async () => {
 
        const terminal = terminalInstance.current;
        if (!terminal || !inputBufferRef.current.trim()) {
            return;
        }
        
        // Show agent is generating
        isGeneratingRef.current = true;

        // Show that agent is thinking
        terminal.write(`\r\n${cyan}>Thinking...\r\n`);

        try {
            await streamRespond(inputBufferRef.current);
        } catch(error) {
            terminal.write(`\r\n${cyan}>Failed to get response from agent`)
            console.log(error);
        }   finally {
            isGeneratingRef.current = false;
            inputBufferRef.current = '';
            terminal.write(`\r\n${cyan}>`)
        }
    }

    const streamRespond = async (prompt: string) => {
        /*
            1. Make a fetch request to our streaming endpoint
            2. Get a ReadableStream from response.body
            3. Create a reader from the stream
            4. Read chunks continuously until done
            5. Display each chunk immediately as it arrives
            
            Key concepts:
            - ReadableStream: Browser API for handling streaming data
            - TextDecoder: Converts bytes to text
            - reader.read(): Returns {value, done} - value is the chunk, done indicates if stream ended
        */

        const terminal = terminalInstance.current;
        if (!terminal) {return;}

        // Fetch stream endpoint
        const response = await fetch("http://localhost:8000/infer/chat", {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'prompt': prompt})
        })

        if (!response.ok) {
            console.log("Fetch stream endpoint failed")
            return
        }
        
        // Get the readable stream from response body, which is a ReadableStream
        const reader = response.body?.getReader();
        if (!reader) {
            console.log('No reader available');
            return;
        }

        // Text decoder to convert bytes to string
        const decoder = new TextDecoder();

        while (true) {
            // Read next chunk of stream, async, will wait fro the next piece of data
            const { done, value } = await reader.read();
            
            // Reach the end of the stream
            if (done) {
                break;   
            }

            // Convert bytes to text
            const chunk = decoder.decode(value, {stream: true})

            // Write the chunk to terminal in real-time
            terminal.write(`${cyan} ${chunk}`)
        }

    }

    return (
        <div className="bg-slate-900 p-3 rounded-lg">
            <div ref={terminalRef}></div>
        </div>
    );
};

export default StreamingTerminal;
