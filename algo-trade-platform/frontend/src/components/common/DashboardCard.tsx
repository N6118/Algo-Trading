import { ReactNode } from 'react';
import { TrendingDown, TrendingUp } from 'lucide-react';

interface DashboardCardProps {
  title: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  onClick?: () => void;
}

const DashboardCard = ({ title, value, change, trend = 'neutral', icon, onClick }: DashboardCardProps) => {
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5 
      ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow duration-200' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
            {change && (
              <p className={`ml-2 flex items-center text-sm font-medium ${
                trend === 'up' 
                  ? 'text-green-600 dark:text-green-400' 
                  : trend === 'down' 
                  ? 'text-red-600 dark:text-red-400' 
                  : 'text-gray-500 dark:text-gray-400'
              }`}>
                {trend === 'up' && <TrendingUp size={16} className="mr-1" />}
                {trend === 'down' && <TrendingDown size={16} className="mr-1" />}
                {change}
              </p>
            )}
          </div>
        </div>
        {icon && (
          <div className="h-10 w-10 flex items-center justify-center bg-blue-50 dark:bg-blue-900/20 rounded-md">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardCard;