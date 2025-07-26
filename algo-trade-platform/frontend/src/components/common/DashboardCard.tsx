import { ReactNode } from 'react';
import { TrendingDown, TrendingUp } from 'lucide-react';

interface DashboardCardProps {
  title: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  onClick?: () => void;
  loading?: boolean;
}

const DashboardCard = ({ 
  title, 
  value, 
  change, 
  trend = 'neutral', 
  icon, 
  onClick,
  loading = false 
}: DashboardCardProps) => {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5 animate-pulse">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-1"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
          </div>
          <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
            {title}
          </h3>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900 dark:text-white truncate">
              {value}
            </p>
            {change && (
              <p className={`ml-2 flex items-center text-sm font-medium transition-colors duration-200 ${
                trend === 'up' 
                  ? 'text-green-600 dark:text-green-400' 
                  : trend === 'down' 
                  ? 'text-red-600 dark:text-red-400' 
                  : 'text-gray-500 dark:text-gray-400'
              }`}>
                {trend === 'up' && <TrendingUp size={16} className="mr-1 flex-shrink-0" />}
                {trend === 'down' && <TrendingDown size={16} className="mr-1 flex-shrink-0" />}
                <span className="truncate">{change}</span>
              </p>
            )}
          </div>
        </div>
        {icon && (
          <div className="h-10 w-10 flex items-center justify-center bg-blue-50 dark:bg-blue-900/20 rounded-md flex-shrink-0 ml-3">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardCard;