import { create } from "zustand";
import { supabase, isAuthEnabled } from "@/lib/supabase";
import type { User, Session } from "@supabase/supabase-js";

interface AuthState {
  user: User | null;
  session: Session | null;
  tier: "free" | "pro" | "premium";
  isLoading: boolean;
  isAuthEnabled: boolean;

  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  signInWithProvider: (provider: "google" | "apple") => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  tier: "free",
  isLoading: true,
  isAuthEnabled,

  initialize: async () => {
    if (!supabase) {
      set({ isLoading: false });
      return;
    }

    // Get current session
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.user) {
      const tier =
        (session.user.app_metadata?.tier as "free" | "pro" | "premium") ??
        "free";
      set({ user: session.user, session, tier, isLoading: false });
    } else {
      set({ isLoading: false });
    }

    // Listen for auth changes
    supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        const tier =
          (session.user.app_metadata?.tier as "free" | "pro" | "premium") ??
          "free";
        set({ user: session.user, session, tier });
      } else {
        set({ user: null, session: null, tier: "free" });
      }
    });
  },

  signIn: async (email: string, password: string) => {
    if (!supabase) throw new Error("Auth not configured");
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
  },

  signUp: async (email: string, password: string) => {
    if (!supabase) throw new Error("Auth not configured");
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
  },

  signOut: async () => {
    if (!supabase) return;
    await supabase.auth.signOut();
    set({ user: null, session: null, tier: "free" });
  },

  signInWithProvider: async (provider: "google" | "apple") => {
    if (!supabase) throw new Error("Auth not configured");
    const { error } = await supabase.auth.signInWithOAuth({ provider });
    if (error) throw error;
  },
}));
