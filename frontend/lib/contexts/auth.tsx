'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthContextType, LoginRequest, RegisterRequest, ChangePasswordRequest } from '../types/auth';
import * as authApi from '../api/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (initialized) return; // Evita reinicialização se já foi feita
    
    const initializeAuth = async () => {
      try {
        // Verifica se há um usuário salvo no localStorage
        const storedUser = authApi.getStoredUser();
        if (storedUser) {
          setUser(storedUser);
        }

        // Verifica se o token ainda é válido apenas se não há usuário carregado
        if (authApi.isAuthenticated() && !storedUser) {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        authApi.logout();
        setUser(null);
      } finally {
        setIsLoading(false);
        setInitialized(true);
      }
    };

    initializeAuth();
  }, [initialized]);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const loggedUser = await authApi.login(credentials);
      setUser(loggedUser);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest) => {
    setIsLoading(true);
    try {
      // Apenas registra o usuário, NÃO faz login automático
      await authApi.register(userData);
      // Não define o user, forçando o usuário a fazer login
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  };

  const changePassword = async (data: ChangePasswordRequest) => {
    await authApi.changePassword(data);
  };

  const updateUser = async (userData: { email?: string; full_name?: string }) => {
    const updatedUser = await authApi.updateUser(userData);
    setUser(updatedUser);
    return updatedUser;
  };

  const isAuthenticated = !!user;

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    changePassword,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}