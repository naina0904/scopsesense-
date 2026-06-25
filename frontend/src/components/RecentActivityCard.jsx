function RecentActivityCard() {

    const activities = [
        "Authentication module completed",
        "Analytics dashboard delayed",
        "Payment integration in progress",
        "Timeline engine updated"
    ];

    return (

        <div className="
            bg-slate-900
            border
            border-slate-800
            rounded-2xl
            p-6
        ">

            <h2 className="text-xl font-semibold mb-6">
                Recent Activity
            </h2>

            <div className="space-y-4">

                {
                    activities.map((activity, index) => (

                        <div
                            key={index}
                            className="
                                bg-slate-800
                                rounded-xl
                                p-4
                            "
                        >

                            {activity}

                        </div>
                    ))
                }

            </div>

        </div>
    );
}

export default RecentActivityCard;