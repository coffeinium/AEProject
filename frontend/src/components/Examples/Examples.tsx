import React from 'react';
import './examples.css';

interface ExampleItem {
  type: string;
  title: string;
  example: string;
  description: string;
}

interface ExamplesProps {
  onExampleClick: (example: string) => void;
}

const examples: ExampleItem[] = [
  {
    type: 'create_contract',
    title: 'Создание контракта',
    example: 'Создай контракт поставка оборудования заказчик ООО Газпром ИНН 7736050003 сумма 500 тысяч категория оборудование закон 44-ФЗ',
    description: 'Создание нового контракта с указанием всех необходимых данных'
  },
  {
    type: 'create_ks',
    title: 'Создание котировочной сессии',
    example: 'Создай КС наименование канцелярские товары заказчик ООО Офис ИНН 7701234567 сумма 300 тысяч категория канцелярские закон 44-ФЗ',
    description: 'Создание котировочной сессии для проведения торгов'
  },
  {
    type: 'search_docs',
    title: 'Поиск документов',
    example: 'Найди документ айди 12345',
    description: 'Поиск документов по ID, номеру или другим параметрам'
  },
  {
    type: 'search_company',
    title: 'Поиск компаний',
    example: 'Найди компанию ООО Газпром',
    description: 'Поиск организаций по названию или ИНН'
  },
  {
    type: 'create_company_profile',
    title: 'Создание профиля компании',
    example: 'Создай профиль компании ООО Рога и Копыта ИНН 1234567890 БИК 044525225',
    description: 'Регистрация новой компании в системе'
  },
  {
    type: 'help',
    title: 'Справка и помощь',
    example: 'Помощь по созданию контракта',
    description: 'Получение справочной информации и инструкций'
  }
];

export default function Examples({ onExampleClick }: ExamplesProps) {
  return (
    <div className="examples">
      <h2 className="examples__title">Примеры запросов</h2>
      <div className="examples__grid">
        {examples.map((item) => (
          <div 
            key={item.type} 
            className="examples__card"
            onClick={() => onExampleClick(item.example)}
          >
            <div className="examples__card-header">
              <h3 className="examples__card-title">{item.title}</h3>
            </div>
            <div className="examples__card-content">
              <p className="examples__description">{item.description}</p>
              <div className="examples__example">
                <strong>Пример:</strong>
                <span className="examples__example-text">"{item.example}"</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
