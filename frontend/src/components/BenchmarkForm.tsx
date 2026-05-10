import { useState } from 'react';
import type { PriceBenchmark } from '../types';

interface Props {
  initial?: Partial<PriceBenchmark>;
  onSubmit: (data: Omit<PriceBenchmark, 'id' | 'created_at' | 'updated_at'>) => void;
  onCancel: () => void;
}

export default function BenchmarkForm({ initial, onSubmit, onCancel }: Props) {
  const [form, setForm] = useState({
    vehicle_type: initial?.vehicle_type || '',
    make: initial?.make || '',
    model: initial?.model || '',
    year_min: initial?.year_min?.toString() || '',
    year_max: initial?.year_max?.toString() || '',
    mileage_min: initial?.mileage_min?.toString() || '',
    mileage_max: initial?.mileage_max?.toString() || '',
    benchmark_price: initial?.benchmark_price?.toString() || '',
    notes: initial?.notes || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      vehicle_type: form.vehicle_type || null,
      make: form.make || null,
      model: form.model || null,
      year_min: form.year_min ? parseInt(form.year_min) : null,
      year_max: form.year_max ? parseInt(form.year_max) : null,
      mileage_min: form.mileage_min ? parseInt(form.mileage_min) : null,
      mileage_max: form.mileage_max ? parseInt(form.mileage_max) : null,
      benchmark_price: parseFloat(form.benchmark_price),
      notes: form.notes || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <input
          type="text" placeholder="Vehicle type" value={form.vehicle_type}
          onChange={(e) => setForm({ ...form, vehicle_type: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text" placeholder="Make" value={form.make}
          onChange={(e) => setForm({ ...form, make: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text" placeholder="Model" value={form.model}
          onChange={(e) => setForm({ ...form, model: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number" placeholder="Benchmark price *" value={form.benchmark_price}
          onChange={(e) => setForm({ ...form, benchmark_price: e.target.value })}
          className="rounded-md border-gray-300 text-sm" required
        />
        <input
          type="number" placeholder="Year min" value={form.year_min}
          onChange={(e) => setForm({ ...form, year_min: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number" placeholder="Year max" value={form.year_max}
          onChange={(e) => setForm({ ...form, year_max: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number" placeholder="Mileage min" value={form.mileage_min}
          onChange={(e) => setForm({ ...form, mileage_min: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number" placeholder="Mileage max" value={form.mileage_max}
          onChange={(e) => setForm({ ...form, mileage_max: e.target.value })}
          className="rounded-md border-gray-300 text-sm"
        />
      </div>
      <input
        type="text" placeholder="Notes" value={form.notes}
        onChange={(e) => setForm({ ...form, notes: e.target.value })}
        className="w-full rounded-md border-gray-300 text-sm"
      />
      <div className="flex gap-2">
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">
          Save
        </button>
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">
          Cancel
        </button>
      </div>
    </form>
  );
}
