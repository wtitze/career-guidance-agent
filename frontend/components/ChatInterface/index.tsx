'use client';

import { useState, useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import { Send, Bot, Loader2, Sparkles } from 'lucide-react';
import { chatAPI } from '@/services/api';

// Tipo per i messaggi
interface Message {
  text: string;
  isUser: boolean;
  timestamp: string;
}

export default function ChatInterface() {
  // Stato per i messaggi
  const [messages, setMessages] = useState<Message[]>([
    { 
      text: "Ciao! Sono il tuo assistente per l'orientamento post-diploma. Posso aiutarti a scoprire università, corsi ITS, opportunità di lavoro e molto altro. Cosa ti interessa sapere?", 
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  
  // Stato per l'input utente
  const [input, setInput] = useState('');
  
  // Stato per il caricamento
  const [loading, setLoading] = useState(false);
  
  // Stato per la session ID
  const [sessionId, setSessionId] = useState<string | undefined>();
  
  // Ref per scroll automatico
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll automatico all'ultimo messaggio
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Funzione per inviare un messaggio
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Aggiungi messaggio utente
    setMessages(prev => [...prev, { 
      text: userMessage, 
      isUser: true,
      timestamp 
    }]);
    
    setLoading(true);

    try {
      // Chiama l'API del backend
      const response = await chatAPI.sendMessage(userMessage, sessionId);
      
      // Salva session ID se è la prima volta
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }
      
      // Aggiungi risposta dell'assistente
      setMessages(prev => [...prev, { 
        text: response.response, 
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
      
    } catch (error) {
      console.error('Errore nella chat:', error);
      
      // Messaggio di errore
      setMessages(prev => [...prev, { 
        text: "Mi dispiace, c'è stato un errore nella comunicazione con il server. Riprova tra un momento.", 
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Gestione Invio con tasto Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Domande suggerite per iniziare
  const suggestedQuestions = [
    "Quali sono i migliori corsi di informatica?",
    "Cosa sono gli ITS?",
    "Mi consigli università a Milano?",
    "Come trovo lavoro dopo il diploma?"
  ];

  return (
    <div className="flex flex-col h-[600px] border border-gray-200 rounded-xl shadow-sm">
      {/* Header della chat */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-gray-800">Assistente Orientamento AI</h2>
            <p className="text-sm text-gray-600">Ti aiuto a trovare il percorso perfetto</p>
          </div>
        </div>
      </div>

      {/* Area messaggi */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          {messages.map((msg, idx) => (
            <ChatBubble 
              key={idx} 
              message={msg.text} 
              isUser={msg.isUser}
              timestamp={msg.timestamp}
            />
          ))}
          
          {/* Indicatore di typing */}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-green-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Domande suggerite (solo prima chat) */}
      {messages.length === 1 && (
        <div className="px-4 pb-3 border-b border-gray-200">
          <div className="max-w-3xl mx-auto">
            <p className="text-sm text-gray-500 mb-2">💡 Domande per iniziare:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInput(question);
                    setTimeout(() => {
                      handleSend();
                    }, 100);
                  }}
                  className="text-sm bg-blue-50 text-blue-700 px-3 py-2 rounded-lg hover:bg-blue-100 transition border border-blue-100"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="p-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <div className="flex space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Scrivi la tua domanda qui..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
                disabled={loading}
              />
              <div className="absolute right-3 top-3">
                <Sparkles className="w-5 h-5 text-gray-400" />
              </div>
            </div>
            
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition self-end"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Invio...</span>
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span>Invia</span>
                </>
              )}
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            L'assistente AI può commettere errori. Verifica sempre le informazioni importanti.
          </p>
        </div>
      </div>
    </div>
  );
}
