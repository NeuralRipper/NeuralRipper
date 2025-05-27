import {Play} from 'lucide-react';
import type {RunCardProps} from '../types/types.ts';
import formatDate from "../utils/format.tsx";

const RunCard: React.FC<RunCardProps> = ({run}) => {
    const statusStyles = {
        RUNNING: "bg-blue-500/20 text-blue-400 border border-blue-500/50",
        FINISHED: "bg-green-500/20 text-green-400 border border-green-500/50",
        FAILED: "bg-red-500/20 text-red-400 border border-red-500/50",
        SCHEDULED: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50"
    };


    // Handle potentially missing info
    const runInfo = run.info;
    const runId = runInfo?.run_id || '';
    const runName = runInfo?.run_name || `Run ${runId.slice(0, 8)}`;
    const status = runInfo?.status || 'SCHEDULED';
    const startTime = runInfo?.start_time;

    return (
        <div
            className="bg-gray-800/50 border border-gray-600/40 rounded-md hover:border-gray-500/60 transition-colors font-mono ml-4 mb-1">
            <div className="p-2">
                <div className="flex items-center gap-2">
                    <Play className="text-purple-400 h-3 w-3 flex-shrink-0"/>
                    <span className="text-purple-300 text-xs font-medium truncate">
                        {runName}
                    </span>
                    <span
                        className={`px-1 py-0.5 rounded text-xs ${statusStyles[status as keyof typeof statusStyles] || statusStyles.SCHEDULED}`}>
                        {status}
                    </span>
                    <div className="text-xs text-gray-400 ml-auto">
                        {formatDate(startTime)}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RunCard;