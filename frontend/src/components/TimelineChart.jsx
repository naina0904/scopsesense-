import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer
} from "recharts";

function TimelineChart({ data = [] }) {

    // Transform data to chart format showing schedule delay or feature delay per feature
    const chartData = data.map(item => ({
        name: item.feature || "Unknown",
        delay: item.schedule_delay_days ?? item.timeline_analysis?.delay_days ?? 0
    }));

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
        ">

            <h2 className="text-2xl font-semibold mb-6">

                Feature Delay Timeline

            </h2>

            <div className="h-96">

                <ResponsiveContainer width="100%" height="100%">

                    <BarChart data={chartData}>

                        <XAxis dataKey="name" />

                        <YAxis />

                        <Tooltip 
                            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '0.5rem', color: '#f8fafc' }}
                            itemStyle={{ color: '#818cf8' }}
                        />

                        <Bar
                            dataKey="delay"
                            fill="#818cf8"
                            radius={[4, 4, 0, 0]}
                        />

                    </BarChart>

                </ResponsiveContainer>

            </div>

        </div>
    );
}

export default TimelineChart;