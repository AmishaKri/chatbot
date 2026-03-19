import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import api from '@/services/api';
import { User, Building2, Lock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

function Section({ title, icon, children }: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
        <div className="text-gray-500">{icon}</div>
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatusMessage({ type, message }: { type: 'success' | 'error'; message: string }) {
  return (
    <div className={`flex items-start gap-2 px-3 py-2 rounded-lg text-sm ${
      type === 'success'
        ? 'bg-green-50 border border-green-200 text-green-700'
        : 'bg-red-50 border border-red-200 text-red-700'
    }`}>
      {type === 'success'
        ? <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        : <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
      }
      {message}
    </div>
  );
}

export default function Settings() {
  const { user, organization, setAuth, token } = useAuthStore();

  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });
  const [profileStatus, setProfileStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordStatus, setPasswordStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileStatus(null);
    try {
      const response = await api.put('/api/auth/me', {
        full_name: profileData.full_name,
      });
      if (user && organization && token) {
        setAuth({ ...user, full_name: response.data.full_name }, organization, token);
      }
      setProfileStatus({ type: 'success', message: 'Profile updated successfully.' });
    } catch (err: any) {
      setProfileStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to update profile.',
      });
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordStatus({ type: 'error', message: 'New passwords do not match.' });
      return;
    }
    if (passwordData.new_password.length < 8) {
      setPasswordStatus({ type: 'error', message: 'Password must be at least 8 characters.' });
      return;
    }
    setPasswordLoading(true);
    setPasswordStatus(null);
    try {
      await api.put('/api/auth/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setPasswordStatus({ type: 'success', message: 'Password changed successfully.' });
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err: any) {
      setPasswordStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to change password.',
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  const inputClass = 'block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary';

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-gray-600">Manage your account and organization preferences</p>
      </div>

      <Section title="Profile" icon={<User className="w-5 h-5" />}>
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                value={profileData.full_name}
                onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={profileData.email}
                disabled
                className={`${inputClass} bg-gray-50 text-gray-500 cursor-not-allowed`}
              />
              <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <span className="inline-block px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm font-medium capitalize">
              {user?.role || 'Member'}
            </span>
          </div>

          {profileStatus && <StatusMessage {...profileStatus} />}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={profileLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {profileLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Save Profile
            </button>
          </div>
        </form>
      </Section>

      <Section title="Organization" icon={<Building2 className="w-5 h-5" />}>
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
              <input
                type="text"
                value={organization?.name || ''}
                disabled
                className={`${inputClass} bg-gray-50 text-gray-500 cursor-not-allowed`}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
              <input
                type="text"
                value={organization?.slug || ''}
                disabled
                className={`${inputClass} bg-gray-50 text-gray-500 cursor-not-allowed`}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Plan</label>
            <span className="inline-block px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium capitalize">
              {organization?.subscription_tier || 'Free'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${organization?.is_active ? 'bg-green-500' : 'bg-red-400'}`} />
            <span className="text-sm text-gray-600">
              Organization is {organization?.is_active ? 'active' : 'inactive'}
            </span>
          </div>
        </div>
      </Section>

      <Section title="Change Password" icon={<Lock className="w-5 h-5" />}>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
              required
              className={inputClass}
              placeholder="••••••••"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                required
                minLength={8}
                className={inputClass}
                placeholder="Min 8 characters"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                required
                className={inputClass}
                placeholder="Repeat new password"
              />
            </div>
          </div>

          {passwordStatus && <StatusMessage {...passwordStatus} />}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={passwordLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2 transition-colors"
            >
              {passwordLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Change Password
            </button>
          </div>
        </form>
      </Section>

      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-red-900 mb-1">Danger Zone</h2>
        <p className="text-sm text-red-700 mb-4">
          These actions are irreversible. Please be certain before proceeding.
        </p>
        <div className="flex items-center justify-between p-4 bg-white border border-red-200 rounded-lg">
          <div>
            <p className="text-sm font-medium text-gray-900">Delete Account</p>
            <p className="text-xs text-gray-500 mt-0.5">Permanently remove your account and all associated data</p>
          </div>
          <button
            disabled
            title="Contact support to delete your account"
            className="px-3 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}
