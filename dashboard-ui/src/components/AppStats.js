import React, { useEffect, useState } from 'react'
import '../App.css';
import styles from '../styles/AppStats.module.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {
	
        fetch(`http://deployment-processor-1:8100/stats`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={styles.StatsTable}>
					<tbody className={styles.StatsTableRows}>
						<tr className={styles.StatsTableData}>
							<th>Enrolled Students</th>
							<th>Dropout Students</th>
						</tr>
						<tr className={styles.StatsTableData}>
							<td># BP: {stats['num_enrolled_students']}</td>
							<td># HR: {stats['num_drop_out_students']}</td>
						</tr>
						<tr className={styles.StatsTableData}>
							<td colspan="2">
                                Average enrolled student gpa: {stats['avg_enrolled_student_gpa']}
                            </td>
							<td colspan="2">
                                Average dropout student gpa: {stats['avg_drop_out_student_gpa']}
                            </td>
						</tr>
						<tr className={styles.StatsTableData}>
                            <td colspan="2">
                                Min enrolled student gpa: {stats['min_enrolled_student_gpa']}
                            </td>
							<td colspan="2">
                                Max dropout student gpa: {stats['max_drop_out_student_gpa']}
                            </td>
						</tr>
					</tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>
            </div>
        )
    }
}
