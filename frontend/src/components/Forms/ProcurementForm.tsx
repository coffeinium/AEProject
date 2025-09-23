// src/components/Forms/ProcurementForm.tsx
import React, { useMemo, useState } from 'react';
import './forms.css';
import { sendFeedback } from '@/lib/api';

// Блоки данных из бэка для закупки
type ProcurementDataBlock = {
  procurement_name?: string | null;
  procurement_amount?: string | number | null;
  customer_name?: string | null;
  customer_inn?: string | null;
  procurement_date?: string | null;
  deadline_date?: string | null;
  procurement_method?: string | null;
  law_type?: string | null; // 44-ФЗ, 223-ФЗ и т.д.
  category?: string | null;
  description?: string | null;
  requirements?: string | null;
  contact_person?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  delivery_address?: string | null;
  delivery_terms?: string | null;
};

type RespData = {
  type?: string;
  status?: string;
  message?: string;
  procurement_data?: ProcurementDataBlock | null;
  provided_data?: ProcurementDataBlock | null;
  additional_data?: Partial<ProcurementDataBlock> | null;
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
  onSubmit: (values: SubmitProcurement) => void;
};

// Строгий тип сабмита: все поля — строки
export type SubmitProcurement = {
  procurement_name: string;
  procurement_amount: string; // нормализованная строка с 2 знаками
  customer_name: string;
  customer_inn: string;    // только цифры
  procurement_date: string;   // YYYY-MM-DD или ISO
  deadline_date: string;   // YYYY-MM-DD или ISO
  procurement_method: string;
  law_type: string;
  category: string;
  description: string;
  requirements: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  delivery_address: string;
  delivery_terms: string;
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

function normalizePhone(s: string): string {
  const digits = onlyDigits(s);
  if (digits.length === 11 && digits.startsWith('8')) {
    return '+7' + digits.slice(1);
  }
  if (digits.length === 11 && digits.startsWith('7')) {
    return '+' + digits;
  }
  if (digits.length === 10) {
    return '+7' + digits;
  }
  return s; // возвращаем как есть, если не удалось нормализовать
}

function normalizeEmail(s: string): string {
  return s.toLowerCase().trim();
}

// Собираем начальные значения из разных источников
function mergeProcurementSeed(ctx?: Props['ctx']): SubmitProcurement {
  const data = ctx?.data ?? null;
  // entities: приоритет ML → hintEntities (история)
  const entities =
    (ctx?.ml_data?.entities && Object.keys(ctx.ml_data.entities).length > 0)
      ? ctx.ml_data.entities
      : (ctx?.hintEntities ?? {});

  const c1 = nonEmpty<ProcurementDataBlock>(data?.procurement_data ?? {});
  const c2 = {
    ...nonEmpty<ProcurementDataBlock>(data?.provided_data ?? {}),
    ...nonEmpty<Partial<ProcurementDataBlock>>(data?.additional_data ?? {}),
  };

  // маппинг entities на поля закупки
  const eName = entities.procurement_name ?? entities.category ?? entities.contract_name ?? entities.ks_name ?? null;
  const eAmount = entities.amount ?? entities.procurement_amount ?? entities.contract_amount ?? entities.ks_amount ?? null;
  const eCustomer = entities.customer_name ?? entities.company_name ?? null;
  const eInn = entities.customer_inn ?? entities.inn ?? null;
  const eMethod = entities.procurement_method ?? null;
  const eLawType = entities.law_type ?? null;
  const eCategory = entities.category ?? null;
  const eDescription = entities.description ?? null;
  const eRequirements = entities.requirements ?? null;
  const eContactPerson = entities.contact_person ?? null;
  const eContactPhone = entities.contact_phone ?? entities.phone ?? null;
  const eContactEmail = entities.contact_email ?? entities.email ?? null;
  const eDeliveryAddress = entities.delivery_address ?? entities.address ?? null;
  const eDeliveryTerms = entities.delivery_terms ?? null;

  const c3: Partial<ProcurementDataBlock> = nonEmpty<ProcurementDataBlock>({
    procurement_name: eName ?? null,
    procurement_amount: eAmount ?? null,
    customer_name: eCustomer ?? null,
    customer_inn: eInn ?? null,
    procurement_date: null,
    deadline_date: null,
    procurement_method: eMethod ?? null,
    law_type: eLawType ?? null,
    category: eCategory ?? null,
    description: eDescription ?? null,
    requirements: eRequirements ?? null,
    contact_person: eContactPerson ?? null,
    contact_phone: eContactPhone ?? null,
    contact_email: eContactEmail ?? null,
    delivery_address: eDeliveryAddress ?? null,
    delivery_terms: eDeliveryTerms ?? null,
  });

  // приоритет: procurement_data -> provided/additional -> entities
  const merged: Partial<ProcurementDataBlock> = { ...c3, ...c2, ...c1 };

  const name = String(merged.procurement_name ?? '');
  const amount = parseAmountLike(merged.procurement_amount);
  const cust = String(merged.customer_name ?? '');
  const inn = onlyDigits(String(merged.customer_inn ?? ''));
  const procurementDate = isoToYMD(merged.procurement_date as string | null);
  const deadlineDate = isoToYMD(merged.deadline_date as string | null);
  const method = String(merged.procurement_method ?? '');
  const lawType = String(merged.law_type ?? '');
  const category = String(merged.category ?? '');
  const description = String(merged.description ?? '');
  const requirements = String(merged.requirements ?? '');
  const contactPerson = String(merged.contact_person ?? '');
  const contactPhone = String(merged.contact_phone ?? '');
  const contactEmail = String(merged.contact_email ?? '');
  const deliveryAddress = String(merged.delivery_address ?? '');
  const deliveryTerms = String(merged.delivery_terms ?? '');

  return {
    procurement_name: name,
    procurement_amount: amount,
    customer_name: cust,
    customer_inn: inn,
    procurement_date: procurementDate,
    deadline_date: deadlineDate,
    procurement_method: method,
    law_type: lawType,
    category: category,
    description: description,
    requirements: requirements,
    contact_person: contactPerson,
    contact_phone: contactPhone,
    contact_email: contactEmail,
    delivery_address: deliveryAddress,
    delivery_terms: deliveryTerms,
  };
}

export default function ProcurementForm({ ctx, onSubmit }: Props) {
  const initial = ctx?.data ?? null;

  // preset всегда строки
  const preset = useMemo(() => mergeProcurementSeed(ctx), [ctx]);

  // Строгий string-стейт для формы
  const [form, setForm] = useState<SubmitProcurement>(preset);
  const [sending, setSending] = useState<'up'|'down'|null>(null);

  const requiredHint = useMemo(
    () => Array.isArray(initial?.missing_fields) ? initial!.missing_fields! : [],
    [initial]
  );
  const suggestions = useMemo(() => initial?.suggestions ?? [], [initial]);
  const nextSteps = useMemo(() => initial?.next_steps ?? [], [initial]);

  const set = (k: keyof SubmitProcurement, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const canSubmit =
    form.procurement_name.trim().length > 0 &&
    form.procurement_amount.trim().length > 0 &&
    form.customer_name.trim().length > 0 &&
    form.customer_inn.trim().length > 0;

  const handleThumb = async (thumb: 'up'|'down') => {
    try {
      setSending(thumb);
      await sendFeedback({
        target: 'procurement',
        response_type: ctx?.responseType ?? initial?.type ?? initial?.status ?? 'unknown',
        thumb,
        payload: {
          procurement_data: initial?.procurement_data ?? null,
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
    'Предварительный отбор',
    'Двухэтапный конкурс',
    'Конкурс с ограниченным участием',
    'Другое'
  ];

  const lawTypes = [
    '44-ФЗ',
    '223-ФЗ',
    'Коммерческие закупки',
    'Другое'
  ];

  const categories = [
    'Товары',
    'Работы',
    'Услуги',
    'Смешанная закупка'
  ];

  const deliveryTermsOptions = [
    'Самовывоз',
    'Доставка до склада заказчика',
    'Доставка до конечного потребителя',
    'По согласованию',
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
            procurement_name: form.procurement_name,
            procurement_amount: parseAmountLike(form.procurement_amount), // гарантируем формат
            customer_name: form.customer_name,
            customer_inn: onlyDigits(form.customer_inn).slice(0, 12),
            procurement_date: form.procurement_date || new Date().toISOString(),
            deadline_date: form.deadline_date,
            procurement_method: form.procurement_method,
            law_type: form.law_type,
            category: form.category,
            description: form.description,
            requirements: form.requirements,
            contact_person: form.contact_person,
            contact_phone: normalizePhone(form.contact_phone),
            contact_email: normalizeEmail(form.contact_email),
            delivery_address: form.delivery_address,
            delivery_terms: form.delivery_terms,
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
          <div className="ae-field ae-field--wide">
            <label className="ae-label">Название закупки *</label>
            <input
              className={`ae-input ${requiredHint.includes('procurement_name') ? 'is-warn' : ''}`}
              value={form.procurement_name}
              onChange={(e) => set('procurement_name', e.target.value)}
              placeholder="например, поставка канцелярских товаров"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Начальная (максимальная) цена *</label>
            <input
              className={`ae-input ${requiredHint.includes('procurement_amount') ? 'is-warn' : ''}`}
              value={form.procurement_amount}
              onChange={(e) => set('procurement_amount', parseAmountLike(e.target.value))}
              placeholder="100000.00"
              inputMode="decimal"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Категория закупки</label>
            <select
              className="ae-input"
              value={form.category}
              onChange={(e) => set('category', e.target.value)}
            >
              <option value="">Выберите категорию</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
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

          <div className="ae-field">
            <label className="ae-label">Дата размещения</label>
            <input
              className="ae-input"
              type="date"
              value={form.procurement_date}
              onChange={(e) => set('procurement_date', e.target.value)}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Срок подачи заявок</label>
            <input
              className="ae-input"
              type="date"
              value={form.deadline_date}
              onChange={(e) => set('deadline_date', e.target.value)}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Контактное лицо</label>
            <input
              className="ae-input"
              value={form.contact_person}
              onChange={(e) => set('contact_person', e.target.value)}
              placeholder="Иванов Иван Иванович"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Телефон контактного лица</label>
            <input
              className="ae-input"
              value={form.contact_phone}
              onChange={(e) => set('contact_phone', e.target.value)}
              placeholder="+7 (900) 123-45-67"
              type="tel"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Email контактного лица</label>
            <input
              className="ae-input"
              value={form.contact_email}
              onChange={(e) => set('contact_email', e.target.value)}
              placeholder="contact@company.ru"
              type="email"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Условия поставки</label>
            <select
              className="ae-input"
              value={form.delivery_terms}
              onChange={(e) => set('delivery_terms', e.target.value)}
            >
              <option value="">Выберите условия</option>
              {deliveryTermsOptions.map((term) => (
                <option key={term} value={term}>{term}</option>
              ))}
            </select>
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Место поставки</label>
            <input
              className="ae-input"
              value={form.delivery_address}
              onChange={(e) => set('delivery_address', e.target.value)}
              placeholder="г. Москва, ул. Примерная, д. 1"
            />
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Описание закупки</label>
            <textarea
              className="ae-input ae-textarea"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="Краткое описание предмета закупки"
              rows={3}
            />
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Требования к участникам</label>
            <textarea
              className="ae-input ae-textarea"
              value={form.requirements}
              onChange={(e) => set('requirements', e.target.value)}
              placeholder="Квалификационные требования к участникам закупки"
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
          <button type="submit" className="ae-btn" disabled={!canSubmit}>Сохранить закупку</button>
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
