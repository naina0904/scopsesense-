import { createContext, useContext, useState } from "react";

const SRSContext = createContext();

export const useSRS = () => useContext(SRSContext);

export const SRSProvider = ({ children }) => {
  const [srsFile, setSRSFile] = useState(null);
  const [extractionConfirmed, setExtractionConfirmed] = useState(false);
  const value = {
    srsFile,
    setSRSFile,
    extractionConfirmed,
    setExtractionConfirmed,
  };
  return <SRSContext.Provider value={value}>{children}</SRSContext.Provider>;
};
