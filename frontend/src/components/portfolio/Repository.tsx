import { useState, useEffect } from "react";
import { ActivityCalendar, type Activity } from 'react-activity-calendar'
import { getContributions } from "@/api/github"

interface ContributionDay {
    date: string;
    contributionCount: number;
}

interface ContributionWeek {
    contributionDays: ContributionDay[];
}

const Repository: React.FC = () => {
    const [activityData, setActivityData] = useState<any>(null)

    useEffect(() => {
        getContributions()
            .then(setActivityData)
            .catch(() => console.log("Fetch repo info failed."))
    }, [])

    const transformData = (weeks: ContributionWeek[]): Activity[] => {
        const data: Activity[] = [];
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
                showMonthLabels={false}
                showTotalCount={false}
                showColorLegend={false}
            />
        </div>

    )
}

export default Repository;
