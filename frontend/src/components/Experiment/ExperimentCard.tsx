import { Terminal, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import RunList from '../Run/RunList.tsx';
import type { ExperimentCardProps } from '../types/types.ts';

const ExperimentCard: React.FC<ExperimentCardProps> = ({ experiment }) => {
    const [isExpanded, setIsExpanded] = useState<boolean>(false);

    const statusStyles = {
        active: "bg-green-500/20 text-green-400 border border-green-500/50",
        deleted: "bg-red-500/20 text-red-400 border border-red-500/50"
    };

    const formatDate = (dateString: string): string => {
        const now = new Date();
        const date = new Date(dateString);
        const diffTime = Math.abs(now.getTime() - date.getTime());
        const diffMinutes = Math.floor(diffTime / (1000 * 60));
        const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
        if (diffHours < 24) return `${diffHours} hours ago`;
        if (diffDays === 1) return "1 day ago";
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        return `${Math.ceil(diffDays / 30)} months ago`;
    };

    const getTags = (): string[] => {
        if (Array.isArray(experiment.tags)) {
            return experiment.tags;
        }
        if (typeof experiment.tags === 'object' && experiment.tags !== null) {
            return Object.keys(experiment.tags);
        }
        return [];
    };

    const handleToggleExpand = (): void => {
        setIsExpanded(!isExpanded);
    };

    return (
        <div className="bg-gray-900/90 border border-cyan-500/40 rounded hover:border-cyan-400/90 transition-colors font-mono">
            <div className="p-2">
                <div className="flex items-center gap-2">
                    <Terminal className="text-cyan-400 h-4 w-4 flex-shrink-0"/>
                    <button
                        onClick={handleToggleExpand}
                        className="text-cyan-400 hover:text-cyan-300 font-bold text-sm truncate flex items-center gap-1"
                    >
                        {isExpanded ? (
                            <ChevronDown className="h-3 w-3" />
                        ) : (
                            <ChevronRight className="h-3 w-3" />
                        )}
                        {experiment.name}
                    </button>
                    <span
                        className={`px-1 py-0.5 rounded text-xs ${statusStyles[experiment.lifecycle_stage as keyof typeof statusStyles]}`}>
                        {experiment.lifecycle_stage.toUpperCase()}
                    </span>
                    <div className="text-xs text-yellow-400">
                        {getTags().length > 0 && (
                            <div className="flex gap-1 flex-wrap">
                                {getTags().map((tag, index) => (
                                    <span key={index} className="text-purple-400">#{tag}</span>
                                ))}
                            </div>
                        )}
                    </div>
                    <div className="text-xs text-yellow-400 ml-auto">
                        Updated {formatDate(experiment.last_update_time)}
                    </div>
                </div>
            </div>
            {isExpanded && (
                <div className="border-t border-cyan-500/20 pb-2">
                    <RunList experimentId={experiment.id} />
                </div>
            )}
        </div>
    );
};

export default ExperimentCard;