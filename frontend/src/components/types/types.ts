// Common types for the application

export interface Experiment {
    id: string;
    name: string;
    artifact_location: string;
    lifecycle_stage: string;
    tags: string[] | Record<string, never>;
    creation_time: number;
    last_update_time: number;
}

// Backend response structure - matches RunResponse from FastApi
// Dynamic key value pairs, no capturing if None
export interface RunInfo {
    artifact_uri?: string;
    end_time?: number;
    experiment_id?: string;
    lifecycle_stage?: string;
    run_id?: string;
    run_name?: string;
    run_uuid?: string;
    start_time?: number;
    status?: string;
    user_id?: string;
}

export interface RunData {
    metrics?: Record<string, never>;
    params?: Record<string, never>;
}

// Nested object structure
export interface Run {
    data?: RunData;
    info?: RunInfo;
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