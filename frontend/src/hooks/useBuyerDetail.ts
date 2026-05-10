import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { BuyerDetail } from '../types';

export function useBuyerDetail(id: number | string) {
  const [data, setData] = useState<BuyerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const result = await api.get<BuyerDetail>(`/buyers/${id}`);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load buyer request');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id]);

  return { data, loading, error };
}
