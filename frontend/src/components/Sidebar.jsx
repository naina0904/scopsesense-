import {
    LayoutDashboard,
    FolderKanban,
    Clock3,
    Bot,
    UploadCloud,
    GitMerge,
    Link2,
    Check,
    Users,
    Layers,
    Sparkles,
    PlayCircle,
    FileBarChart,
    BrainCircuit,
    Plug,
    HelpCircle
} from "lucide-react";

import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";
import api from "../api/client";
import IntegrationModal from "./IntegrationModal";
import { useAudit } from "../context/AuditContext";

function Sidebar() {
    const location = useLocation();
    const navigate = useNavigate();
    const pathname = location.pathname;
    const { showCopilot, setShowCopilot, showFaqs, setShowFaqs } = useAudit();
    const [role, setRole] = useState(localStorage.getItem("scopesense_role") || "manager");
    
    // Modal state
    const [isIntegrationModalOpen, setIntegrationModalOpen] = useState(false);
    const [modalPlatform, setModalPlatform] = useState("jira");
    const [connections, setConnections] = useState([]);

    const loginWithRole = useCallback(async (newRole) => {
        localStorage.setItem("scopesense_role", newRole);
        try {
            const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
                user_id: 1,
                role: newRole
            });
            localStorage.setItem("scopesense_token", response.data.access_token);
            window.dispatchEvent(new Event("loginComplete"));
        } catch (err) {
            console.error("Login failed", err);
        }
    }, []);

    const handleRoleChange = async (newRole) => {
        setRole(newRole);
        await loginWithRole(newRole);
    };

    useEffect(() => {
        loginWithRole(role);
    }, [loginWithRole, role]);

    const fetchConnections = async () => {
        try {
            const res = await api.get(`/api/v1/confirm/integrations/connections`);
            setConnections(res.data.connections || []);
            window.dispatchEvent(new Event("connectionsUpdated"));
        } catch (err) {
            console.error("Failed to fetch connections in Sidebar", err);
        }
    };

    useEffect(() => {
        fetchConnections();
    }, []);

    const NAV = [
        { section: "Audit workflow" },
        { to: "/upload-srs", label: "Upload SRS", icon: UploadCloud, step: 1 },
        { to: "/requirements", label: "Planned Requirements", icon: FolderKanban, step: 2 },
        { to: "/configuration", label: "Fetch & Review Tasks", icon: LayoutDashboard, step: 3 },
        { to: "/normalization", label: "Normalization", icon: GitMerge, step: 4 },
        { to: "/matches", label: "Semantic Matches", icon: Link2, step: 5 },
        { to: "/execute", label: "Execute Audit", icon: PlayCircle, step: 6 },
        { section: "Outcomes" },
        { to: "/results", label: "Results", icon: Clock3 },
        { 
            label: "Project FAQs", 
            icon: HelpCircle, 
            onClick: () => {
                if (pathname !== "/results") navigate("/results");
                setShowFaqs(!showFaqs);
                if (!showFaqs) {
                    setTimeout(() => document.getElementById("faq-section")?.scrollIntoView({ behavior: "smooth" }), 100);
                }
            },
            active: pathname.startsWith("/results") && showFaqs
        },
        { 
            label: "Project AI Copilot", 
            icon: Bot, 
            onClick: () => {
                if (pathname !== "/results") navigate("/results");
                setShowCopilot(!showCopilot);
                if (!showCopilot) {
                    setTimeout(() => document.getElementById("copilot-section")?.scrollIntoView({ behavior: "smooth" }), 100);
                }
            },
            active: pathname.startsWith("/results") && showCopilot
        },
    ];

    return (
        <>
        <aside className="hidden lg:flex w-72 shrink-0 border-r border-hairline bg-sidebar flex-col">
            <div className="h-16 flex items-center gap-2 px-6 border-b border-hairline">
                <NavLink to="/" className="flex items-center gap-2">
                    <div className="size-8 rounded-xl bg-ink text-background grid place-items-center font-display text-lg">S</div>
                    <span className="font-display text-lg text-ink font-bold">ScopeSense</span>
                </NavLink>
            </div>
            
            <div className="px-4 py-4">
                <div className="rounded-2xl bg-card border border-hairline p-3 flex items-center gap-3">
                    <div className="size-9 rounded-xl bg-lavender/60 grid place-items-center font-display">v2</div>
                    <div className="text-xs">
                        <div className="font-medium text-ink">ScopeSense Production</div>
                        <div className="text-subtext">Active session</div>
                    </div>
                </div>
            </div>

            <nav className="flex-1 overflow-y-auto px-3 pb-6 space-y-0.5">
                {NAV.map((it, i) => {
                    if ("section" in it) return (
                        <div key={i} className="px-3 pt-5 pb-2 text-[10px] uppercase tracking-[0.18em] text-subtext">
                            {it.section}
                        </div>
                    );
                    const active = "active" in it ? it.active : pathname.startsWith(it.to);
                    const Icon = it.icon;
                    if ("onClick" in it) {
                        return (
                            <button 
                                key={it.label} 
                                onClick={it.onClick}
                                className={`w-full group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition text-left cursor-pointer ${
                                    active ? "bg-card border border-hairline text-ink shadow-[0_1px_2px_rgba(31,41,55,0.04)] font-semibold" : "text-ink/70 hover:bg-sidebar-accent"
                                }`}
                            >
                                <Icon className="size-4" />
                                <span className="flex-1">{it.label}</span>
                            </button>
                        );
                    }
                    return (
                        <NavLink 
                            key={it.to} 
                            to={it.to}
                            className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition ${
                                active ? "bg-card border border-hairline text-ink shadow-[0_1px_2px_rgba(31,41,55,0.04)]" : "text-ink/70 hover:bg-sidebar-accent"
                            }`}
                        >
                            <Icon className="size-4" />
                            <span className="flex-1">{it.label}</span>
                            {"step" in it && it.step && it.step < 4 && <Check className="size-3.5 text-success" />}
                        </NavLink>
                    );
                })}
            </nav>

            <div className="px-3 pb-4">
                <div className="px-3 pt-5 pb-2 text-[10px] uppercase tracking-[0.18em] text-subtext">
                    Integrations
                </div>
                <button
                    onClick={() => { setModalPlatform("jira"); setIntegrationModalOpen(true); }}
                    className="w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition text-ink/70 hover:bg-sidebar-accent"
                >
                    <div className="flex items-center gap-3">
                        <Plug className="size-4" />
                        <span>Jira / Atlassian</span>
                    </div>
                    {connections.find(c => c.platform === "jira") && (
                        <span className="flex size-2 rounded-full bg-success"></span>
                    )}
                </button>
                <button
                    onClick={() => { setModalPlatform("github"); setIntegrationModalOpen(true); }}
                    className="w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition text-ink/70 hover:bg-sidebar-accent mt-0.5"
                >
                    <div className="flex items-center gap-3">
                        <Plug className="size-4" />
                        <span>GitHub</span>
                    </div>
                    {connections.find(c => c.platform === "github") && (
                        <span className="flex size-2 rounded-full bg-success"></span>
                    )}
                </button>
            </div>

            <div className="p-4 border-t border-hairline">
                <label className="block text-xs text-subtext font-semibold uppercase tracking-wider mb-2">
                    Current Role
                </label>
                <select
                    value={role}
                    onChange={(e) => handleRoleChange(e.target.value)}
                    className="w-full bg-card border border-hairline rounded-lg p-2 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                    <option value="manager">Manager</option>
                    <option value="analyst">Analyst</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
        </aside>
        
        <IntegrationModal 
            isOpen={isIntegrationModalOpen} 
            onClose={() => setIntegrationModalOpen(false)} 
            platformName={modalPlatform}
            onConnectionChange={fetchConnections}
        />
        </>
    );
}

export default Sidebar;
