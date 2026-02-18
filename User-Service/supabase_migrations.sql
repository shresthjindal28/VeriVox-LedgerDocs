-- Supabase SQL Migrations for User Service
-- Run these in your Supabase SQL Editor

-- ============================================================================
-- PROFILES TABLE
-- Extends auth.users with custom profile data
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    phone TEXT,
    role TEXT DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Policy: Insert is allowed for authenticated users (for their own profile)
CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Policy: Service role can do anything
CREATE POLICY "Service role full access"
    ON public.profiles
    USING (auth.jwt() ->> 'role' = 'service_role');


-- ============================================================================
-- STUDY PREFERENCES TABLE
-- User preferences for the study platform
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.study_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    voice TEXT DEFAULT 'nova' CHECK (voice IN ('nova', 'alloy', 'echo', 'fable', 'onyx', 'shimmer')),
    theme TEXT DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    language TEXT DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    auto_play_audio BOOLEAN DEFAULT FALSE,
    playback_speed DECIMAL(2,1) DEFAULT 1.0 CHECK (playback_speed >= 0.5 AND playback_speed <= 2.0),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.study_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own preferences
CREATE POLICY "Users can view own preferences"
    ON public.study_preferences FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can update their own preferences
CREATE POLICY "Users can update own preferences"
    ON public.study_preferences FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own preferences
CREATE POLICY "Users can insert own preferences"
    ON public.study_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Service role can do anything
CREATE POLICY "Service role full access on preferences"
    ON public.study_preferences
    USING (auth.jwt() ->> 'role' = 'service_role');


-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON public.profiles(created_at);


-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for profiles
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for study_preferences
DROP TRIGGER IF EXISTS update_study_preferences_updated_at ON public.study_preferences;
CREATE TRIGGER update_study_preferences_updated_at
    BEFORE UPDATE ON public.study_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================================

-- Function to create profile when user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, display_name, avatar_url, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(NEW.raw_user_meta_data->>'role', 'student')
    );
    
    INSERT INTO public.study_preferences (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();


-- ============================================================================
-- ADMIN VIEWS (optional)
-- ============================================================================

-- View to easily see users with profiles
CREATE OR REPLACE VIEW public.user_profiles AS
SELECT 
    u.id,
    u.email,
    u.phone,
    u.email_confirmed_at,
    u.phone_confirmed_at,
    u.created_at as user_created_at,
    u.last_sign_in_at,
    p.display_name,
    p.avatar_url,
    p.bio,
    p.role,
    p.created_at as profile_created_at,
    sp.voice,
    sp.theme,
    sp.language
FROM auth.users u
LEFT JOIN public.profiles p ON u.id = p.id
LEFT JOIN public.study_preferences sp ON p.id = sp.user_id;


-- ============================================================================
-- OAUTH SETUP NOTES
-- ============================================================================
-- 
-- To enable OAuth providers (Google, LinkedIn), go to your Supabase dashboard:
-- 1. Navigate to Authentication > Providers
-- 2. Enable Google:
--    - Client ID: from Google Cloud Console
--    - Client Secret: from Google Cloud Console
--    - Authorized redirect URI: https://your-project.supabase.co/auth/v1/callback
-- 3. Enable LinkedIn:
--    - Client ID: from LinkedIn Developer Portal
--    - Client Secret: from LinkedIn Developer Portal
--    - Authorized redirect URI: https://your-project.supabase.co/auth/v1/callback
--
-- Remember to add your app URLs to the Google/LinkedIn OAuth app settings.


-- ============================================================================
-- DOCUMENT OWNERSHIP TABLE
-- Tracks which user owns which document (for voice call authorization)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.document_ownership (
    document_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.document_ownership ENABLE ROW LEVEL SECURITY;

-- Index for fast lookups by user
CREATE INDEX IF NOT EXISTS idx_document_ownership_user_id 
    ON public.document_ownership(user_id);

-- Policy: Users can view their own documents
CREATE POLICY "Users can view own documents"
    ON public.document_ownership FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own document ownership
CREATE POLICY "Users can register own documents"
    ON public.document_ownership FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own document ownership
CREATE POLICY "Users can delete own documents"
    ON public.document_ownership FOR DELETE
    USING (auth.uid() = user_id);

-- Policy: Service role can do anything (for internal API)
CREATE POLICY "Service role full access on document_ownership"
    ON public.document_ownership
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Allow public inserts for service-to-service communication
-- (Protected by service key in the application layer)
ALTER TABLE public.document_ownership DISABLE ROW LEVEL SECURITY;
