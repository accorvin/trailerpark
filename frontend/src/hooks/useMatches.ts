import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Match, PaginatedResponse } from '../types';

export function useMatches(page: number = 1) {
  const [data, setData] = useState<PaginatedResponse<Match> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.get<PaginatedResponse<Match>>(`/matches?page=${page}`);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load matches');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [page]);

  return { data, loading, error };
}
