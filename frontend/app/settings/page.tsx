'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { DashboardLayout } from '@/components/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/contexts/auth';
import { Settings, User, Lock, LogOut, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const { user, logout, changePassword, updateUser } = useAuth();
  const router = useRouter();
  
  // Estado para edição de perfil
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');

  // Estado para alteração de senha
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
    setProfileError('');
    setProfileSuccess('');
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    setPasswordError('');
    setPasswordSuccess('');
  };

  const handleSaveProfile = async () => {
    setProfileLoading(true);
    setProfileError('');
    setProfileSuccess('');

    try {
      await updateUser({
        email: profileData.email,
        full_name: profileData.name,
      });
      
      setProfileSuccess('Perfil atualizado com sucesso!');
      setIsEditingProfile(false);
      
      // Limpa a mensagem após 3 segundos
      setTimeout(() => setProfileSuccess(''), 3000);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : 'Erro ao atualizar perfil');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordLoading(true);
    setPasswordError('');
    setPasswordSuccess('');

    // Validações
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('As senhas não coincidem');
      setPasswordLoading(false);
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setPasswordError('A senha deve ter pelo menos 6 caracteres');
      setPasswordLoading(false);
      return;
    }

    try {
      await changePassword({
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword,
      });
      
      setPasswordSuccess('Senha alterada com sucesso!');
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      setIsChangingPassword(false);
      
      // Limpa a mensagem após 3 segundos
      setTimeout(() => setPasswordSuccess(''), 3000);
    } catch (error) {
      setPasswordError(error instanceof Error ? error.message : 'Erro ao alterar senha');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
      // Mesmo com erro, redireciona para login
      router.push('/login');
    }
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Settings className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Configurações</h1>
              <p className="text-gray-600 mt-1">
                Gerencie suas informações pessoais e preferências
              </p>
            </div>
          </div>

          {/* Informações do Perfil */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="h-5 w-5 text-gray-600" />
                <CardTitle>Informações Pessoais</CardTitle>
              </div>
              <CardDescription>
                Atualize seus dados pessoais e informações de contato
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mensagens de sucesso/erro */}
              {profileSuccess && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="text-sm font-medium">{profileSuccess}</span>
                </div>
              )}
              
              {profileError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">{profileError}</span>
                </div>
              )}

              {!isEditingProfile ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Nome</Label>
                      <p className="mt-1 text-sm text-gray-900">{user?.name}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Email</Label>
                      <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                    </div>
                  </div>
                  
                  <div className="pt-2">
                    <Button onClick={() => setIsEditingProfile(true)}>
                      Editar Perfil
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Nome Completo</Label>
                      <Input
                        id="name"
                        name="name"
                        value={profileData.name}
                        onChange={handleProfileChange}
                        disabled={profileLoading}
                        placeholder="Seu nome completo"
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={profileData.email}
                        onChange={handleProfileChange}
                        disabled={profileLoading}
                        placeholder="seu@email.com"
                      />
                    </div>
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={handleSaveProfile}
                      disabled={profileLoading}
                    >
                      {profileLoading ? 'Salvando...' : 'Salvar Alterações'}
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setIsEditingProfile(false);
                        setProfileData({ name: user?.name || '', email: user?.email || '' });
                        setProfileError('');
                        setProfileSuccess('');
                      }}
                      disabled={profileLoading}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Alteração de Senha */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-gray-600" />
                <CardTitle>Segurança</CardTitle>
              </div>
              <CardDescription>
                Altere sua senha para manter sua conta segura
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mensagens de sucesso/erro */}
              {passwordSuccess && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="text-sm font-medium">{passwordSuccess}</span>
                </div>
              )}
              
              {passwordError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">{passwordError}</span>
                </div>
              )}

              {!isChangingPassword ? (
                <div>
                  <p className="text-sm text-gray-600 mb-4">
                    Recomendamos alterar sua senha periodicamente para manter sua conta segura.
                  </p>
                  <Button onClick={() => setIsChangingPassword(true)}>
                    Alterar Senha
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="oldPassword">Senha Atual</Label>
                    <Input
                      id="oldPassword"
                      name="oldPassword"
                      type="password"
                      value={passwordData.oldPassword}
                      onChange={handlePasswordChange}
                      disabled={passwordLoading}
                      placeholder="Digite sua senha atual"
                    />
                  </div>
                  <div>
                    <Label htmlFor="newPassword">Nova Senha</Label>
                    <Input
                      id="newPassword"
                      name="newPassword"
                      type="password"
                      value={passwordData.newPassword}
                      onChange={handlePasswordChange}
                      disabled={passwordLoading}
                      placeholder="Mínimo 6 caracteres"
                      minLength={6}
                    />
                  </div>
                  <div>
                    <Label htmlFor="confirmPassword">Confirmar Nova Senha</Label>
                    <Input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      value={passwordData.confirmPassword}
                      onChange={handlePasswordChange}
                      disabled={passwordLoading}
                      placeholder="Digite a senha novamente"
                      minLength={6}
                    />
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={handleChangePassword}
                      disabled={passwordLoading}
                    >
                      {passwordLoading ? 'Alterando...' : 'Alterar Senha'}
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setIsChangingPassword(false);
                        setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
                        setPasswordError('');
                        setPasswordSuccess('');
                      }}
                      disabled={passwordLoading}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sair da Conta */}
          <Card className="border-red-200">
            <CardHeader>
              <div className="flex items-center gap-2">
                <LogOut className="h-5 w-5 text-red-600" />
                <CardTitle className="text-red-600">Sair da Conta</CardTitle>
              </div>
              <CardDescription>
                Encerre sua sessão e volte para a tela de login
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                variant="destructive" 
                onClick={handleLogout}
                className="w-full md:w-auto"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sair da Aplicação
              </Button>
            </CardContent>
          </Card>

          {/* Informações da Conta */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-gray-700">Informações da Conta</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Conta criada em:</span>
                  <p className="font-medium text-gray-900 mt-1">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric'
                    }) : '-'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Última atualização:</span>
                  <p className="font-medium text-gray-900 mt-1">
                    {user?.updated_at ? new Date(user.updated_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric'
                    }) : '-'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
