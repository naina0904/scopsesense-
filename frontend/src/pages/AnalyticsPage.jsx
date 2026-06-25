import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
} from "recharts";

function AnalyticsPage() {
    const [overview, setOverview] = useState(null);
    const [history, setHistory] = useState([]);
    const [risks, setRisks] = useState(null);
    const [roadmap, setRoadmap] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5;

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const [overviewRes, historyRes, risksRes, roadmapRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/analytics/overview`),
                axios.get(`${API_BASE_URL}/analytics/history`),
                axios.get(`${API_BASE_URL}/analytics/risks`),
                axios.get(`${API_BASE_URL}/analytics/roadmap`)
            ]);
            setOverview(overviewRes.data);
            setHistory(historyRes.data);
            setRisks(risksRes.data);
            setRoadmap(roadmapRes.data);
        } catch (error) {
            console.error(error);
        }
    };

    const pieData = risks ? [
        { name: "High", value: risks.high_risk, color: "#ef4444" },
        { name: "Medium", value: risks.medium_risk, color: "#f59e0b" },
        { name: "Low", value: risks.low_risk, color: "#10b981" }
    ] : [];

    const totalPages = Math.ceil(roadmap.length / itemsPerPage);
    const paginatedRoadmap = roadmap.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* HEADER */}
                <div>
                    <h1 className="text-4xl font-bold text-slate-900">Engineering Analytics</h1>
                    <p className="text-slate-500 mt-2 text-lg">AI-Native Engineering Governance Dashboard</p>
                </div>

                {/* OVERVIEW CARDS */}
                {overview && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-slate-500 font-medium">Total Audits</h2>
                            <div className="text-4xl font-bold text-indigo-600 mt-4">{overview.total_audits}</div>
                        </div>
                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-slate-500 font-medium">Average Health</h2>
                            <div className="text-4xl font-bold text-emerald-600 mt-4">{overview.average_health}%</div>
                        </div>
                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-slate-500 font-medium">Latest Audit</h2>
                            <div className="text-2xl font-bold text-slate-700 mt-4">{overview.latest_audit}</div>
                        </div>
                    </div>
                )}

                {/* HEALTH TREND */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                    <h2 className="text-xl font-bold text-slate-800 mb-6">Engineering Health Trend</h2>
                    <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={history}>
                                <XAxis dataKey="project" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Line type="monotone" dataKey="health_score" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* RISK + ROADMAP */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* RISK */}
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                        <h2 className="text-xl font-bold text-slate-800 mb-6">Risk Distribution</h2>
                        <div className="h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={pieData} dataKey="value" outerRadius={120} label>
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* ROADMAP */}
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-slate-800">Engineering Roadmap</h2>
                            <span className="text-sm text-slate-500">{roadmap.length} items total</span>
                        </div>
                        
                        <div className="space-y-4 flex-1">
                            {paginatedRoadmap.map((item, index) => (
                                <div key={index} className="border border-slate-100 bg-slate-50 rounded-lg p-4 transition hover:shadow-md">
                                    <div className="flex justify-between items-start">
                                        <h3 className="font-semibold text-slate-800">{item.project}</h3>
                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                            item.priority === 'High' ? 'bg-red-100 text-red-700' :
                                            item.priority === 'Medium' ? 'bg-amber-100 text-amber-700' :
                                            'bg-emerald-100 text-emerald-700'
                                        }`}>
                                            {item.priority} Priority
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-600 mt-2">{item.recommended_action}</p>
                                </div>
                            ))}
                            {roadmap.length === 0 && (
                                <div className="text-center text-slate-500 py-8">No roadmap items available.</div>
                            )}
                        </div>

                        {/* Pagination Controls */}
                        {roadmap.length > 0 && (
                            <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
                                <button 
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={currentPage === 1}
                                    className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Previous
                                </button>
                                <span className="text-sm text-slate-500">
                                    Page {currentPage} of {totalPages || 1}
                                </span>
                                <button 
                                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                    disabled={currentPage === totalPages || totalPages === 0}
                                    className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Next
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AnalyticsPage;