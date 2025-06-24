import {Terminal} from 'lucide-react';
import type { RunListCardProps } from '../types/types.ts';
import formatDate from "../utils/format.tsx";
import statusStyles from "../types/statusStyles.ts";


const RunListCard: React.FC<RunListCardProps> = ({run, onSelectedRunId}) => {
    const { RunStatusStyles } = statusStyles;       // Destructure
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
        <div
            className="bg-gray-800/50 border border-gray-600/40 rounded-md hover:border-gray-500/60 transition-colors font-mono ml-7 mb-0.5 mr-2">
            <div className="p-1">
                <div className="flex items-center gap-2">
                    <Terminal className="text-purple-400 h-3 w-3"/>
                    {/*Click the RunListCard will redirect to RunDetail*/}
                    <button onClick={handleRunClick}
                        className="text-purple-300 text-xs font-medium truncate">
                        {runName}
                    </button>
                    <span
                        className={`px-1 py-0.5 rounded text-xs ${RunStatusStyles[status as keyof typeof RunStatusStyles] || RunStatusStyles.SCHEDULED}`}>
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

export default RunListCard;