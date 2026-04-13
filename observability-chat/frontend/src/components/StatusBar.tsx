import { useState, useEffect } from 'react';
import type { HealthResponse } from '../types';

interface StatusBarProps {
  onClear: () => void;
}

export function StatusBar({ onClear }: StatusBarProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) setHealth(await res.json());
      } catch {
        setHealth(null);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-4 border-b border-neutral-200 px-4 py-2">
      <span className="text-sm font-semibold text-black">Observability Chat</span>
      <div className="ml-auto flex items-center gap-3">
        {health ? (
          Object.entries(health.mcp_servers).map(([name, status]) => (
            <div key={name} className="flex items-center gap-1.5 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  status === 'connected' ? 'bg-black' : 'bg-neutral-300'
                }`}
              />
              <span className="text-neutral-500">{name}</span>
            </div>
          ))
        ) : (
          <span className="text-xs text-neutral-400">Connecting...</span>
        )}
        <button
          onClick={onClear}
          className="ml-2 rounded px-2 py-1 text-xs text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-black"
        >
          New chat
        </button>
      </div>
    </div>
  );
}
