import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import CreatorList from "@/pages/CreatorList";
import CreatorNew from "@/pages/CreatorNew";
import CreatorDetail from "@/pages/CreatorDetail";
import BrandDiscovery from "@/pages/BrandDiscovery";
import CreatorContacts from "@/pages/CreatorContacts";
import ContactList from "@/pages/ContactList";
import EmailDrafts from "@/pages/EmailDrafts";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/creators" element={<CreatorList />} />
            <Route path="/creators/new" element={<CreatorNew />} />
            <Route path="/creators/:id" element={<CreatorDetail />} />
            <Route path="/creators/:id/brands" element={<BrandDiscovery />} />
            <Route path="/creators/:id/contacts" element={<CreatorContacts />} />
            <Route path="/creators/:id/brands/:brandId/contacts" element={<ContactList />} />
            <Route path="/creators/:id/emails" element={<EmailDrafts />} />
          </Route>
          <Route path="*" element={<Navigate to="/creators" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
