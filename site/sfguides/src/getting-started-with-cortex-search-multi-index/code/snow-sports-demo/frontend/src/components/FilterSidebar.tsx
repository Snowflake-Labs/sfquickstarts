import { BRAND_COLORS } from '../constants';
import type { FiltersResponse } from '../api';

const SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Professional'];
const GENDERS = ['Mens', 'Womens', 'Unisex', 'Kids'];

interface FilterSidebarProps {
  filters: FiltersResponse | null;
  activeFilters: Record<string, string>;
  onChange: (filters: Record<string, string>) => void;
}

export default function FilterSidebar({ filters, activeFilters, onChange }: FilterSidebarProps) {
  const selectedBrands = new Set(
    activeFilters.brand ? activeFilters.brand.split(',').filter(Boolean) : [],
  );
  const selectedSkills = new Set(
    activeFilters.skill_level ? activeFilters.skill_level.split(',').filter(Boolean) : [],
  );
  const selectedGender = activeFilters.gender ?? '';

  const toggleBrand = (brand: string) => {
    const next = new Set(selectedBrands);
    if (next.has(brand)) next.delete(brand);
    else next.add(brand);
    const updated = { ...activeFilters };
    if (next.size === 0) delete updated.brand;
    else updated.brand = Array.from(next).join(',');
    onChange(updated);
  };

  const toggleSkill = (skill: string) => {
    const next = new Set(selectedSkills);
    if (next.has(skill)) next.delete(skill);
    else next.add(skill);
    const updated = { ...activeFilters };
    if (next.size === 0) delete updated.skill_level;
    else updated.skill_level = Array.from(next).join(',');
    onChange(updated);
  };

  const setGender = (gender: string) => {
    const updated = { ...activeFilters };
    if (selectedGender === gender) delete updated.gender;
    else updated.gender = gender;
    onChange(updated);
  };

  const clearAll = () => onChange({});

  const hasFilters =
    selectedBrands.size > 0 || selectedSkills.size > 0 || selectedGender !== '';

  const brands = filters?.brands ?? Object.keys(BRAND_COLORS);

  return (
    <div className="w-60 shrink-0 hidden md:flex flex-col border-r border-slate-200 bg-white overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Brand */}
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Brand
          </h3>
          <div className="space-y-2">
            {brands.map(brand => (
              <label key={brand} className="flex items-center gap-2.5 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={selectedBrands.has(brand)}
                  onChange={() => toggleBrand(brand)}
                  className="rounded border-slate-300 text-[#29B5E8] focus:ring-[#29B5E8]"
                />
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: BRAND_COLORS[brand] ?? '#64748B' }}
                />
                <span className="text-sm text-slate-700 group-hover:text-slate-900 truncate">
                  {brand}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Skill Level */}
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Skill Level
          </h3>
          <div className="space-y-2">
            {SKILL_LEVELS.map(skill => (
              <label key={skill} className="flex items-center gap-2.5 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={selectedSkills.has(skill)}
                  onChange={() => toggleSkill(skill)}
                  className="rounded border-slate-300 text-[#29B5E8] focus:ring-[#29B5E8]"
                />
                <span className="text-sm text-slate-700 group-hover:text-slate-900">
                  {skill}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Gender */}
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Gender
          </h3>
          <div className="space-y-2">
            {GENDERS.map(gender => (
              <label key={gender} className="flex items-center gap-2.5 cursor-pointer group">
                <input
                  type="radio"
                  name="gender"
                  checked={selectedGender === gender}
                  onChange={() => setGender(gender)}
                  className="border-slate-300 text-[#29B5E8] focus:ring-[#29B5E8]"
                />
                <span className="text-sm text-slate-700 group-hover:text-slate-900">
                  {gender}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Clear All */}
        {hasFilters && (
          <button
            onClick={clearAll}
            className="w-full py-2 text-sm font-medium text-slate-600 hover:text-slate-900 border border-slate-200 hover:border-slate-400 rounded-lg transition-colors"
          >
            Clear All Filters
          </button>
        )}
      </div>
    </div>
  );
}
