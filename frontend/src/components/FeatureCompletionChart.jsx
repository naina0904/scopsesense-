import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer
} from "recharts";

const data = [
    { name: "Auth", completed: 100 },
    { name: "Payments", completed: 75 },
    { name: "Dashboard", completed: 90 },
    { name: "Analytics", completed: 55 },
];

function FeatureCompletionChart() {

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
            h-full
        ">

            <h2 className="text-xl font-semibold mb-6">
                Feature Completion
            </h2>

            <div className="h-72">

                <ResponsiveContainer width="100%" height="100%">

                    <BarChart data={data}>

                        <XAxis dataKey="name" />

                        <YAxis />

                        <Tooltip />

                        <Bar
                            dataKey="completed"
                            fill="#6366f1"
                            radius={[6, 6, 0, 0]}
                        />

                    </BarChart>

                </ResponsiveContainer>

            </div>

        </div>
    );
}

export default FeatureCompletionChart;