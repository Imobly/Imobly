import { ChargesView } from "@/components/charges/charges-view"

export default function ChargesPage() {
  return (
    <>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">Cobranças</h1>
        <p className="text-muted-foreground mt-2">
          Aluguéis do mês, recebimentos e saldo devedor de cada inquilino
        </p>
      </div>
      <ChargesView />
    </>
  )
}
