import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { SyncStatus, SyncResponse } from '../types';

type ModalState = {
  open: boolean;
  title: string;
  status: 'running' | 'success' | 'error';
  message: string;
};

export default function SyncPanel() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [detectingDeals, setDetectingDeals] = useState(false);
  const [runningMatches, setRunningMatches] = useState(false);
  const [modal, setModal] = useState<ModalState>({ open: false, title: '', status: 'running', message: '' });

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
    setModal({ open: true, title: 'Email Sync', status: 'running', message: 'Fetching new emails from Gmail...' });
    try {
      const result = await api.post<SyncResponse>('/emails/sync', {});
      setModal({ open: true, title: 'Email Sync', status: 'success', message: result.message });
      await loadStatus();
    } catch {
      setModal({ open: true, title: 'Email Sync', status: 'error', message: 'Sync failed. Check your Gmail connection.' });
    } finally {
      setSyncing(false);
    }
  };

  const handleDetectDeals = async () => {
    setDetectingDeals(true);
    setModal({ open: true, title: 'Deal Detection', status: 'running', message: 'Scanning listings against benchmarks...' });
    try {
      const result = await api.post<{ message: string }>('/deals/detect', {});
      setModal({ open: true, title: 'Deal Detection', status: 'success', message: result.message });
    } catch {
      setModal({ open: true, title: 'Deal Detection', status: 'error', message: 'Deal detection failed.' });
    } finally {
      setDetectingDeals(false);
    }
  };

  const handleRunMatches = async () => {
    setRunningMatches(true);
    setModal({ open: true, title: 'Buyer-Seller Matching', status: 'running', message: 'Matching buyers to listings...' });
    try {
      const result = await api.post<{ message: string }>('/matches/run', {});
      setModal({ open: true, title: 'Buyer-Seller Matching', status: 'success', message: result.message });
    } catch {
      setModal({ open: true, title: 'Buyer-Seller Matching', status: 'error', message: 'Matching failed.' });
    } finally {
      setRunningMatches(false);
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

      <div className="flex gap-2 mt-2">
        <button
          onClick={handleDetectDeals}
          disabled={detectingDeals}
          className="flex-1 px-3 py-1.5 text-xs font-medium rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {detectingDeals ? 'Running...' : 'Detect Deals'}
        </button>
        <button
          onClick={handleRunMatches}
          disabled={runningMatches}
          className="flex-1 px-3 py-1.5 text-xs font-medium rounded bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {runningMatches ? 'Running...' : 'Run Matching'}
        </button>
      </div>

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
      {modal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => modal.status !== 'running' && setModal(m => ({ ...m, open: false }))}>
          <div className="bg-white rounded-lg shadow-xl w-80 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">{modal.title}</h3>

            <div className="flex items-center gap-3 mb-4">
              {modal.status === 'running' && (
                <svg className="animate-spin h-5 w-5 text-blue-600 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {modal.status === 'success' && (
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-100 text-green-600 shrink-0">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              )}
              {modal.status === 'error' && (
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-100 text-red-600 shrink-0">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </span>
              )}
              <p className="text-sm text-gray-700">{modal.message}</p>
            </div>

            {modal.status !== 'running' && (
              <button
                onClick={() => setModal(m => ({ ...m, open: false }))}
                className="w-full px-3 py-1.5 text-xs font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
