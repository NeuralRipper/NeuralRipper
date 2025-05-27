import { Play } from 'lucide-react';
import type { RunCardProps } from '../types/types.ts';

const RunCard: React.FC<RunCardProps> = ({ run }) => {
    const statusStyles = {
        RUNNING: "bg-blue-500/20 text-blue-400 border border-blue-500/50",
        FINISHED: "bg-green-500/20 text-green-400 border border-green-500/50",
        FAILED: "bg-red-500/20 text-red-400 border border-red-500/50",
        SCHEDULED: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50"
    };

    const formatDate = (dateString: string) => {
        const now = new Date();
        const date = new Date(dateString);
        const diffTime = Math.abs(now.getTime() - date.getTime());
        const diffMinutes = Math.floor(diffTime / (1000 * 60));
        const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return "1d ago";
        if (diffDays < 7) return `${diffDays}d ago`;
        return `${Math.ceil(diffDays / 7)}w ago`;
    };

    return (
        <div className="bg-gray-800/50 border border-gray-600/40 rounded-md hover:border-gray-500/60 transition-colors font-mono ml-4 mb-1">
            <div className="p-2">
                <div className="flex items-center gap-2">
                    <Play className="text-purple-400 h-3 w-3 flex-shrink-0"/>
                    <span className="text-purple-300 text-xs font-medium truncate">
                        {run.name || `Run ${run.id.slice(0, 8)}`}
                    </span>
                    <span
                        className={`px-1 py-0.5 rounded text-xs ${statusStyles[run.status as keyof typeof statusStyles] || statusStyles.SCHEDULED}`}>
                        {run.status}
                    </span>
                    <div className="text-xs text-gray-400 ml-auto">
                        {formatDate(run.start_time)}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RunCard;