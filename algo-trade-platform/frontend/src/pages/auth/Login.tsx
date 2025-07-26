import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, TrendingUp } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [show2FA, setShow2FA] = useState(false);
  const [form, setForm] = useState({
    username: '',
    password: '',
    remember: false,
    code2FA: '',
  });
  const [error, setError] = useState('');
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    
    // Clear error when user starts typing
    if (error) setError('');
  };
  
  const validateForm = () => {
    if (!form.username.trim()) {
      setError('Username is required');
      return false;
    }
    if (!form.password.trim()) {
      setError('Password is required');
      return false;
    }
    if (show2FA && !form.code2FA.trim()) {
      setError('2FA code is required');
      return false;
    }
    return true;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!validateForm()) return;
    
    try {
      await login(form.username, form.password, form.code2FA);
      toast.success('Successfully logged in');
      navigate('/');
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.message === '2FA_REQUIRED') {
        setShow2FA(true);
        setError('Please enter your 2FA code');
      } else {
        setError(err.message || 'Invalid username or password');
      }
    }
  };

  const handlePasswordReset = async () => {
    if (!form.username.trim()) {
      setError('Please enter your username to reset password');
      return;
    }
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('Password reset instructions sent to your email');
    } catch (err) {
      console.error('Password reset error:', err);
      toast.error('Failed to request password reset');
    }
  };
  
  return (
    <div className="w-full max-w-md mx-auto">
      <div className="flex justify-center mb-8">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-blue-600 rounded-md flex items-center justify-center">
            <TrendingUp size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AlgoTrader</h1>
        </div>
      </div>
      
      <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-6 text-center">
          Sign in to your account
        </h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm rounded-md">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={form.username}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter your username"
              disabled={isLoading}
              autoComplete="username"
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white pr-10"
                placeholder="Enter your password"
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff size={18} className="text-gray-500 dark:text-gray-400" />
                ) : (
                  <Eye size={18} className="text-gray-500 dark:text-gray-400" />
                )}
              </button>
            </div>
          </div>

          {show2FA && (
            <div className="mb-4">
              <label htmlFor="code2FA" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                2FA Code
              </label>
              <input
                id="code2FA"
                name="code2FA"
                type="text"
                value={form.code2FA}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Enter your 2FA code"
                disabled={isLoading}
                autoComplete="one-time-code"
                maxLength={6}
              />
            </div>
          )}
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                checked={form.remember}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={isLoading}
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Remember me
              </label>
            </div>
            
            <button
              type="button"
              onClick={handlePasswordReset}
              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 disabled:opacity-50"
              disabled={isLoading}
            >
              Forgot password?
            </button>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              'Sign in'
            )}
          </button>
        </form>
      </div>
      
      <p className="text-center text-sm text-gray-600 dark:text-gray-400">
        Don't have an account?{' '}
        <a href="#" className="font-medium text-blue-600 dark:text-blue-400 hover:underline">
          Contact administrator
        </a>
      </p>
    </div>
  );
};

export default Login;