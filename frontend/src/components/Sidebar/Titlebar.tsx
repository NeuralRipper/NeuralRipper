import {Brain} from "lucide-react";

const Titlebar = () => {
    return (
        <header className="border border-gray-800 bg-gray-900/30">
            <div className="px-6 py-4">
                <div className="flex items-center gap-3">
                    <Brain className="text-cyan-400"/>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 text-transparent bg-clip-text">
                        NEURAL RIPPER
                    </h1>
                </div>
            </div>
        </header>
    )
}

export default Titlebar;