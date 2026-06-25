import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useSRS } from "../context/SRSContext";
import { useProject } from "../context/ProjectContext";
import { useAudit } from "../context/AuditContext";

/**
 * ProtectedRoute renders the given component only if the SRS extraction
 * has been confirmed and the project data has been confirmed.
 * Otherwise it redirects the user to the appropriate step.
 */
const ProtectedRoute = ({ component: Component }) => {
  const { auditSession, fetchActiveSession, sessionLoading } = useAudit();
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    if (!auditSession) {
      fetchActiveSession().catch(() => {});
    }
  }, [auditSession, fetchActiveSession]);

  React.useEffect(() => {
    if (sessionLoading) return;
    
    if (!auditSession) {
      navigate("/upload-srs");
      return;
    }

    const path = location.pathname;
    let canAccess = false;
    let redirectTo = "/";

    if (path === "/configuration") {
      canAccess = auditSession.planned_data_approved;
      redirectTo = "/upload-srs";
    } else if (path === "/normalization") {
      canAccess = auditSession.planned_data_approved && auditSession.actual_data_approved && auditSession.capacity_approved;
      redirectTo = "/configuration";
    } else if (path === "/matches") {
      canAccess = auditSession.normalized_data_approved;
      redirectTo = "/normalization";
    } else if (path === "/execute") {
      canAccess = auditSession.matches_approved;
      redirectTo = "/matches";
    } else if (path === "/results" || path === "/audit-intelligence" || path.startsWith("/audit/")) {
      canAccess = auditSession.matches_approved;
      redirectTo = "/execute";
    } else {
      canAccess = true;
    }

    if (!canAccess) {
      navigate(redirectTo, { state: { from: location.pathname } });
    }
  }, [auditSession, sessionLoading, location.pathname, navigate]);

  if (sessionLoading && !auditSession) {
    return (
      <div className="mx-auto max-w-2xl rounded-md border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
        Loading workflow state...
      </div>
    );
  }

  if (!auditSession) {
    return null; // Will redirect in useEffect
  }

  // Prevent flicker before redirect
  const path = location.pathname;
  let canAccess = false;
  if (path === "/configuration") canAccess = auditSession.planned_data_approved;
  else if (path === "/normalization") canAccess = auditSession.planned_data_approved && auditSession.actual_data_approved && auditSession.capacity_approved;
  else if (path === "/matches") canAccess = auditSession.normalized_data_approved;
  else if (path === "/execute" || path === "/results" || path === "/audit-intelligence" || path.startsWith("/audit/")) canAccess = auditSession.matches_approved;
  else canAccess = true;

  if (canAccess) {
    return <Component />;
  }
  return null;
};

export default ProtectedRoute;

