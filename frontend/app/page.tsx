import ChatInterface from '@/components/ChatInterface';
import Header from '@/components/Navigation/Header';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Hero section */}
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">
            Trova il tuo percorso perfetto con l'AI 🤖
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Il nostro assistente AI ti aiuta a scoprire le migliori opzioni post-diploma: 
            università, ITS, o mondo del lavoro. Conversa naturalmente e ricevi consigli personalizzati.
          </p>
        </div>
        
        {/* Chat principale */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-10">
          <ChatInterface />
        </div>
        
        {/* Cards informative */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition">
            <div className="text-blue-500 mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-2xl">🎓</span>
              </div>
            </div>
            <h3 className="font-semibold text-lg mb-2">Università</h3>
            <p className="text-gray-600 text-sm">
              Scopri i corsi di laurea più adatti ai tuoi interessi e capacità, 
              con informazioni su accesso, costi e sbocchi professionali.
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition">
            <div className="text-green-500 mb-4">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-2xl">💼</span>
              </div>
            </div>
            <h3 className="font-semibold text-lg mb-2">ITS</h3>
            <p className="text-gray-600 text-sm">
              Corsi tecnici superiori con alto tasso di occupazione (90%+). 
              Formazione pratica in 2 anni con stage in azienda.
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition">
            <div className="text-purple-500 mb-4">
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                <span className="text-2xl">🚀</span>
              </div>
            </div>
            <h3 className="font-semibold text-lg mb-2">Lavoro</h3>
            <p className="text-gray-600 text-sm">
              Percorsi professionali, opportunità di carriera, competenze richieste 
              dal mercato e guide per entrare nel mondo del lavoro.
            </p>
          </div>
        </div>
        
        {/* Footer info */}
        <div className="text-center text-gray-500 text-sm border-t border-gray-200 pt-6">
          <p>✨ Assistente AI per l'orientamento universitario e professionale</p>
          <p className="mt-2">
            Il backend deve essere in esecuzione su 
            <code className="bg-gray-100 px-2 py-1 rounded mx-2 font-mono">localhost:8000</code>
            per la chat completa
          </p>
        </div>
      </main>
    </div>
  );
}
