// src/App.tsx
import React from 'react';
import './app.css';

import SearchBar from '@/components/SearchBar/SearchBar';
import Modal from '@/components/Modal/Modal';
import DocumentForm, { DocumentData } from '@/components/DocumentForm/DocumentForm';
import LikeDislike from '@/components/LikeDislike/LikeDislike';

import { analyzeQuery, BackendEnvelope } from '@/lib/api';

export default function App() {
  // UI state
  const [openModal, setOpenModal] = React.useState(false);

  // Данные для форм/модалки
  const [envelopes, setEnvelopes] = React.useState<BackendEnvelope[]>([]);
  const [initialDoc, setInitialDoc] = React.useState<DocumentData | null>(null);

  // Последняя выбранная подсказка (из выпадашки)
  const [picked, setPicked] = React.useState<{ label: string; payload: any } | null>(null);

  // Поиск — наполняем envelopes массивом объектов от бэка/мока
  const doSearch = async (q: string) => {
    const items = await analyzeQuery(q);
    setEnvelopes(items || []);
  };

  // Создать — модалка открывается ТОЛЬКО по этой кнопке
  const handleCreate = (payload: any) => {
    // Предзаполнение "фолбэк" формы, если не будет найден envelope по типу
    setInitialDoc({
      title: payload?.title ?? '',
      customer: payload?.customer ?? '',
      price: payload?.price ?? '',
      deadline: payload?.deadline ?? '',
      notes: '',
    });
    setOpenModal(true);
  };

  // Ищем envelope подходящего типа под выбранную подсказку
  const envelopeForForm = React.useMemo<BackendEnvelope | null>(() => {
  if (!envelopes?.length) return null;

  const typeOf = (e: BackendEnvelope) =>
    (e.response?.type ?? e.ml_data?.intent ?? '').toString().toLowerCase();

  const groupOf = (t: string) =>
    t.startsWith('company') ? 'company' :
    t.startsWith('contract') ? 'contract' :
    t.startsWith('session') ? 'session' : t;

  const pickedType = picked?.payload?.__type?.toString()?.toLowerCase();
  if (pickedType) {
    // 1) точное совпадение
    const exact = envelopes.find(e => typeOf(e) === pickedType);
    if (exact) return exact;

    // 2) совпадение по группе (company/contract/session)
    const g = groupOf(pickedType);
    const byGroup = envelopes.find(e => groupOf(typeOf(e)) === g);
    if (byGroup) return byGroup;

    // 3) совпадение по сигнатуре entities
    const sig: Record<string, string[]> = {
      company: ['company_name','name','company_inn','company_ogrn'],
      contract: ['contract_id','contract_amount','customer_name','supplier_name'],
      session:  ['session_name','session_id','session_amount','customer_name','supplier_name'],
    };
    const byEntities = envelopes.find(e => {
      const ents = e.ml_data?.entities || {};
      return (sig[g] || []).some(k => k in ents);
    });
    if (byEntities) return byEntities;
  }

  // иначе — первый
  return envelopes[0] ?? null;
  }, [envelopes, picked]);



  const modalTitle = React.useMemo(() => {
    if (envelopeForForm) {
      return `Тип: ${envelopeForForm.response?.type ?? envelopeForForm.ml_data?.intent ?? '—'}`;
    }
    return 'Создание документа';
  }, [envelopeForForm]);

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">TenderHack</div>
      </header>

      <main className="content">
        <h1 className="title">Поиск</h1>

        <SearchBar
          placeholder="Найти тендер, команду, участника…"
          onSearch={doSearch}
          onCreate={handleCreate}
          onSelectSuggestion={(s) => setPicked(s)}
        />
      </main>

      <Modal
        open={openModal}
        onClose={() => setOpenModal(false)}
        title={modalTitle}
      >
        <DocumentForm
          envelope={envelopeForForm}
          initial={initialDoc || undefined}
          onSubmit={(data) => {
            console.log('CREATE DOCUMENT', data);
            setOpenModal(false);
          }}
          onCancel={() => setOpenModal(false)}
        />
      </Modal>
    </div>
  );
}
