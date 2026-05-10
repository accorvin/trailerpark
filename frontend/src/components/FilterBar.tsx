interface Filters {
  vehicle_type: string;
  make: string;
  model: string;
  year_min: string;
  year_max: string;
  price_min: string;
  price_max: string;
  mileage_max: string;
  engine_type: string;
  location: string;
}

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export default function FilterBar({ filters, onChange }: Props) {
  const update = (key: keyof Filters, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <input
          type="text"
          placeholder="Vehicle type"
          value={filters.vehicle_type}
          onChange={(e) => update('vehicle_type', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text"
          placeholder="Make"
          value={filters.make}
          onChange={(e) => update('make', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text"
          placeholder="Model"
          value={filters.model}
          onChange={(e) => update('model', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number"
          placeholder="Year min"
          value={filters.year_min}
          onChange={(e) => update('year_min', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number"
          placeholder="Year max"
          value={filters.year_max}
          onChange={(e) => update('year_max', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number"
          placeholder="Price min"
          value={filters.price_min}
          onChange={(e) => update('price_min', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number"
          placeholder="Price max"
          value={filters.price_max}
          onChange={(e) => update('price_max', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="number"
          placeholder="Max mileage"
          value={filters.mileage_max}
          onChange={(e) => update('mileage_max', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text"
          placeholder="Engine type"
          value={filters.engine_type}
          onChange={(e) => update('engine_type', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
        <input
          type="text"
          placeholder="Location"
          value={filters.location}
          onChange={(e) => update('location', e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        />
      </div>
    </div>
  );
}
