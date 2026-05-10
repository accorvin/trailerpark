interface Props {
  savings: number | null;
}

export default function DealBadge({ savings }: Props) {
  if (savings === null) return null;

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      Deal: ${savings.toLocaleString()} below market
    </span>
  );
}
