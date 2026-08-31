"use client";

import { useState, useEffect, useCallback, useRef } from "react";

// ── Generic async data hook ──────────────────────────────────────────────────
export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  lastFetchedAt: Date | null;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  options: {
    initialData?: T;
    autoFetch?: boolean;
    pollingIntervalMs?: number;
    deps?: unknown[];
  } = {}
): UseApiState<T> {
  const {
    initialData = null,
    autoFetch = true,
    pollingIntervalMs,
    deps = [],
  } = options;

  const [data, setData] = useState<T | null>(initialData ?? null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState<string | null>(null);
  const [lastFetchedAt, setLastFetchedAt] = useState<Date | null>(null);
  const mountedRef = useRef(true);

  const fetch = useCallback(async () => {
    if (!mountedRef.current) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) {
        setData(result);
        setLastFetchedAt(new Date());
      }
    } catch (err) {
      if (mountedRef.current) {
        setError((err as Error).message ?? "Unknown error");
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    if (autoFetch) fetch();

    let interval: ReturnType<typeof setInterval> | null = null;
    if (pollingIntervalMs && pollingIntervalMs > 0) {
      interval = setInterval(fetch, pollingIntervalMs);
    }

    return () => {
      mountedRef.current = false;
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetch]);

  return { data, loading, error, refetch: fetch, lastFetchedAt };
}

// ── Mutation hook (POST/PUT/DELETE) ──────────────────────────────────────────
export interface UseMutationState<TArg, TResult> {
  mutate: (arg: TArg) => Promise<TResult | null>;
  loading: boolean;
  error: string | null;
  data: TResult | null;
}

export function useMutation<TArg, TResult>(
  mutator: (arg: TArg) => Promise<TResult>
): UseMutationState<TArg, TResult> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TResult | null>(null);

  const mutate = useCallback(async (arg: TArg): Promise<TResult | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await mutator(arg);
      setData(result);
      return result;
    } catch (err) {
      setError((err as Error).message ?? "Unknown error");
      return null;
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { mutate, loading, error, data };
}

// Note: a generic per-event WebSocket hook used to live here, built on top of
// services/webSocketClient.ts (a second client that connected to a
// nonexistent endpoint and fabricated data on failure). That client has been
// retired — see context/TraffixContext.tsx and hooks/useWebSocket.ts (the
// real, single connection) for the app's live data.
