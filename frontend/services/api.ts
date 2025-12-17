import axios from 'axios';

// ⚠️ MODIFICA QUESTA RIGA! Usa il TUO URL del backend
const API_BASE_URL = 'https://fluffy-waddle-5g99rp4w79346xq-8000.app.github.dev';

// Crea istanza axios configurata
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 secondi per connessione internet
});

// Tipi per le risposte
export interface ChatMessageRequest {
  message: string;
  session_id?: string;
}

export interface ChatMessageResponse {
  response: string;
  session_id: string;
  recommendations?: any[];
  conversation_history: any[];
}

// Funzioni API
export const chatAPI = {
  // Invia un messaggio all'agente
  sendMessage: async (message: string, sessionId?: string): Promise<ChatMessageResponse> => {
    try {
      console.log('Invio messaggio a:', API_BASE_URL);
      const response = await api.post('/api/chat', {
        message,
        session_id: sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error('Errore invio messaggio:', error.message);
      if (error.response) {
        console.error('Dettaglio errore:', error.response.data);
      }
      throw error;
    }
  },

  // Ottieni raccomandazioni
  getRecommendations: async (data: {
    interests: string[];
    skills: string[];
    location?: string;
    budget?: number;
  }) => {
    try {
      const response = await api.post('/api/recommendations', data);
      return response.data;
    } catch (error) {
      console.error('Errore raccomandazioni:', error);
      throw error;
    }
  },

  // Controlla salute backend
  checkHealth: async (): Promise<{status: string, agent_ready: boolean}> => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Backend non raggiungibile:', error);
      throw error;
    }
  },
};

// Esporta anche l'istanza axios se serve
export default api;
