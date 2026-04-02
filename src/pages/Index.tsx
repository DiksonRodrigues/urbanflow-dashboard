import { useEffect } from "react";
import Dashboard from "@/components/Dashboard";

const Index = () => {
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  return <Dashboard />;
};

export default Index;
