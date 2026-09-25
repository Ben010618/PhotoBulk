import React, { useState } from 'react';
import { CreditCard, X, ShieldCheck, CheckCircle2, Zap } from 'lucide-react';
import { api } from '../api/client';

interface TopUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (addedCredits: number, message: string) => void;
}

export const TopUpModal: React.FC<TopUpModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [selectedPackage, setSelectedPackage] = useState<string>('school_500');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  if (!isOpen) return null;

  const packages = [
    {
      id: 'starter_100',
      name: 'Starter Batch (100 Portraits)',
      credits: 100,
      price: '₱450.00',
      perPhoto: '₱4.50 / head',
      desc: 'Ideal for preschool, kindergarten, or individual class sections.',
    },
    {
      id: 'school_500',
      name: 'School Batch Pro (500 Portraits)',
      credits: 500,
      price: '₱1,850.00',
      perPhoto: '₱3.70 / head',
      popular: true,
      desc: 'Most popular: Senior High School or College commencement cohort.',
    },
    {
      id: 'volume_2500',
      name: 'Studio Enterprise (2,500 Portraits)',
      credits: 2500,
      price: '₱7,500.00',
      perPhoto: '₱3.00 / head',
      desc: 'Full graduation season pictorial contract license with priority queue.',
    },
  ];

  const handleCheckout = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await api.createCheckout(selectedPackage);
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        onSuccess(500, 'Top-up request registered.');
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Payment initiation error.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-6 text-[#c9d1d9]">
        <div className="flex items-center justify-between border-b border-[#30363d] pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-[#21262d] rounded-lg border border-[#30363d] text-[#f0f6fc]">
              <CreditCard className="w-5 h-5 text-[#58a6ff]" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#f0f6fc]">Top Up Studio Credits</h3>
              <p className="text-xs text-[#8b949e]">Native Philippine Checkout &bull; GCash, Maya, Debit/Credit Cards</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800 rounded-md text-red-200 text-xs">
            {error}
          </div>
        )}

        <div className="space-y-3">
          {packages.map((pkg) => {
            const isSelected = selectedPackage === pkg.id;
            return (
              <div
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg.id)}
                className={`p-4 rounded-lg border cursor-pointer transition relative ${
                  isSelected
                    ? 'border-[#58a6ff] bg-[#1f6feb]/10 shadow-sm'
                    : 'border-[#30363d] bg-[#0d1117] hover:border-[#8b949e]'
                }`}
              >
                {pkg.popular && (
                  <span className="absolute -top-2.5 right-4 bg-[#238636] text-white text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider shadow">
                    Most Popular
                  </span>
                )}
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-[#f0f6fc]">{pkg.name}</h4>
                    <p className="text-xs text-[#8b949e] mt-0.5">{pkg.desc}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-base font-bold text-[#f0f6fc]">{pkg.price}</span>
                    <span className="block text-[11px] text-[#8b949e] font-mono">{pkg.perPhoto}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-3 bg-[#0d1117] rounded-lg border border-[#30363d] flex items-center justify-between text-xs text-[#8b949e]">
          <span className="flex items-center gap-1.5 text-[#3fb950]">
            <ShieldCheck className="w-4 h-4" />
            <span>PayMongo 256-bit Encrypted</span>
          </span>
          <span className="font-mono">Instant Automatic Credit</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 rounded-lg border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] font-medium text-xs transition"
          >
            Cancel
          </button>
          <button
            onClick={handleCheckout}
            disabled={isLoading}
            className="flex-1 py-2.5 px-4 rounded-lg bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md transition disabled:opacity-50"
          >
            <Zap className="w-4 h-4 fill-white" />
            <span>{isLoading ? 'Connecting...' : 'Proceed to Checkout'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
