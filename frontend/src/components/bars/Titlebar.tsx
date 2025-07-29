import {Brain} from "lucide-react";

const Titlebar = ({ onPageChange }) => {

    return (
        <header className="border border-gray-800 bg-gray-900/30">
            <div className="px-6 py-4">
                <div className="flex items-center gap-3">
                    <Brain className="text-cyan-400"/>
                    <h1 onClick={() => onPageChange('home')} className="cursor-pointer text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 text-transparent bg-clip-text">
                        NEURAL RIPPER
                    </h1>

                    <div className="ml-auto flex gap-6">
                        {/* <h2 onClick={() => onPageChange("echo")} className="cursor-pointer font-bold bg-gradient-to-r from-purple-500 to-cyan-400 text-transparent bg-clip-text">
                            Echo
                        </h2>
                        <h2 onClick={() => onPageChange('infer')} className="cursor-pointer font-bold bg-gradient-to-r from-purple-500 to-cyan-400 text-transparent bg-clip-text">
                            Infer
                        </h2> */}
                        <h2 onClick={() => onPageChange('about')} className="cursor-pointer font-bold bg-gradient-to-r  from-purple-500 to-cyan-400 text-transparent bg-clip-text">
                            About
                        </h2>
                    </div>
                </div>
            </div>
        </header>
    )
}

export default Titlebar;