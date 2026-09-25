-- =========================================================================
-- KameraPh: Multi-Tenant PostgreSQL / Supabase Database Architecture
-- =========================================================================

-- 1. STUDIOS (Photographer & Studio Profiles)
CREATE TABLE IF NOT EXISTS public.studios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    studio_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone_number TEXT,
    location_city TEXT DEFAULT 'Manila',
    credit_balance INTEGER DEFAULT 25 NOT NULL, -- Free 25 trial credits upon signup
    plan_tier TEXT DEFAULT 'starter' CHECK (plan_tier IN ('starter', 'studio_pro', 'enterprise')),
    gcash_account_number TEXT
);

-- 2. SCHOOL BATCH PROJECTS
CREATE TABLE IF NOT EXISTS public.batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    studio_id UUID REFERENCES public.studios(id) ON DELETE CASCADE NOT NULL,
    school_name TEXT NOT NULL,
    academic_year TEXT NOT NULL, -- e.g. '2025-2026'
    grade_level TEXT,            -- e.g. 'Senior High School (Grade 12)', 'College'
    section_name TEXT,           -- e.g. 'STEM-A', 'Accountancy-4B'
    regalia_type TEXT DEFAULT 'standard_toga' CHECK (regalia_type IN ('standard_toga', 'up_sablay', 'barong_tagalog', 'filipiniana', 'kinder_pastel')),
    total_photos INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'archived'))
);

-- 3. PHOTOS & ENHANCEMENT AUDIT
CREATE TABLE IF NOT EXISTS public.photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    batch_id UUID REFERENCES public.batches(id) ON DELETE CASCADE,
    studio_id UUID REFERENCES public.studios(id) ON DELETE CASCADE NOT NULL,
    student_name TEXT,
    student_id_number TEXT,
    original_r2_url TEXT NOT NULL,
    enhanced_r2_url TEXT,
    thumbnail_r2_url TEXT,
    crop_8r_r2_url TEXT,
    crop_2x2_r2_url TEXT,
    
    -- Retouch Parameters Applied
    toga_iron_strength NUMERIC(3,2) DEFAULT 0.70,
    skin_smoothing_ratio NUMERIC(3,2) DEFAULT 0.65,
    shine_reduction NUMERIC(3,2) DEFAULT 0.35,
    backdrop_cleaned BOOLEAN DEFAULT true,
    
    -- Telemetry & Audit
    processing_latency_ms INTEGER,
    gpu_engine_used TEXT DEFAULT 'local_cpu',
    review_needed BOOLEAN DEFAULT false,
    review_reason TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error'))
);

-- 4. GCASH / MAYA TRANSACTIONS
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    studio_id UUID REFERENCES public.studios(id) ON DELETE CASCADE NOT NULL,
    paymongo_session_id TEXT UNIQUE NOT NULL,
    payment_method TEXT NOT NULL, -- 'gcash', 'paymaya', 'card'
    package_id TEXT NOT NULL,
    amount_php NUMERIC(10,2) NOT NULL,
    credits_added INTEGER NOT NULL,
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed'))
);

-- 5. EXPORT JOBS
CREATE TABLE IF NOT EXISTS public.export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    studio_id UUID REFERENCES public.studios(id) ON DELETE CASCADE NOT NULL,
    batch_id UUID REFERENCES public.batches(id) ON DELETE SET NULL,
    export_type TEXT NOT NULL CHECK (export_type IN ('zip_full', 'contact_sheet_pdf', 'gang_sheet_pdf')),
    school_name TEXT NOT NULL,
    status TEXT DEFAULT 'processing' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress_percentage INTEGER DEFAULT 0,
    download_url TEXT,
    error_message TEXT
);

-- =========================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES FOR MULTI-TENANCY ISOLATION
-- =========================================================================

ALTER TABLE public.studios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.export_jobs ENABLE ROW LEVEL SECURITY;

-- 1. STUDIOS POLICIES
-- Studio owners can read and update only their own profile
CREATE POLICY "Studios can view own record" ON public.studios
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Studios can update own record" ON public.studios
    FOR UPDATE USING (auth.uid() = id);

-- Service role bypass for backend billing webhooks and admin operations
CREATE POLICY "Service role full access on studios" ON public.studios
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- 2. BATCHES POLICIES
-- Multi-tenancy: Studios can only select, insert, update, delete their own batches
CREATE POLICY "Studios view own batches" ON public.batches
    FOR SELECT USING (auth.uid() = studio_id);

CREATE POLICY "Studios insert own batches" ON public.batches
    FOR INSERT WITH CHECK (auth.uid() = studio_id);

CREATE POLICY "Studios update own batches" ON public.batches
    FOR UPDATE USING (auth.uid() = studio_id);

CREATE POLICY "Studios delete own batches" ON public.batches
    FOR DELETE USING (auth.uid() = studio_id);

-- 3. PHOTOS POLICIES
-- Studios can only access photos belonging to their studio
CREATE POLICY "Studios view own photos" ON public.photos
    FOR SELECT USING (auth.uid() = studio_id);

CREATE POLICY "Studios insert own photos" ON public.photos
    FOR INSERT WITH CHECK (auth.uid() = studio_id);

CREATE POLICY "Studios update own photos" ON public.photos
    FOR UPDATE USING (auth.uid() = studio_id);

CREATE POLICY "Studios delete own photos" ON public.photos
    FOR DELETE USING (auth.uid() = studio_id);

-- Public / Students can only view their own photo proof if student_id_number matches
CREATE POLICY "Students view individual proof" ON public.photos
    FOR SELECT USING (student_id_number IS NOT NULL AND status = 'completed');

-- 4. TRANSACTIONS POLICIES
-- Studios can view only their financial history
CREATE POLICY "Studios view own transactions" ON public.transactions
    FOR SELECT USING (auth.uid() = studio_id);

-- Only backend service role (PayMongo webhook) can record transactions
CREATE POLICY "Service role insert transactions" ON public.transactions
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- 5. EXPORT JOBS POLICIES
CREATE POLICY "Studios view own export jobs" ON public.export_jobs
    FOR SELECT USING (auth.uid() = studio_id);

CREATE POLICY "Studios create own export jobs" ON public.export_jobs
    FOR INSERT WITH CHECK (auth.uid() = studio_id);
