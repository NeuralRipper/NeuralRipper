import { useState } from 'react';
import FilterCard from "../Filter/FilterCard";

const Sidebar: React.FC = () => {
    const [activeModelTypes, setActiveModelTypes] = useState<string[]>([]);
    const [activeStatusTypes, setActiveStatusTypes] = useState<string[]>([]);

    const modelTypes = ["Transformer", "CNN", "RNN", "GAN", "Diffusion", "Reinforcement"];
    const statusTypes = ["Active", "Training", "Paused", "Completed", "Error"];

    const handleModelTypeClick = (type: string): void => {
        setActiveModelTypes(prev =>
            prev.includes(type)
                ? prev.filter(t => t !== type)
                : [...prev, type]
        );
    };

    const handleStatusTypeClick = (type: string): void => {
        setActiveStatusTypes(prev =>
            prev.includes(type)
                ? prev.filter(t => t !== type)
                : [...prev, type]
        );
    };

    return (
        <div className="w-64 bg-gray-900/50 border-r border-cyan-500/30 min-h-screen overflow-y-auto rounded-r-2xl">

            {/* Model Types */}
            <div className="p-4 border-b border-cyan-500/20">
                <h3 className="text-cyan-400 font-mono text-sm font-bold mb-3">MODEL TYPES</h3>
                <div className="grid grid-cols-2 gap-2">
                    {modelTypes.map((type) => (
                        <FilterCard
                            key={type}
                            label={type}
                            active={activeModelTypes.includes(type)}
                            onClick={() => handleModelTypeClick(type)}
                        />
                    ))}
                </div>
            </div>

            {/* Status */}
            <div className="p-4 border-b border-cyan-500/20">
                <h3 className="text-cyan-400 font-mono text-sm font-bold mb-3">STATUS</h3>
                <div className="grid grid-cols-2 gap-2">
                    {statusTypes.map((status) => (
                        <FilterCard
                            key={status}
                            label={status}
                            active={activeStatusTypes.includes(status)}
                            onClick={() => handleStatusTypeClick(status)}
                        />
                    ))}
                </div>
            </div>

            {/* Stats */}
            <div className="p-4 border-t border-cyan-500/20 mt-4">
                <div className="text-xs font-mono text-gray-500 space-y-1">
                    <div>TOTAL: <span className="text-cyan-400">1,247</span></div>
                    <div>ACTIVE: <span className="text-green-400">892</span></div>
                    <div>TRAINING: <span className="text-yellow-400">234</span></div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;