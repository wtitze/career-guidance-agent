import { Bot, User } from 'lucide-react';
import { FC } from 'react';

interface ChatBubbleProps {
  message: string;
  isUser: boolean;
  timestamp?: string;
}

const ChatBubble: FC<ChatBubbleProps> = ({ message, isUser, timestamp }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* Icona utente/assistente */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-100' : 'bg-green-100'
          }`}>
            {isUser ? (
              <User className="w-5 h-5 text-blue-600" />
            ) : (
              <Bot className="w-5 h-5 text-green-600" />
            )}
          </div>
        </div>
        
        {/* Bolla messaggio */}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-blue-500 text-white rounded-tr-none' 
            : 'bg-gray-100 text-gray-800 rounded-tl-none'
        }`}>
          <p className="text-sm whitespace-pre-wrap">{message}</p>
          
          {/* Timestamp (opzionale) */}
          {timestamp && (
            <p className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>
              {timestamp}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
