import type { ParamGroup } from "../types/types";

const groupParameters = (runParams: Record<string, any>): ParamGroup[] => {
    const groups: ParamGroup[] = [];

    // Define all categories for all params we get from runInfo
    const paramCategories = {
        core: {
        title: "Core Training",
        color: "blue-400",
        keys: ["model_name", "dataset_name", "batch_size", "learning_rate", "epochs", "optimizer", "loss_function", "device", "random_seed", "weight_decay", "momentum"]
        },
        model: {
        title: "Model Architecture", 
        color: "green-400",
        keys: ["total_parameters", "trainable_parameters", "parameters_millions", "model_size_mb", "flops_millions", "input_size", "use_pretrained", "model_architecture"]
        },
        system: {
        title: "System Hardware",
        color: "purple-400", 
        keys: ["cpu_count", "memory_total_gb", "platform", "python_version", "pytorch_version", "gpu_name", "gpu_memory_gb", "cuda_version", "num_gpus", "device_type"]
        },
        data: {
        title: "Data Pipeline",
        color: "yellow-400",
        keys: ["train_size", "val_size", "total_samples", "num_workers"]
        },
        environment: {
        title: "Environment",
        color: "cyan-400",
        keys: ["git_commit", "git_branch", "mlflow_uri", "experiment_name"]
        }
    }

    // Retrieve valid params from runInfo
    Object.entries(paramCategories).forEach(([categoryKey, category]) => {
        const categoryParams: Record<string, any> = {};

        // assign each valid value to the same key into current category
        category.keys.forEach((key) => {
            if (runParams[key] !== undefined) {
                categoryParams[key] = runParams[key];
            }
        })

        if (Object.keys(categoryParams).length > 0) {
            groups.push({
                title: category.title,
                color: category.color,
                params: categoryParams
            })
        }
    })

    // Add ungrouped parameters
    const allGroupedKeys = Object.values(paramCategories).flatMap(cat => cat.keys);
    const ungroupedParams = Object.entries(runParams)
        .filter(([key]) => !allGroupedKeys.includes(key))
        .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

    if (Object.keys(ungroupedParams).length > 0) {
        groups.push({
        title: "Other",
        color: "-gray-400",
        params: ungroupedParams
        });
    }

    return groups;
}

// Helper to format parameter display names
const formatParamName = (key: string): string => {
return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/Gpu/g, 'GPU')
    .replace(/Cpu/g, 'CPU')
    .replace(/Mb/g, 'MB')
    .replace(/Gb/g, 'GB');
};


export {groupParameters, formatParamName};