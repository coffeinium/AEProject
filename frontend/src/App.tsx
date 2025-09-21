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
  const [contractData, setContractData] = useState<any | null>(null); // данные для формы

  async function loadHistory() {
    try {
      const items = await fetchHistory(HISTORY_LIMIT);
      setHistory(items);
    } catch (e) {
      console.warn(e);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const openContractForm = (payload?: any) => {
    setFormType('contract');
    setContractData(payload ?? null);
    setIsModalOpen(true);
  };

  const handleSearch = async (q: string) => {
    const resp: SearchResponse<AnyData> = await search(q, true, true);
    // по доке нас интересуют create_contract_* для заполненной формы
    const t = resp?.response?.type;
    const data = resp?.response?.data ?? {};

    if (t === 'create_contract_needs_more_info' || t === 'create_contract_ready_to_create') {
      openContractForm(data);
    } else {
      // если тип не про контракт — всё равно откроем пустую форму (по ТЗ: модалка при поиске)
      openContractForm(null);
    }

    // обновим историю
    loadHistory();
  };

  return (
    <div style={{ padding: 16 }}>
      <SearchBar
        placeholder="Например: создай контракт на канцтовары 50000 рублей"
        onSearch={handleSearch}
        onCreate={() => openContractForm(null)}
      />

      <History items={history} onPick={(text) => handleSearch(text)} />

      <Modal open={isModalOpen} onClose={() => setIsModalOpen(false)} title="Создание контракта">
        {formType === 'contract' && (
          <ContractForm
            initial={contractData}
            onSubmit={(values) => {
              // здесь отправка на ваш endpoint создания контракта (когда будет готов)
              console.log('submit contract:', values);
              setIsModalOpen(false);
            }}
          />
        )}
      </Modal>
    </div>
  );
}
