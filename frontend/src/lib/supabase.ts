/**
 * Supabase client for authentication and user management.
 *
 * Configured via VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.
 * When these are not set, auth features are disabled (local/offline mode).
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";

/** Whether Supabase auth is configured and available */
export const isAuthEnabled = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

/** Supabase client (null if auth is not configured) */
export const supabase: SupabaseClient | null = isAuthEnabled
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

/**
 * Get the current session's access token for API calls.
 * Returns null if not authenticated or auth is not configured.
 */
export async function getAccessToken(): Promise<string | null> {
  if (!supabase) return null;
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}
