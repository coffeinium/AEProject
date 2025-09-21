// src/components/Forms/ContractForm.tsx
import React, { useMemo, useState } from 'react';
import './forms.css';
import { sendFeedback } from '@/lib/api';

// Блоки данных из бэка (оставляем типы под доку)
type ContractDataBlock = {
  contract_name?: string | null;
  contract_amount?: string | number | null;
  customer_name?: string | null;
  customer_inn?: string | null;
  contract_date?: string | null;
};

type RespData = {
  type?: string;
  status?: string;
  message?: string;
  contract_data?: ContractDataBlock | null;
  provided_data?: ContractDataBlock | null;
  additional_data?: Partial<ContractDataBlock> | null;
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
  onSubmit: (values: SubmitContract) => void;
};

// Строгий тип сабмита: все поля — строки
export type SubmitContract = {
  contract_name: string;
  contract_amount: string; // нормализованная строка с 2 знаками
  customer_name: string;
  customer_inn: string;    // только цифры
  contract_date: string;   // YYYY-MM-DD или ISO
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
function mergeContractSeed(ctx?: Props['ctx']): SubmitContract {
  const data = ctx?.data ?? null;
  // entities: приоритет ML → hintEntities (история)
  const entities =
    (ctx?.ml_data?.entities && Object.keys(ctx.ml_data.entities).length > 0)
      ? ctx.ml_data.entities
      : (ctx?.hintEntities ?? {});

  const c1 = nonEmpty<ContractDataBlock>(data?.contract_data ?? {});
  const c2 = {
    ...nonEmpty<ContractDataBlock>(data?.provided_data ?? {}),
    ...nonEmpty<Partial<ContractDataBlock>>(data?.additional_data ?? {}),
  };

  // company_name → customer_name; amount → contract_amount; category как запасное имя
  const eName = entities.contract_name ?? entities.category ?? null;
  const eAmount = entities.amount ?? entities.contract_amount ?? null;
  const eCustomer = entities.customer_name ?? entities.company_name ?? null;
  const eInn = entities.customer_inn ?? entities.inn ?? null;

  const c3: Partial<ContractDataBlock> = nonEmpty<ContractDataBlock>({
    contract_name: eName ?? null,
    contract_amount: eAmount ?? null,
    customer_name: eCustomer ?? null,
    customer_inn: eInn ?? null,
    contract_date: null,
  });

  // приоритет: contract_data -> provided/additional -> entities
  const merged: Partial<ContractDataBlock> = { ...c3, ...c2, ...c1 };

  const name = String(merged.contract_name ?? '');
  const amount = parseAmountLike(merged.contract_amount);
  const cust = String(merged.customer_name ?? '');
  const inn = onlyDigits(String(merged.customer_inn ?? ''));
  const date = isoToYMD(merged.contract_date as string | null);

  return {
    contract_name: name,
    contract_amount: amount,
    customer_name: cust,
    customer_inn: inn,
    contract_date: date,
  };
}

export default function ContractForm({ ctx, onSubmit }: Props) {
  const initial = ctx?.data ?? null;

  // preset всегда строки
  const preset = useMemo(() => mergeContractSeed(ctx), [ctx]);

  // Строгий string-стейт для формы
  const [form, setForm] = useState<SubmitContract>(preset);
  const [sending, setSending] = useState<'up'|'down'|null>(null);

  const requiredHint = useMemo(
    () => Array.isArray(initial?.missing_fields) ? initial!.missing_fields! : [],
    [initial]
  );
  const suggestions = useMemo(() => initial?.suggestions ?? [], [initial]);
  const nextSteps = useMemo(() => initial?.next_steps ?? [], [initial]);

  const set = (k: keyof SubmitContract, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const canSubmit =
    form.contract_name.trim().length > 0 &&
    form.contract_amount.trim().length > 0 &&
    form.customer_name.trim().length > 0 &&
    form.customer_inn.trim().length > 0;

  const handleThumb = async (thumb: 'up'|'down') => {
    try {
      setSending(thumb);
      await sendFeedback({
        target: 'contract',
        response_type: ctx?.responseType ?? initial?.type ?? initial?.status ?? 'unknown',
        thumb,
        payload: {
          contract_data: initial?.contract_data ?? null,
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

  return (
    <>
      <form
        className="ae-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!canSubmit) return;
          onSubmit({
            contract_name: form.contract_name,
            contract_amount: parseAmountLike(form.contract_amount), // гарантируем формат
            customer_name: form.customer_name,
            customer_inn: onlyDigits(form.customer_inn).slice(0, 12),
            contract_date: form.contract_date || new Date().toISOString(),
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
            <label className="ae-label">Название контракта *</label>
            <input
              className={`ae-input ${requiredHint.includes('contract_name') ? 'is-warn' : ''}`}
              value={form.contract_name}
              onChange={(e) => set('contract_name', e.target.value)}
              placeholder="например, поставка канцтоваров"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Сумма *</label>
            <input
              className={`ae-input ${requiredHint.includes('contract_amount') ? 'is-warn' : ''}`}
              value={form.contract_amount}
              onChange={(e) => set('contract_amount', parseAmountLike(e.target.value))}
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
            <label className="ae-label">Дата контракта</label>
            <input
              className="ae-input"
              value={form.contract_date}
              onChange={(e) => set('contract_date', e.target.value)}
              placeholder="YYYY-MM-DD"
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
          <button type="submit" className="ae-btn" disabled={!canSubmit}>Сохранить</button>
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
