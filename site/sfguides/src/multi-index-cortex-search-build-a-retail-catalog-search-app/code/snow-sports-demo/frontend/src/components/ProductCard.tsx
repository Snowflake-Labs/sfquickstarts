import { BRAND_COLORS, BRAND_TAGLINES, BRAND_IDENTITY, PRODUCT_TYPE_EMOJI, PRODUCT_TYPE_IMAGE, SKILL_BADGE, INDEX_COLORS } from '../constants';
import type { Product, SearchResult } from '../api';

function isSearchResult(p: Product | SearchResult): p is SearchResult {
  return 'source_index' in p;
}

interface ProductCardProps {
  product: Product | SearchResult;
  isSearch?: boolean;
  index?: number;
}

export default function ProductCard({ product, isSearch = false, index = 0 }: ProductCardProps) {
  const brandColor = BRAND_COLORS[product.brand] ?? '#64748B';
  const emoji = PRODUCT_TYPE_EMOJI[product.product_type] ?? '📦';
  const skillClass = SKILL_BADGE[product.skill_level] ?? 'bg-slate-100 text-slate-700';
  const imageName = PRODUCT_TYPE_IMAGE[product.product_type] ?? product.product_type.toLowerCase().replace(/\s+/g, '_');
  const imageSrc = `/product-images/${imageName}.png`;
  const formattedPrice = `$${product.price.toFixed(2)}`;

  return (
    <div
      className="bg-white rounded-xl shadow hover:shadow-lg transition-shadow overflow-hidden flex flex-col card-enter"
      style={{ animationDelay: `${index * 0.04}s` }}
    >
      {/* Image area */}
      <div
        className="relative h-48 flex items-center justify-center overflow-hidden bg-white"
      >
        <img
          src={imageSrc}
          alt={product.product_type}
          className="h-full w-full object-contain p-4"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = 'none';
            (e.currentTarget.nextElementSibling as HTMLElement | null)?.style.setProperty('display', 'flex');
          }}
        />
        {/* Fallback emoji — hidden when image loads */}
        <span
          className="text-6xl select-none absolute inset-0 items-center justify-center hidden"
          style={{ backgroundColor: brandColor, display: 'none' }}
        >{emoji}</span>
        {/* Brand color tint overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ backgroundColor: brandColor, mixBlendMode: 'multiply', opacity: 0.35 }}
        />

        {/* Category badge */}
        <span
          className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-xs font-semibold text-white shadow"
          style={{ backgroundColor: isSearch && isSearchResult(product) ? product.source_color : (INDEX_COLORS[product.category] ?? '#64748B') }}
        >
          {isSearch && isSearchResult(product) ? product.source_label : product.category}
        </span>
      </div>

      {/* Body */}
      <div className="p-4 flex flex-col gap-1 flex-1">
        {/* Brand */}
        <div
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: brandColor }}
        >
          {product.brand}
        </div>
        {BRAND_TAGLINES[product.brand] && (
          <div className="text-xs text-slate-500 italic leading-tight">
            {BRAND_TAGLINES[product.brand]}
          </div>
        )}
        {BRAND_IDENTITY[product.brand] && (
          <div className="text-[10px] uppercase tracking-widest text-slate-400 font-medium">
            {BRAND_IDENTITY[product.brand]}
          </div>
        )}

        {/* Name */}
        <div className="font-bold text-slate-900 text-sm leading-snug line-clamp-2">
          {product.item_name}
        </div>

        {/* Subcategory */}
        <div className="text-xs text-slate-500">{product.subcategory}</div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Discipline pill */}
        <div className="mt-2">
          <span className="inline-block px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">
            {product.discipline}
          </span>
        </div>

        {/* Bottom row: price + skill badge */}
        <div className="flex items-center justify-between mt-1">
          <span className="text-lg font-bold text-slate-900">{formattedPrice}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${skillClass}`}>
            {product.skill_level}
          </span>
        </div>

        {/* Flex rating if present */}
        {product.flex_rating && (
          <div className="text-xs text-slate-400">Flex: {product.flex_rating}</div>
        )}
      </div>
    </div>
  );
}
