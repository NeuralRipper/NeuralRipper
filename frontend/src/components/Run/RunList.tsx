import {useEffect, useState} from "react";
import RunListCard from "./RunListCard.tsx";
import type {RunListProps, Run} from '../types/types.ts';
import { API_BASE_URL } from "../../config.ts";


const RunList: React.FC<RunListProps> = ({experimentId, onSelectedRunId, selectedRunId}) => {
    const [runs, setRuns] = useState<Run[]>([]);

    const getRuns = async () => {
        try {
            const url = `${API_BASE_URL}/runs/list/${experimentId}`;
            const response = await fetch(url);

            if (!response.ok) {
                console.log(`Fetch Failed: ${response.status}`);
                return;
            }
            const data = await response.json();
            
            // Sort Runs by time
            data.sort((a: Run, b: Run) => Number(a.info?.end_time) - Number(b.info?.end_time))
            setRuns(data);
        } catch (error) {
            console.error('Error fetching runs:', error);
        }
    };

    useEffect(() => {
        // Fetch once mounted
        getRuns();

        // IMPORTANT: setInterval only called inside useEffect to avoid multiple intervals
        const intervalId = setInterval(() => {
            try {
                console.log("Fetching run list...")
                getRuns();
            } catch(e) {
                console.error("Failed to fetch run data.")
            }         
        }, 60000)
        
        return () => clearInterval(intervalId);
    }, [experimentId]);

    useEffect(() => {
        if (runs.length === 0 || runs[0]?.info?.run_id === undefined || runs[0]?.info?.run_id === "") {
            return;
        }
        // Render the first RunDetail from current Experiment by default
        onSelectedRunId(runs[0]?.info?.run_id)
    }, [runs])


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
                <RunListCard key={run?.info?.run_id} run={run} onSelectedRunId={onSelectedRunId} selectedRunId={selectedRunId}/>
            ))}
        </div>
    );
};

export default RunList;