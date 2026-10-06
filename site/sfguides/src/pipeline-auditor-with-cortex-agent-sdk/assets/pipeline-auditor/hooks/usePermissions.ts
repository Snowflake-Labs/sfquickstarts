"use client";

import { useState, useEffect, useRef } from "react";

interface Permissions {
  role: string;
  canExecute: boolean;
  loading: boolean;
}

export function usePermissions(database: string, schema: string): Permissions {
  const [state, setState] = useState<Permissions>({ role: "", canExecute: false, loading: false });
  const cacheRef = useRef<Map<string, { role: string; canExecute: boolean }>>(new Map());

  useEffect(() => {
    if (!database) {
      setState({ role: "", canExecute: false, loading: false });
      return;
    }

    const key = `${database}.${schema || "*"}`;
    const cached = cacheRef.current.get(key);
    if (cached) {
      setState({ ...cached, loading: false });
      return;
    }

    setState((prev) => ({ ...prev, loading: true }));

    const params = new URLSearchParams({ database });
    if (schema) params.set("schema", schema);

    fetch(`/api/permissions?${params.toString()}`, {
      credentials: "include",
    })
      .then((r) => r.json())
      .then((data) => {
        const result = { role: data.role || "", canExecute: Boolean(data.canExecute) };
        cacheRef.current.set(key, result);
        setState({ ...result, loading: false });
      })
      .catch(() => {
        setState({ role: "", canExecute: false, loading: false });
      });
  }, [database, schema]);

  return state;
}
