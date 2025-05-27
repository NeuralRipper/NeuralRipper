import type { FilterCardProps } from '../types/types.ts';

const FilterCard: React.FC<FilterCardProps> = ({ label, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-lg text-xs font-mono border transition-all ${
        active 
          ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50' 
          : 'bg-gray-900/50 text-gray-400 border-gray-700/50 hover:border-cyan-500/30 hover:text-cyan-300'
      }`}
    >
      {label}
    </button>
  );
};

export default FilterCard;