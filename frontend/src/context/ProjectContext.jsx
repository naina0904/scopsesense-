import { createContext, useContext, useState } from "react";

const ProjectContext = createContext();

export const useProject = () => useContext(ProjectContext);

export const ProjectProvider = ({ children }) => {
  const [platform, setPlatform] = useState("github");
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [githubPat, setGithubPat] = useState("");
  const [jiraDomain, setJiraDomain] = useState("");
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraApiToken, setJiraApiToken] = useState("");
  const [jiraUsername, setJiraUsername] = useState("");
  const [projectDataConfirmed, setProjectDataConfirmed] = useState(false);

  const value = {
    platform,
    setPlatform,
    owner,
    setOwner,
    repo,
    setRepo,
    githubPat,
    setGithubPat,
    jiraDomain,
    setJiraDomain,
    jiraProjectKey,
    setJiraProjectKey,
    jiraEmail,
    setJiraEmail,
    jiraApiToken,
    setJiraApiToken,
    jiraUsername,
    setJiraUsername,
    projectDataConfirmed,
    setProjectDataConfirmed,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};
