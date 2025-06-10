import {useEffect, useState} from "react";
import {useParams} from "react-router";


const RunDetail = () => {

    const { runId } = useParams<{ runId: string}>();
    const [runData, setRunData] = useState(null);

    useEffect(() => {
        // fetch detail data from the received runId from the list
        const getRunData = async () => {
            const url = `http://localhost:8000/runs/detail/${runId}`
            const response = await fetch(url);

            if (!response.ok) {
                console.log(`Fetch Failed: ${response.status}`);
                return;
            }
            const data = await response.json();
            setRunData(data);
        }
        getRunData();
    }, [runId])

    return (
        <h1>Run Detail Data: {runData}</h1>
    )
}


export default RunDetail;