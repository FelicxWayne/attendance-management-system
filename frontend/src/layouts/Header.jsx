import React from 'react';
import { Menu, LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Header({ onMenuClick }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const username = user?.username || 'User';
  const role = user?.role || 'MEMBER';

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between h-16 px-4 sm:px-6 bg-white border-b border-slate-200 shadow-xs">
      {/* Left side: Hamburger toggle & App title on mobile */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="lg:hidden p-2 -ml-1.5 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
        <span className="hidden sm:inline-block text-sm font-medium text-slate-500">
          Attendance Management
        </span>
      </div>

      {/* Right side: User info (username + role) & Logout button */}
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 shrink-0">
            <UserIcon className="w-4 h-4" aria-hidden="true" />
          </div>
          <div className="flex flex-col items-start leading-tight">
            <span className="text-xs sm:text-sm font-semibold text-slate-800 max-w-[90px] sm:max-w-[150px] truncate" title={username}>
              {username}
            </span>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wide">
              {role}
            </span>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-200 mx-0.5 sm:mx-1" aria-hidden="true" />

        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs sm:text-sm font-medium text-slate-700 hover:text-red-700 hover:bg-red-50 rounded-lg border border-slate-200 hover:border-red-200 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          title="Log out of your account"
          aria-label="Log out"
        >
          <LogOut className="w-4 h-4 shrink-0 text-slate-500 group-hover:text-red-600" aria-hidden="true" />
          <span className="hidden xs:inline sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
}
