import { Outlet } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { SunMoon } from 'lucide-react';

const AuthLayout = () => {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <div className={`${theme === 'dark' ? 'dark' : ''} h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900`}>
      <div className="absolute top-4 right-4">
        <button 
          onClick={toggleTheme}
          className="p-2 rounded-full bg-white dark:bg-gray-800 shadow-md"
        >
          <SunMoon size={20} className="text-gray-700 dark:text-gray-300" />
        </button>
      </div>
      <div className="w-full max-w-md px-6">
        <Outlet />
      </div>
    </div>
  );
};

export default AuthLayout;