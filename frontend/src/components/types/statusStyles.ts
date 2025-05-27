const RunStatusStyles = {
    RUNNING: "bg-blue-500/20 text-blue-400 border border-blue-500/50",
    FINISHED: "bg-green-500/20 text-green-400 border border-green-500/50",
    FAILED: "bg-red-500/20 text-red-400 border border-red-500/50",
    SCHEDULED: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50"
};

const ExperimentStatusStyles = {
    active: "bg-green-500/20 text-green-400 border border-green-500/50",
    deleted: "bg-red-500/20 text-red-400 border border-red-500/50"
};

export default {
    RunStatusStyles,
    ExperimentStatusStyles
}