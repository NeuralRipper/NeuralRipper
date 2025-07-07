import {useEffect, useState} from "react";
import RunListCard from "./RunListCard.tsx";
import type {RunListProps, Run} from '../types/types.ts';
import { API_BASE_URL } from "../../config.ts";


const RunList: React.FC<RunListProps> = ({experimentId, onSelectedRunId}) => {
    const [runs, setRuns] = useState<Run[]>([]);

    useEffect(() => {
        // only use for this useEffect hook
        const getRuns = async () => {
            try {
                console.log(API_BASE_URL)
                const url = `${API_BASE_URL}/runs/list/${experimentId}`;
                const response = await fetch(url);

                if (!response.ok) {
                    console.log(`Fetch Failed: ${response.status}`);
                    return;
                }

                const data = await response.json();
                setRuns(data);
            } catch (error) {
                console.error('Error fetching runs:', error);
            }
        };

        getRuns();
    }, [experimentId]);

    if (runs.length === 0) {
        return (
            <div className="ml-4 text-gray-500 text-xs font-mono">
                No runs found
            </div>
        );
    }

    return (
        <div>
            {runs.map(run => (
                <RunListCard key={run?.info?.run_id} run={run} onSelectedRunId={onSelectedRunId}/>
            ))}
        </div>
    );
};

export default RunList;