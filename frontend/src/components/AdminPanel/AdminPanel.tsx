import React from 'react';
import { AdminDashboard } from '../AdminDashboard';
import { PageView } from '../../types';
import { useAuthStore } from '../../store/useAuthStore';

interface AdminPanelProps {
  onNavigate: (page: PageView) => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ onNavigate }) => {
  const { currentUser } = useAuthStore();

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <AdminDashboard onNavigate={onNavigate} currentUser={currentUser} />
    </div>
  );
};
