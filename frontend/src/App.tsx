// src/App.tsx
import React, { useEffect, useState } from 'react';
import SearchBar from '@/components/SearchBar/SearchBar';
import History from '@/components/History/History';
import { fetchHistory, search, type HistoryRecord, type SearchResponse } from '@/lib/api';
import { HISTORY_LIMIT } from '@/lib/config';
import Modal from '@/components/Modal/Modal';
import ContractForm from '@/components/Forms/ContractForm';

type AnyData = Record<string, any>;

export default function App() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formType, setFormType] = useState<'contract' | 'none'>('none');

  // Контекст для формы + "подсказочные" сущности из истории
  const [contractCtx, setContractCtx] = useState<{
    responseType?: string;
    data?: AnyData | null;
    ml_data?: AnyData | null;
    hintEntities?: Record<string, any> | null;
  } | null>(null);

  const [hintEntities, setHintEntities] = useState<Record<string, any> | null>(null);

  async function loadHistory() {
    try {
      const items = await fetchHistory(HISTORY_LIMIT);
      setHistory(items);
    } catch (e) {
      console.warn(e);
    }
  }

  useEffect(() => { loadHistory(); }, []);

  const openContractForm = (ctx?: {
    responseType?: string;
    data?: AnyData | null;
    ml_data?: AnyData | null;
    hintEntities?: Record<string, any> | null;
  } | null) => {
    setFormType('contract');
    setContractCtx(ctx ?? null);
    setIsModalOpen(true);
  };

  const handleSearch = async (q: string) => {
    const resp: SearchResponse<AnyData> = await search(q, true, true);
    const t = resp?.response?.type;
    const data = resp?.response?.data ?? null;
    const ml = resp?.ml_data ?? null;

    if (t === 'create_contract_needs_more_info' || t === 'create_contract_ready_to_create') {
      openContractForm({ responseType: t, data, ml_data: ml, hintEntities });
    } else {
      // По требованию — всё равно открыть форму при поиске
      openContractForm({ responseType: t, data: null, ml_data: ml, hintEntities });
    }

    setHintEntities(null); // сброс для следующего поиска
    loadHistory();
  };

  return (
    <div style={{ padding: 16, minHeight: '100vh', background: '#1e1e2f', color: '#f2f2f2' }}>
      <SearchBar
        placeholder="Например: создай контракт на канцтовары 50000 рублей"
        onSearch={handleSearch}
        onCreate={() => openContractForm(null)}
      />

      <History
        items={history}
        onPick={(text, rec) => {
          setHintEntities(rec?.entities ?? null);
          handleSearch(text);
        }}
      />

      <Modal open={isModalOpen} onClose={() => setIsModalOpen(false)} title="Создание контракта">
        {formType === 'contract' && (
          <ContractForm
            ctx={contractCtx}
            onSubmit={(values) => {
              // TODO: подключить конечную точку создания контракта
              console.log('submit contract:', values);
              setIsModalOpen(false);
            }}
          />
        )}
      </Modal>
    </div>
  );
}
