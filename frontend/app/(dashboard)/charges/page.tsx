import { ChargesView } from "@/components/charges/charges-view"

export default function ChargesPage() {
  return (
    <>
      <div className="mb-6">
        <h1 className="font-display text-3xl font-bold tracking-tight">Cobranças</h1>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Aluguéis do mês, recebimentos e saldo devedor de cada inquilino
        </p>
      </div>
      <ChargesView />
    </>
  )
}
