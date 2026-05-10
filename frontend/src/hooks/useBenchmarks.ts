import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import type { PriceBenchmark } from '../types';

export function useBenchmarks() {
  const [data, setData] = useState<PriceBenchmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<PriceBenchmark[]>('/benchmarks');
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load benchmarks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const create = async (benchmark: Omit<PriceBenchmark, 'id' | 'created_at' | 'updated_at'>) => {
    await api.post('/benchmarks', benchmark);
    await fetch();
  };

  const update = async (id: number, benchmark: Partial<PriceBenchmark>) => {
    await api.put(`/benchmarks/${id}`, benchmark);
    await fetch();
  };

  const remove = async (id: number) => {
    await api.delete(`/benchmarks/${id}`);
    await fetch();
  };

  return { data, loading, error, create, update, remove, refetch: fetch };
}
