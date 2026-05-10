import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DealsPage from './pages/DealsPage';
import ListingsPage from './pages/ListingsPage';
import ListingDetailPage from './pages/ListingDetailPage';
import BuyersPage from './pages/BuyersPage';
import MatchesPage from './pages/MatchesPage';
import BenchmarksPage from './pages/BenchmarksPage';
import ArchivePage from './pages/ArchivePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DealsPage />} />
          <Route path="/listings" element={<ListingsPage />} />
          <Route path="/listings/:id" element={<ListingDetailPage />} />
          <Route path="/buyers" element={<BuyersPage />} />
          <Route path="/matches" element={<MatchesPage />} />
          <Route path="/benchmarks" element={<BenchmarksPage />} />
          <Route path="/archive" element={<ArchivePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
