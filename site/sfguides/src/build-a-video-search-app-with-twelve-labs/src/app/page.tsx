import { Studio } from '@/components/studio';
import { Suspense } from 'react';

export const dynamic = 'force-dynamic';

export default function Page() {
  return (
    <Suspense>
      <Studio />
    </Suspense>
  );
}
