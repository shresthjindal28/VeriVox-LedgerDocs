'use client';

import * as React from 'react';
import { useProfile, usePreferences, useUpdateProfile, useUpdatePreferences } from '@/hooks';
import { useAuthStore } from '@/stores';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components/ui';
import { User, Settings, BookOpen, Moon, Sun } from 'lucide-react';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const { data: profile, isLoading: profileLoading } = useProfile();
  const { data: preferences, isLoading: prefsLoading } = usePreferences();
  const updateProfile = useUpdateProfile();
  const updatePreferences = useUpdatePreferences();
  
  const [displayName, setDisplayName] = React.useState('');
  const [bio, setBio] = React.useState('');
  
  React.useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setBio(profile.bio || '');
    }
  }, [profile]);
  
  const handleProfileSave = () => {
    updateProfile.mutate({
      display_name: displayName,
      bio,
    });
  };
  
  const handleThemeToggle = () => {
    const newTheme = preferences?.theme === 'dark' ? 'light' : 'dark';
    updatePreferences.mutate({ theme: newTheme });
    
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };
  
  if (profileLoading || prefsLoading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }
  
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-8 text-3xl font-bold">Profile Settings</h1>
      
      <div className="space-y-6">
        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Account Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p className="mt-1">{user?.email}</p>
            </div>
            
            <Input
              label="Display Name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Your display name"
            />
            
            <div>
              <label className="mb-2 block text-sm font-medium">Bio</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell us about yourself..."
                rows={3}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            
            <Button
              onClick={handleProfileSave}
              isLoading={updateProfile.isPending}
            >
              Save Changes
            </Button>
          </CardContent>
        </Card>
        
        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Theme</p>
                <p className="text-sm text-muted-foreground">
                  Choose between light and dark mode
                </p>
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={handleThemeToggle}
              >
                {preferences?.theme === 'dark' ? (
                  <Moon className="h-4 w-4" />
                ) : (
                  <Sun className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Preferred Voice</p>
                <p className="text-sm text-muted-foreground">
                  Voice for AI responses
                </p>
              </div>
              <select
                value={preferences?.preferred_voice || 'alloy'}
                onChange={(e) => updatePreferences.mutate({ preferred_voice: e.target.value })}
                className="rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="alloy">Alloy</option>
                <option value="echo">Echo</option>
                <option value="fable">Fable</option>
                <option value="onyx">Onyx</option>
                <option value="nova">Nova</option>
                <option value="shimmer">Shimmer</option>
              </select>
            </div>
          </CardContent>
        </Card>
        
        {/* Study Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Study Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="font-medium">Subjects</p>
              <p className="text-sm text-muted-foreground">
                {preferences?.subjects?.join(', ') || 'No subjects set'}
              </p>
            </div>
            
            <div>
              <p className="font-medium">Study Goals</p>
              <p className="text-sm text-muted-foreground">
                {preferences?.study_goals?.join(', ') || 'No goals set'}
              </p>
            </div>
            
            <div>
              <p className="font-medium">Daily Study Time</p>
              <p className="text-sm text-muted-foreground">
                {preferences?.daily_study_time || 0} minutes
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
