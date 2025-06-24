import {useEffect, useState} from "react";
import RunListCard from "./RunListCard.tsx";
import type {RunListProps, Run} from '../types/types.ts';


const RunList: React.FC<RunListProps> = ({experimentId, onSelectedRunId}) => {
    const [runs, setRuns] = useState<Run[]>([]);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {

        // only use for this useEffect hook
        const getRuns = async () => {
            try {
                setLoading(true);
                const url = `http://localhost:8000/runs/list/${experimentId}`;
                const response = await fetch(url);

                if (!response.ok) {
                    console.log(`Fetch Failed: ${response.status}`);
                    return;
                }

                const data = await response.json();
                console.log(data);
                setRuns(data);
            } catch (error) {
                console.error('Error fetching runs:', error);
            } finally {
                setLoading(false);
            }
        };

        getRuns();
    }, [experimentId]);

    if (loading) {
        return (
            <div className="ml-4 text-gray-400 text-xs font-mono">
                Loading runs...
            </div>
        );
    }

    if (runs.length === 0) {
        return (
            <div className="ml-4 text-gray-500 text-xs font-mono">
                No runs found
            </div>
        );
    }

    return (
        <div className="mt-2">
            {runs.map(run => (
                <RunListCard key={run?.info?.run_id} run={run} onSelectedRunId={onSelectedRunId}/>
            ))}
        </div>
    );
};

export default RunList;