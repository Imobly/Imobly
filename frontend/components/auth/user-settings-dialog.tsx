'use client';

import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { useAuth } from '../../lib/contexts/auth';

interface UserSettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UserSettingsDialog({ open, onOpenChange }: UserSettingsDialogProps) {
  const { user, logout, changePassword } = useAuth();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    setErrors({});

    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/me', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          email: profileData.email,
          full_name: profileData.name,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erro ao atualizar perfil' }));
        throw new Error(errorData.detail || 'Erro ao atualizar perfil');
      }

      const userData = await response.json();
      
      // Atualiza o localStorage com os novos dados
      const updatedUser = {
        id: userData.id.toString(),
        email: userData.email,
        name: userData.full_name || userData.username,
        created_at: userData.created_at,
        updated_at: userData.updated_at,
      };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      setIsEditingProfile(false);
      // Force re-render para mostrar os dados atualizados
      window.location.reload();
    } catch (error) {
      setErrors({ profile: error instanceof Error ? error.message : 'Erro ao atualizar perfil' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePassword = async () => {
    setIsLoading(true);
    setErrors({});

    // Validações
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setErrors({ confirmPassword: 'As senhas não coincidem' });
      setIsLoading(false);
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setErrors({ newPassword: 'A senha deve ter pelo menos 6 caracteres' });
      setIsLoading(false);
      return;
    }

    try {
      await changePassword({
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword,
      });
      
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      setIsChangingPassword(false);
      alert('Senha alterada com sucesso!');
    } catch (error) {
      setErrors({ oldPassword: error instanceof Error ? error.message : 'Erro ao alterar senha' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    onOpenChange(false);
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Configurações da Conta</DialogTitle>
          <DialogDescription>
            Gerencie suas informações pessoais e preferências
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* User Info Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Informações Pessoais</h3>
            
            {!isEditingProfile ? (
              <div className="space-y-3">
                <div>
                  <Label className="text-sm font-medium">Nome</Label>
                  <p className="text-sm text-gray-600">{user.name}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Email</Label>
                  <p className="text-sm text-gray-600">{user.email}</p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setIsEditingProfile(true)}
                >
                  Editar Perfil
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <Label htmlFor="name">Nome</Label>
                  <Input
                    id="name"
                    name="name"
                    value={profileData.name}
                    onChange={handleProfileChange}
                    disabled={isLoading}
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
                    disabled={isLoading}
                  />
                </div>
                {errors.profile && (
                  <p className="text-sm text-red-500">{errors.profile}</p>
                )}
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    onClick={handleSaveProfile}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Salvando...' : 'Salvar'}
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      setIsEditingProfile(false);
                      setProfileData({ name: user.name, email: user.email });
                      setErrors({});
                    }}
                    disabled={isLoading}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Password Change Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Alterar Senha</h3>
            
            {!isChangingPassword ? (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setIsChangingPassword(true)}
              >
                Alterar Senha
              </Button>
            ) : (
              <div className="space-y-3">
                <div>
                  <Label htmlFor="oldPassword">Senha Atual</Label>
                  <Input
                    id="oldPassword"
                    name="oldPassword"
                    type="password"
                    value={passwordData.oldPassword}
                    onChange={handlePasswordChange}
                    disabled={isLoading}
                  />
                  {errors.oldPassword && (
                    <p className="text-sm text-red-500">{errors.oldPassword}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="newPassword">Nova Senha</Label>
                  <Input
                    id="newPassword"
                    name="newPassword"
                    type="password"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                    disabled={isLoading}
                  />
                  {errors.newPassword && (
                    <p className="text-sm text-red-500">{errors.newPassword}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="confirmPassword">Confirmar Nova Senha</Label>
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={handlePasswordChange}
                    disabled={isLoading}
                  />
                  {errors.confirmPassword && (
                    <p className="text-sm text-red-500">{errors.confirmPassword}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    onClick={handleChangePassword}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Alterando...' : 'Alterar Senha'}
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      setIsChangingPassword(false);
                      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
                      setErrors({});
                    }}
                    disabled={isLoading}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Logout Section */}
          <div className="pt-4 border-t">
            <Button 
              variant="destructive" 
              onClick={handleLogout}
              className="w-full"
            >
              Sair da Conta
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}