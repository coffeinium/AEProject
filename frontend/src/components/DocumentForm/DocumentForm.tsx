import React, { useMemo, useState, useEffect } from 'react';
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

function isNil(v: any): boolean { return v === null || v === undefined; }
function isEmpty(v: any): boolean {
  if (isNil(v)) return true;
  if (typeof v === 'string') return v.trim().length === 0;
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === 'object') return Object.keys(v).length === 0;
  return false;
}

const asText = (v: any) => (isNil(v) ? '' : String(v));
const asMoney = (v: any) => {
  if (isNil(v)) return '';
  const s = String(v).replace(',', '.').replace(/[^\d.]/g, '');
  return s;
};
const asDate = (v: any) => {
  if (isNil(v)) return '';
  // допускаем ISO с 'T' и без
  const s = String(v).replace(' ', 'T');
  return s;
};

function baseType(t: string): string {
  const s = (t || '').toLowerCase();
  if (!s) return '';
  return s
    .replace(/^create_/, '')
    .replace(/^search_/, '')
    .replace(/_profile$/, '')
    .trim();
}
function normalizeType(t: string): string {
  const b = baseType(t);
  if (!b) return '';
  if (b.includes('contract')) return 'create_contract';
  if (b.includes('session')) return 'create_session';
  if (b.includes('company')) return 'create_company_profile';
  return t;
}

function payloadKeyFor(t: string): 'contract_data' | 'session_data' | 'company_data' | null {
  if (t.includes('contract')) return 'contract_data';
  if (t.includes('session')) return 'session_data';
  if (t.includes('company')) return 'company_data';
  return null;
}

/** Известные поля для предзаполнения и порядка в Entities */
const CONTRACT_FIELDS: Array<{ key: string; label: string; type?: 'text' | 'date' | 'money' | 'textarea' }> = [
  { key: 'contract_name', label: 'Название контракта' },
  { key: 'contract_id', label: 'ID контракта' },
  { key: 'contract_amount', label: 'Сумма', type: 'money' },
  { key: 'contract_date', label: 'Дата', type: 'date' },
  { key: 'law_basis', label: 'Правовая база' },
  { key: 'category_pp_first_position', label: 'Категория (первая позиция)' },
  { key: 'customer_name', label: 'Заказчик (наименование)' },
  { key: 'customer_inn', label: 'Заказчик (ИНН)' },
  { key: 'supplier_name', label: 'Поставщик (наименование)' },
  { key: 'supplier_inn', label: 'Поставщик (ИНН)' }
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
  { key: 'supplier_inn', label: 'Поставщик (ИНН)' }
];

const COMPANY_FIELDS: Array<{ key: string; label: string; type?: 'text' | 'date' | 'money' | 'textarea' }> = [
  { key: 'company_name', label: 'Название компании' },
  { key: 'company_inn', label: 'ИНН' },
  { key: 'company_kpp', label: 'КПП' },
  { key: 'company_ogrn', label: 'ОГРН' },
  { key: 'company_okved', label: 'ОКВЭД' },
  { key: 'company_address', label: 'Адрес', type: 'textarea' },
  { key: 'company_phone', label: 'Телефон' },
  { key: 'company_email', label: 'Email' },
  { key: 'company_site', label: 'Сайт' }
];

const KNOWN_FIELDS_BY_TYPE: Record<string, typeof CONTRACT_FIELDS> = {
  create_contract: CONTRACT_FIELDS,
  contract_search: CONTRACT_FIELDS,
  create_session: SESSION_FIELDS,
  session_search: SESSION_FIELDS,
  create_company_profile: COMPANY_FIELDS,
  company_search: COMPANY_FIELDS
};

/** Обязательные поля для каждого типа */
function requiredByType(normalized: string): Array<{ key: string; label: string; type?: 'text' | 'date' | 'money' }> {
  if (normalized.includes('contract')) {
    return [
      { key: 'customer_name', label: 'Заказчик (наименование)' },
      { key: 'customer_inn', label: 'Заказчик (ИНН)' }
    ];
  }
  if (normalized.includes('session')) {
    return [
      { key: 'customer_name', label: 'Заказчик (наименование)' },
      { key: 'customer_inn', label: 'Заказчик (ИНН)' },
      { key: 'law_basis', label: 'Правовая база' }
    ];
  }
  if (normalized.includes('company')) {
    return [
      { key: 'company_name', label: 'Название компании' },
      { key: 'company_inn', label: 'ИНН' }
    ];
  }
  return [];
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <fieldset className="th-section">
      <legend className="th-section__title">{title}</legend>
      <div className="th-section__body">{children}</div>
    </fieldset>
  );
}
function Row({ children }: { children: React.ReactNode }) {
  return <div className="th-row">{children}</div>;
}

function Field({
  label,
  name,
  value,
  onChange,
  type = 'text'
}: {
  label?: string;
  name: string;
  value: string;
  type?: 'text' | 'textarea' | 'date' | 'money';
  onChange: (name: string, value: string) => void;
}) {
  const norm = (t: string | undefined, v: any) => {
    if (t === 'date') return asDate(v);
    if (t === 'money') return asMoney(v);
    return asText(v);
  };
  const inputProps = {
    name,
    value: norm(type, value),
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(name, e.target.value)
  };
  return (
    <label className="th-field">
      {!!label && <span className="th-field__label">{label}</span>}
      {type === 'textarea' ? (
        <textarea className="th-input th-input--area" rows={6} readOnly {...(inputProps as any)} />
      ) : (
        <input
          className="th-input"
          type={type === 'date' ? 'datetime-local' : 'text'}
          readOnly
          {...(inputProps as any)}
        />
      )}
    </label>
  );
}

function SystemGroup({ status }: { status: BackendEnvelope['status'] }) {
  return (
    <Section title="Системные">
      <Row>
        <Field label="status" name="__status" value={asText(status)} onChange={() => {}} />
      </Row>
    </Section>
  );
}

function ResponseGroup({ response, normalized }: { response: BackendEnvelope['response']; normalized: string }) {
  if (!response) return null;
  const t = asText(response.type);
  const data = response.data;

  // helper to guess field type by name
  const guessType = (k: string): 'text' | 'date' | 'money' => {
    const key = k.toLowerCase();
    if (key.includes('date') || key.endsWith('_at') || key.endsWith('date')) return 'date';
    if (key.includes('amount') || key.includes('sum') || key.includes('price')) return 'money';
    return 'text';
  };

  // Render primitives as Field
  const renderPrimitive = (label: string, name: string, value: any) => {
    const type = guessType(label);
    const v = type === 'date' ? asDate(value) : type === 'money' ? asMoney(value) : asText(value);
    if (isEmpty(v)) return null;
    return <Field key={name} label={label} name={name} type={type} value={v} onChange={() => {}} />;
  };

  // If data is not object – fallback to text
  if (isNil(data) || typeof data !== 'object') {
    if (isEmpty(t) && isEmpty(data)) return null;
    return (
      <Section title="Response">
        <Row>
          {!isEmpty(t) && <Field label="type" name="__response.type" value={t} onChange={() => {}} />}
          {!isNil(data) && <Field label="data" name="__response.data" type="textarea" value={asText(data)} onChange={() => {}} />}
        </Row>
      </Section>
    );
  }

  // data is object: split into simple fields and nested objects/arrays
  const entries = Object.entries(data as Record<string, any>);
  const simple: Array<[string, any]> = [];
  const nested: Array<[string, any]> = [];
  for (const [k, v] of entries) {
    if (v && typeof v === 'object') nested.push([k, v]);
    else simple.push([k, v]);
  }

  return (
    <Section title="Response">
      <Row>
        {!isEmpty(t) && <Field label="type" name="__response.type" value={t} onChange={() => {}} />}
        {simple.map(([k, v]) => renderPrimitive(k, `__response.data.${k}`, v))}
      </Row>

      {nested.map(([k, v]) => {
        if (Array.isArray(v)) {
          if (v.length === 0) return null;
          return (
            <Section key={k} title={`Response › ${k}`}>
              <Row>
                <Field
                  label={k}
                  name={`__response.data.${k}`}
                  type="textarea"
                  value={JSON.stringify(v, null, 2)}
                  onChange={() => {}}
                />
              </Row>
            </Section>
          );
        }
        // object: render its leaf fields
        const inner = v as Record<string, any>;
        const innerEntries = Object.entries(inner);
        const innerFields = innerEntries
          .map(([ik, iv]) => renderPrimitive(ik, `__response.data.${k}.${ik}`, iv))
          .filter(Boolean) as React.ReactNode[];

        if (innerFields.length === 0) return null;
        return (
          <Section key={k} title={`Response › ${k}`}>
            <Row>{innerFields}</Row>
          </Section>
        );
      })}
    </Section>
  );
}

function MLGroup({ ml }: { ml: BackendEnvelope['ml_data'] }) {
  if (!ml) return null;
  return (
    <Section title="ML">
      <Row>
        <Field label="intent" name="__ml.intent" value={asText(ml.intent)} onChange={() => {}} />
        <Field label="confidence" name="__ml.confidence" value={asText(ml.confidence)} onChange={() => {}} />
        {!isEmpty(ml.entities) && (
          <Field
            label="entities"
            name="__ml.entities"
            type="textarea"
            value={JSON.stringify(ml.entities, null, 2)}
            onChange={() => {}}
          />
        )}
      </Row>
    </Section>
  );
}

function EntitiesGroup({
  normalized,
  entities,
  excludeKeys = [],
  onChange
}: {
  normalized: string;
  entities: Record<string, any>;
  excludeKeys?: string[];
  onChange: (name: string, value: string) => void;
}) {
  const known = KNOWN_FIELDS_BY_TYPE[normalized] ?? [];
  const exclude = new Set(excludeKeys);

  const orderedVisible = known.filter(
    (f) => !exclude.has(f.key) && !isNil(entities[f.key]) && String(entities[f.key]) !== ''
  );

  const extra = Object.keys(entities)
    .filter(
      (k) => !exclude.has(k) && orderedVisible.findIndex((f) => f.key === k) === -1 && !isEmpty(entities[k])
    )
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
            type={f.type ?? 'text'}
            value={
              f.type === 'date' ? asDate(entities[f.key]) : f.type === 'money' ? asMoney(entities[f.key]) : asText(entities[f.key])
            }
            onChange={onChange}
          />
        ))}
      </Row>
    </Section>
  );
}

type Props = {
  formId: string;
  envelope?: BackendEnvelope | null; // <-- было только BackendEnvelope | undefined
  initial?: DocumentData;
  onSubmit: (payload: any) => void;
  onCancel: () => void;
};

export default function DocumentForm({ formId, envelope, initial, onSubmit, onCancel }: Props) {
  const typeRaw = envelope?.response?.type || envelope?.ml_data?.intent || '';
  const normalized = useMemo(() => baseType(typeRaw), [typeRaw]);

  // Поднять payload из response.data.{...}_data
  const responsePayload = useMemo(() => {
    const key = payloadKeyFor(normalized);
    const data = envelope?.response?.data || {};
    return key && data && typeof data === 'object' ? (data as any)[key] ?? {} : {};
  }, [normalized, envelope]);

  // Merge: responsePayload + ML.entities
  const [entities, setEntities] = useState<Record<string, any>>(() => {
    const ml = envelope?.ml_data?.entities || {};
    return { ...(responsePayload || {}), ...(ml || {}) };
  });

  useEffect(() => {
    const ml = envelope?.ml_data?.entities || {};
    setEntities({ ...(responsePayload || {}), ...(ml || {}) });
  }, [responsePayload, envelope]);

  // Required
  const req = requiredByType(normalizeType(typeRaw));
  const [requiredState, setRequiredState] = useState<Record<string, string>>(() =>
    Object.fromEntries(req.map((f) => [f.key, '']))
  );

  const onChangeReq = (name: string, value: string) => {
    setRequiredState((s) => ({ ...s, [name]: value }));
  };

  const onChange = (name: string, value: string) => {
    setEntities((s) => ({ ...s, [name.replace(/^entities\./, '')]: value }));
  };

  const submitAll: React.FormEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault();
    onSubmit({
      __doc_type: normalized,
      required: requiredState,
      entities,
      status: envelope!.status,
      response: envelope!.response,
      ml_data: { intent: envelope!.ml_data?.intent, confidence: envelope!.ml_data?.confidence }
    });
  };

  if (!envelope) {
    return <div>Нет данных.</div>;
  }

  return (
    <form id={formId} className="th-form" onSubmit={submitAll}>
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

      {/* Системные/Response/ML — readonly */}
      <SystemGroup status={envelope.status} />
      <ResponseGroup response={envelope.response} normalized={normalized} />
      <MLGroup ml={envelope.ml_data} />

      {/* Entities */}
      <EntitiesGroup
        normalized={normalized}
        entities={entities}
        excludeKeys={req.map((f) => f.key)}
        onChange={() => {}}
      />

      {/* Кнопки */}
      <div className="th-actions">
        <button type="button" className="th-btn th-btn--ghost" onClick={onCancel}>Отмена</button>
        <button type="submit" className="th-btn th-btn--primary">Сохранить</button>
      </div>
    </form>
  );
}
