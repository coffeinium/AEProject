import React, { useState } from 'react';
import './likeDislike.css';

export type Rate = 'like' | 'dislike';
export type Variant = 'inline' | 'floating';

export default function LikeDislike({
  onRate,
  variant = 'inline',
}: {
  onRate?: (v: Rate) => void;
  variant?: Variant;
}) {
  const [value, setValue] = useState<Rate | null>(null);
  const click = (v: Rate) => { setValue(v); onRate?.(v); };

  return (
    <div className={`th-rate ${variant === 'floating' ? 'th-rate--floating' : 'th-rate--inline'}`}>
      <button
        type="button"
        className={`th-rate__btn ${value === 'like' ? 'is-active-like' : ''}`}
        onClick={() => click('like')}
        aria-label="Нравится"
        title="Нравится"
      >
        👍
      </button>
      <button
        type="button"
        className={`th-rate__btn ${value === 'dislike' ? 'is-active-dislike' : ''}`}
        onClick={() => click('dislike')}
        aria-label="Не нравится"
        title="Не нравится"
      >
        👎
      </button>
    </div>
  );
}
