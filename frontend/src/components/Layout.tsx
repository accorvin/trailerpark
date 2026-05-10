import { NavLink, Outlet } from 'react-router-dom';
import StatsBar from './StatsBar';

const navItems = [
  { to: '/', label: 'Deals' },
  { to: '/listings', label: 'Listings' },
  { to: '/buyers', label: 'Buyers' },
  { to: '/matches', label: 'Matches' },
  { to: '/benchmarks', label: 'Benchmarks' },
  { to: '/archive', label: 'Archive' },
];

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <nav className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">TrailerPark</h1>
          <p className="text-xs text-gray-500 mt-1">Deal Aggregator</p>
        </div>
        <ul className="flex-1 py-2">
          {navItems.map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `block px-4 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <StatsBar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
