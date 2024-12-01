import logo from './logo.jpg';
import './App.css';

import EndpointAnalyzer from './components/EndpointAnalyzer'
import AppStats from './components/AppStats'
import Anomaly from './components/Anomalies';

function App() {

    const endpoints = ["enroll", "drop-out"]
    const anomalyTypes = ["TooLow", "TooHigh"]

    const rendered_endpoints = endpoints.map((endpoint) => {
        return <EndpointAnalyzer key={endpoint} endpoint={endpoint}/>
    })

    return (
        <div className="App">
            <img src={logo} className="App-logo" alt="logo" height="150px" width="400px"/>
            <div>
                <AppStats/>
                <h1>Analyzer Endpoints</h1>
                {rendered_endpoints}
                <h1>Most Recent Anomalies</h1>
                {anomalyTypes.map((type) => (
                    <Anomaly key={type} anomalyType={type} />
                ))}
            </div>
        </div>
    );
}


export default App;
