import Image from 'next/image';

interface BrandLogoProps {
  variant?: 'dark' | 'light';
  className?: string;
}

export function BrandLogo({ variant = 'dark', className = '' }: BrandLogoProps) {
  const text = variant === 'light' ? 'text-white' : 'text-gray-900';
  const sub = variant === 'light' ? 'text-white/60' : 'text-gray-400';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <Image src="/logo-icon.svg" alt="Imobly" width={40} height={40} className="drop-shadow-sm" />
      <span className="flex flex-col leading-none">
        <span className={`font-sans text-lg font-bold tracking-tight ${text}`}>Imobly</span>
        <span className={`text-[11px] font-medium tracking-wide ${sub}`}>Gestão Imobiliária</span>
      </span>
    </div>
  );
}
