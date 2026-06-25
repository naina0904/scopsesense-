import {
    AlertTriangle
} from "lucide-react";

function DelayInsightsCard({ insights = [] }) {

    if (!insights || insights.length === 0) {
        return null;
    }

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
        ">

            <div className="
                flex
                items-center
                gap-3
                mb-6
            ">

                <AlertTriangle
                    className="text-yellow-400"
                />

                <h2 className="text-2xl font-semibold">

                    Delay Intelligence

                </h2>

            </div>

            <div className="space-y-4">

                {
                    insights.map((item, index) => (

                        <div
                            key={index}
                            className="
                                bg-slate-800
                                rounded-xl
                                p-4
                                border
                                border-slate-700
                            "
                        >

                            {item.narrative || item}

                        </div>
                    ))
                }

            </div>

        </div>
    );
}

export default DelayInsightsCard;