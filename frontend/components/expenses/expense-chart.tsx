"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { formatCurrency, formatDate } from '@/lib/utils/format'

interface Expense {
  id: string
  type: "expense" | "maintenance"
  category: string
  description: string
  amount: number
  date: string
  property: string
  status: "pending" | "paid" | "scheduled"
  priority?: "low" | "medium" | "high" | "urgent"
  vendor?: string
  receipt?: string
  notes?: string
}

interface ExpenseChartProps {
  expenses: Expense[]
}

export function ExpenseChart({ expenses }: ExpenseChartProps) {
  // Dados para gráfico de indicadores
  const currentMonth = formatDate(new Date(), { month: "long", year: "numeric" })
  const lastMonth = formatDate(new Date(new Date().setMonth(new Date().getMonth() - 1)), { month: "long", year: "numeric" })
  
  // Calcula os indicadores atuais
  const currentMonthExpenses = expenses.filter(expense => {
    const expenseMonth = formatDate(expense.date, { month: "long", year: "numeric" })
    return expenseMonth === currentMonth
  })
  
  const lastMonthExpenses = expenses.filter(expense => {
    const expenseMonth = formatDate(expense.date, { month: "long", year: "numeric" })
    return expenseMonth === lastMonth
  })

  const indicators = [
    {
      title: "Total Atual",
      value: currentMonthExpenses.reduce((sum, expense) => sum + expense.amount, 0),
      subtitle: currentMonth,
      trend: "neutral" as const
    },
    {
      title: "Despesas",
      value: currentMonthExpenses.filter(e => e.type === "expense").reduce((sum, expense) => sum + expense.amount, 0),
      subtitle: "Apenas despesas operacionais",
      trend: "neutral" as const
    },
    {
      title: "Manutenções", 
      value: currentMonthExpenses.filter(e => e.type === "maintenance").reduce((sum, expense) => sum + expense.amount, 0),
      subtitle: "Manutenções e reparos",
      trend: "neutral" as const
    },
    {
      title: "Comparação",
      value: currentMonthExpenses.reduce((sum, expense) => sum + expense.amount, 0) - lastMonthExpenses.reduce((sum, expense) => sum + expense.amount, 0),
      subtitle: `vs ${lastMonth}`,
      trend: (currentMonthExpenses.reduce((sum, expense) => sum + expense.amount, 0) - lastMonthExpenses.reduce((sum, expense) => sum + expense.amount, 0)) > 0 ? "up" as const : "down" as const
    }
  ]

  // Dados para gráfico de pizza (por categoria)
  const categoryData = expenses.reduce((acc, expense) => {
    const existing = acc.find((item) => item.name === expense.category)

    if (existing) {
      existing.value += expense.amount
    } else {
      acc.push({
        name: expense.category,
        value: expense.amount,
      })
    }

    return acc
  }, [] as any[])

  // Séries do sistema (app/globals.css): mesma família, luminâncias distintas.
  const COLORS = ["#095bbd", "#2e7ccb", "#80bcee", "#0b7a62", "#9b2fb4", "#e2872f", "#5b7086", "#c06fd4"]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Indicadores Principais */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>Indicadores de Despesas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              {indicators.map((indicator, index) => (
                <div key={index} className="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="text-2xl font-bold text-blue-600 mb-1">
                    {indicator.value < 0 ? 
                      `-${formatCurrency(Math.abs(indicator.value))}` :
                      formatCurrency(indicator.value)
                    }
                  </div>
                  <div className="text-sm font-medium text-blue-700 mb-1">{indicator.title}</div>
                  <div className="text-xs text-blue-500">{indicator.subtitle}</div>
                  {indicator.trend !== "neutral" && (
                    <div className={`text-xs mt-1 ${indicator.trend === "up" ? "text-red-500" : "text-green-500"}`}>
                      {indicator.trend === "up" ? "↑ Aumento" : "↓ Redução"}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Despesas por Categoria */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>Despesas por Categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#095bbd"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [
                    formatCurrency(value),
                    "Valor",
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
