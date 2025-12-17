'use client';

import { GraduationCap, Menu, X, Home, BookOpen, Briefcase, HelpCircle, User } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { name: 'Home', icon: <Home className="w-4 h-4" />, href: '/' },
    { name: 'Università', icon: <GraduationCap className="w-4 h-4" />, href: '#' },
    { name: 'ITS', icon: <BookOpen className="w-4 h-4" />, href: '#' },
    { name: 'Lavoro', icon: <Briefcase className="w-4 h-4" />, href: '#' },
    { name: 'Guide', icon: <HelpCircle className="w-4 h-4" />, href: '#' },
  ];

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo e nome */}
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-3 no-underline">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">OrientamentoAI</h1>
                <p className="text-xs text-gray-600 hidden sm:block">La tua guida intelligente post-diploma</p>
              </div>
            </Link>
          </div>
          
          {/* Navigazione desktop */}
          <nav className="hidden md:flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center space-x-1 text-gray-700 hover:text-blue-600 font-medium text-sm transition"
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            ))}
            
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 text-gray-700 hover:text-blue-600">
                <User className="w-5 h-5" />
                <span className="text-sm">Profilo</span>
              </button>
              <button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-2 rounded-lg font-medium hover:opacity-90 transition">
                Inizia Chat
              </button>
            </div>
          </nav>
          
          {/* Menu mobile toggle */}
          <button 
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
        
        {/* Menu mobile (aperto) */}
        {isMenuOpen && (
          <div className="mt-4 md:hidden border-t border-gray-200 pt-4">
            <div className="flex flex-col space-y-3">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.icon}
                  <span>{item.name}</span>
                </Link>
              ))}
              
              <div className="pt-3 border-t border-gray-200 space-y-3">
                <button className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-700">
                  <User className="w-5 h-5" />
                  <span>Profilo</span>
                </button>
                <button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 py-3 rounded-lg font-medium hover:opacity-90 transition">
                  Inizia Chat
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
