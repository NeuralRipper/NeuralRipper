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
                setExperiments(data);
            } catch (error) {
                console.error('Error fetching experiments:', error);
            }
        };

        getExperimentList();

    }, [setExperiments]);


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