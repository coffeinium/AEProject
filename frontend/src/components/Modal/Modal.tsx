import React, { ReactNode, useEffect } from 'react';
import LikeDislike from '@/components/LikeDislike/LikeDislike';
import './modal.css';

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  width?: number | string;
  height?: number | string;
  /** id формы внутри children; если указан — кнопка "Создать" сабмитит эту форму */
  formId?: string;
  /** колбэк для оценки */
  onRate?: (v: 'like' | 'dislike') => void;
  /** подписи кнопок */
  submitLabel?: string;
  closeLabel?: string;
  /** показать/скрыть футер (по умолчанию true) */
  showFooter?: boolean;
};

export default function Modal({
  open,
  onClose,
  title,
  children,
  width,
  height,
  formId,
  onRate,
  submitLabel = 'Создать',
  closeLabel = 'Закрыть',
  showFooter = true,
}: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  const dialogStyle: React.CSSProperties = {
    width: width ?? 840,
    maxWidth: '90vw',
    height: height ?? '80vh',
    maxHeight: '90vh',
  };

  return (
    <div className="th-modal__backdrop" onMouseDown={onClose}>
      <div
        className="th-modal"
        style={dialogStyle}
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {title && <div className="th-modal__header">{title}</div>}

        <div className="th-modal__body">
          {children}
        </div>

        {showFooter && (
          <div className="th-modal__footer">
            <div className="th-footerbar">
              <LikeDislike variant="inline" onRate={onRate} />
              <div className="th-actions__spacer" />
              <button
                type="button"
                className="th-btn th-btn--ghost"
                onClick={onClose}
              >
                {closeLabel}
              </button>

              {/* если formId указан — сабмитим форму; иначе просто disabled */}
              <button
                type={formId ? 'submit' : 'button'}
                form={formId}
                className="th-btn th-btn--primary"
                disabled={!formId}
              >
                {submitLabel}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
