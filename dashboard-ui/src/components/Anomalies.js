import React, { useState, useEffect } from 'react';
import '../App.css';

function Anomalies({ anomalyType }) {
    const [anomaly, setAnomaly] = useState({});
    const [isLoaded, setIsLoaded] = useState(false);
    const [error, setError] = useState(null);

    const getAnomaly = () => {
        fetch(`http://ec2-18-206-137-36.compute-1.amazonaws.com/anomalies/anomalies?anomaly_type=${anomalyType}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then((response) => response.json())
        .then((result) => {
            setAnomaly(result[0]);
            setIsLoaded(true);
        })
        .catch((err) => setError(err));
    };

    useEffect(() => {
        const intervalId = setInterval(getAnomaly, 4000);
        return () => clearInterval(intervalId);
    }, [getAnomaly]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return (
            <div>
                    <h2>{anomaly.event_type}</h2>
                    <div>
                        <h5>{anomaly.event_id}</h5>
                        <h5>{anomaly.description}</h5>
                        <h5>Detected on {anomaly.timestamp}</h5>
                    </div>
            </div>
        );
    }
};

export default Anomalies;
