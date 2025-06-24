import {useEffect, useState} from "react";
import ExperimentCard from "./ExperimentCard";
import type {Experiment, ExperimentListProps} from '../types/types.ts';

const ExperimentList: React.FC<ExperimentListProps> = ({ onSelectedExpId }) => {

    const [experiments, setExperiments] = useState<Experiment[]>([]);

    useEffect(() => {
        const getExperimentList = async (): Promise<void> => {
            try {
                const url = "http://localhost:8000/experiments";
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
                <ExperimentCard key={experiment.id} experiment={experiment} onSelectedExpId={onSelectedExpId}/>
            ))}
        </div>
    );
};

export default ExperimentList;