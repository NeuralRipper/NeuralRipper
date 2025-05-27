// Common types for the application

export interface Experiment {
    id: string;
    name: string;
    artifact_location: string;
    lifecycle_stage: string;
    tags: string[] | Record<string, never>;
    creation_time: string;
    last_update_time: string;
}

export interface Run {
    id: string;
    experiment_id: string;
    name: string;
    status: string;
    start_time: string;
    end_time?: string;
    metrics?: Record<string, any>;
    parameters?: Record<string, any>;
}

export interface ExperimentCardProps {
    experiment: Experiment;
}

export interface RunCardProps {
    run: Run;
}

export interface FilterCardProps {
    label: string;
    active: boolean;
    onClick: () => void;
}