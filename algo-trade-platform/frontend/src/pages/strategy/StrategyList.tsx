import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Check, 
  ChevronDown, 
  Copy, 
  Cpu, 
  Edit, 
  Filter, 
  MoreHorizontal, 
  Plus, 
  Search, 
  Trash2, 
  X 
} from 'lucide-react';
import { useTradingData } from '../../context/TradingDataContext';
import { Strategy } from '../../types/strategy';
import toast from 'react-hot-toast';

const StrategyList = () => {
  const { strategies } = useTradingData();
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    status: 'all',
    type: 'all',
    performance: 'all',
  });
  const [strategyTypes, setStrategyTypes] = useState([]);

  useEffect(() => {
    // Fetch strategy types
    fetch('/api/strategies/types')
      .then(res => res.json())
      .then(data => setStrategyTypes(data))
      .catch(err => {
        console.error('Failed to fetch strategy types:', err);
        toast.error('Failed to load strategy types');
      });
  }, []);

  const handleCloneStrategy = async (id: string) => {
    try {
      const response = await fetch(`/api/strategies/${id}/clone`, {
        method: 'POST',
      });
      const data = await response.json();
      toast.success('Strategy cloned successfully');
      // Refresh strategies list
    } catch (err) {
      console.error('Failed to clone strategy:', err);
      toast.error('Failed to clone strategy');
    }
  };

  const handleDeleteStrategy = async (id: string) => {
    if (!confirm('Are you sure you want to delete this strategy?')) return;

    try {
      await fetch(`/api/strategies/${id}`, {
        method: 'DELETE',
      });
      toast.success('Strategy deleted successfully');
      // Refresh strategies list
    } catch (err) {
      console.error('Failed to delete strategy:', err);
      toast.error('Failed to delete strategy');
    }
  };

  const toggleStrategyStatus = async (id: string, currentStatus: boolean) => {
    try {
      const endpoint = currentStatus ? 'disable' : 'enable';
      await fetch(`/api/strategies/${id}/${endpoint}`, {
        method: 'POST',
      });
      toast.success(`Strategy ${currentStatus ? 'disabled' : 'enabled'} successfully`);
      // Refresh strategies list
    } catch (err) {
      console.error('Failed to toggle strategy status:', err);
      toast.error('Failed to update strategy status');
    }
  };

  // Filter strategies based on search query and filters
  const filteredStrategies = strategies.filter((strategy) => {
    const matchesSearch = strategy.name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = 
      filters.status === 'all' || 
      (filters.status === 'active' && strategy.isActive) || 
      (filters.status === 'inactive' && !strategy.isActive);
    
    const matchesType = 
      filters.type === 'all' || 
      filters.type === strategy.type;
    
    const matchesPerformance =
      filters.performance === 'all' ||
      (filters.performance === 'profitable' && strategy.performance > 0) ||
      (filters.performance === 'unprofitable' && strategy.performance <= 0);
    
    return matchesSearch && matchesStatus && matchesType && matchesPerformance;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Strategy Management</h1>
        <Link
          to="/strategy/new"
          className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
        >
          <Plus size={16} className="mr-2" />
          Create New Strategy
        </Link>
      </div>
      
      {/* Search and Filter section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search strategies..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
            />
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            <Filter size={16} className="mr-2" />
            Filters
            <ChevronDown size={16} className="ml-2" />
          </button>
        </div>
        
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                id="status-filter"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Strategy Type
              </label>
              <select
                id="type-filter"
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="all">All Types</option>
                {strategyTypes.map((type: string) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="performance-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Performance
              </label>
              <select
                id="performance-filter"
                value={filters.performance}
                onChange={(e) => setFilters({ ...filters, performance: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="all">All Performance</option>
                <option value="profitable">Profitable</option>
                <option value="unprofitable">Unprofitable</option>
              </select>
            </div>
          </div>
        )}
      </div>
      
      {/* Strategies Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Strategy Name
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Symbols
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Performance
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredStrategies.length > 0 ? (
                filteredStrategies.map((strategy) => (
                  <tr key={strategy.id} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-md flex items-center justify-center">
                          <Cpu size={20} className="text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            <Link to={`/strategy/dashboard/${strategy.id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                              {strategy.name}
                            </Link>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Created: {new Date(strategy.createdAt).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                        {strategy.type.charAt(0).toUpperCase() + strategy.type.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {strategy.symbols.join(', ')}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${
                        strategy.performance > 0 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {strategy.performance > 0 ? '+' : ''}{strategy.performance.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <button 
                          onClick={() => toggleStrategyStatus(strategy.id, strategy.isActive)}
                          className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                            strategy.isActive ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                          }`}
                        >
                          <span
                            className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                              strategy.isActive ? 'translate-x-5' : 'translate-x-0'
                            }`}
                          />
                        </button>
                        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                          {strategy.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <Link 
                          to={`/strategy/edit/${strategy.id}`}
                          className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          <Edit size={18} />
                        </Link>
                        <button 
                          onClick={() => handleCloneStrategy(strategy.id)}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          <Copy size={18} />
                        </button>
                        <button 
                          onClick={() => handleDeleteStrategy(strategy.id)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
                    No strategies found that match your filters. Try adjusting your search or filters, or create a new strategy.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StrategyList;