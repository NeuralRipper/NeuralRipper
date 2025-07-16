import {Terminal} from 'lucide-react';
import type {RunListCardProps} from '../types/types.ts';
import formatDate from "../utils/format.tsx";
import statusStyles from "../types/statusStyles.ts";


const RunListCard: React.FC<RunListCardProps> = ({run, onSelectedRunId, selectedRunId}) => {
    const {RunStatusStyles} = statusStyles;       // Destructure
    // Handle potentially missing info
    const runInfo = run.info;
    const runId = runInfo?.run_id || '';
    const runName = runInfo?.run_name || `Run ${runId.slice(0, 8)}`;
    const status = runInfo?.status || 'SCHEDULED';
    const startTime = runInfo?.start_time;

    const handleRunClick = () => {
        onSelectedRunId(runId);
    }

    return (
        <div className={`rounded-md transition-colors font-mono mb-0.5 ${
            selectedRunId === runId 
                ? 'bg-cyan-500/10 border border-cyan-500/50' 
                : 'bg-gray-800/50 hover:bg-gray-700/50'
        }`}>

            <button
                onClick={handleRunClick}
                className="w-full text-left px-3 py-2 rounded transition-colors bg-gray-800/50 hover:bg-gray-700/50"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Terminal className="h-3 w-3 text-purple-400"/>
                        <span className="text-sm font-mono">{runName}</span>
                    </div>

                </div>
                <div className="flex gap-2">
                    {runInfo?.start_time && (
                        <div className="text-xs text-gray-400 mt-1">
                            {formatDate(startTime)}
                        </div>
                    )}
                    <span
                        className={`text-xs px-1.5 py-0.5 rounded ${RunStatusStyles[status as keyof typeof RunStatusStyles] || RunStatusStyles.SCHEDULED}`}>
                            {status}
                    </span>
                </div>

            </button>

        </div>
    );
};

export default RunListCard;