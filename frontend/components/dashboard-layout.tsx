"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Home, Building2, Users, CreditCard, Receipt, Menu, Settings, LogOut, Wallet } from "lucide-react"
import Image from "next/image"
import { useAuth } from "@/lib/contexts/auth"

/**
 * Navegação agrupada.
 *
 * Sete itens numa lista corrida obrigam a ler todos para achar um. Divididos
 * por assunto — o que é cadastro, o que é dinheiro, o que é ajuste — a busca
 * vira escolha de seção.
 */
const navigation: { section?: string; items: { name: string; href: string; icon: typeof Home }[] }[] = [
  { items: [{ name: "Dashboard", href: "/dashboard", icon: Home }] },
  {
    section: "Gestão",
    items: [
      { name: "Imóveis", href: "/properties", icon: Building2 },
      { name: "Inquilinos", href: "/tenants", icon: Users },
    ],
  },
  {
    section: "Financeiro",
    items: [
      { name: "Cobranças", href: "/charges", icon: Wallet },
      { name: "Pagamentos", href: "/payments", icon: CreditCard },
      { name: "Despesas", href: "/expenses", icon: Receipt },
    ],
  },
  {
    section: "Sistema",
    items: [{ name: "Configurações", href: "/settings", icon: Settings }],
  },
]

interface DashboardLayoutProps {
  children: React.ReactNode
}

function SidebarNav({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <nav className="flex-1 space-y-0.5 px-3 py-4">
      {navigation.map((group, i) => (
        <div key={group.section ?? i}>
          {group.section && (
            <p className="text-muted-foreground px-3 pt-4 pb-1.5 text-[11px] font-bold tracking-widest uppercase">
              {group.section}
            </p>
          )}
          {group.items.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  // Pílula azul-claro no lugar da barra azul sólida: marca a
                  // página atual sem virar o elemento mais pesado da tela.
                  "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-semibold"
                    : "text-sidebar-foreground hover:bg-muted font-medium",
                )}
                onClick={onNavigate}
              >
                <item.icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.7} />
                {item.name}
              </Link>
            )
          })}
        </div>
      ))}
    </nav>
  )
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/login')
    } catch (error) {
      console.error('Erro ao fazer logout:', error)
      router.push('/login')
    }
  }

  const getUserInitials = () => {
    if (!user?.name) return 'U'
    return user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  const brand = (
    <div className="flex h-16 items-center gap-2.5 px-6">
      <Image src="/logo-icon.svg" alt="" width={32} height={32} className="h-8 w-8" aria-hidden />
      <span className="font-display text-xl font-bold tracking-tight">Imobly</span>
    </div>
  )

  const userBlock = (onDone?: () => void) => (
    <div className="border-hairline border-t p-4">
      <div className="flex items-center gap-3">
        <span className="bg-brand-50 text-brand-700 flex size-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold">
          {getUserInitials()}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{user?.name || 'Usuário'}</p>
          <p className="text-muted-foreground truncate text-xs">{user?.email}</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Sair da conta"
          className="text-muted-foreground hover:text-critical-strong hover:bg-critical-soft"
          onClick={() => {
            onDone?.()
            handleLogout()
          }}
        >
          <LogOut className="h-[18px] w-[18px]" />
        </Button>
      </div>
    </div>
  )

  return (
    <div className="bg-background min-h-screen">
      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetTrigger asChild>
          <Button
            variant="outline"
            className="bg-card fixed top-4 left-4 z-40 md:hidden"
            size="icon"
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="bg-sidebar w-64 p-0">
          <div className="flex h-full flex-col">
            {brand}
            <SidebarNav pathname={pathname} onNavigate={() => setSidebarOpen(false)} />
            {userBlock(() => setSidebarOpen(false))}
          </div>
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <div className="hidden md:fixed md:inset-y-0 md:flex md:w-64 md:flex-col">
        <div className="bg-sidebar border-sidebar-border flex min-h-0 flex-1 flex-col border-r">
          {brand}
          <SidebarNav pathname={pathname} />
          {userBlock()}
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64">
        <main className="p-4 md:p-8">{children}</main>
      </div>
    </div>
  )
}
