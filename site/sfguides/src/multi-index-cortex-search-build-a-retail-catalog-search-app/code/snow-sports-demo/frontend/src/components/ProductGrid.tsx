import { SearchX } from 'lucide-react';
import ProductCard from './ProductCard';
import type { Product, SearchResult } from '../api';

interface ProductGridProps {
  products: (Product | SearchResult)[];
  total?: number;
  isLoading?: boolean;
  isSearch?: boolean;
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden animate-pulse">
      <div className="h-48 bg-slate-200" />
      <div className="p-4 space-y-3">
        <div className="h-3 bg-slate-200 rounded w-1/3" />
        <div className="h-4 bg-slate-200 rounded w-4/5" />
        <div className="h-3 bg-slate-200 rounded w-1/2" />
        <div className="h-6 bg-slate-200 rounded w-1/4 mt-4" />
      </div>
    </div>
  );
}

export default function ProductGrid({
  products,
  total,
  isLoading = false,
  isSearch = false,
}: ProductGridProps) {
  return (
    <div>
      {/* Header count */}
      {!isLoading && (
        <div className="text-sm text-slate-500 mb-4">
          {isSearch ? (
            <span>
              Found{' '}
              <span className="font-semibold text-slate-900">{products.length}</span> results
            </span>
          ) : (
            <span>
              Showing{' '}
              <span className="font-semibold text-slate-900">{products.length}</span>
              {total !== undefined && total > products.length && (
                <> of <span className="font-semibold text-slate-900">{total}</span></>
              )}{' '}
              products
            </span>
          )}
        </div>
      )}

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
          <SearchX className="w-12 h-12 opacity-40" />
          <p className="text-lg font-medium">No products found</p>
          <p className="text-sm">Try adjusting your filters or search query</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product, i) => (
            <ProductCard
              key={product.product_id}
              product={product}
              isSearch={isSearch}
              index={i}
            />
          ))}
        </div>
      )}
    </div>
  );
}
