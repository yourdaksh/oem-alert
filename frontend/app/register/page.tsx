'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();
  
  useEffect(() => {
    // Registration now happens through the onboarding + Stripe payment flow
    router.replace('/onboarding');
  }, [router]);

  return (
    <div className="flex-center" style={{ minHeight: '100vh' }}>
      <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Redirecting to onboarding...</p>
    </div>
  );
}
