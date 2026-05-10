import type { BuyerRequest } from '../types';

interface Props {
  buyer: BuyerRequest;
}

function formatPrice(price: number | null): string {
  if (price === null) return 'Any';
  return `$${price.toLocaleString()}`;
}

export default function BuyerCard({ buyer }: Props) {
  const specs = [buyer.make, buyer.model].filter(Boolean).join(' ') || 'Any vehicle';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-gray-900">{specs}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {buyer.vehicle_type && <span className="capitalize">{buyer.vehicle_type}</span>}
          </p>
        </div>
        <div className="text-right text-sm">
          <p className="text-gray-600">
            Budget: {formatPrice(buyer.price_min)} - {formatPrice(buyer.price_max)}
          </p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-sm text-gray-600">
        {buyer.year_min && buyer.year_max && (
          <span>Year: {buyer.year_min}-{buyer.year_max}</span>
        )}
        {buyer.mileage_max && <span>Max mileage: {(buyer.mileage_max / 1000).toFixed(0)}k</span>}
        {buyer.engine_type && <span>{buyer.engine_type}</span>}
        {buyer.location && <span>{buyer.location}</span>}
      </div>
      {buyer.buyer_name && (
        <p className="mt-2 text-xs text-gray-400">
          Buyer: {buyer.buyer_name}
          {buyer.buyer_contact && ` (${buyer.buyer_contact})`}
        </p>
      )}
      {buyer.description && (
        <p className="mt-2 text-sm text-gray-500 italic">{buyer.description}</p>
      )}
    </div>
  );
}
