// src/components/Modal/Modal.tsx
import React from 'react';
import './modal.css';

type Props = {
  open: boolean;
  title?: string;
  onClose: () => void;
  children: React.ReactNode;
};

export default function Modal({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="modal__backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal__card" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h3 className="modal__title">{title ?? 'Модальное окно'}</h3>
          <button className="modal__close" onClick={onClose} aria-label="Закрыть">
            ✕
          </button>
        </div>
        <div className="modal__body">{children}</div>
      </div>
    </div>
  );
}
