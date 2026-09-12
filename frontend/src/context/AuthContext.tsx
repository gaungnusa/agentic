'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserProfile {
  username: string;
  full_name: string;
  email: string;
  role: 'purchasing' | 'sales' | 'warehouse' | 'treasury' | 'auditor' | 'admin';
  entity_code: string;
}

interface AuthContextType {
  user: UserProfile;
  token: string | null;
  switchPersona: (username: string) => Promise<void>;
  demoPersonas: UserProfile[];
  loading: boolean;
}

const DEFAULT_USER: UserProfile = {
  username: 'sg_purchaser',
  full_name: 'Tan Wei Ming (Purchasing Specialist)',
  email: 'weiming.tan@batu-networks.sg',
  role: 'purchasing',
  entity_code: 'SG',
};

const DEMO_PERSONAS: UserProfile[] = [
  {
    username: 'sg_purchaser',
    full_name: 'Tan Wei Ming (Purchasing Lead)',
    email: 'weiming.tan@batu-networks.sg',
    role: 'purchasing',
    entity_code: 'SG',
  },
  {
    username: 'sg_sales',
    full_name: 'Clara Lim (Sales Director)',
    email: 'clara.lim@batu-networks.sg',
    role: 'sales',
    entity_code: 'SG',
  },
  {
    username: 'vn_logistics',
    full_name: 'Nguyen Van Thao (Warehouse Head)',
    email: 'thao.nguyen@batu-networks.vn',
    role: 'warehouse',
    entity_code: 'VN',
  },
  {
    username: 'sg_treasurer',
    full_name: 'Marcus Goh (Treasury Controller)',
    email: 'marcus.goh@batu-networks.sg',
    role: 'treasury',
    entity_code: 'SG',
  },
  {
    username: 'compliance_auditor',
    full_name: 'Sarah Jenkins (Senior Auditor)',
    email: 'sarah.jenkins@batu-networks.com',
    role: 'auditor',
    entity_code: 'ALL',
  },
  {
    username: 'admin',
    full_name: 'Enterprise System Admin',
    email: 'admin@batu-networks.com',
    role: 'admin',
    entity_code: 'ALL',
  },
];

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile>(DEFAULT_USER);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check localStorage for saved persona & access token
    const savedUser = localStorage.getItem('batu_active_user');
    const savedToken = localStorage.getItem('batu_access_token');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
      } catch {
        // ignore
      }
    }
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  const switchPersona = async (username: string) => {
    const matched = DEMO_PERSONAS.find((p) => p.username === username);
    if (!matched) return;

    setLoading(true);
    try {
      // Try login to get valid JWT from backend
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: matched.username,
          password: 'password', // Demo mode allows 'password'
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setToken(data.access_token);
        localStorage.setItem('batu_active_user', JSON.stringify(data.user));
        localStorage.setItem('batu_access_token', data.access_token);
      } else {
        // Fallback local switch
        setUser(matched);
        localStorage.setItem('batu_active_user', JSON.stringify(matched));
      }
    } catch {
      // Fallback local switch if server offline
      setUser(matched);
      localStorage.setItem('batu_active_user', JSON.stringify(matched));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        switchPersona,
        demoPersonas: DEMO_PERSONAS,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
