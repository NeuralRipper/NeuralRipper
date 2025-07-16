// Common types for the application

import * as React from "react";

export interface Experiment {
    id: string;
    name: string;
    artifact_location: string;
    lifecycle_stage: string;
    tags: string[] | Record<string, never>;
    creation_time: number;
    last_update_time: number;
}

export interface ExperimentListProps {
    onSelectedExpId: React.Dispatch<React.SetStateAction<string>>;
    selectedExpId: string;
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
    start_time?: number;
    status?: string;
    user_id?: string;
}

export interface RunListProps {
    experimentId: string;
    onSelectedRunId: React.Dispatch<React.SetStateAction<string>>;
    selectedRunId: string;
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
    onSelectedExpId: React.Dispatch<React.SetStateAction<string>>
    selectedExpId: string;
}

export interface RunListCardProps {
    run: Run;
    onSelectedRunId: React.Dispatch<React.SetStateAction<string>>;
    selectedRunId: string;
}

export interface FilterCardProps {
    label: string;
    active: boolean;
    onClick: () => void;
}

export interface MetricDetail {
    key: string;
    value: number;
    timestamp: number;
    step: number;
    run_id: string;
}

export interface MetricList {
    metrics: MetricDetail[];
}

export interface RunDetailCardProps {
    selectedRunId: string;
}

export interface SidebarProps {
    onSelectedExpId: React.Dispatch<React.SetStateAction<string>>;
    onSelectedRunId: React.Dispatch<React.SetStateAction<string>>;
    selectedExpId: string;
    selectedRunId: string;
}

export interface SystemParamsProps {
    runParams: Record<string, any>[];
}

export interface ParamGroup {
    title: string,
    color: string,
    params: Record<string, any>;
}