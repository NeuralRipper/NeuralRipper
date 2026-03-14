import { useState, useEffect } from "react";
import { ActivityCalendar } from 'react-activity-calendar'
import { getContributions } from "@/api/github"

const Repository: React.FC = () => {
    const [activityData, setActivityData] = useState(null)

    useEffect(() => {
        getContributions()
            .then(setActivityData)
            .catch(() => console.log("Fetch repo info failed."))
    }, [])

    const transformData = (weeks) => {
        const data = [];
        weeks.forEach(week => {
            week.contributionDays.forEach(day => {
                data.push({
                    date: day.date,
                    count: day.contributionCount,
                    level: Math.min(Math.floor(day.contributionCount / 3), 4)
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
                            '#161b22',
                            '#0a4a5c',
                            '#0891b2',
                            '#22d3ee',
                            '#67e8f9'
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
