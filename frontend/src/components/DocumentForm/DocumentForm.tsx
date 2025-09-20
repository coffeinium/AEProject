// src/components/DocumentForm/DocumentForm.tsx
import React, { useMemo, useState } from 'react';
import LikeDislike from '@/components/LikeDislike/LikeDislike';
import './documentForm.css';

// единый конверт ответа
export type BackendEnvelope = {
  status: 'success' | 'error';
  response: { type: string; data: any };
  ml_data: { intent: string; confidence: number | null; entities: Record<string, any> };
};

// внешний API компонента
export type DocumentData = {
  title?: string;
  customer?: string;
  price?: string;
  deadline?: string;
  notes?: string;
};

type Props = {
  envelope?: BackendEnvelope | null; // если есть — рисуем конкретную форму по типу
  initial?: DocumentData;            // используется в fallback-форме
  onSubmit: (data: any) => void;
  onCancel: () => void;
};

// ===== УТИЛЫ =====
const isEmpty = (v: any) => v === null || v === undefined || v === '';
const money = (v: any) => (isEmpty(v) ? '' : String(v));
const date = (v: any) => (isEmpty(v) ? '' : String(v).slice(0, 10));
const text = (v: any) => (isEmpty(v) ? '' : String(v));

const entriesOfEntities = (e: Record<string, any>, used: string[]) =>
  Object.entries(e || {}).filter(([k, v]) => !used.includes(k) && !isEmpty(v));

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="th-section">
    <div className="th-section__title">{title}</div>
    <div className="th-section__body">{children}</div>
  </div>
);
const Row: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="th-form__row">{children}</div>
);
const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <label className="th-field">
    <span className="th-field__label">{label}</span>
    {children}
  </label>
);

// ===== ФОРМЫ =====

// company_search / create_company_profile
const CompanyForm: React.FC<Omit<Props, 'initial'>> = ({ envelope, onSubmit, onCancel }) => {
  const e = envelope?.ml_data?.entities || {};
  const [form, setForm] = useState({
    company_name: text(e.company_name ?? e.name),
    company_inn: text(e.company_inn),
    company_ogrn: text(e.company_ogrn),
    comment: '',
  });
  const change =
    (k: keyof typeof form) =>
    (ev: React.ChangeEvent<HTMLInputElement>) =>
      setForm((s) => ({ ...s, [k]: ev.target.value }));

  const usedKeys = ['company_name', 'name', 'company_inn', 'company_ogrn'];
  const rest = entriesOfEntities(e, usedKeys);

  return (
    <form
      className="th-form"
      onSubmit={(ev) => {
        ev.preventDefault();
        onSubmit({ type: 'company', ...form });
      }}
    >
      <Section title="Реквизиты">
        <Row>
          <Field label="Наименование">
            <input
              value={form.company_name}
              onChange={change('company_name')}
              placeholder="ООО «Ромашка»"
            />
          </Field>
          <Field label="ИНН">
            <input
              value={form.company_inn}
              onChange={change('company_inn')}
              placeholder="1234567890"
            />
          </Field>
        </Row>
        <Row>
          <Field label="ОГРН">
            <input
              value={form.company_ogrn}
              onChange={change('company_ogrn')}
              placeholder="1234567890123"
            />
          </Field>
          <Field label="Комментарий">
            <input value={form.comment} onChange={change('comment')} placeholder="Примечание" />
          </Field>
        </Row>
      </Section>

      {rest.length > 0 && (
        <Section title="Дополнительные поля">
          <div className="th-grid-2">
            {rest.map(([k, v]) => (
              <label className="th-field" key={k}>
                <span className="th-field__label">{k}</span>
                <input defaultValue={String(v)} />
              </label>
            ))}
          </div>
        </Section>
      )}

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>
          Закрыть
        </button>
        <button type="submit" className="th-btn th-btn--primary">
          Создать
        </button>
      </div>
    </form>
  );
};

// contract_search / create_contract
const ContractForm: React.FC<Omit<Props, 'initial'>> = ({ envelope, onSubmit, onCancel }) => {
  const e = envelope?.ml_data?.entities || {};
  const [form, setForm] = useState({
    contract_id: text(e.contract_id),
    contract_amount: money(e.contract_amount),
    contract_date: date(e.contract_date),
    law_basis: text(e.law_basis),
    customer_name: text(e.customer_name),
    customer_inn: text(e.customer_inn),
    supplier_name: text(e.supplier_name),
    supplier_inn: text(e.supplier_inn),
    notes: '',
  });
  const change =
    (k: keyof typeof form) =>
    (ev: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((s) => ({ ...s, [k]: ev.target.value }));

  const usedKeys = [
    'contract_id',
    'contract_amount',
    'contract_date',
    'law_basis',
    'customer_name',
    'customer_inn',
    'supplier_name',
    'supplier_inn',
  ];
  const rest = entriesOfEntities(e, usedKeys);

  return (
    <form
      className="th-form"
      onSubmit={(ev) => {
        ev.preventDefault();
        onSubmit({ type: 'contract', ...form });
      }}
    >
      <Section title="Основное">
        <Row>
          <Field label="ID контракта">
            <input value={form.contract_id} onChange={change('contract_id')} placeholder="210293850" />
          </Field>
          <Field label="Дата">
            <input type="date" value={form.contract_date} onChange={change('contract_date')} />
          </Field>
        </Row>
        <Row>
          <Field label="Сумма">
            <input value={form.contract_amount} onChange={change('contract_amount')} placeholder="129 996.70" />
          </Field>
          <Field label="Правовая база">
            <input value={form.law_basis} onChange={change('law_basis')} placeholder="44-ФЗ" />
          </Field>
        </Row>
      </Section>

      <Section title="Стороны">
        <Row>
          <Field label="Заказчик (наименование)">
            <input value={form.customer_name} onChange={change('customer_name')} />
          </Field>
          <Field label="Заказчик (ИНН)">
            <input value={form.customer_inn} onChange={change('customer_inn')} />
          </Field>
        </Row>
        <Row>
          <Field label="Поставщик (наименование)">
            <input value={form.supplier_name} onChange={change('supplier_name')} />
          </Field>
          <Field label="Поставщик (ИНН)">
            <input value={form.supplier_inn} onChange={change('supplier_inn')} />
          </Field>
        </Row>
      </Section>

      <Section title="Прочее">
        <label className="th-field th-field--block">
          <span className="th-field__label">Заметки</span>
          <textarea rows={3} value={form.notes} onChange={change('notes')} placeholder="Доп. сведения" />
        </label>
      </Section>

      {rest.length > 0 && (
        <Section title="Дополнительные поля">
          <div className="th-grid-2">
            {rest.map(([k, v]) => (
              <label className="th-field" key={k}>
                <span className="th-field__label">{k}</span>
                <input defaultValue={String(v)} />
              </label>
            ))}
          </div>
        </Section>
      )}

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>
          Закрыть
        </button>
        <button type="submit" className="th-btn th-btn--primary">
          Создать
        </button>
      </div>
    </form>
  );
};

// session_search / create_session
const SessionForm: React.FC<Omit<Props, 'initial'>> = ({ envelope, onSubmit, onCancel }) => {
  const e = envelope?.ml_data?.entities || {};
  const [form, setForm] = useState({
    session_name: text(e.session_name),
    session_id: text(e.session_id),
    session_amount: money(e.session_amount),
    session_created_date: date(e.session_created_date),
    session_completed_date: date(e.session_completed_date),
    law_basis: text(e.law_basis),
    customer_name: text(e.customer_name),
    customer_inn: text(e.customer_inn),
    supplier_name: text(e.supplier_name),
    supplier_inn: text(e.supplier_inn),
    notes: '',
  });
  const change =
    (k: keyof typeof form) =>
    (ev: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((s) => ({ ...s, [k]: ev.target.value }));

  const usedKeys = [
    'session_name',
    'session_id',
    'session_amount',
    'session_created_date',
    'session_completed_date',
    'law_basis',
    'customer_name',
    'customer_inn',
    'supplier_name',
    'supplier_inn',
  ];
  const rest = entriesOfEntities(e, usedKeys);

  return (
    <form
      className="th-form"
      onSubmit={(ev) => {
        ev.preventDefault();
        onSubmit({ type: 'session', ...form });
      }}
    >
      <Section title="Основное">
        <Row>
          <Field label="Название сессии">
            <input
              value={form.session_name}
              onChange={change('session_name')}
              placeholder="Фильтры очистки воды…"
            />
          </Field>
          <Field label="ID сессии">
            <input value={form.session_id} onChange={change('session_id')} placeholder="10044030" />
          </Field>
        </Row>
        <Row>
          <Field label="Сумма">
            <input value={form.session_amount} onChange={change('session_amount')} placeholder="23 974.86" />
          </Field>
          <Field label="Правовая база">
            <input value={form.law_basis} onChange={change('law_basis')} placeholder="44-ФЗ" />
          </Field>
        </Row>
      </Section>

      <Section title="Сроки">
        <Row>
          <Field label="Создана">
            <input
              type="date"
              value={form.session_created_date}
              onChange={change('session_created_date')}
            />
          </Field>
          <Field label="Завершена">
            <input
              type="date"
              value={form.session_completed_date}
              onChange={change('session_completed_date')}
            />
          </Field>
        </Row>
      </Section>

      <Section title="Стороны">
        <Row>
          <Field label="Заказчик (наименование)">
            <input value={form.customer_name} onChange={change('customer_name')} />
          </Field>
          <Field label="Заказчик (ИНН)">
            <input value={form.customer_inn} onChange={change('customer_inn')} />
          </Field>
        </Row>
        <Row>
          <Field label="Поставщик (наименование)">
            <input value={form.supplier_name} onChange={change('supplier_name')} />
          </Field>
          <Field label="Поставщик (ИНН)">
            <input value={form.supplier_inn} onChange={change('supplier_inn')} />
          </Field>
        </Row>
      </Section>

      <Section title="Прочее">
        <label className="th-field th-field--block">
          <span className="th-field__label">Заметки</span>
          <textarea rows={3} value={form.notes} onChange={change('notes')} placeholder="Доп. сведения" />
        </label>
      </Section>

      {rest.length > 0 && (
        <Section title="Дополнительные поля">
          <div className="th-grid-2">
            {rest.map(([k, v]) => (
              <label className="th-field" key={k}>
                <span className="th-field__label">{k}</span>
                <input defaultValue={String(v)} />
              </label>
            ))}
          </div>
        </Section>
      )}

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>
          Закрыть
        </button>
        <button type="submit" className="th-btn th-btn--primary">
          Создать
        </button>
      </div>
    </form>
  );
};

// fallback (ручное создание)
const GenericCreateForm: React.FC<{
  initial?: DocumentData;
  onSubmit: (data: DocumentData) => void;
  onCancel: () => void;
}> = ({ initial, onSubmit, onCancel }) => {
  const [form, setForm] = useState<DocumentData>({
    ...(initial ?? {}),
    title: text(initial?.title),
    customer: text(initial?.customer),
    price: money(initial?.price),
    deadline: date(initial?.deadline),
    notes: text(initial?.notes),
  });

  const change =
    (k: keyof DocumentData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((s) => ({ ...s, [k]: e.target.value }));

  return (
    <form
      className="th-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
    >
      <Section title="Документ">
        <Row>
          <Field label="Название">
            <input value={form.title || ''} onChange={change('title')} placeholder="Название документа" />
          </Field>
          <Field label="Заказчик">
            <input
              value={form.customer || ''}
              onChange={change('customer')}
              placeholder="Организация / заказчик"
            />
          </Field>
        </Row>
        <Row>
          <Field label="Стоимость">
            <input value={form.price || ''} onChange={change('price')} placeholder="1 200 000 ₽" />
          </Field>
          <Field label="Срок">
            <input value={form.deadline || ''} onChange={change('deadline')} placeholder="2025-10-20" />
          </Field>
        </Row>
        <label className="th-field th-field--block">
          <span className="th-field__label">Заметки</span>
          <textarea value={form.notes || ''} onChange={change('notes')} rows={4} placeholder="Доп. сведения" />
        </label>
      </Section>

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>
          Закрыть
        </button>
        <button type="submit" className="th-btn th-btn--primary">
          Создать
        </button>
      </div>
    </form>
  );
};

// роутер форм
export default function DocumentForm({ envelope, initial, onSubmit, onCancel }: Props) {
  const type = envelope?.response?.type || envelope?.ml_data?.intent || '';
  const normalized = useMemo(() => String(type).toLowerCase(), [type]);

  if (normalized === 'company_search' || normalized === 'create_company_profile') {
    return <CompanyForm envelope={envelope} onSubmit={onSubmit} onCancel={onCancel} />;
  }
  if (normalized === 'contract_search' || normalized === 'create_contract') {
    return <ContractForm envelope={envelope} onSubmit={onSubmit} onCancel={onCancel} />;
  }
  if (normalized === 'session_search' || normalized === 'create_session') {
    return <SessionForm envelope={envelope} onSubmit={onSubmit} onCancel={onCancel} />;
  }

  if (normalized === 'error') {
    const msg = text(envelope?.response?.data ?? 'Ошибка');
    return (
      <form
        className="th-form"
        onSubmit={(e) => {
          e.preventDefault();
          onCancel();
        }}
      >
        <Section title="Ошибка">
          <div className="th-error">{msg}</div>
        </Section>
        <div className="th-actions">
          <button type="button" className="th-btn th-btn--primary" onClick={onCancel}>
            Закрыть
          </button>
        </div>
      </form>
    );
  }

  return <GenericCreateForm initial={initial} onSubmit={onSubmit} onCancel={onCancel} />;
}
