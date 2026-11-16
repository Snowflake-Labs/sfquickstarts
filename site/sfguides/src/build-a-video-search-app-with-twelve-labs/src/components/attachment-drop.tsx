'use client';

import { uploadAttachment } from '@/lib/use-agent';
import { cn } from '@/lib/utils';
import { FileVideo, ImageIcon, Loader2, Paperclip, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export interface Attachment {
  path: string;
  kind: 'image' | 'video';
  name: string;
  previewUrl: string;
}

/** Drag/drop or pick an image or video; uploads to SEARCH_UPLOADS and reports the staged path. */
export function AttachmentDrop({
  value,
  onChange,
  accept = 'image/*,video/*',
  label = 'Drop an image or video clip',
  compact = false,
}: {
  value: Attachment | null;
  onChange: (a: Attachment | null) => void;
  accept?: string;
  label?: string;
  compact?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);

  useEffect(() => () => {
    if (value) URL.revokeObjectURL(value.previewUrl);
  }, [value]);

  async function handle(file: File | undefined) {
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      const res = await uploadAttachment(file);
      onChange({ path: res.path, kind: res.kind, name: file.name, previewUrl: URL.createObjectURL(file) });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  }

  if (value) {
    return (
      <div className="flex min-w-0 items-center gap-3 rounded-xl border border-[color:var(--accent-tab)]/40 bg-[color:var(--accent-tab)]/5 p-2 pr-3">
        <div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-black">
          {value.kind === 'image' ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={value.previewUrl} alt="" className="h-full w-full object-cover" />
          ) : (
            <video src={value.previewUrl} muted className="h-full w-full object-cover" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{value.name}</p>
          <p className="text-xs text-muted-foreground">
            {value.kind === 'image' ? 'Image' : 'Video'} · staged on SEARCH_UPLOADS
          </p>
        </div>
        <button
          type="button"
          onClick={() => onChange(null)}
          className="rounded-full p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Remove attachment"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          handle(e.dataTransfer.files?.[0]);
        }}
        disabled={busy}
        className={cn(
          'flex w-full items-center gap-3 rounded-xl border border-dashed px-4 text-left text-sm text-muted-foreground transition-colors',
          compact ? 'py-2.5' : 'py-4',
          drag ? 'border-[color:var(--accent-tab)] bg-[color:var(--accent-tab)]/5' : 'hover:border-ash hover:bg-muted/40',
        )}
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin text-tab" />
        ) : (
          <Paperclip className="h-4 w-4 text-tab" />
        )}
        <span className="min-w-0 flex-1 truncate">{busy ? 'Uploading to Snowflake…' : label}</span>
        {!compact && (
          <span className="hidden items-center gap-2 sm:flex">
            <ImageIcon className="h-4 w-4" />
            <FileVideo className="h-4 w-4" />
          </span>
        )}
      </button>
      <input
        ref={input}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          handle(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
    </div>
  );
}
