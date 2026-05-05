const CATEGORIES = ['All', 'Equipment', 'Apparel', 'Protection', 'Accessories'];

interface CategoryTabsProps {
  activeCategory: string;
  onChange: (category: string) => void;
}

export default function CategoryTabs({ activeCategory, onChange }: CategoryTabsProps) {
  return (
    <div className="sticky top-0 z-40 bg-white shadow-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex gap-0">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => onChange(cat)}
              className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeCategory === cat
                  ? 'border-[#29B5E8] text-[#29B5E8] font-semibold'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
