import { Routes, Route } from "react-router-dom";
import { SRSProvider } from "./context/SRSContext";
import { ProjectProvider } from "./context/ProjectContext";
import { AuditProvider } from "./context/AuditContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { Toaster } from "react-hot-toast";

import FeaturesPage from "./pages/FeaturesPage";
import ResultsDashboard from "./pages/ResultsDashboard";
import AuditPage from "./pages/AuditPage";
import SRSUploadPage from "./pages/SRSUploadPage";
import ProjectSetupPage from "./pages/ProjectSetupPage";
import NormalizationPage from "./pages/NormalizationPage";
import MatchApprovalPage from "./pages/MatchApprovalPage";
import AuditReportPage from "./pages/AuditReportPage";

import MainLayout from "./layouts/MainLayout";

function App() {
    return (
        <SRSProvider>
            <ProjectProvider>
                <AuditProvider>
                    <MainLayout>
                        <Toaster position="bottom-right" toastOptions={{ style: { background: '#fefefe', color: '#1a1a1a', borderRadius: '12px', border: '1px solid #e5e5e5' } }} />
                        <Routes>
                             <Route path="/upload-srs" element={<SRSUploadPage />} />
                             <Route path="/requirements" element={<FeaturesPage />} />
                             <Route path="/configuration" element={<ProtectedRoute component={ProjectSetupPage} />} />
                             <Route path="/normalization" element={<ProtectedRoute component={NormalizationPage} />} />
                             <Route path="/matches" element={<ProtectedRoute component={MatchApprovalPage} />} />
                             <Route path="/execute" element={<ProtectedRoute component={AuditPage} />} />
                             <Route path="/results" element={<ProtectedRoute component={ResultsDashboard} />} />
                             <Route path="/audit/:auditId/report" element={<ProtectedRoute component={AuditReportPage} />} />
                        </Routes>
                    </MainLayout>
                </AuditProvider>
            </ProjectProvider>
        </SRSProvider>
    );
}

export default App;
