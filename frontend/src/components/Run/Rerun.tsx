import { Eye } from 'lucide-react';

// Install: npm install @rerun-io/web-viewer-react
import WebViewer from "@rerun-io/web-viewer-react";

const Rerun = () => {
    // Your Rerun data source URL
    const rerunDataSource = "rerun+http://localhost:9876/proxy";

    return (
        <div className="flex-1 bg-gray-900/30">
            {/* Simple Header */}
            <div className="border-b border-gray-800 bg-gray-900/50 p-4">
                <div className="flex items-center gap-3">
                    <Eye className="text-cyan-400" size={20} />
                    <h2 className="text-xl font-bold text-cyan-400">
                        Neural Ripper Echo
                    </h2>
                </div>
            </div>

            {/* Rerun Viewer */}
            <div>
                <WebViewer
                    rrd={rerunDataSource}
                    hide_welcome_screen={false}
                />
            </div>
        </div>
    );
};

export default Rerun;