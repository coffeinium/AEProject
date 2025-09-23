// src/components/Forms/KSForm.tsx
import React, { useMemo, useState } from 'react';
import './forms.css';
import { sendFeedback } from '@/lib/api';

// Блоки данных из бэка для КС (котировочной сессии)
type KSDataBlock = {
  ks_name?: string | null;
  ks_amount?: string | number | null;
  customer_name?: string | null;
  customer_inn?: string | null;
  ks_date?: string | null;
  procurement_method?: string | null;
  description?: string | null;
  law_type?: string | null; // 44-ФЗ, 223-ФЗ и т.д.
};

type RespData = {
  type?: string;
  status?: string;
  message?: string;
  ks_data?: KSDataBlock | null;
  provided_data?: KSDataBlock | null;
  additional_data?: Partial<KSDataBlock> | null;
  missing_fields?: string[] | null;
  suggestions?: string[] | null;
  next_steps?: string[] | null;
};

type MLDataLike = {
  intent?: string;
  confidence?: number | null;
  entities?: Record<string, any>;
};

type Props = {
  ctx?: {
    responseType?: string;
    data?: RespData | null;
    ml_data?: MLDataLike | null;
    hintEntities?: Record<string, any> | null; // entities из истории
  } | null;
  onSubmit: (values: SubmitKS) => void;
};

// Строгий тип сабмита: все поля — строки
export type SubmitKS = {
  ks_name: string;
  ks_amount: string; // нормализованная строка с 2 знаками
  customer_name: string;
  customer_inn: string;    // только цифры
  ks_date: string;   // YYYY-MM-DD или ISO
  procurement_method: string;
  description: string;
  law_type: string;
};

// ---------- helpers ----------
const isEmptyStr = (v: any) => typeof v === 'string' && v.trim() === '';
const nonEmpty = <T extends Record<string, any>>(obj: T | null | undefined): Partial<T> => {
  const out: Partial<T> = {};
  if (!obj) return out;
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined) continue;
    if (isEmptyStr(v)) continue;
    (out as any)[k] = v;
  }
  return out;
};

function onlyDigits(s: string) {
  return (s || '').replace(/\D+/g, '');
}

function parseAmountLike(v: any): string {
  if (v === null || v === undefined) return '';
  let s = String(v).trim();
  // убираем все, кроме цифр/разделителей
  s = s.replace(/[^\d.,-]/g, '');
  // один десятичный разделитель — точка
  if (s.includes(',') && !s.includes('.')) s = s.replace(',', '.');
  const parts = s.split('.');
  if (parts.length > 2) {
    const dec = parts.pop();
    s = parts.join('') + '.' + dec;
  }
  const num = Number(s);
  if (!isFinite(num)) return '';
  return num.toFixed(2);
}

function isoToYMD(iso?: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

// Собираем начальные значения из разных источников
function mergeKSSeed(ctx?: Props['ctx']): SubmitKS {
  const data = ctx?.data ?? null;
  // entities: приоритет ML → hintEntities (история)
  const entities =
    (ctx?.ml_data?.entities && Object.keys(ctx.ml_data.entities).length > 0)
      ? ctx.ml_data.entities
      : (ctx?.hintEntities ?? {});

  const c1 = nonEmpty<KSDataBlock>(data?.ks_data ?? {});
  const c2 = {
    ...nonEmpty<KSDataBlock>(data?.provided_data ?? {}),
    ...nonEmpty<Partial<KSDataBlock>>(data?.additional_data ?? {}),
  };

  // маппинг entities на поля КС
  const eName = entities.ks_name ?? entities.category ?? entities.contract_name ?? null;
  const eAmount = entities.amount ?? entities.ks_amount ?? entities.contract_amount ?? null;
  const eCustomer = entities.customer_name ?? entities.company_name ?? null;
  const eInn = entities.customer_inn ?? entities.inn ?? null;
  const eMethod = entities.procurement_method ?? null;
  const eDescription = entities.description ?? null;
  const eLawType = entities.law_type ?? null;

  const c3: Partial<KSDataBlock> = nonEmpty<KSDataBlock>({
    ks_name: eName ?? null,
    ks_amount: eAmount ?? null,
    customer_name: eCustomer ?? null,
    customer_inn: eInn ?? null,
    ks_date: null,
    procurement_method: eMethod ?? null,
    description: eDescription ?? null,
    law_type: eLawType ?? null,
  });

  // приоритет: ks_data -> provided/additional -> entities
  const merged: Partial<KSDataBlock> = { ...c3, ...c2, ...c1 };

  const name = String(merged.ks_name ?? '');
  const amount = parseAmountLike(merged.ks_amount);
  const cust = String(merged.customer_name ?? '');
  const inn = onlyDigits(String(merged.customer_inn ?? ''));
  const date = isoToYMD(merged.ks_date as string | null);
  const method = String(merged.procurement_method ?? '');
  const description = String(merged.description ?? '');
  const lawType = String(merged.law_type ?? '');

  return {
    ks_name: name,
    ks_amount: amount,
    customer_name: cust,
    customer_inn: inn,
    ks_date: date,
    procurement_method: method,
    description: description,
    law_type: lawType,
  };
}

export default function KSForm({ ctx, onSubmit }: Props) {
  const initial = ctx?.data ?? null;

  // preset всегда строки
  const preset = useMemo(() => mergeKSSeed(ctx), [ctx]);

  // Строгий string-стейт для формы
  const [form, setForm] = useState<SubmitKS>(preset);
  const [sending, setSending] = useState<'up'|'down'|null>(null);

  const requiredHint = useMemo(
    () => Array.isArray(initial?.missing_fields) ? initial!.missing_fields! : [],
    [initial]
  );
  const suggestions = useMemo(() => initial?.suggestions ?? [], [initial]);
  const nextSteps = useMemo(() => initial?.next_steps ?? [], [initial]);

  const set = (k: keyof SubmitKS, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const canSubmit =
    form.ks_name.trim().length > 0 &&
    form.ks_amount.trim().length > 0 &&
    form.customer_name.trim().length > 0 &&
    form.customer_inn.trim().length > 0;

  const handleThumb = async (thumb: 'up'|'down') => {
    try {
      setSending(thumb);
      await sendFeedback({
        target: 'ks',
        response_type: ctx?.responseType ?? initial?.type ?? initial?.status ?? 'unknown',
        thumb,
        payload: {
          ks_data: initial?.ks_data ?? null,
          provided_data: initial?.provided_data ?? null,
          additional_data: initial?.additional_data ?? null,
          ml_entities: ctx?.ml_data?.entities ?? null,
          hint_entities: ctx?.hintEntities ?? null,
        },
      });
    } finally {
      setSending(null);
    }
  };

  // Опции для выпадающих списков
  const procurementMethods = [
    'Открытый конкурс',
    'Закрытый конкурс', 
    'Электронный аукцион',
    'Запрос котировок',
    'Запрос предложений',
    'Единственный поставщик',
    'Малые закупки',
    'Другое'
  ];

  const lawTypes = [
    '44-ФЗ',
    '223-ФЗ',
    'Коммерческие закупки',
    'Другое'
  ];

  return (
    <>
      <form
        className="ae-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!canSubmit) return;
          onSubmit({
            ks_name: form.ks_name,
            ks_amount: parseAmountLike(form.ks_amount), // гарантируем формат
            customer_name: form.customer_name,
            customer_inn: onlyDigits(form.customer_inn).slice(0, 12),
            ks_date: form.ks_date || new Date().toISOString(),
            procurement_method: form.procurement_method,
            description: form.description,
            law_type: form.law_type,
          });
        }}
      >
        {(initial?.status || initial?.message || ctx?.responseType) && (
          <div className="ae-form__status">
            <div className="ae-form__status-line">
              {(initial?.status ?? ctx?.responseType) && (
                <span className="ae-badge">{initial?.status ?? ctx?.responseType}</span>
              )}
              {initial?.message && <span className="ae-form__status-msg">{initial.message}</span>}
            </div>
          </div>
        )}

        <div className="ae-grid">
          <div className="ae-field">
            <label className="ae-label">Название КС *</label>
            <input
              className={`ae-input ${requiredHint.includes('ks_name') ? 'is-warn' : ''}`}
              value={form.ks_name}
              onChange={(e) => set('ks_name', e.target.value)}
              placeholder="например, закупка канцтоваров"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Сумма *</label>
            <input
              className={`ae-input ${requiredHint.includes('ks_amount') ? 'is-warn' : ''}`}
              value={form.ks_amount}
              onChange={(e) => set('ks_amount', parseAmountLike(e.target.value))}
              placeholder="50000.00"
              inputMode="decimal"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Заказчик *</label>
            <input
              className={`ae-input ${requiredHint.includes('customer_name') ? 'is-warn' : ''}`}
              value={form.customer_name}
              onChange={(e) => set('customer_name', e.target.value)}
              placeholder="ООО Ромашка"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">ИНН заказчика *</label>
            <input
              className={`ae-input ${requiredHint.includes('customer_inn') ? 'is-warn' : ''}`}
              value={form.customer_inn}
              onChange={(e) => set('customer_inn', onlyDigits(e.target.value))}
              placeholder="10 или 12 цифр"
              inputMode="numeric"
              maxLength={12}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Дата КС</label>
            <input
              className="ae-input"
              type="date"
              value={form.ks_date}
              onChange={(e) => set('ks_date', e.target.value)}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Способ закупки</label>
            <select
              className="ae-input"
              value={form.procurement_method}
              onChange={(e) => set('procurement_method', e.target.value)}
            >
              <option value="">Выберите способ</option>
              {procurementMethods.map((method) => (
                <option key={method} value={method}>{method}</option>
              ))}
            </select>
          </div>

          <div className="ae-field">
            <label className="ae-label">Тип закона</label>
            <select
              className="ae-input"
              value={form.law_type}
              onChange={(e) => set('law_type', e.target.value)}
            >
              <option value="">Выберите тип</option>
              {lawTypes.map((law) => (
                <option key={law} value={law}>{law}</option>
              ))}
            </select>
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Описание</label>
            <textarea
              className="ae-input ae-textarea"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="Дополнительная информация о котировочной сессии"
              rows={3}
            />
          </div>
        </div>

        {Array.isArray(suggestions) && suggestions.length > 0 && (
          <div className="ae-hint">
            <div className="ae-hint__title">Подсказки</div>
            <ul className="ae-hint__list">{suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
        )}

        {Array.isArray(nextSteps) && nextSteps.length > 0 && (
          <div className="ae-hint">
            <div className="ae-hint__title">Следующие шаги</div>
            <ul className="ae-hint__list">{nextSteps.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
        )}

        <div className="ae-actions">
          <button type="submit" className="ae-btn" disabled={!canSubmit}>Сохранить КС</button>
        </div>
      </form>

      {/* Лайк/Дизлайк — footer модалки */}
      <div className="modal__footer">
        <button
          className="modal__btn modal__btn--like"
          onClick={() => handleThumb('up')}
          disabled={sending !== null}
          title="Нравится (лайк)"
        >
          👍 {sending === 'up' ? '...' : ''}
        </button>
        <button
          className="modal__btn modal__btn--dislike"
          onClick={() => handleThumb('down')}
          disabled={sending !== null}
          title="Не нравится (дизлайк)"
        >
          👎 {sending === 'down' ? '...' : ''}
        </button>
      </div>
    </>
  );
}