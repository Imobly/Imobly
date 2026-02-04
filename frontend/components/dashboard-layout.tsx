"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Home, Building2, Users, CreditCard, Receipt, Bell, Menu, Settings, LogOut, User } from "lucide-react"
import { useAuth } from "@/lib/contexts/auth"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Imóveis", href: "/properties", icon: Building2 },
  { name: "Inquilinos", href: "/tenants", icon: Users },
  { name: "Pagamentos", href: "/payments", icon: CreditCard },
  { name: "Despesas", href: "/expenses", icon: Receipt },
  { name: "Notificações", href: "/notifications", icon: Bell },
  { name: "Configurações", href: "/settings", icon: Settings },
]

interface DashboardLayoutProps {
  children: React.ReactNode
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

  return (
    <div className="min-h-screen bg-white">
      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" className="fixed top-4 left-4 z-40 md:hidden" size="icon">
            <Menu className="h-6 w-6" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0 bg-white">
          <div className="flex h-full flex-col">
            <div className="flex h-16 items-center border-b px-6">
              <Building2 className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold">Imobly</span>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      isActive ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
            
            {/* Mobile user info */}
            <div className="border-t p-4 space-y-2">
              <div className="flex items-center gap-3 p-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src="/placeholder-user.jpg" alt={user?.name} />
                  <AvatarFallback className="bg-blue-100 text-blue-600 text-sm">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {user?.name || 'Usuário'}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {user?.email}
                  </p>
                </div>
              </div>
              
              <Button
                variant="ghost"
                className="w-full justify-start text-red-600 hover:bg-red-100 hover:text-red-700"
                onClick={() => {
                  setSidebarOpen(false)
                  handleLogout()
                }}
              >
                <LogOut className="mr-3 h-5 w-5" />
                Sair
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <div className="hidden md:fixed md:inset-y-0 md:flex md:w-64 md:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r bg-white">
          <div className="flex h-16 items-center border-b px-6">
            <Building2 className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold">Imobly</span>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                  )}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
          <div className="border-t p-4 space-y-2">
            {/* User info */}
            <div className="flex items-center gap-3 p-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src="/placeholder-user.jpg" alt={user?.name} />
                <AvatarFallback className="bg-blue-100 text-blue-600 text-sm">
                  {getUserInitials()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.name || 'Usuário'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.email}
                </p>
              </div>
            </div>
            
            {/* Logout button */}
            <Button
              variant="ghost"
              className="w-full justify-start text-red-600 hover:bg-red-100 hover:text-red-700"
              onClick={handleLogout}
            >
              <LogOut className="mr-3 h-5 w-5" />
              Sair
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64">
        <main className="flex-1">
          <div className="p-4 md:p-8">{children}</div>
        </main>
      </div>
    </div>
  )
}
