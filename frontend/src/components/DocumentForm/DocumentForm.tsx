// src/components/DocumentForm/DocumentForm.tsx
import React, { useMemo, useState, useEffect } from 'react';
import LikeDislike from '@/components/LikeDislike/LikeDislike';
import './documentForm.css';

export type BackendEnvelope = {
  status: 'success' | 'error';
  response: { type: string; data: any };
  ml_data: { intent: string; confidence: number | null; entities: Record<string, any> };
};

export type DocumentData = {
  title?: string;
  customer?: string;
  price?: string;
  deadline?: string;
  notes?: string;
};

type Props = {
  envelope?: BackendEnvelope | null;
  initial?: DocumentData;
  onSubmit: (data: any) => void;
  onCancel: () => void;
};

const isNil = (v: any) => v === null || v === undefined;
const isEmpty = (v: any) => isNil(v) || v === '';
const asText = (v: any) => (isEmpty(v) ? '' : String(v));
const asDate = (v: any) => (isEmpty(v) ? '' : String(v).slice(0, 10));
const asMoney = (v: any) => (isEmpty(v) ? '' : String(v));

/* UI */
const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="th-section">
    <div className="th-section__title">{title}</div>
    <div className="th-section__body">{children}</div>
  </div>
);

const Row: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="th-form__row">{children}</div>
);

function Field({
  label,
  name,
  type = 'text',
  value,
  onChange,
}: {
  label: string;
  name: string;
  type?: 'text' | 'date' | 'money' | 'textarea' | 'number';
  value: string;
  onChange: (name: string, value: string) => void;
}) {
  if (type === 'textarea') {
    return (
      <label className="th-field th-field--block">
        <span className="th-field__label">{label}</span>
        <textarea
          rows={4}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          placeholder={label}
        />
      </label>
    );
  }
  const inputType = type === 'date' ? 'date' : type === 'number' ? 'number' : 'text';
  return (
    <label className="th-field">
      <span className="th-field__label">{label}</span>
      <input
        type={inputType}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        placeholder={label}
      />
    </label>
  );
}

/* ===== общие группы (НЕ entities) ===== */
function SystemGroup({
  status,
  onChange,
}: {
  status?: string;
  onChange: (name: string, value: string) => void;
}) {
  if (isEmpty(status)) return null;
  return (
    <Section title="Системные">
      <Row>
        <Field label="status" name="__status" value={asText(status)} onChange={onChange} />
      </Row>
    </Section>
  );
}

function ResponseGroup({
  response,
  onChange,
}: {
  response?: { type?: string; data?: any };
  onChange: (name: string, value: string) => void;
}) {
  if (!response) return null;
  const t = asText(response.type);
  const d = isNil(response.data)
    ? ''
    : typeof response.data === 'string'
    ? response.data
    : JSON.stringify(response.data);
  if (isEmpty(t) && isEmpty(d)) return null;
  return (
    <Section title="Response">
      <Row>
        {!isEmpty(t) && <Field label="type" name="__response.type" value={t} onChange={onChange} />}
        {!isEmpty(d) && (
          <Field label="data" name="__response.data" type="textarea" value={d} onChange={onChange} />
        )}
      </Row>
    </Section>
  );
}

function MLGroup({
  ml,
  onChange,
}: {
  ml?: { intent?: string; confidence?: number | null };
  onChange: (name: string, value: string) => void;
}) {
  if (!ml) return null;
  const i = asText(ml.intent);
  const c = isNil(ml.confidence) ? '' : String(ml.confidence);
  if (isEmpty(i) && isEmpty(c)) return null;
  return (
    <Section title="ML">
      <Row>
        {!isEmpty(i) && <Field label="intent" name="__ml.intent" value={i} onChange={onChange} />}
        {!isEmpty(c) && <Field label="confidence" name="__ml.confidence" value={c} onChange={onChange} />}
      </Row>
    </Section>
  );
}

/* ===== Entities (известные поля для красивого порядка) ===== */
const COMPANY_FIELDS: Array<{ key: string; label: string; type?: 'text' | 'textarea' }> = [
  { key: 'company_name', label: 'Наименование' },
  { key: 'name', label: 'Альтернативное наименование' },
  { key: 'company_inn', label: 'ИНН' },
  { key: 'company_ogrn', label: 'ОГРН' },
  { key: 'company_kpp', label: 'КПП' },
  { key: 'company_address', label: 'Юр. адрес', type: 'textarea' },
  { key: 'company_post_address', label: 'Почтовый адрес', type: 'textarea' },
  { key: 'company_phone', label: 'Телефон' },
  { key: 'company_email', label: 'Email' },
  { key: 'company_site', label: 'Сайт' },
];

const CONTRACT_FIELDS: Array<{ key: string; label: string; type?: 'text' | 'date' | 'money' | 'textarea' }> = [
  { key: 'contract_id', label: 'ID контракта' },
  { key: 'contract_date', label: 'Дата', type: 'date' },
  { key: 'contract_amount', label: 'Сумма', type: 'money' },
  { key: 'law_basis', label: 'Правовая база' },
  { key: 'category_pp_first_position', label: 'Категория (первая позиция)' },
  { key: 'customer_name', label: 'Заказчик (наименование)' },
  { key: 'customer_inn', label: 'Заказчик (ИНН)' },
  { key: 'supplier_name', label: 'Поставщик (наименование)' },
  { key: 'supplier_inn', label: 'Поставщик (ИНН)' },
];

const SESSION_FIELDS: Array<{ key: string; label: string; type?: 'text' | 'date' | 'money' | 'textarea' }> = [
  { key: 'session_name', label: 'Название сессии' },
  { key: 'session_id', label: 'ID сессии' },
  { key: 'session_amount', label: 'Сумма', type: 'money' },
  { key: 'session_created_date', label: 'Создана', type: 'date' },
  { key: 'session_completed_date', label: 'Завершена', type: 'date' },
  { key: 'law_basis', label: 'Правовая база' },
  { key: 'category_pp_first_position', label: 'Категория (первая позиция)' },
  { key: 'customer_name', label: 'Заказчик (наименование)' },
  { key: 'customer_inn', label: 'Заказчик (ИНН)' },
  { key: 'supplier_name', label: 'Поставщик (наименование)' },
  { key: 'supplier_inn', label: 'Поставщик (ИНН)' },
];

function normByType(type: string | undefined, v: any) {
  if (type === 'date') return asDate(v);
  if (type === 'money') return asMoney(v);
  return asText(v);
}

function EntitiesGroup({
  type,
  entities,
  excludeKeys = [],
  onChange,
}: {
  type: string;
  entities: Record<string, any>;
  excludeKeys?: string[];
  onChange: (name: string, value: string) => void;
}) {
  const sorted =
    type.startsWith('company') ? COMPANY_FIELDS :
    type.startsWith('contract') ? CONTRACT_FIELDS :
    type.startsWith('session') ? SESSION_FIELDS :
    [];

  const exclude = new Set(excludeKeys);

  const orderedVisible = sorted.filter(
    (f) => !exclude.has(f.key) && !isEmpty(entities[f.key])
  );
  const extra = Object.keys(entities)
    .filter((k) => !exclude.has(k) && orderedVisible.findIndex((f) => f.key === k) === -1 && !isEmpty(entities[k]))
    .map((k) => ({ key: k, label: k, type: 'text' as const }));

  if (orderedVisible.length === 0 && extra.length === 0) return null;

  return (
    <Section title="Entities">
      <Row>
        {[...orderedVisible, ...extra].map((f) => (
          <Field
            key={f.key}
            name={`entities.${f.key}`}
            label={f.label}
            type={(f.type as any) ?? 'text'}
            value={normByType(f.type, entities[f.key])}
            onChange={onChange}
          />
        ))}
      </Row>
    </Section>
  );
}

/* Прочие ключи верхнего уровня */
function OtherRootGroup({
  envelope,
  onChange,
}: {
  envelope: any;
  onChange: (name: string, value: string) => void;
}) {
  if (!envelope || typeof envelope !== 'object') return null;
  const exclude = new Set(['status', 'response', 'ml_data']);
  const other = Object.entries(envelope).filter(([k, v]) => !exclude.has(k) && !isEmpty(v));
  if (other.length === 0) return null;

  return (
    <Section title="Прочее (корень)">
      <Row>
        {other.map(([k, v]) => (
          <Field
            key={k}
            label={k}
            name={`__root.${k}`}
            type={typeof v === 'number' ? 'number' : 'text'}
            value={asText(v)}
            onChange={onChange}
          />
        ))}
      </Row>
    </Section>
  );
}

/* ===== ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ПО ТИПАМ (добавлено) ===== */
type ReqField = { key: string; label: string; type?: 'text' | 'number' | 'money' | 'date' | 'textarea' };

function requiredByType(normalized: string): ReqField[] {
  if (normalized === 'create_contract') {
    return [
      { key: 'contract_name', label: 'Наименование контракта' },
      { key: 'customer_name', label: 'Наименование заказчика' },
      { key: 'customer_inn', label: 'ИНН заказчика' },
      { key: 'contract_amount', label: 'Сумма', type: 'money' },
      { key: 'category_pp_first_position', label: 'Категория' },
      { key: 'law_basis', label: 'Закон' },
    ];
  }
  if (normalized === 'create_session') {
    return [
      { key: 'session_name', label: 'Наименование КС' },
      { key: 'customer_name', label: 'Наименование заказчика' },
      { key: 'customer_inn', label: 'ИНН заказчика' },
      { key: 'session_amount', label: 'Сумма', type: 'money' },
      { key: 'category_pp_first_position', label: 'Категория' },
      { key: 'law_basis', label: 'Закон' },
    ];
  }
  if (normalized === 'contract_search') {
    return [{ key: 'contract_id', label: 'ID' }];
  }
  if (normalized === 'session_search') {
    return [{ key: 'session_id', label: 'ID' }];
  }
  if (normalized === 'company_search') {
    return [
      { key: 'name', label: 'Имя компании' },
      { key: 'company_inn', label: 'ИНН компании' },
    ];
  }
  if (normalized === 'create_company_profile') {
    return [
      { key: 'company_name', label: 'Имя компании' },
      { key: 'company_inn', label: 'ИНН' },
      { key: 'company_bik', label: 'БИК' },
    ];
  }
  if (normalized === 'help') {
    return [{ key: 'help_data', label: 'Данные', type: 'textarea' }];
  }
  return [];
}

/* ===== Fallback (нет envelope) ===== */
function GenericCreateForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: DocumentData;
  onSubmit: (data: DocumentData) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<DocumentData>({
    ...(initial ?? {}),
    title: asText(initial?.title),
    customer: asText(initial?.customer),
    price: asMoney(initial?.price),
    deadline: asDate(initial?.deadline),
    notes: asText(initial?.notes),
  });
  const change = (name: string, value: string) => setForm((s) => ({ ...s, [name]: value }));

  return (
    <form className="th-form" onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}>
      <Section title="Документ">
        <Row>
          <Field label="Название" name="title" value={form.title || ''} onChange={change} />
          <Field label="Заказчик" name="customer" value={form.customer || ''} onChange={change} />
        </Row>
        <Row>
          <Field label="Стоимость" name="price" value={form.price || ''} onChange={change} />
          <Field label="Срок" name="deadline" value={form.deadline || ''} onChange={change} />
        </Row>
        <Field label="Заметки" name="notes" type="textarea" value={form.notes || ''} onChange={change} />
      </Section>

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>Закрыть</button>
        <button type="submit" className="th-btn th-btn--primary">Создать</button>
      </div>
    </form>
  );
}

/* ===== Основной компонент ===== */
export default function DocumentForm({ envelope, initial, onSubmit, onCancel }: Props) {
  const typeRaw = envelope?.response?.type || envelope?.ml_data?.intent || '';
  const normalized = useMemo(() => String(typeRaw).toLowerCase(), [typeRaw]);
  const entities = envelope?.ml_data?.entities || {};

  if (!envelope) {
    return <GenericCreateForm initial={initial} onSubmit={onSubmit} onCancel={onCancel} />;
  }

  // обязательные поля (всегда рендерим)
  const req = useMemo(() => requiredByType(normalized), [normalized]);

  const buildReqInit = () =>
    req.reduce<Record<string, string>>((acc, f) => {
      const raw = entities[f.key];
      const val =
        f.type === 'date' ? asDate(raw) :
        f.type === 'money' ? asMoney(raw) :
        f.type === 'number' ? asText(raw) :
        f.type === 'textarea' ? asText(raw) :
        asText(raw);
      acc[f.key] = val; // даже если пусто — поле рендерим
      return acc;
    }, {});

  const [requiredState, setRequiredState] = useState<Record<string, string>>(buildReqInit());

  // если сменился тип/данные — пересобрать обязательные поля
  useEffect(() => {
    setRequiredState(buildReqInit());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [normalized, entities]);

  const onChangeReq = (name: string, value: string) =>
    setRequiredState((s) => ({ ...s, [name]: value }));

  const submitAll = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      __doc_type: normalized,
      required: requiredState,     // значения из обязательного блока
      entities,                    // сырые entities (остальное)
      status: envelope.status,
      response: envelope.response,
      ml_data: { intent: envelope.ml_data?.intent, confidence: envelope.ml_data?.confidence },
    });
  };

  const excludeKeys = useMemo(() => req.map((f) => f.key), [req]);

  return (
    <form className="th-form" onSubmit={submitAll}>
      {/* Обязательные поля */}
      {req.length > 0 && (
        <Section title="Обязательные поля">
          <Row>
            {req.map((f) => (
              <Field
                key={f.key}
                name={f.key}
                label={f.label}
                type={f.type ?? 'text'}
                value={requiredState[f.key] ?? ''}
                onChange={onChangeReq}
              />
            ))}
          </Row>
        </Section>
      )}

      {/* Остальные блоки оставляем как есть */}
      <SystemGroup status={envelope.status} onChange={() => {}} />
      <ResponseGroup response={envelope.response} onChange={() => {}} />
      <MLGroup ml={envelope.ml_data} onChange={() => {}} />

      {/* Entities, но без дублирования обязательных ключей */}
      <EntitiesGroup
        type={normalized}
        entities={entities}
        excludeKeys={excludeKeys}
        onChange={() => {}}
      />

      <OtherRootGroup envelope={envelope as any} onChange={() => {}} />

      <div className="th-actions">
        <LikeDislike onRate={(v) => console.log('rate:', v)} />
        <div className="th-actions__spacer" />
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>Закрыть</button>
        <button type="submit" className="th-btn th-btn--primary">Создать</button>
      </div>
    </form>
  );
}
