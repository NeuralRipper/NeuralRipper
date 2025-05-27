import {ChevronDown, ChevronRight} from 'lucide-react';
import {useState} from 'react';
import RunList from '../Run/RunList.tsx';
import type {ExperimentCardProps} from '../types/types.ts';
import formatDate from "../utils/format.tsx";
import statusStyles from "../types/statusStyles.ts"

const ExperimentCard: React.FC<ExperimentCardProps> = ({experiment}) => {
    const [isExpanded, setIsExpanded] = useState<boolean>(false);
    const {ExperimentStatusStyles} = statusStyles;  // Destructure

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
        <div
            className="bg-gray-900/90 border border-cyan-500/40 rounded hover:border-cyan-400/90 transition-colors font-mono">
            <div className="p-1.5">
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleToggleExpand}
                        className="text-cyan-400 hover:text-cyan-300 font-bold text-sm truncate flex items-center gap-1"
                    >
                        {isExpanded ? (
                            <ChevronDown className="h-3.5 w-3.5"/>
                        ) : (
                            <ChevronRight className="h-3.5 w-3.5"/>
                        )}
                        {experiment.name}
                    </button>
                    <span
                        className={`px-1 py-0.5 rounded text-xs ${ExperimentStatusStyles[experiment.lifecycle_stage as keyof typeof ExperimentStatusStyles]}`}>
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
                    <RunList experimentId={experiment.id}/>
                </div>
            )}
        </div>
    );
};

export default ExperimentCard;