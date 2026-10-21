import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "@/components/Spinner";
import { useAuth } from "@/hooks/useAuth";

export function ProtectedRoute({ requireSuperuser = false }: { requireSuperuser?: boolean }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Checking your session" />
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (requireSuperuser && !user?.is_superuser) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
