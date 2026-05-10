import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { SyncStatus, SyncResponse } from '../types';

export default function SyncPanel() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const data = await api.get<SyncStatus>('/emails/sync-status');
      setStatus(data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await api.post<SyncResponse>('/emails/sync', {});
      setSyncResult(result.message);
      await loadStatus();
    } catch {
      setSyncResult('Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  if (!status) return null;

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <div className="border-t border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Email Sync
        </h3>
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            status.gmail_connected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={status.gmail_connected ? 'Gmail connected' : 'Gmail not connected'}
        />
      </div>

      {status.last_sync_at && (
        <p className="text-xs text-gray-500 mb-1">
          Last sync: {formatTime(status.last_sync_at)}
          {status.last_sync_status === 'error' && (
            <span className="text-red-500 ml-1" title={status.last_sync_error || ''}>
              (error)
            </span>
          )}
        </p>
      )}

      <div className="grid grid-cols-2 gap-1 text-xs text-gray-600 mb-3">
        <span>Listings: {status.seller_listings}</span>
        <span>Buyers: {status.buyer_requests}</span>
        <span>Irrelevant: {status.irrelevant}</span>
        <span>Errors: {status.parse_errors}</span>
      </div>

      <p className="text-xs text-gray-500 mb-2">
        Total processed: {status.total_emails}
      </p>

      <button
        onClick={handleSync}
        disabled={syncing || !status.gmail_connected}
        className="w-full px-3 py-1.5 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {syncing ? 'Syncing...' : 'Sync Now'}
      </button>

      {syncResult && (
        <p className="text-xs text-gray-600 mt-1.5 text-center">{syncResult}</p>
      )}

      {status.recent_emails.length > 0 && (
        <div className="mt-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Recent
          </h4>
          <ul className="space-y-1">
            {status.recent_emails.slice(0, 5).map((email) => (
              <li key={email.id} className="text-xs text-gray-600 truncate" title={email.subject || ''}>
                <span
                  className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${
                    email.classification === 'seller_listing'
                      ? 'bg-blue-500'
                      : email.classification === 'buyer_request'
                        ? 'bg-green-500'
                        : email.classification === 'parse_error'
                          ? 'bg-red-500'
                          : 'bg-gray-400'
                  }`}
                />
                {email.subject || '(no subject)'}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
