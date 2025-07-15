import { useState, useEffect } from "react";
import { ActivityCalendar } from 'react-activity-calendar'
import { GITHUB_API_KEY } from "../../config";

const Repository: React.FC = () => {
    const [activityData, setActivityData] = useState(null)

    useEffect(() => {
        const getRepoInfo = async () => {
            const url = "https://api.github.com/graphql"
            const headers = {
                'Authorization': `Bearer ${GITHUB_API_KEY}`,
                'Content-Type': "application/json"
            }   
            console.log(headers)
            const query = `
                query($username: String!) {
                    user(login: $username) {
                    contributionsCollection {
                        contributionCalendar {
                        totalContributions
                        weeks {
                            contributionDays {
                            contributionCount
                            date
                            }
                        }
                        }
                    }
                    }
                }
                `;
            const body = JSON.stringify({
                query,
                variables: {username: "dizzydoze"}
            })
            
            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: body
            });

            if (!response.ok) {
                console.log("Fetch repo info failed.")
                return;
            }
            const data = await response.json();
            setActivityData(data);
        }

        getRepoInfo()
    }, [])

    const transformData = (weeks) => {
        const data = [];
        weeks.forEach(week => {
            week.contributionDays.forEach(day => {
                data.push({
                    date: day.date,
                    count: day.contributionCount,
                    level: Math.min(Math.floor(day.contributionCount / 3), 4) // Convert to 0-4 scale
                });
            });
        });
        return data;
    };

    const calendarData = transformData(activityData?.data?.user?.contributionsCollection?.contributionCalendar?.weeks || [])

    if (!activityData || !calendarData.length) {return;}

    return (
        <div className="bg-gray-950">
            <ActivityCalendar 
                data={calendarData} 
                weekStart={1} 
                theme={{
                        dark: [
                            '#161b22',        // Dark background
                            '#0a4a5c',        // Dark cyan
                            '#0891b2',        // Medium cyan  
                            '#22d3ee',        // Bright cyan
                            '#67e8f9'         // Light cyan
                            ]
                }}
                hideMonthLabels
                hideTotalCount
                hideColorLegend
            />
        </div>

    )
}

export default Repository;