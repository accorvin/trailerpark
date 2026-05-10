import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Listing, PaginatedResponse } from '../types';

export function useDeals(page: number = 1) {
  const [data, setData] = useState<PaginatedResponse<Listing> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.get<PaginatedResponse<Listing>>(`/deals?page=${page}`);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load deals');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [page]);

  return { data, loading, error };
}
