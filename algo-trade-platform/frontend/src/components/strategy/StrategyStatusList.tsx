import { Link } from 'react-router-dom';
import { CheckCircle, Clock, XCircle, AlertTriangle } from 'lucide-react';
import { Strategy } from '../../types/strategy';

interface StrategyStatusListProps {
  strategies: Strategy[];
}

export const StrategyStatusList = ({ strategies }: StrategyStatusListProps) => {
  if (strategies.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500 dark:text-gray-400">
        No active strategies found.
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {strategies.map((strategy) => (
        <div 
          key={strategy.id} 
          className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-750 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-sm transition-shadow duration-200"
        >
          <div className="flex items-center space-x-3">
            {strategy.isActive ? (
              <CheckCircle size={20} className="text-green-500 dark:text-green-400" />
            ) : (
              <XCircle size={20} className="text-red-500 dark:text-red-400" />
            )}
            <div>
              <Link 
                to={`/strategy/dashboard/${strategy.id}`}
                className="text-sm font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
              >
                {strategy.name}
              </Link>
              <div className="flex items-center mt-1">
                <span className="text-xs text-gray-500 dark:text-gray-400 mr-2">
                  {strategy.type.charAt(0).toUpperCase() + strategy.type.slice(1)}
                </span>
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {strategy.symbols.slice(0, 3).join(', ')}
                  {strategy.symbols.length > 3 && '...'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center">
            {strategy.signalCount > 0 && (
              <div className="mr-4 flex items-center">
                <AlertTriangle size={16} className="text-yellow-500 dark:text-yellow-400 mr-1" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {strategy.signalCount} signals
                </span>
              </div>
            )}
            
            <div className="flex items-center space-x-1">
              <Clock size={16} className="text-gray-400 dark:text-gray-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(strategy.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            
            <div className={`ml-4 flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              strategy.performance > 0 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' 
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
            }`}>
              {strategy.performance > 0 ? '+' : ''}{strategy.performance.toFixed(2)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};