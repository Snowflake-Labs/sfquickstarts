const API_BASE = '/api';

export interface Product {
  product_id: number;
  item_name: string;
  description?: string;
  category: string;
  subcategory: string;
  brand: string;
  price: number;
  skill_level: string;
  discipline: string;
  gender: string;
  product_type: string;
  flex_rating?: string;
}

export interface SearchResult extends Product {
  source_index: string;
  source_label: string;
  source_color: string;
}

export interface IndexBreakdown {
  [key: string]: { count: number; label: string; color: string };
}

export interface MultiSearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
  index_breakdown: IndexBreakdown;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
}

export interface FiltersResponse {
  categories: string[];
  brands: string[];
  skill_levels: string[];
  disciplines: string[];
  genders: string[];
}

export async function multiSearch(
  query: string,
  limit = 20,
): Promise<MultiSearchResponse> {
  const res = await fetch(`${API_BASE}/search/multi`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getProducts(
  filters: Record<string, string> = {},
  limit = 20,
  offset = 0,
): Promise<ProductsResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    ...filters,
  });
  const res = await fetch(`${API_BASE}/products?${params}`);
  if (!res.ok) throw new Error(`Products failed: ${res.status}`);
  return res.json();
}

export async function getFilters(): Promise<FiltersResponse> {
  const res = await fetch(`${API_BASE}/products/meta/filters`);
  if (!res.ok) throw new Error(`Filters failed: ${res.status}`);
  return res.json();
}
