import React, { useState, useEffect } from 'react';

function Anomalies({ anomalyType }) {
    const [anomaly, setAnomaly] = useState({});
    const [isLoaded, setIsLoaded] = useState(false);
    const [error, setError] = useState(null);

    const getAnomaly = async () => {
        await fetch(`http://ec2-52-90-75-251.compute-1.amazonaws.com/anomalies/anomalies/?anomaly_type=${anomalyType}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then((response) => response.json())
        .then((result) => {
            setAnomaly(result[0]);
            setIsLoaded(True);
        })
        .catch((err) => setError(err));
    };

    useEffect(() => {
        const intervalId = setInterval(getAnomaly, 4000);
        return () => clearInterval(intervalId);
    }, [getAnomaly]);
    
    return (
        <div>
                <h2>{anomaly.anomaly_type}</h2>
                <div>
                    <h5>{anomaly.event_id}</h5>
                    <h5>{anomaly.description}</h5>
                    <h5>Detected on {anomaly.timestamp}</h5>
                </div>
        </div>
    );
};

export default Anomalies;