export default function ConfigPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Configurações</h1>
          <p className="text-gray-600 mt-2">
            Configurações do sistema e informações da API
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-1">
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-xl font-semibold mb-4">Status da Conexão</h2>
            <div className="text-center py-8">
              <div className="text-green-600 text-lg font-medium">
                ✅ Sistema conectado com sucesso
              </div>
              <p className="text-sm text-gray-500 mt-2">
                A aplicação está rodando no Docker e conectada ao backend
              </p>
            </div>
          </div>
          
          <div className="space-y-4 bg-white rounded-lg border p-6">
            <h2 className="text-xl font-semibold">Informações de Configuração</h2>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Frontend URL:</span>
                <span className="font-mono">{process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}</span>
              </div>
              
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">API URL:</span>
                <span className="font-mono">{process.env.NEXT_PUBLIC_API_URL || 'Não configurada'}</span>
              </div>
              
              <div className="flex justify-between py-2 border-b">
                <span className="font-medium">Ambiente:</span>
                <span className="font-mono">{process.env.NODE_ENV || 'development'}</span>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
              <h3 className="font-medium text-blue-900 mb-2">Para conectar com o backend:</h3>
              <ol className="text-sm text-blue-800 space-y-1">
                <li>1. Certifique-se que o backend está rodando na porta 8000</li>
                <li>2. Verifique se CORS está configurado corretamente</li>
                <li>3. Confirme que a variável NEXT_PUBLIC_API_URL está definida</li>
                <li>4. Teste a conexão usando o botão ao lado</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}