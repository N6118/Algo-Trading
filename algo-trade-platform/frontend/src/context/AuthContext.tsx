import { createContext, useContext, useState, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string, code2FA?: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const savedUser = localStorage.getItem('user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch (error) {
      console.error('Error parsing saved user data:', error);
      localStorage.removeItem('user');
      return null;
    }
  });
  
  const [isLoading, setIsLoading] = useState(false);

  const login = async (username: string, password: string, code2FA?: string) => {
    if (!username.trim() || !password.trim()) {
      throw new Error('Username and password are required');
    }
    
    setIsLoading(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate 2FA requirement
      if (!code2FA && Math.random() > 0.7) {
        throw new Error('2FA_REQUIRED');
      }
      
      // Mock user data with better validation
      const mockUser: User = {
        id: `user-${Date.now()}`,
        name: username.charAt(0).toUpperCase() + username.slice(1),
        email: `${username.toLowerCase()}@example.com`,
        role: 'trader'
      };
      
      // Save user to state and localStorage
      setUser(mockUser);
      try {
        localStorage.setItem('user', JSON.stringify(mockUser));
      } catch (error) {
        console.warn('Failed to save user to localStorage:', error);
      }
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem('user');
    } catch (error) {
      console.warn('Failed to remove user from localStorage:', error);
    }
  };
  
  const value = {
    user,
    isAuthenticated: user !== null,
    login,
    logout,
    isLoading
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};