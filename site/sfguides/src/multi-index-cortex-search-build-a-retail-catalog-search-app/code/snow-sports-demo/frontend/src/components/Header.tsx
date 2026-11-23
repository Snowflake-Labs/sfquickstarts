import { useState, useEffect } from 'react';
import { Mountain, Search, X } from 'lucide-react';

const SAMPLE_QUERIES = [
  'ultra-cold sub-zero polar thermal insulation',
  'storm-proof rough weather wind survival waterproof',
  'FIS racing gates competition speed precision',
  'Scandinavian engineering millimetre precision technical',
  'freeride deep powder backcountry adventure',
  'park freestyle tricks stomp impact',
  'beginner complete setup learn progress',
  'avalanche backcountry transceiver safety rescue',
];

interface HeaderProps {
  searchQuery: string;
  onSearch: (query: string) => void;
  onClear: () => void;
  isSearching: boolean;
}

export default function Header({ searchQuery, onSearch, onClear, isSearching }: HeaderProps) {
  const [inputValue, setInputValue] = useState('');

  // Sync input when parent clears the query
  useEffect(() => {
    if (!searchQuery) setInputValue('');
  }, [searchQuery]);

  // Debounced auto-search — fires 400ms after typing stops (min 3 chars)
  useEffect(() => {
    if (inputValue.trim().length < 3) return;
    const timer = setTimeout(() => {
      onSearch(inputValue.trim());
    }, 400);
    return () => clearTimeout(timer);
  }, [inputValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) onSearch(inputValue.trim());
  };

  const handleClear = () => {
    setInputValue('');
    onClear();
  };

  const handleChipClick = (chip: string) => {
    setInputValue(chip);
    onSearch(chip);
  };

  return (
    <div className="bg-[#0F172A] px-6 py-3 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center gap-6">
        {/* Left: branding */}
        <div className="flex items-center gap-3 shrink-0">
          <Mountain className="w-7 h-7 text-[#29B5E8]" />
          <div>
            <div className="text-white font-bold text-lg leading-tight tracking-wide">
              SNOWFIELD PRO
            </div>
            <div className="text-slate-400 text-xs leading-tight">Winter Sports</div>
          </div>
        </div>

        {/* Center: search */}
        <div className="flex-1 min-w-0">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder="Search products with Cortex Search..."
              className="flex-1 px-4 py-2 rounded-lg bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#29B5E8]"
            />
            <button
              type="submit"
              disabled={isSearching || !inputValue.trim()}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-50"
              style={{ backgroundColor: '#29B5E8' }}
            >
              <Search className="w-4 h-4" />
              {isSearching ? 'Searching…' : 'Search'}
            </button>
            {(inputValue || searchQuery) && (
              <button
                type="button"
                onClick={handleClear}
                className="flex items-center gap-1 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 text-sm transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </form>

          {/* Sample chips — only when input is empty */}
          {!inputValue && (
            <div className="flex flex-wrap gap-2 mt-2">
              {SAMPLE_QUERIES.map(q => (
                <button
                  key={q}
                  onClick={() => handleChipClick(q)}
                  className="px-3 py-0.5 rounded-full text-xs text-slate-300 bg-slate-700 hover:bg-slate-600 hover:text-white transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: badge */}
        <div className="shrink-0 hidden lg:block text-slate-500 text-xs text-right leading-snug">
          Powered by ❄️<br />
          <span className="text-slate-400 font-medium">Snowflake Cortex Search</span>
        </div>
      </div>
    </div>
  );
}
