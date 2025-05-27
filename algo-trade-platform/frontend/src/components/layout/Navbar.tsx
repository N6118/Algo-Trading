import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, ChevronDown, Search, User, Settings, SunMoon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';

interface NavbarProps {
  onMenuClick: () => void;
}

const Navbar = ({ onMenuClick }: NavbarProps) => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  
  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 py-3 px-4 flex items-center justify-between">
      <div className="flex items-center">
        <button 
          onClick={onMenuClick} 
          className="text-gray-500 dark:text-gray-400 lg:hidden"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
          </svg>
        </button>
        
        <div className="ml-4 md:ml-6 relative hidden md:block">
          <div className="flex items-center border rounded-md px-3 py-1 bg-gray-100 dark:bg-gray-700">
            <Search size={18} className="text-gray-400" />
            <input 
              type="text" 
              placeholder="Search..." 
              className="ml-2 bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-gray-600 dark:text-gray-300 w-56"
            />
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <button 
          onClick={toggleTheme}
          className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <SunMoon size={20} className="text-gray-600 dark:text-gray-300" />
        </button>
        
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 relative"
          >
            <Bell size={20} className="text-gray-600 dark:text-gray-300" />
            <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-red-500"></span>
          </button>
          
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-10 border border-gray-200 dark:border-gray-700">
              <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Notifications</h3>
              </div>
              <div className="max-h-80 overflow-y-auto">
                <div className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <p className="text-sm text-gray-700 dark:text-gray-300">Strategy "AAPL Momentum" triggered a buy signal</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">5 minutes ago</p>
                </div>
                <div className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <p className="text-sm text-gray-700 dark:text-gray-300">SPY trade closed with +2.5% profit</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">20 minutes ago</p>
                </div>
                <div className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <p className="text-sm text-gray-700 dark:text-gray-300">Daily performance report is ready</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">1 hour ago</p>
                </div>
              </div>
              <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
                <a href="#" className="text-xs text-blue-600 dark:text-blue-400 hover:underline">View all notifications</a>
              </div>
            </div>
          )}
        </div>
        
        <div className="relative">
          <button 
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center space-x-2"
          >
            <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
              <User size={16} />
            </div>
            <span className="hidden md:block text-sm text-gray-700 dark:text-gray-300">{user?.name || 'Guest'}</span>
            <ChevronDown size={16} className="text-gray-500" />
          </button>
          
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-10 border border-gray-200 dark:border-gray-700">
              <Link to="/profile" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                <div className="flex items-center">
                  <User size={16} className="mr-2" />
                  Profile
                </div>
              </Link>
              <Link to="/settings" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                <div className="flex items-center">
                  <Settings size={16} className="mr-2" />
                  Settings
                </div>
              </Link>
              <button 
                onClick={logout}
                className="w-full text-left block px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;