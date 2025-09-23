import React from 'react';
import './searchResults.css';

interface SearchResult {
  type: 'contract' | 'session' | 'company';
  data: Record<string, any>;
}

interface SearchResultsProps {
  type: string;
  status: string;
  message: string;
  results?: SearchResult[];
  totalCount?: number;
  searchParams?: Record<string, any>;
  companyData?: Record<string, any>;
}

const formatAmount = (amount: number | string): string => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return 'Не указано';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num);
};

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'Не указано';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU');
  } catch {
    return 'Некорректная дата';
  }
};

const ContractCard: React.FC<{ contract: Record<string, any> }> = ({ contract }) => (
  <div className="search-result-card search-result-card--contract">
    <div className="search-result-header">
      <h3 className="search-result-title">
        {contract.contract_name || contract.name || 'Контракт без названия'}
      </h3>
      <span className="search-result-badge search-result-badge--contract">Контракт</span>
    </div>
    
    <div className="search-result-details">
      <div className="search-result-row">
        <span className="search-result-label">Заказчик:</span>
        <span className="search-result-value">{contract.customer_name || 'Не указано'}</span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">ИНН заказчика:</span>
        <span className="search-result-value">{contract.customer_inn || 'Не указано'}</span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">Сумма:</span>
        <span className="search-result-value search-result-amount">
          {formatAmount(contract.contract_amount || contract.amount || 0)}
        </span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">Дата:</span>
        <span className="search-result-value">{formatDate(contract.contract_date || contract.date)}</span>
      </div>
      
      {contract.law_basis && (
        <div className="search-result-row">
          <span className="search-result-label">Закон:</span>
          <span className="search-result-value">{contract.law_basis}</span>
        </div>
      )}
      
      {contract.category_pp_first_position && (
        <div className="search-result-row">
          <span className="search-result-label">Категория:</span>
          <span className="search-result-value">{contract.category_pp_first_position}</span>
        </div>
      )}
    </div>
  </div>
);

const SessionCard: React.FC<{ session: Record<string, any> }> = ({ session }) => (
  <div className="search-result-card search-result-card--session">
    <div className="search-result-header">
      <h3 className="search-result-title">
        {session.session_name || session.name || 'КС без названия'}
      </h3>
      <span className="search-result-badge search-result-badge--session">КС</span>
    </div>
    
    <div className="search-result-details">
      <div className="search-result-row">
        <span className="search-result-label">Заказчик:</span>
        <span className="search-result-value">{session.customer_name || 'Не указано'}</span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">ИНН заказчика:</span>
        <span className="search-result-value">{session.customer_inn || 'Не указано'}</span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">Сумма:</span>
        <span className="search-result-value search-result-amount">
          {formatAmount(session.session_amount || session.amount || 0)}
        </span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">Создано:</span>
        <span className="search-result-value">{formatDate(session.session_created_date || session.created_date)}</span>
      </div>
      
      <div className="search-result-row">
        <span className="search-result-label">Завершение:</span>
        <span className="search-result-value">{formatDate(session.session_completed_date || session.completed_date)}</span>
      </div>
      
      {session.law_basis && (
        <div className="search-result-row">
          <span className="search-result-label">Закон:</span>
          <span className="search-result-value">{session.law_basis}</span>
        </div>
      )}
    </div>
  </div>
);

const CompanyCard: React.FC<{ company: Record<string, any> }> = ({ company }) => {
  const summary = company.summary || {};
  
  return (
    <div className="search-result-card search-result-card--company">
      <div className="search-result-header">
        <h3 className="search-result-title">
          {summary.name || company.name || 'Компания без названия'}
        </h3>
        <span className="search-result-badge search-result-badge--company">Компания</span>
      </div>
      
      <div className="search-result-details">
        <div className="search-result-row">
          <span className="search-result-label">ИНН:</span>
          <span className="search-result-value">{summary.inn || company.inn || 'Не указано'}</span>
        </div>
        
        <div className="search-result-row">
          <span className="search-result-label">Контрактов:</span>
          <span className="search-result-value">{summary.contracts_count || 0}</span>
        </div>
        
        <div className="search-result-row">
          <span className="search-result-label">КС:</span>
          <span className="search-result-value">{summary.sessions_count || 0}</span>
        </div>
        
        <div className="search-result-row">
          <span className="search-result-label">Сумма контрактов:</span>
          <span className="search-result-value search-result-amount">
            {formatAmount(summary.total_contract_amount || 0)}
          </span>
        </div>
        
        <div className="search-result-row">
          <span className="search-result-label">Сумма КС:</span>
          <span className="search-result-value search-result-amount">
            {formatAmount(summary.total_session_amount || 0)}
          </span>
        </div>
      </div>
      
      {(company.contracts?.length > 0 || company.sessions?.length > 0) && (
        <div className="search-result-related">
          <h4 className="search-result-related-title">Связанные документы:</h4>
          <div className="search-result-related-items">
            {company.contracts?.slice(0, 3).map((contract: any, index: number) => (
              <div key={`contract-${index}`} className="search-result-related-item">
                <span className="search-result-related-type">Контракт:</span>
                <span className="search-result-related-name">
                  {contract.contract_name || `Контракт #${contract.id}`}
                </span>
              </div>
            ))}
            {company.sessions?.slice(0, 3).map((session: any, index: number) => (
              <div key={`session-${index}`} className="search-result-related-item">
                <span className="search-result-related-type">КС:</span>
                <span className="search-result-related-name">
                  {session.session_name || `КС #${session.id}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const SearchResults: React.FC<SearchResultsProps> = ({
  type,
  status,
  message,
  results = [],
  totalCount = 0,
  searchParams = {},
  companyData
}) => {
  if (status === 'no_results') {
    return (
      <div className="search-results">
        <div className="search-results-empty">
          <div className="search-results-empty-icon">🔍</div>
          <h3 className="search-results-empty-title">Ничего не найдено</h3>
          <p className="search-results-empty-message">{message}</p>
          
          {Object.keys(searchParams).length > 0 && (
            <div className="search-results-params">
              <p className="search-results-params-title">Параметры поиска:</p>
              <ul className="search-results-params-list">
                {Object.entries(searchParams).map(([key, value]) => (
                  <li key={key} className="search-results-params-item">
                    <strong>{key}:</strong> {String(value)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Обработка поиска компании
  if (type.includes('company') && companyData) {
    return (
      <div className="search-results">
        <div className="search-results-header">
          <h2 className="search-results-title">Результат поиска компании</h2>
          <p className="search-results-message">{message}</p>
        </div>
        
        <div className="search-results-list">
          <CompanyCard company={companyData} />
        </div>
      </div>
    );
  }

  // Обработка поиска документов
  if (results.length > 0) {
    return (
      <div className="search-results">
        <div className="search-results-header">
          <h2 className="search-results-title">
            Результаты поиска {type.includes('contract') ? 'контрактов' : 
                               type.includes('session') ? 'КС' : 
                               type.includes('mixed') ? 'документов' : 'данных'}
          </h2>
          <p className="search-results-message">
            {message} (всего: {totalCount})
          </p>
        </div>
        
        <div className="search-results-list">
          {results.map((result, index) => {
            if (result.type === 'contract') {
              return <ContractCard key={`contract-${index}`} contract={result.data} />;
            } else if (result.type === 'session') {
              return <SessionCard key={`session-${index}`} session={result.data} />;
            }
            return null;
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="search-results">
      <div className="search-results-empty">
        <p>{message}</p>
      </div>
    </div>
  );
};

export default SearchResults;
