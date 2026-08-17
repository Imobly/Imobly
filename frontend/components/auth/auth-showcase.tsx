export function AuthShowcase() {
  return (
    <div className="relative hidden overflow-hidden bg-blue-950 lg:block">
      {/* Camada 1 — gradientes de profundidade */}
      <div
        className="absolute inset-0 animate-ink-drift"
        style={{
          backgroundColor: '#0b1f5c',
          backgroundImage: [
            'radial-gradient(120% 80% at 70% 18%, rgba(96,165,250,0.55) 0%, rgba(37,99,235,0) 55%)',
            'radial-gradient(90% 70% at 20% 12%, rgba(30,64,175,0.85) 0%, rgba(30,64,175,0) 60%)',
            'radial-gradient(120% 90% at 30% 100%, rgba(8,15,45,0.95) 0%, rgba(8,15,45,0) 55%)',
            'radial-gradient(80% 60% at 85% 75%, rgba(59,130,246,0.45) 0%, rgba(59,130,246,0) 60%)',
          ].join(','),
        }}
      />

      {/* Camada 2 — textura de tinta (SVG turbulence tingido em azul) */}
      <svg className="absolute inset-0 h-full w-full opacity-[0.45] mix-blend-soft-light" aria-hidden="true">
        <filter id="ink-texture">
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="4" seed="7" stitchTiles="stitch" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.04
                    0 0 0 0 0.18
                    0 0 0 0 0.65
                    0 0 0 0.9 0"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#ink-texture)" />
      </svg>

      {/* Camada 3 — foto do prédio */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-70 mix-blend-overlay"
        style={{ backgroundImage: "url('/login-bg.jpg')" }}
        aria-hidden="true"
      />

      {/* Vinheta para legibilidade do texto */}
      <div className="absolute inset-0 bg-gradient-to-t from-blue-950/80 via-transparent to-blue-950/20" />

      {/* Grão sutil */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        }}
        aria-hidden="true"
      />

      {/* Conteúdo */}
      <div className="relative z-10 flex h-full flex-col justify-between p-12 xl:p-16">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.25em] text-white/50">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-300" />
          Gestão Imobiliária Inteligente
        </div>

        <div className="max-w-md animate-fade-up [animation-delay:120ms]">
          <h2 className="text-4xl font-bold leading-[1.1] text-white xl:text-5xl">
            Seu portfólio de imóveis, sob controle total.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-white/70">
            Centralize propriedades, contratos, inquilinos e pagamentos em uma
            única plataforma — com clareza financeira em tempo real.
          </p>

          <div className="mt-10 grid grid-cols-3 gap-4">
            {[
              { value: 'Imóveis', label: 'Controle de propriedades' },
              { value: 'Contratos', label: 'Inquilinos e aluguéis' },
              { value: 'Financeiro', label: 'Pagamentos e despesas' },
            ].map((item) => (
              <div
                key={item.value}
                className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
              >
                <div className="text-lg font-bold text-white">{item.value}</div>
                <div className="mt-1 text-[11px] leading-tight text-white/55">{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        <p className="max-w-sm text-sm text-white/60">
          Menos planilhas, mais visibilidade sobre o seu negócio imobiliário.
        </p>
      </div>
    </div>
  );
}
