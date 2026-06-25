import {

    useEffect,
    useState

} from "react";

import {

    getAuditHistory,

    getContributorHistory

} from "../api/history";

import AnalyticsDashboard from
"../components/AnalyticsDashboard";


function DashboardPage() {

    const [audits, setAudits] =
        useState([]);

    const [contributors,
        setContributors] =
        useState([]);

    useEffect(() => {

        async function loadData() {

            try {

                const auditData =
                    await getAuditHistory();

                const contributorData =
                    await getContributorHistory();

                setAudits(
                    auditData.audits
                );

                setContributors(
                    contributorData.contributors
                );

            } catch (error) {

                console.error(error);
            }
        }

        loadData();

    }, []);

    return (

        <div className="space-y-10">

            <div>

                <h1
                    className="
                    text-4xl
                    font-bold
                "
                >

                    ScopeSense Dashboard

                </h1>

                <p
                    className="
                    text-slate-400
                    mt-2
                "
                >

                    AI Engineering Intelligence Platform

                </p>

            </div>

            <AnalyticsDashboard

                audits={audits}

                contributors={
                    contributors
                }
            />

        </div>
    );
}

export default DashboardPage;