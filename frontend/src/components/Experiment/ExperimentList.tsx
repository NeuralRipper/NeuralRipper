import {useEffect, useState} from "react";
import ExperimentCard from "./ExperimentCard";
import type {Experiment, ExperimentListProps} from '../types/types.ts';
import { API_BASE_URL } from "../../config.ts";

const ExperimentList: React.FC<ExperimentListProps> = ({onSelectedExpId, selectedExpId}) => {

    const [experiments, setExperiments] = useState<Experiment[]>([]);

    useEffect(() => {
        const getExperimentList = async (): Promise<void> => {
            try {
                const url = `${API_BASE_URL}/experiments/`;
                const response = await fetch(url);

                if (!response.ok) {
                    console.log(`Fetch Failed: ${response.status}`);
                    return;
                }
                const data = await response.json();

                // Sort the experiments by experimentID
                data.sort((a: Experiment, b: Experiment) => Number(a.id) - Number(b.id));

                setExperiments(data);
            } catch (error) {
                console.error('Error fetching experiments:', error);
            }
        };

        getExperimentList();
    }, [setExperiments]);

    useEffect(() => {
        if (experiments.length === 0) {
            return;
        }
        // Render the first experiment by default
        onSelectedExpId(experiments[0]?.id)
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