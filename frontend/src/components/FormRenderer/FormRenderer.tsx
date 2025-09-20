import React from 'react';
import './formrenderer.css';

type Props = {
  envelope: any;
};

const safe = (v: any) => (v !== null && v !== undefined ? String(v) : '');

export default function FormRenderer({ envelope }: Props) {
  const type = envelope?.response?.type;
  const e = envelope?.ml_data?.entities || {};

  switch (type) {
    case 'company_search':
    case 'create_company_profile':
      return (
        <form className="th-form">
          <div className="th-form__row">
            <label>Название компании
              <input defaultValue={safe(e.name || e.company_name)} placeholder="Название" />
            </label>
            <label>ИНН
              <input defaultValue={safe(e.company_inn)} placeholder="ИНН" />
            </label>
            <label>ОГРН
              <input defaultValue={safe(e.company_ogrn)} placeholder="ОГРН" />
            </label>
          </div>
        </form>
      );

    case 'contract_search':
    case 'create_contract':
      return (
        <form className="th-form">
          <div className="th-form__row">
            <label>Номер контракта
              <input defaultValue={safe(e.contract_id)} placeholder="№ контракта" />
            </label>
            <label>Заказчик
              <input defaultValue={safe(e.customer_name)} placeholder="Организация" />
            </label>
          </div>
          <div className="th-form__row">
            <label>Поставщик
              <input defaultValue={safe(e.supplier_name)} placeholder="Поставщик" />
            </label>
            <label>Стоимость
              <input defaultValue={safe(e.contract_amount)} placeholder="₽" />
            </label>
            <label>Дата
              <input defaultValue={safe(e.contract_date)} placeholder="Дата" />
            </label>
          </div>
        </form>
      );

    case 'session_search':
    case 'create_session':
      return (
        <form className="th-form">
          <div className="th-form__row">
            <label>Название сессии
              <input defaultValue={safe(e.session_name)} placeholder="Название" />
            </label>
          </div>
          <div className="th-form__row">
            <label>Заказчик
              <input defaultValue={safe(e.customer_name)} placeholder="Организация" />
            </label>
            <label>Стоимость
              <input defaultValue={safe(e.session_amount)} placeholder="₽" />
            </label>
          </div>
          <div className="th-form__row">
            <label>Дата создания
              <input defaultValue={safe(e.session_created_date)} placeholder="Дата" />
            </label>
            <label>Дата завершения
              <input defaultValue={safe(e.session_completed_date)} placeholder="Дата" />
            </label>
          </div>
        </form>
      );

    case 'error':
      return <div className="th-error">Ошибка: {envelope.response?.data}</div>;

    default:
      return <div className="th-unknown">Неизвестный тип: {type}</div>;
  }
}
