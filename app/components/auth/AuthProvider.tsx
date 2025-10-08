import type { ReactNode } from 'react';
import { useAuth } from '~/hooks/useAuth';

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize auth on app load
  useAuth();
  
  return <>{children}</>;
}
