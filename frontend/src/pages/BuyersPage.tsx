import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { BuyerRequest, PaginatedResponse } from '../types';
import BuyerCard from '../components/BuyerCard';
import Pagination from '../components/Pagination';

export default function BuyersPage() {
  const [data, setData] = useState<PaginatedResponse<BuyerRequest> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const result = await api.get<PaginatedResponse<BuyerRequest>>(`/buyers?page=${page}`);
        setData(result);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [page]);

  if (loading) return <p className="text-gray-500">Loading buyers...</p>;
  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No buyer requests</h2>
        <p className="text-gray-500">Buyer requests will appear as they are extracted from emails.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Buyer Requests ({data.total})</h2>
      <div className="space-y-3">
        {data.items.map((buyer) => (
          <BuyerCard key={buyer.id} buyer={buyer} />
        ))}
      </div>
      <Pagination page={page} pages={data.pages} onPageChange={setPage} />
    </div>
  );
}
