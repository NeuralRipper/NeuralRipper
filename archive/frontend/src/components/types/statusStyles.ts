const RunStatusStyles = {
    RUNNING: "bg-blue-500/20 text-blue-400",
    FINISHED: "bg-green-500/20 text-green-400",
    FAILED: "bg-red-500/20 text-red-400",
    SCHEDULED: "bg-yellow-500/20 text-yellow-400"
};

const ExperimentStatusStyles = {
    active: "bg-green-500/20 text-green-400",
    deleted: "bg-red-500/20 text-red-400"
};

export default {
    RunStatusStyles,
    ExperimentStatusStyles
}