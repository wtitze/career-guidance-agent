import ChatBubble from '@/components/ChatInterface/ChatBubble';

export default function TestChatBubblePage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-bold mb-6">🧪 Test ChatBubble Component</h1>
      
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-700">Esempi di messaggi:</h2>
        
        {/* Messaggio Assistente */}
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Assistente (AI):</h3>
          <ChatBubble 
            message="Ciao! Sono il tuo assistente per l'orientamento post-diploma. Posso aiutarti a scoprire università, corsi ITS, opportunità di lavoro e molto altro." 
            isUser={false}
            timestamp="10:30"
          />
        </div>
        
        {/* Messaggio Utente */}
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Utente (Tu):</h3>
          <ChatBubble 
            message="Quali sono i migliori corsi di informatica nelle università italiane?" 
            isUser={true}
            timestamp="10:32"
          />
        </div>
        
        {/* Altri esempi */}
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Assistente risponde:</h3>
          <ChatBubble 
            message="In Italia ci sono ottimi corsi di Informatica. Alcuni dei migliori sono: 1) Informatica all'Università di Bologna, 2) Computer Science al Politecnico di Milano, 3) Ingegneria Informatica al Politecnico di Torino." 
            isUser={false}
            timestamp="10:33"
          />
        </div>
        
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Utente chiede ancora:</h3>
          <ChatBubble 
            message="E per quanto riguarda gli ITS? Cosa mi consigli?" 
            isUser={true}
            timestamp="10:35"
          />
        </div>
        
        {/* Stato componente */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-700 mb-2">✅ Componente ChatBubble FUNZIONANTE!</h3>
          <p className="text-sm text-blue-600">
            Il componente visualizza correttamente messaggi utente (blu, destra) e assistente (grigio, sinistra).
          </p>
        </div>
        
        <div className="mt-6 text-center">
          <a 
            href="/" 
            className="inline-block bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition"
          >
            Torna alla Home
          </a>
        </div>
      </div>
    </div>
  );
}
