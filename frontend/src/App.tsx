// src/App.tsx
import React, { useEffect, useState } from 'react';
import SearchBar from '@/components/SearchBar/SearchBar';
import History from '@/components/History/History';
import Examples from '@/components/Examples/Examples';
import { fetchHistory, search, type HistoryRecord, type SearchResponse } from '@/lib/api';
import { HISTORY_LIMIT } from '@/lib/config';
import Modal from '@/components/Modal/Modal';
import ContractForm from '@/components/Forms/ContractForm';
import KSForm from '@/components/Forms/KSForm';
import CompanyForm from '@/components/Forms/CompanyForm';
import ProcurementForm from '@/components/Forms/ProcurementForm';
import SearchResults from '@/components/SearchResults/SearchResults';
import Help from '@/components/Help/Help';

type AnyData = Record<string, any>;

export default function App() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formType, setFormType] = useState<'contract' | 'ks' | 'company' | 'procurement' | 'none'>('none');
  const [searchHighlighted, setSearchHighlighted] = useState(false);
  const [searchResults, setSearchResults] = useState<AnyData | null>(null);
  const [helpData, setHelpData] = useState<AnyData | null>(null);

  // Контекст для формы + "подсказочные" сущности из истории
  const [formCtx, setFormCtx] = useState<{
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

  // Функция определения типа формы по ответу API
  const determineFormType = (responseType?: string, intent?: string): 'contract' | 'ks' | 'company' | 'procurement' => {
    if (responseType) {
      if (responseType.includes('contract')) return 'contract';
      if (responseType.includes('ks') || responseType.includes('session')) return 'ks';
      if (responseType.includes('company')) return 'company';
      if (responseType.includes('procurement') || responseType.includes('zakupka')) return 'procurement';
    }
    
    if (intent) {
      if (intent === 'create_contract') return 'contract';
      if (intent === 'create_ks') return 'ks';
      if (intent === 'create_company_profile') return 'company';
      if (intent === 'create_procurement') return 'procurement';
      if (intent === 'create_zakupka') return 'procurement';
    }
    
    return 'contract'; // По умолчанию
  };

  const openForm = (type: 'contract' | 'ks' | 'company' | 'procurement', ctx?: {
    responseType?: string;
    data?: AnyData | null;
    ml_data?: AnyData | null;
    hintEntities?: Record<string, any> | null;
  } | null) => {
    setFormType(type);
    setFormCtx(ctx ?? null);
    setIsModalOpen(true);
  };

  // Обратная совместимость
  const openContractForm = (ctx?: {
    responseType?: string;
    data?: AnyData | null;
    ml_data?: AnyData | null;
    hintEntities?: Record<string, any> | null;
  } | null) => {
    openForm('contract', ctx);
  };

  const handleSearch = async (q: string) => {
    const resp: SearchResponse<AnyData> = await search(q, true, true);
    const t = resp?.response?.type;
    const data = resp?.response?.data ?? null;
    const ml = resp?.ml_data ?? null;

    // Определяем тип формы на основе ответа
    const formTypeToOpen = determineFormType(t, ml?.intent);

    // Проверяем, нужно ли открыть форму создания
    const shouldOpenForm = (t && (
      t.includes('create_contract') ||
      t.includes('create_ks') ||
      t.includes('create_company') ||
      t.includes('create_procurement') ||
      t.includes('create_zakupka') ||
      t.includes('needs_more_info') ||
      t.includes('ready_to_create')
    )) || (ml?.intent && (
      ml.intent === 'create_contract' ||
      ml.intent === 'create_ks' ||
      ml.intent === 'create_company_profile' ||
      ml.intent === 'create_procurement' ||
      ml.intent === 'create_zakupka'
    ));

    // Проверяем, это результаты поиска
    const isSearchResults = t && (
      t.includes('search_') ||
      t.includes('company_search') ||
      t.includes('company_found') ||
      ml?.intent === 'search_docs' ||
      ml?.intent === 'search_company'
    );

    // Проверяем, это запрос справки
    const isHelpRequest = t && (
      t.includes('help_response') ||
      ml?.intent === 'help'
    );

    if (shouldOpenForm) {
      setSearchResults(null); // Очищаем результаты поиска
      setHelpData(null); // Очищаем данные справки
      openForm(formTypeToOpen, { responseType: t, data, ml_data: ml, hintEntities });
    } else if (isSearchResults && data) {
      // Отображаем результаты поиска
      setHelpData(null); // Очищаем данные справки
      setSearchResults({
        type: t,
        status: resp.status || 'success',
        message: data.message || 'Результаты поиска',
        results: data.results || [],
        totalCount: data.total_count || data.results?.length || 0,
        searchParams: data.search_params || {},
        companyData: data.company_data || (t && (t.includes('company') || ml?.intent === 'search_company') ? data : null)
      });
    } else if (isHelpRequest && data) {
      // Отображаем справку
      setSearchResults(null); // Очищаем результаты поиска
      setHelpData({
        type: t,
        status: resp.status || 'success',
        message: data.message || 'Справочная информация',
        helpSections: data.help_sections || []
      });
    } else {
      // По умолчанию открываем форму контракта
      setSearchResults(null);
      setHelpData(null);
      openForm('contract', { responseType: t, data: null, ml_data: ml, hintEntities });
    }

    setHintEntities(null); // сброс для следующего поиска
    loadHistory();
  };

  const handleExampleClick = (example: string) => {
    // Подсвечиваем строку поиска
    setSearchHighlighted(true);
    
    // Убираем подсветку через 600ms (время анимации)
    setTimeout(() => {
      setSearchHighlighted(false);
    }, 600);
    
    // Выполняем поиск
    handleSearch(example);
  };

  return (
    <div style={{ padding: 16, minHeight: '100vh', background: '#1e1e2f', color: '#f2f2f2' }}>
      <SearchBar
        placeholder="Например: создай контракт на канцтовары 50000 рублей"
        onSearch={handleSearch}
        onCreate={() => openContractForm(null)}
        highlighted={searchHighlighted}
      />

      <Examples onExampleClick={handleExampleClick} />

      {searchResults && (
        <SearchResults
          type={searchResults.type}
          status={searchResults.status}
          message={searchResults.message}
          results={searchResults.results}
          totalCount={searchResults.totalCount}
          searchParams={searchResults.searchParams}
          companyData={searchResults.companyData}
        />
      )}

      {helpData && (
        <Help
          type={helpData.type}
          status={helpData.status}
          message={helpData.message}
          helpSections={helpData.helpSections}
        />
      )}

      <History
        items={history}
        onPick={(text, rec) => {
          setHintEntities(rec?.entities ?? null);
          handleSearch(text);
        }}
      />

      <Modal 
        open={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        title={
          formType === 'contract' ? 'Создание контракта' :
          formType === 'ks' ? 'Создание КС (котировочной сессии)' :
          formType === 'company' ? 'Создание профиля компании' :
          formType === 'procurement' ? 'Создание закупки' :
          'Создание документа'
        }
      >
        {formType === 'contract' && (
          <ContractForm
            ctx={formCtx}
            onSubmit={(values) => {
              // TODO: подключить конечную точку создания контракта
              console.log('submit contract:', values);
              setIsModalOpen(false);
            }}
          />
        )}
        
        {formType === 'ks' && (
          <KSForm
            ctx={formCtx}
            onSubmit={(values) => {
              // TODO: подключить конечную точку создания КС
              console.log('submit ks:', values);
              setIsModalOpen(false);
            }}
          />
        )}
        
        {formType === 'company' && (
          <CompanyForm
            ctx={formCtx}
            onSubmit={(values) => {
              // TODO: подключить конечную точку создания компании
              console.log('submit company:', values);
              setIsModalOpen(false);
            }}
          />
        )}

        {formType === 'procurement' && (
          <ProcurementForm
            ctx={formCtx}
            onSubmit={(values) => {
              // TODO: подключить конечную точку создания закупки
              console.log('submit procurement:', values);
              setIsModalOpen(false);
            }}
          />
        )}
      </Modal>
    </div>
  );
}
