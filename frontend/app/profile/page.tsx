'use client';

import * as React from 'react';
import { AppLayout } from '@/components/layout';
import { Card, Button, Input } from '@/components/ui';
import { Camera, Pencil, Check, X, Trash2, User, Mail, Shield, Calendar, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores';
import { useProfile, useUpdateProfile, useUploadAvatar, useDeleteAvatar } from '@/hooks';
import { toast } from 'sonner';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';

export default function ProfilePage() {
  const { user, profile } = useAuthStore();
  const { data: profileData, isLoading: profileLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const uploadAvatar = useUploadAvatar();
  const deleteAvatar = useDeleteAvatar();

  const currentProfile = profileData || profile;

  const [isEditingName, setIsEditingName] = React.useState(false);
  const [isEditingBio, setIsEditingBio] = React.useState(false);
  const [displayName, setDisplayName] = React.useState('');
  const [bio, setBio] = React.useState('');
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Sync state when profile loads
  React.useEffect(() => {
    if (currentProfile) {
      setDisplayName(currentProfile.display_name || '');
      setBio(currentProfile.bio || '');
    }
  }, [currentProfile]);

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type', {
        description: 'Please upload a PNG, JPG, GIF, or WEBP image.',
      });
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File too large', {
        description: 'Maximum file size is 5 MB.',
      });
      return;
    }

    try {
      await uploadAvatar.mutateAsync(file);
      toast.success('Avatar updated!', {
        description: 'Your profile picture has been updated successfully.',
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to upload avatar';
      toast.error('Upload failed', { description: message });
    }

    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDeleteAvatar = async () => {
    try {
      await deleteAvatar.mutateAsync();
      toast.success('Avatar removed', {
        description: 'Your profile picture has been removed.',
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete avatar';
      toast.error('Delete failed', { description: message });
    }
  };

  const handleSaveName = async () => {
    if (!displayName.trim()) {
      toast.error('Name required', { description: 'Display name cannot be empty.' });
      return;
    }
    try {
      await updateProfile.mutateAsync({ display_name: displayName.trim() });
      setIsEditingName(false);
      toast.success('Name updated!');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update name';
      toast.error('Update failed', { description: message });
    }
  };

  const handleSaveBio = async () => {
    try {
      await updateProfile.mutateAsync({ bio: bio.trim() });
      setIsEditingBio(false);
      toast.success('Bio updated!');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update bio';
      toast.error('Update failed', { description: message });
    }
  };

  const avatarUrl = currentProfile?.avatar_url;
  const initials = (currentProfile?.display_name || user?.display_name || 'U')[0]?.toUpperCase();

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : 'N/A';

  return (
    <AppLayout>
      <div className="min-h-screen text-white p-6 md:p-8 lg:p-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="max-w-3xl mx-auto"
        >
          {/* Page Title */}
          <h1 className="text-3xl font-bold mb-8 tracking-tight">Profile</h1>

          {/* Avatar & Main Info Card */}
          <Card className="relative overflow-hidden border-brand-500/10 bg-brand-950/20 backdrop-blur-xl mb-6">
            {/* Decorative Gradient Header */}
            <div className="h-32 bg-gradient-to-br from-brand-500/30 via-brand-600/20 to-brand-900/30 relative">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(34,197,94,0.15),transparent_60%)]" />
            </div>

            <div className="px-6 md:px-8 pb-8 -mt-16 relative">
              {/* Avatar Section */}
              <div className="flex flex-col sm:flex-row items-center sm:items-end gap-6">
                <div className="relative group">
                  <motion.div
                    whileHover={{ scale: 1.03 }}
                    className="relative h-28 w-28 rounded-2xl overflow-hidden border-4 border-black bg-brand-950 shadow-2xl shadow-brand-500/20 cursor-pointer"
                    onClick={handleAvatarClick}
                  >
                    {avatarUrl ? (
                      <Image
                        src={avatarUrl}
                        alt="Profile"
                        fill
                        className="object-cover"
                        unoptimized
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-black text-4xl font-bold">
                        {initials}
                      </div>
                    )}

                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      {uploadAvatar.isPending ? (
                        <Loader2 className="h-6 w-6 text-white animate-spin" />
                      ) : (
                        <Camera className="h-6 w-6 text-white" />
                      )}
                    </div>
                  </motion.div>

                  {/* Delete avatar button */}
                  {avatarUrl && (
                    <button
                      onClick={handleDeleteAvatar}
                      disabled={deleteAvatar.isPending}
                      className="absolute -bottom-1 -right-1 p-1.5 rounded-lg bg-red-500/90 text-white hover:bg-red-500 transition-colors shadow-lg"
                      title="Remove photo"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/gif,image/webp"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </div>

                {/* Name & Email */}
                <div className="flex-1 text-center sm:text-left pb-1">
                  <AnimatePresence mode="wait">
                    {isEditingName ? (
                      <motion.div
                        key="editing"
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="flex items-center gap-2"
                      >
                        <Input
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          className="bg-white/5 border-brand-500/30 text-white text-lg font-semibold h-10 max-w-[250px]"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveName();
                            if (e.key === 'Escape') {
                              setDisplayName(currentProfile?.display_name || '');
                              setIsEditingName(false);
                            }
                          }}
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={handleSaveName}
                          disabled={updateProfile.isPending}
                          className="text-brand-500 hover:text-brand-400 hover:bg-brand-500/10 h-9 w-9"
                        >
                          {updateProfile.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Check className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setDisplayName(currentProfile?.display_name || '');
                            setIsEditingName(false);
                          }}
                          className="text-brand-100/40 hover:text-white hover:bg-white/5 h-9 w-9"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="display"
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="flex items-center gap-2 justify-center sm:justify-start"
                      >
                        <h2 className="text-2xl font-bold text-white">
                          {currentProfile?.display_name || user?.display_name || 'User'}
                        </h2>
                        <button
                          onClick={() => setIsEditingName(true)}
                          className="p-1.5 rounded-lg text-brand-100/30 hover:text-brand-500 hover:bg-brand-500/10 transition-all"
                          title="Edit name"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <p className="text-brand-100/50 mt-1 flex items-center gap-1.5 justify-center sm:justify-start">
                    <Mail className="h-3.5 w-3.5" />
                    {user?.email || 'No email'}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Bio Card */}
          <Card className="border-brand-500/10 bg-brand-950/20 backdrop-blur-xl mb-6 p-6 md:p-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">About</h3>
              {!isEditingBio && (
                <button
                  onClick={() => setIsEditingBio(true)}
                  className="p-1.5 rounded-lg text-brand-100/30 hover:text-brand-500 hover:bg-brand-500/10 transition-all"
                  title="Edit bio"
                >
                  <Pencil className="h-4 w-4" />
                </button>
              )}
            </div>

            <AnimatePresence mode="wait">
              {isEditingBio ? (
                <motion.div
                  key="editing-bio"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                >
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    placeholder="Tell us about yourself..."
                    maxLength={500}
                    rows={4}
                    className="w-full bg-white/5 border border-brand-500/20 rounded-xl px-4 py-3 text-white placeholder:text-brand-100/20 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 resize-none text-sm"
                    autoFocus
                  />
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-brand-100/30">{bio.length}/500</span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setBio(currentProfile?.bio || '');
                          setIsEditingBio(false);
                        }}
                        className="text-brand-100/60 hover:text-white"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSaveBio}
                        disabled={updateProfile.isPending}
                        className="bg-brand-500 text-black hover:bg-brand-400 font-bold"
                      >
                        {updateProfile.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-1" />
                        ) : null}
                        Save
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.p
                  key="display-bio"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                  className="text-brand-100/60 text-sm leading-relaxed"
                >
                  {currentProfile?.bio || 'No bio yet. Click the edit icon to add one.'}
                </motion.p>
              )}
            </AnimatePresence>
          </Card>

          {/* Account Details Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card className="border-brand-500/10 bg-brand-950/20 backdrop-blur-xl p-5 hover:border-brand-500/20 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-brand-500/10">
                    <Shield className="h-4 w-4 text-brand-500" />
                  </div>
                  <h3 className="text-sm font-medium text-brand-100/50">Role</h3>
                </div>
                <p className="text-lg font-semibold text-white capitalize">
                  {currentProfile?.role || user?.role || 'Student'}
                </p>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              <Card className="border-brand-500/10 bg-brand-950/20 backdrop-blur-xl p-5 hover:border-brand-500/20 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-brand-500/10">
                    <Calendar className="h-4 w-4 text-brand-500" />
                  </div>
                  <h3 className="text-sm font-medium text-brand-100/50">Member Since</h3>
                </div>
                <p className="text-lg font-semibold text-white">{memberSince}</p>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="border-brand-500/10 bg-brand-950/20 backdrop-blur-xl p-5 hover:border-brand-500/20 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-brand-500/10">
                    <User className="h-4 w-4 text-brand-500" />
                  </div>
                  <h3 className="text-sm font-medium text-brand-100/50">Account</h3>
                </div>
                <p className="text-lg font-semibold text-white">Free Plan</p>
              </Card>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </AppLayout>
  );
}
