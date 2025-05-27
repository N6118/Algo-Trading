import { useState, useEffect } from 'react';
import { Settings, Shield, User, Key, Bell } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';

const UserProfile = () => {
  const { user } = useAuth();
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [apiKeys, setApiKeys] = useState([]);
  const [notificationSettings, setNotificationSettings] = useState({
    email: true,
    push: true,
    trade: true,
    risk: true,
    system: true
  });

  useEffect(() => {
    // Fetch user's 2FA status
    fetch('/api/users/2fa/status')
      .then(res => res.json())
      .then(data => setIs2FAEnabled(data.enabled))
      .catch(err => console.error('Failed to fetch 2FA status:', err));

    // Fetch API keys
    fetch('/api/users/api-keys')
      .then(res => res.json())
      .then(data => setApiKeys(data))
      .catch(err => console.error('Failed to fetch API keys:', err));

    // Fetch notification settings
    fetch('/api/users/notifications/settings')
      .then(res => res.json())
      .then(data => setNotificationSettings(data))
      .catch(err => console.error('Failed to fetch notification settings:', err));
  }, []);

  const handle2FAToggle = async () => {
    try {
      if (is2FAEnabled) {
        await fetch('/api/users/2fa/disable', { method: 'POST' });
        setIs2FAEnabled(false);
        toast.success('2FA disabled successfully');
      } else {
        const response = await fetch('/api/users/2fa/enable', { method: 'POST' });
        const data = await response.json();
        setShowQRCode(true);
        // Handle QR code display
      }
    } catch (err) {
      console.error('Failed to toggle 2FA:', err);
      toast.error('Failed to update 2FA settings');
    }
  };

  const handleNotificationSettingsUpdate = async (setting: string, value: boolean) => {
    try {
      const newSettings = { ...notificationSettings, [setting]: value };
      await fetch('/api/users/notifications/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings),
      });
      setNotificationSettings(newSettings);
      toast.success('Notification settings updated');
    } catch (err) {
      console.error('Failed to update notification settings:', err);
      toast.error('Failed to update notification settings');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">User Profile</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Personal Information */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold">Personal Information</h2>
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
            <h2 className="text-xl font-semibold">Security</h2>
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
            </div>
            <div>
              <button
                onClick={() => {/* Handle password change */}}
                className="text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline"
              >
                Change Password
              </button>
            </div>
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <Key className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold">API Keys</h2>
          </div>
          <div className="space-y-4">
            {apiKeys.map((key: any) => (
              <div key={key.id} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{key.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{key.exchange}</p>
                </div>
                <button
                  onClick={() => {/* Handle key deletion */}}
                  className="text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  Delete
                </button>
              </div>
            ))}
            <button
              onClick={() => {/* Handle add new key */}}
              className="w-full mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Add New API Key
            </button>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <Bell className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-xl font-semibold">Notification Settings</h2>
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
    </div>
  );
};

export default UserProfile;