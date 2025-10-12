import {useEffect, useState} from "react";
import ExperimentCard from "./ExperimentCard.tsx";
import type {Experiment, ExperimentListProps} from '../types/types.ts';
import { API_BASE_URL } from "../../config.ts";

const ExperimentList: React.FC<ExperimentListProps> = ({onSelectedExpId, selectedExpId}) => {

    const [experiments, setExperiments] = useState<Experiment[]>([]);

    const getExperimentList = async (): Promise<void> => {
        try {
            const url = `${API_BASE_URL}/experiments/`;
            console.log(`Experiement list url: ${url}`)
            const response = await fetch(url);

            if (!response.ok) {
                console.log(`Fetch Failed: ${response.status}`);
                return;
            }
            const data = await response.json();
            console.log(`Experiment list return data: ${data}`)
            
            // Sort the experiments by experimentID
            data.sort((a: Experiment, b: Experiment) => Number(a.id) - Number(b.id));

            setExperiments(data);
        } catch (error) {
            console.error('Error fetching experiments:', error);
        }
    };

    useEffect(() => {
        // Fetch once mounted
        getExperimentList();
        // IMPORTANT: only call setInterval inside useEffect with NO dependencies, so it won't create multiple intervals
        const intervalId = setInterval(() => {
            try {
                console.log("[INTERVAL]Experiment list updated.")
                getExperimentList();        
            } catch(e) {
                console.log("Failed to fetch experiment list.")
            }
        }, 60000)

        return () => clearInterval(intervalId);
    }, []);

    useEffect(() => {
        if (experiments.length === 0) {
            return;
        }
        // Only auto-select first experiment if nothing is currently selected
        if (!selectedExpId) {
            onSelectedExpId(experiments[0]?.id)
        }
    }, [experiments])

    return (
        <div className="grid gap-1">
            {experiments && experiments.map(experiment => (
                <ExperimentCard key={experiment.id} experiment={experiment} onSelectedExpId={onSelectedExpId}
                                selectedExpId={selectedExpId}/>
            ))}
        </div>
    );
};

export default ExperimentList;