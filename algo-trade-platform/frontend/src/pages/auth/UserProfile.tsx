import { useState, useEffect } from 'react';
import { Settings, Shield, User, Key, Bell, Eye, EyeOff, Plus, Trash2, Edit2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';

interface ApiKey {
  id: string;
  name: string;
  exchange: string;
  status: 'active' | 'inactive';
  createdAt: string;
  lastUsed?: string;
}

const UserProfile = () => {
  const { user } = useAuth();
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showAddApiKey, setShowAddApiKey] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState({
    email: true,
    push: true,
    trade: true,
    risk: true,
    system: true
  });

  // Password change form
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // API Key form
  const [apiKeyForm, setApiKeyForm] = useState({
    name: '',
    exchange: '',
    apiKey: '',
    secretKey: '',
    passphrase: ''
  });

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      // Fetch 2FA status
      const twoFAResponse = await fetch('/api/users/2fa/status');
      if (twoFAResponse.ok) {
        const data = await twoFAResponse.json();
        setIs2FAEnabled(data.enabled);
      }

      // Fetch API keys
      const apiKeysResponse = await fetch('/api/users/api-keys');
      if (apiKeysResponse.ok) {
        const data = await apiKeysResponse.json();
        setApiKeys(data);
      }

      // Fetch notification settings
      const notificationsResponse = await fetch('/api/users/notifications/settings');
      if (notificationsResponse.ok) {
        const data = await notificationsResponse.json();
        setNotificationSettings(data);
      }
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    }
  };

  const handle2FAToggle = async () => {
    try {
      if (is2FAEnabled) {
        const response = await fetch('/api/users/2fa/disable', { method: 'POST' });
        if (response.ok) {
          setIs2FAEnabled(false);
          setShowQRCode(false);
          toast.success('2FA disabled successfully');
        }
      } else {
        const response = await fetch('/api/users/2fa/enable', { method: 'POST' });
        if (response.ok) {
          const data = await response.json();
          setQrCodeUrl(data.qrCode);
          setShowQRCode(true);
          toast.success('2FA setup initiated. Please scan the QR code.');
        }
      }
    } catch (err) {
      console.error('Failed to toggle 2FA:', err);
      toast.error('Failed to update 2FA settings');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    try {
      const response = await fetch('/api/users/password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword: passwordForm.currentPassword,
          newPassword: passwordForm.newPassword
        }),
      });

      if (response.ok) {
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
        setShowChangePassword(false);
        toast.success('Password changed successfully');
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to change password');
      }
    } catch (err) {
      console.error('Failed to change password:', err);
      toast.error('Failed to change password');
    }
  };

  const handleAddApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/users/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiKeyForm),
      });

      if (response.ok) {
        const newApiKey = await response.json();
        setApiKeys([...apiKeys, newApiKey]);
        setApiKeyForm({ name: '', exchange: '', apiKey: '', secretKey: '', passphrase: '' });
        setShowAddApiKey(false);
        toast.success('API key added successfully');
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to add API key');
      }
    } catch (err) {
      console.error('Failed to add API key:', err);
      toast.error('Failed to add API key');
    }
  };

  const handleDeleteApiKey = async (id: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      const response = await fetch(`/api/users/api-keys/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setApiKeys(apiKeys.filter(key => key.id !== id));
        toast.success('API key deleted successfully');
      } else {
        toast.error('Failed to delete API key');
      }
    } catch (err) {
      console.error('Failed to delete API key:', err);
      toast.error('Failed to delete API key');
    }
  };

  const handleNotificationSettingsUpdate = async (setting: string, value: boolean) => {
    try {
      const newSettings = { ...notificationSettings, [setting]: value };
      const response = await fetch('/api/users/notifications/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings),
      });

      if (response.ok) {
        setNotificationSettings(newSettings);
        toast.success('Notification settings updated');
      } else {
        toast.error('Failed to update notification settings');
      }
    } catch (err) {
      console.error('Failed to update notification settings:', err);
      toast.error('Failed to update notification settings');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-900 dark:text-white">User Profile</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Personal Information */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Personal Information</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Name</label>
              <p className="mt-1 text-lg text-gray-900 dark:text-white">{user?.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Email</label>
              <p className="mt-1 text-lg text-gray-900 dark:text-white">{user?.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Role</label>
              <p className="mt-1 text-lg text-gray-900 dark:text-white">{user?.role}</p>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <Shield className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Security</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Two-Factor Authentication</label>
              <div className="mt-2 flex items-center">
                <button
                  onClick={handle2FAToggle}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    is2FAEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      is2FAEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
                  {is2FAEnabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              
              {showQRCode && (
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Scan this QR code with your authenticator app:
                  </p>
                  <div className="flex justify-center">
                    <img src={qrCodeUrl} alt="2FA QR Code" className="w-32 h-32" />
                  </div>
                </div>
              )}
            </div>
            
            <div>
              <button
                onClick={() => setShowChangePassword(!showChangePassword)}
                className="text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline flex items-center"
              >
                <Edit2 size={14} className="mr-1" />
                Change Password
              </button>
            </div>
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Key className="w-5 h-5 mr-2 text-blue-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">API Keys</h2>
            </div>
            <button
              onClick={() => setShowAddApiKey(!showAddApiKey)}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
            >
              <Plus size={20} />
            </button>
          </div>
          
          <div className="space-y-4">
            {apiKeys.map((key) => (
              <div key={key.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{key.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{key.exchange}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Status: <span className={key.status === 'active' ? 'text-green-600' : 'text-red-600'}>{key.status}</span>
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteApiKey(key.id)}
                  className="text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            
            {apiKeys.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No API keys configured
              </p>
            )}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <Bell className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Notification Settings</h2>
          </div>
          <div className="space-y-4">
            {Object.entries(notificationSettings).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                  {key} Notifications
                </label>
                <button
                  onClick={() => handleNotificationSettingsUpdate(key, !value)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    value ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      value ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Change Password Modal */}
      {showChangePassword && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Change Password</h3>
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.current ? 'text' : 'password'}
                    value={passwordForm.currentPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.current ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  New Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.new ? 'text' : 'password'}
                    value={passwordForm.newPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.new ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Confirm New Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.confirm ? 'text' : 'password'}
                    value={passwordForm.confirmPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.confirm ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowChangePassword(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add API Key Modal */}
      {showAddApiKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Add API Key</h3>
            <form onSubmit={handleAddApiKey} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Key Name
                </label>
                <input
                  type="text"
                  value={apiKeyForm.name}
                  onChange={(e) => setApiKeyForm({ ...apiKeyForm, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="e.g., My Trading Account"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Exchange
                </label>
                <select
                  value={apiKeyForm.exchange}
                  onChange={(e) => setApiKeyForm({ ...apiKeyForm, exchange: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  required
                >
                  <option value="">Select Exchange</option>
                  <option value="Interactive Brokers">Interactive Brokers</option>
                  <option value="TD Ameritrade">TD Ameritrade</option>
                  <option value="E*TRADE">E*TRADE</option>
                  <option value="Alpaca">Alpaca</option>
                  <option value="Binance">Binance</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  API Key
                </label>
                <input
                  type="text"
                  value={apiKeyForm.apiKey}
                  onChange={(e) => setApiKeyForm({ ...apiKeyForm, apiKey: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Secret Key
                </label>
                <input
                  type="password"
                  value={apiKeyForm.secretKey}
                  onChange={(e) => setApiKeyForm({ ...apiKeyForm, secretKey: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Passphrase (if required)
                </label>
                <input
                  type="password"
                  value={apiKeyForm.passphrase}
                  onChange={(e) => setApiKeyForm({ ...apiKeyForm, passphrase: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddApiKey(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Add API Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;