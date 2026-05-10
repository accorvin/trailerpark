import { useState } from 'react';
import { useBenchmarks } from '../hooks/useBenchmarks';
import BenchmarkForm from '../components/BenchmarkForm';

export default function BenchmarksPage() {
  const { data, loading, error, create, update, remove } = useBenchmarks();
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);

  if (loading) return <p className="text-gray-500">Loading benchmarks...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Price Benchmarks</h2>
        <button
          onClick={() => { setShowForm(true); setEditId(null); }}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        >
          Add Benchmark
        </button>
      </div>

      {showForm && !editId && (
        <BenchmarkForm
          onSubmit={async (data) => { await create(data); setShowForm(false); }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {data.length === 0 && !showForm ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No benchmarks set. Add one to enable deal detection.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Make</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Year Range</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mileage Range</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Benchmark Price</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((bench) => (
                <tr key={bench.id}>
                  {editId === bench.id ? (
                    <td colSpan={8} className="p-0">
                      <BenchmarkForm
                        initial={bench}
                        onSubmit={async (data) => { await update(bench.id, data); setEditId(null); }}
                        onCancel={() => setEditId(null)}
                      />
                    </td>
                  ) : (
                    <>
                      <td className="px-4 py-3 text-sm text-gray-900">{bench.vehicle_type || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{bench.make || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{bench.model || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {bench.year_min && bench.year_max ? `${bench.year_min}-${bench.year_max}` : bench.year_min || bench.year_max || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {bench.mileage_min != null || bench.mileage_max != null
                          ? `${bench.mileage_min?.toLocaleString() || '0'}-${bench.mileage_max?.toLocaleString() || '...'}`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        ${bench.benchmark_price.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">{bench.notes || '-'}</td>
                      <td className="px-4 py-3 text-sm text-right space-x-2">
                        <button
                          onClick={() => setEditId(bench.id)}
                          className="text-blue-600 hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => { if (confirm('Delete this benchmark?')) remove(bench.id); }}
                          className="text-red-600 hover:underline"
                        >
                          Delete
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
