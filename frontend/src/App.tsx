import { Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { HomePage } from "@/pages/HomePage";
import { DiagnoseView } from "@/pages/DiagnoseView";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/diagnose" element={<DiagnoseView />} />
      </Routes>
    </QueryClientProvider>
  );
}
