import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/auth.service';
import { LogOut, User } from 'lucide-react';

export default function Header() {
  const { user, organization, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    await authService.logout();
    clearAuth();
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex-1" />
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
          <p className="text-xs text-gray-500">{organization?.name}</p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="p-2 rounded-lg hover:bg-gray-100">
            <User className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <LogOut className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>
    </header>
  );
}
