function HealthScoreCard() {

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
                Project Health
            </h2>

            <div className="flex items-center justify-center h-56">

                <div className="
                    w-40
                    h-40
                    rounded-full
                    border-[12px]
                    border-emerald-500
                    flex
                    items-center
                    justify-center
                    text-4xl
                    font-bold
                ">

                    82%

                </div>

            </div>

        </div>
    );
}

export default HealthScoreCard;