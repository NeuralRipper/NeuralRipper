import WebViewer from "@rerun-io/web-viewer-react";

const Rerun = () => {
    // Rerun data source URL
    const rerunDataSource = "rerun+http://localhost:9876/proxy";

    return (
        <div className="flex flex-auto justify-center items-center bg-gray-850/10">
            {/* Rerun Viewer */}
            <div>
                <WebViewer
                    rrd={rerunDataSource}
                    hide_welcome_screen={true}
                />
            </div>
        </div>
    );
};

export default Rerun;