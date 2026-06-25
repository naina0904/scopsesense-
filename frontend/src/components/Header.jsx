import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";
import { Search, Bell, ChevronRight } from "lucide-react";
import { useLocation, Link } from "react-router-dom";

// Mapping routes to clean names for Breadcrumbs
const ROUTE_NAMES = {
  "/upload-srs": "Upload SRS",
  "/requirements": "Planned Requirements",
  "/configuration": "Platform Configuration",
  "/normalization": "Normalization",
  "/matches": "Semantic Matches",
  "/execute": "Execute Audit",
  "/results": "Results",
  "/audit-intelligence": "Audit Intelligence"
};

function Breadcrumb({ pathname }) {
  const seg = pathname.split("/").filter(Boolean);
  const matchedName = ROUTE_NAMES[pathname] || (seg.length > 0 ? seg[0] : "Dashboard");

  return (
    <nav className="flex items-center gap-2 text-sm">
      <Link to="/" className="text-subtext hover:text-ink">Workspace</Link>
      {seg.length > 0 && (
        <span className="flex items-center gap-2">
          <ChevronRight className="size-3.5 text-subtext" />
          <span className="text-ink font-medium">{matchedName}</span>
        </span>
      )}
    </nav>
  );
}

function Header() {
  const location = useLocation();
  const [role, setRole] = useState(localStorage.getItem("scopesense_role") || "manager");

  const handleRoleChange = async (newRole) => {
    setRole(newRole);
    localStorage.setItem("scopesense_role", newRole);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
        user_id: 1,
        role: newRole
      });
      localStorage.setItem("scopesense_token", response.data.access_token);
    } catch (err) {
      console.error("Login failed", err);
    }
  };

  useEffect(() => {
    handleRoleChange(role);
  }, []);

  return (
    <header className="h-16 border-b border-hairline bg-background/80 backdrop-blur sticky top-0 z-30 flex items-center gap-4 px-6 lg:px-10">
      <Breadcrumb pathname={location.pathname} />
      <div className="flex-1" />
      <div className="hidden md:flex items-center gap-2 h-10 px-3 rounded-full border border-hairline bg-card w-80 max-w-full">
        <Search className="size-4 text-subtext" />
        <input placeholder="Search requirements, issues, people…" className="bg-transparent text-ink outline-none text-sm flex-1" />
        <span className="text-[10px] text-subtext font-mono">⌘K</span>
      </div>
      <button className="size-10 rounded-full border border-hairline bg-card grid place-items-center text-ink"><Bell className="size-4" /></button>
    </header>
  );
}

export default Header;
