import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { LucideIcon } from "lucide-react"

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  variant?: 'default' | 'error'
}

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  variant = 'default'
}: EmptyStateProps) {
  const isError = variant === 'error'
  
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16">
        {Icon && (
          <div className={`w-16 h-16 ${isError ? 'bg-red-100' : 'bg-gray-100'} rounded-full flex items-center justify-center mb-4`}>
            <Icon className={`h-8 w-8 ${isError ? 'text-red-500' : 'text-gray-400'}`} />
          </div>
        )}
        <h3 className={`text-lg font-semibold mb-2 ${isError ? 'text-red-600' : 'text-gray-700'}`}>
          {title}
        </h3>
        <p className="text-gray-500 text-center mb-4 max-w-md">
          {description}
        </p>
        {action && (
          <Button onClick={action.onClick} variant={isError ? "outline" : "default"}>
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
