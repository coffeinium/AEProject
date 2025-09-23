// src/components/Forms/CompanyForm.tsx
import React, { useMemo, useState } from 'react';
import './forms.css';
import { sendFeedback } from '@/lib/api';

// Блоки данных из бэка для компании
type CompanyDataBlock = {
  name?: string | null;
  inn?: string | null;
  kpp?: string | null;
  ogrn?: string | null;
  legal_address?: string | null;
  postal_address?: string | null;
  phone?: string | null;
  email?: string | null;
  director?: string | null;
  website?: string | null;
  activity_type?: string | null;
  description?: string | null;
};

type RespData = {
  type?: string;
  status?: string;
  message?: string;
  company_data?: CompanyDataBlock | null;
  provided_data?: CompanyDataBlock | null;
  additional_data?: Partial<CompanyDataBlock> | null;
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
  onSubmit: (values: SubmitCompany) => void;
};

// Строгий тип сабмита: все поля — строки
export type SubmitCompany = {
  name: string;
  inn: string;    // только цифры
  kpp: string;    // только цифры
  ogrn: string;   // только цифры
  legal_address: string;
  postal_address: string;
  phone: string;
  email: string;
  director: string;
  website: string;
  activity_type: string;
  description: string;
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
function mergeCompanySeed(ctx?: Props['ctx']): SubmitCompany {
  const data = ctx?.data ?? null;
  // entities: приоритет ML → hintEntities (история)
  const entities =
    (ctx?.ml_data?.entities && Object.keys(ctx.ml_data.entities).length > 0)
      ? ctx.ml_data.entities
      : (ctx?.hintEntities ?? {});

  const c1 = nonEmpty<CompanyDataBlock>(data?.company_data ?? {});
  const c2 = {
    ...nonEmpty<CompanyDataBlock>(data?.provided_data ?? {}),
    ...nonEmpty<Partial<CompanyDataBlock>>(data?.additional_data ?? {}),
  };

  // маппинг entities на поля компании
  const eName = entities.name ?? entities.company_name ?? entities.customer_name ?? null;
  const eInn = entities.inn ?? entities.customer_inn ?? null;
  const eKpp = entities.kpp ?? null;
  const eOgrn = entities.ogrn ?? null;
  const eLegalAddress = entities.legal_address ?? entities.address ?? null;
  const ePostalAddress = entities.postal_address ?? null;
  const ePhone = entities.phone ?? null;
  const eEmail = entities.email ?? null;
  const eDirector = entities.director ?? null;
  const eWebsite = entities.website ?? null;
  const eActivityType = entities.activity_type ?? null;
  const eDescription = entities.description ?? null;

  const c3: Partial<CompanyDataBlock> = nonEmpty<CompanyDataBlock>({
    name: eName ?? null,
    inn: eInn ?? null,
    kpp: eKpp ?? null,
    ogrn: eOgrn ?? null,
    legal_address: eLegalAddress ?? null,
    postal_address: ePostalAddress ?? null,
    phone: ePhone ?? null,
    email: eEmail ?? null,
    director: eDirector ?? null,
    website: eWebsite ?? null,
    activity_type: eActivityType ?? null,
    description: eDescription ?? null,
  });

  // приоритет: company_data -> provided/additional -> entities
  const merged: Partial<CompanyDataBlock> = { ...c3, ...c2, ...c1 };

  const name = String(merged.name ?? '');
  const inn = onlyDigits(String(merged.inn ?? ''));
  const kpp = onlyDigits(String(merged.kpp ?? ''));
  const ogrn = onlyDigits(String(merged.ogrn ?? ''));
  const legalAddress = String(merged.legal_address ?? '');
  const postalAddress = String(merged.postal_address ?? '');
  const phone = String(merged.phone ?? '');
  const email = String(merged.email ?? '');
  const director = String(merged.director ?? '');
  const website = String(merged.website ?? '');
  const activityType = String(merged.activity_type ?? '');
  const description = String(merged.description ?? '');

  return {
    name,
    inn,
    kpp,
    ogrn,
    legal_address: legalAddress,
    postal_address: postalAddress,
    phone,
    email,
    director,
    website,
    activity_type: activityType,
    description,
  };
}

export default function CompanyForm({ ctx, onSubmit }: Props) {
  const initial = ctx?.data ?? null;

  // preset всегда строки
  const preset = useMemo(() => mergeCompanySeed(ctx), [ctx]);

  // Строгий string-стейт для формы
  const [form, setForm] = useState<SubmitCompany>(preset);
  const [sending, setSending] = useState<'up'|'down'|null>(null);

  const requiredHint = useMemo(
    () => Array.isArray(initial?.missing_fields) ? initial!.missing_fields! : [],
    [initial]
  );
  const suggestions = useMemo(() => initial?.suggestions ?? [], [initial]);
  const nextSteps = useMemo(() => initial?.next_steps ?? [], [initial]);

  const set = (k: keyof SubmitCompany, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const canSubmit =
    form.name.trim().length > 0 &&
    form.inn.trim().length >= 10; // минимум для ИНН

  const handleThumb = async (thumb: 'up'|'down') => {
    try {
      setSending(thumb);
      await sendFeedback({
        target: 'company',
        response_type: ctx?.responseType ?? initial?.type ?? initial?.status ?? 'unknown',
        thumb,
        payload: {
          company_data: initial?.company_data ?? null,
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
  const activityTypes = [
    'Торговля',
    'Производство',
    'Услуги',
    'IT и разработка',
    'Строительство',
    'Транспорт и логистика',
    'Образование',
    'Здравоохранение',
    'Финансы и страхование',
    'Сельское хозяйство',
    'Энергетика',
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
            name: form.name.trim(),
            inn: onlyDigits(form.inn).slice(0, 12),
            kpp: onlyDigits(form.kpp).slice(0, 9),
            ogrn: onlyDigits(form.ogrn).slice(0, 15),
            legal_address: form.legal_address.trim(),
            postal_address: form.postal_address.trim(),
            phone: normalizePhone(form.phone),
            email: normalizeEmail(form.email),
            director: form.director.trim(),
            website: form.website.trim(),
            activity_type: form.activity_type,
            description: form.description.trim(),
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
            <label className="ae-label">Название компании *</label>
            <input
              className={`ae-input ${requiredHint.includes('name') ? 'is-warn' : ''}`}
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder="например, ООО 'Ромашка'"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">ИНН *</label>
            <input
              className={`ae-input ${requiredHint.includes('inn') ? 'is-warn' : ''}`}
              value={form.inn}
              onChange={(e) => set('inn', onlyDigits(e.target.value))}
              placeholder="10 или 12 цифр"
              inputMode="numeric"
              maxLength={12}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">КПП</label>
            <input
              className="ae-input"
              value={form.kpp}
              onChange={(e) => set('kpp', onlyDigits(e.target.value))}
              placeholder="9 цифр"
              inputMode="numeric"
              maxLength={9}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">ОГРН</label>
            <input
              className="ae-input"
              value={form.ogrn}
              onChange={(e) => set('ogrn', onlyDigits(e.target.value))}
              placeholder="13 или 15 цифр"
              inputMode="numeric"
              maxLength={15}
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Тип деятельности</label>
            <select
              className="ae-input"
              value={form.activity_type}
              onChange={(e) => set('activity_type', e.target.value)}
            >
              <option value="">Выберите тип</option>
              {activityTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Юридический адрес</label>
            <input
              className="ae-input"
              value={form.legal_address}
              onChange={(e) => set('legal_address', e.target.value)}
              placeholder="г. Москва, ул. Примерная, д. 1"
            />
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Почтовый адрес</label>
            <input
              className="ae-input"
              value={form.postal_address}
              onChange={(e) => set('postal_address', e.target.value)}
              placeholder="г. Москва, ул. Примерная, д. 1"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Телефон</label>
            <input
              className="ae-input"
              value={form.phone}
              onChange={(e) => set('phone', e.target.value)}
              placeholder="+7 (900) 123-45-67"
              type="tel"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Email</label>
            <input
              className="ae-input"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              placeholder="info@company.ru"
              type="email"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Руководитель</label>
            <input
              className="ae-input"
              value={form.director}
              onChange={(e) => set('director', e.target.value)}
              placeholder="Иванов Иван Иванович"
            />
          </div>

          <div className="ae-field">
            <label className="ae-label">Веб-сайт</label>
            <input
              className="ae-input"
              value={form.website}
              onChange={(e) => set('website', e.target.value)}
              placeholder="https://company.ru"
              type="url"
            />
          </div>

          <div className="ae-field ae-field--wide">
            <label className="ae-label">Описание</label>
            <textarea
              className="ae-input ae-textarea"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="Краткое описание деятельности компании"
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
          <button type="submit" className="ae-btn" disabled={!canSubmit}>Сохранить компанию</button>
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