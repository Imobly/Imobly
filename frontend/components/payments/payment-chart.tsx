"use client"

import { ResponsiveContainer, XAxis, YAxis, Tooltip, Legend, Bar, BarChart } from "recharts"

const data = [
  {
    name: "Jul",
    recebido: 42000,
    pendente: 3200,
    atrasado: 1500,
  },
  {
    name: "Ago",
    recebido: 44000,
    pendente: 2800,
    atrasado: 900,
  },
  {
    name: "Set",
    recebido: 43500,
    pendente: 3500,
    atrasado: 1200,
  },
  {
    name: "Out",
    recebido: 45000,
    pendente: 2200,
    atrasado: 800,
  },
  {
    name: "Nov",
    recebido: 46500,
    pendente: 3200,
    atrasado: 1800,
  },
  {
    name: "Dez",
    recebido: 45000,
    pendente: 3200,
    atrasado: 4725,
  },
]

export function PaymentChart() {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `R$ ${value.toLocaleString("pt-BR")}`}
        />
        <Tooltip
          formatter={(value: number) => [`R$ ${value.toLocaleString("pt-BR")}`, ""]}
          labelStyle={{ color: "#000" }}
        />
        <Legend />
        <Bar dataKey="recebido" name="Recebido" fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="pendente" name="Pendente" fill="#eab308" radius={[4, 4, 0, 0]} />
        <Bar dataKey="atrasado" name="Atrasado" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
