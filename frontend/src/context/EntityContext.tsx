'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type EntityCode = 'SG' | 'VN' | 'KR' | 'IN' | 'JP';

interface EntityContextType {
  entity: EntityCode;
  setEntity: (code: EntityCode) => void;
  entityName: string;
  currency: string;
}

const ENTITY_CONFIG: Record<EntityCode, { name: string; currency: string }> = {
  SG: { name: 'Singapore HQ', currency: 'SGD / USD' },
  VN: { name: 'Vietnam SSC', currency: 'VND' },
  KR: { name: 'Korea Branch', currency: 'KRW' },
  IN: { name: 'India Back-Office', currency: 'INR' },
  JP: { name: 'Japan Office', currency: 'JPY' },
};

const EntityContext = createContext<EntityContextType | undefined>(undefined);

export function EntityProvider({ children }: { children: React.ReactNode }) {
  const [entity, setEntity] = useState<EntityCode>('SG');

  useEffect(() => {
    const handleSwitch = (e: CustomEvent<EntityCode>) => {
      if (e.detail && ['SG', 'VN', 'KR', 'IN', 'JP'].includes(e.detail)) {
        setEntity(e.detail);
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('batu:switch-entity' as any, handleSwitch);
      return () => window.removeEventListener('batu:switch-entity' as any, handleSwitch);
    }
  }, []);

  return (
    <EntityContext.Provider 
      value={{ 
        entity, 
        setEntity, 
        entityName: ENTITY_CONFIG[entity].name,
        currency: ENTITY_CONFIG[entity].currency 
      }}
    >
      {children}
    </EntityContext.Provider>
  );
}

export function useEntity() {
  const context = useContext(EntityContext);
  if (!context) throw new Error('useEntity harus digunakan di dalam EntityProvider');
  return context;
}