import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
  { path: "/creators", label: "Creators" },
];

export default function Layout() {
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-64 border-r bg-muted/30 p-6 flex flex-col">
        <h1 className="text-lg font-semibold mb-8">Creator Outreach</h1>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-2 rounded-md text-sm transition-colors ${
                location.pathname.startsWith(item.path)
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={logout}
          className="px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted transition-colors text-left"
        >
          Sign out
        </button>
      </aside>
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
