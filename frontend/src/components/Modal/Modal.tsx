import React, { ReactNode, useEffect } from 'react';
import './modal.css';

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: number | string;
};

export default function Modal({ open, onClose, title, children, footer, width }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="th-modal__backdrop" onMouseDown={onClose}>
      <div
        className="th-modal"
        style={{ maxWidth: '90vw', width: width ?? 720 }}
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {title && <div className="th-modal__header">{title}</div>}
        <div className="th-modal__body">{children}</div>
        {footer && <div className="th-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}
