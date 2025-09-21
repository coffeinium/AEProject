// src/components/Forms/ContractForm.tsx
import React, { useMemo, useState } from 'react';
import './forms.css';

type ContractData = {
  type?: string;
  status?: string;
  message?: string;
  contract_data?: {
    contract_name?: string | null;
    contract_amount?: string | number | null;
    customer_name?: string | null;
    customer_inn?: string | null;
    contract_date?: string | null;
  } | null;
  missing_fields?: string[] | null;
  suggestions?: string[] | null;
  next_steps?: string[] | null;
};

type Props = {
  initial?: ContractData | null;
  onSubmit: (values: Required<NonNullable<ContractData['contract_data']>>) => void;
};

// утилита: берём только непустые значения
function nonEmpty<T extends Record<string, any>>(obj: T | null | undefined): Partial<T> {
  const out: Partial<T> = {};
  if (!obj) return out;
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined) continue;
    if (typeof v === 'string' && v.trim() === '') continue;
    (out as any)[k] = v;
  }
  return out;
}

export default function ContractForm({ initial, onSubmit }: Props) {
  const preset = useMemo(() => {
    const seed = nonEmpty(initial?.contract_data ?? {});
    return {
      contract_name: String(seed.contract_name ?? ''),
      contract_amount: String(seed.contract_amount ?? ''),
      customer_name: String(seed.customer_name ?? ''),
      customer_inn: String(seed.customer_inn ?? ''),
      contract_date: String(seed.contract_date ?? ''),
    };
  }, [initial]);

  const [form, setForm] = useState(preset);

  const requiredHint = useMemo(() => {
    const miss = initial?.missing_fields ?? [];
    return Array.isArray(miss) ? miss : [];
  }, [initial]);

  const suggestions = useMemo(() => initial?.suggestions ?? [], [initial]);
  const nextSteps = useMemo(() => initial?.next_steps ?? [], [initial]);

  const set = (k: keyof typeof form, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const canSubmit =
    (form.contract_name?.trim()?.length ?? 0) > 0 &&
    (form.contract_amount?.trim()?.length ?? 0) > 0 &&
    (form.customer_name?.trim()?.length ?? 0) > 0 &&
    (form.customer_inn?.trim()?.length ?? 0) > 0;

  return (
    <form
      className="ae-form"
      onSubmit={(e) => {
        e.preventDefault();
        if (!canSubmit) return;
        onSubmit({
          contract_name: form.contract_name,
          contract_amount: form.contract_amount,
          customer_name: form.customer_name,
          customer_inn: form.customer_inn,
          contract_date: form.contract_date || new Date().toISOString(),
        });
      }}
    >
      {/* Верхняя плашка статуса из доки */}
      {(initial?.status || initial?.message) && (
        <div className="ae-form__status">
          <div className="ae-form__status-line">
            {initial?.status && <span className="ae-badge">{initial.status}</span>}
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
            onChange={(e) => set('contract_amount', e.target.value)}
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
            onChange={(e) => set('customer_inn', e.target.value)}
            placeholder="10 или 12 цифр"
            inputMode="numeric"
          />
        </div>

        <div className="ae-field">
          <label className="ae-label">Дата контракта</label>
          <input
            className="ae-input"
            value={form.contract_date}
            onChange={(e) => set('contract_date', e.target.value)}
            placeholder="ISO или оставьте пустым"
          />
        </div>
      </div>

      {Array.isArray(suggestions) && suggestions.length > 0 && (
        <div className="ae-hint">
          <div className="ae-hint__title">Подсказки</div>
          <ul className="ae-hint__list">
            {suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      {Array.isArray(nextSteps) && nextSteps.length > 0 && (
        <div className="ae-hint">
          <div className="ae-hint__title">Следующие шаги</div>
          <ul className="ae-hint__list">
            {nextSteps.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      <div className="ae-actions">
        <button type="submit" className="ae-btn" disabled={!canSubmit}>
          Сохранить
        </button>
      </div>
    </form>
  );
}
