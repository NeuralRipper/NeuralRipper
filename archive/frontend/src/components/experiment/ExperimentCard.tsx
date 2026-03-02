import type {ExperimentCardProps} from '../types/types.ts';
import formatDate from "../utils/format.tsx";


const ExperimentCard: React.FC<ExperimentCardProps> = ({experiment, onSelectedExpId, selectedExpId}) => {
    const handleExpClick = (): void => {
        onSelectedExpId(experiment.id);
    };

    return (
        <button
            onClick={handleExpClick}
            className={`w-full text-left px-3 py-2 rounded transition-colors ${
                selectedExpId === experiment.id 
                    ? 'bg-cyan-500/10 border border-cyan-500/50' 
                    : 'bg-gray-800/50 hover:bg-gray-700/50'
            }`}
        >
            <div className="flex items-center justify-between">
                <span className="text-sm font-medium truncate text-cyan-400">{experiment.name}</span>
            </div>
            <div className="flex items-center gap-2 mb-0.5">
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                    experiment.lifecycle_stage === 'active' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                }`}>
                    {experiment.lifecycle_stage}
                </span>
                <span className="text-xs text-gray-500">
                    {formatDate(experiment.last_update_time)}
                </span>
            </div>
        </button>
    );
};

export default ExperimentCard;