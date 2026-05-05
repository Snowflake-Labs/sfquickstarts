import { useState, useEffect, useCallback } from 'react';
import { getFilters, getProducts, multiSearch } from './api';
import type { Product, SearchResult, MultiSearchResponse, FiltersResponse } from './api';
import Header from './components/Header';
import CategoryTabs from './components/CategoryTabs';
import FilterSidebar from './components/FilterSidebar';
import ProductGrid from './components/ProductGrid';
import MultiIndexInsights from './components/MultiIndexInsights';

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MultiSearchResponse | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<FiltersResponse | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [isSearching, setIsSearching] = useState(false);
  const [isBrowsing, setIsBrowsing] = useState(false);
  const [activeCategory, setActiveCategory] = useState('All');

  // Load filter metadata once
  useEffect(() => {
    getFilters().then(setFilters).catch(console.error);
  }, []);

  // Reload products whenever category/filters change (browse mode only)
  useEffect(() => {
    if (searchResults !== null) return;

    const combinedFilters: Record<string, string> = { ...activeFilters };
    if (activeCategory !== 'All') combinedFilters.category = activeCategory;

    setIsBrowsing(true);
    getProducts(combinedFilters, 20, 0)
      .then(result => {
        setProducts(result.products);
        setTotal(result.total);
      })
      .catch(console.error)
      .finally(() => setIsBrowsing(false));
    // intentionally omit searchResults from deps — it's used only as a guard
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCategory, activeFilters]);

  // When searchResults is cleared go back to browse and reload products
  useEffect(() => {
    if (searchResults !== null) return;

    const combinedFilters: Record<string, string> = { ...activeFilters };
    if (activeCategory !== 'All') combinedFilters.category = activeCategory;

    setIsBrowsing(true);
    getProducts(combinedFilters, 20, 0)
      .then(result => {
        setProducts(result.products);
        setTotal(result.total);
      })
      .catch(console.error)
      .finally(() => setIsBrowsing(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchResults]);

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) return;
    setSearchQuery(query);
    setIsSearching(true);
    try {
      const results = await multiSearch(query);
      setSearchResults(results);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleClear = useCallback(() => {
    setSearchQuery('');
    setSearchResults(null);
  }, []);

  const handleCategoryChange = useCallback((cat: string) => {
    setActiveCategory(cat);
    // Clear search when switching category
    if (searchResults) {
      setSearchQuery('');
      setSearchResults(null);
    }
  }, [searchResults]);

  const handleFilterChange = useCallback((newFilters: Record<string, string>) => {
    setActiveFilters(newFilters);
    // Clear search when filters change
    if (searchResults) {
      setSearchQuery('');
      setSearchResults(null);
    }
  }, [searchResults]);

  const searchResultsAsProducts: (Product | SearchResult)[] =
    searchResults?.results ?? [];

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <Header
        searchQuery={searchQuery}
        onSearch={handleSearch}
        onClear={handleClear}
        isSearching={isSearching}
      />

      {/* Category tabs */}
      <CategoryTabs activeCategory={activeCategory} onChange={handleCategoryChange} />

      {/* Body: sidebar + main */}
      <div className="flex flex-1 overflow-hidden max-w-7xl w-full mx-auto">
        <FilterSidebar
          filters={filters}
          activeFilters={activeFilters}
          onChange={handleFilterChange}
        />

        <main className="flex-1 overflow-y-auto p-6">
          {searchResults ? (
            <div className="flex gap-6 items-start">
              <div className="flex-1 min-w-0">
                <ProductGrid products={searchResultsAsProducts} isSearch />
              </div>
              <div className="w-52 shrink-0 sticky top-6">
                <MultiIndexInsights data={searchResults} onClear={handleClear} />
              </div>
            </div>
          ) : (
            <ProductGrid
              products={products}
              total={total}
              isLoading={isBrowsing}
            />
          )}
        </main>
      </div>
    </div>
  );
}
