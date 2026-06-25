import {
    CheckCircle,
    AlertCircle,
    User
} from "lucide-react";

function FeatureCard({ feature }) {

    const completed =
        feature.status === "Completed";

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
            hover:border-indigo-500
            transition
        ">

            <div className="
                flex
                items-start
                justify-between
            ">

                <div>

                    <h2 className="
                        text-2xl
                        font-semibold
                    ">

                        {feature.name}

                    </h2>

                    <div className="
                        flex
                        items-center
                        gap-2
                        mt-4
                        text-slate-400
                    ">

                        <User size={18} />

                        <span>

                            {feature.developer}

                        </span>

                    </div>

                </div>

                <div>

                    {
                        completed ? (

                            <div className="
                                flex
                                items-center
                                gap-2
                                text-emerald-400
                            ">

                                <CheckCircle size={20} />

                                <span>
                                    Completed
                                </span>

                            </div>

                        ) : (

                            <div className="
                                flex
                                items-center
                                gap-2
                                text-red-400
                            ">

                                <AlertCircle size={20} />

                                <span>
                                    Incomplete
                                </span>

                            </div>

                        )
                    }

                </div>

            </div>

        </div>
    );
}

export default FeatureCard;