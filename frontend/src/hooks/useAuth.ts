import { useState, useCallback } from "react";

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  const login = useCallback((newToken: string) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
  }, []);

  return {
    token,
    isAuthenticated: !!token,
    login,
    logout,
  };
}
