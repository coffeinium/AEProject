import React from 'react';
import './help.css';

interface HelpSection {
  topic: string;
  description: string;
  examples?: string[];
  commands?: string[];
}

interface HelpProps {
  type: string;
  status: string;
  message: string;
  helpSections?: HelpSection[];
}

const HelpIcon: React.FC = () => (
  <svg className="help-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 17h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const LightBulbIcon: React.FC = () => (
  <svg className="lightbulb-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M9 21h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 3a6 6 0 0 0-6 6c0 2 1 3 1 3h10s1-1 1-3a6 6 0 0 0-6-6z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const BookIcon: React.FC = () => (
  <svg className="book-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const HelpSection: React.FC<{ section: HelpSection }> = ({ section }) => (
  <div className="help-section">
    <div className="help-section-header">
      <BookIcon />
      <h3 className="help-section-title">{section.topic}</h3>
    </div>
    
    <p className="help-section-description">{section.description}</p>
    
    {section.examples && section.examples.length > 0 && (
      <div className="help-examples">
        <div className="help-examples-header">
          <LightBulbIcon />
          <h4 className="help-examples-title">Примеры:</h4>
        </div>
        <ul className="help-examples-list">
          {section.examples.map((example, index) => (
            <li key={index} className="help-example-item">
              <code className="help-example-code">"{example}"</code>
            </li>
          ))}
        </ul>
      </div>
    )}
    
    {section.commands && section.commands.length > 0 && (
      <div className="help-commands">
        <h4 className="help-commands-title">Доступные команды:</h4>
        <ul className="help-commands-list">
          {section.commands.map((command, index) => (
            <li key={index} className="help-command-item">
              <span className="help-command-bullet">▶</span>
              {command}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const Help: React.FC<HelpProps> = ({
  type,
  status,
  message,
  helpSections = []
}) => {
  if (status !== 'success' || helpSections.length === 0) {
    return (
      <div className="help-container">
        <div className="help-empty">
          <div className="help-empty-icon">
            <HelpIcon />
          </div>
          <h3 className="help-empty-title">Справка недоступна</h3>
          <p className="help-empty-message">
            {message || 'Не удалось найти справочную информацию по вашему запросу'}
          </p>
          
          <div className="help-general-tips">
            <h4 className="help-general-tips-title">Общие команды:</h4>
            <ul className="help-general-tips-list">
              <li>• Создание контрактов: "создай контракт на..."</li>
              <li>• Создание КС: "создай КС на..."</li>
              <li>• Поиск документов: "найди контракты..."</li>
              <li>• Поиск компаний: "найди компанию..."</li>
              <li>• Создание профиля: "создай профиль компании..."</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="help-container">
      <div className="help-header">
        <div className="help-header-icon">
          <HelpIcon />
        </div>
        <div className="help-header-content">
          <h2 className="help-title">Справка и помощь</h2>
          <p className="help-message">{message}</p>
        </div>
      </div>
      
      <div className="help-sections">
        {helpSections.map((section, index) => (
          <HelpSection key={index} section={section} />
        ))}
      </div>
      
      <div className="help-footer">
        <div className="help-footer-content">
          <h4 className="help-footer-title">Нужна дополнительная помощь?</h4>
          <p className="help-footer-text">
            Попробуйте следующие запросы:
          </p>
          <div className="help-footer-examples">
            <code>"помощь по созданию контракта"</code>
            <code>"как искать документы"</code>
            <code>"помощь по КС"</code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Help;
