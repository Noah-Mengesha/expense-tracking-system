import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api } from './api.js';
import './styles.css';

const h = React.createElement;
const emptyForm = { description: '', amount: '', expense_date: new Date().toISOString().slice(0, 10), category_id: '', notes: '' };

function App() {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [summary, setSummary] = useState({ expense_count: 0, total_spending: 0, average_expense: 0, by_category: [] });
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [filters, setFilters] = useState({ category_id: '', start_date: '', end_date: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function refresh(activeFilters = filters) {
    setError('');
    try {
      const [expenseData, summaryData] = await Promise.all([api.getExpenses(activeFilters), api.getSummary()]);
      setExpenses(expenseData);
      setSummary(summaryData);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const categoryData = await api.getCategories();
        setCategories(categoryData);
        setForm((current) => ({ ...current, category_id: current.category_id || String(categoryData[0]?.id || '') }));
        await refresh();
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const currency = useMemo(() => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }), []);

  function changeForm(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitForm(event) {
    event.preventDefault();
    setError('');
    const payload = { ...form, amount: Number(form.amount), category_id: Number(form.category_id) };
    try {
      if (editingId) await api.updateExpense(editingId, payload);
      else await api.createExpense(payload);
      setEditingId(null);
      setForm({ ...emptyForm, category_id: String(categories[0]?.id || '') });
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  function beginEdit(expense) {
    setEditingId(expense.id);
    setForm({
      description: expense.description,
      amount: String(expense.amount),
      expense_date: expense.expense_date,
      category_id: String(expense.category_id),
      notes: expense.notes || '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function removeExpense(expense) {
    if (!window.confirm(`Delete “${expense.description}”?`)) return;
    try {
      await api.deleteExpense(expense.id);
      if (editingId === expense.id) cancelEdit();
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  function cancelEdit() {
    setEditingId(null);
    setForm({ ...emptyForm, category_id: String(categories[0]?.id || '') });
  }

  async function applyFilters(event) {
    event.preventDefault();
    await refresh(filters);
  }

  async function clearFilters() {
    const blank = { category_id: '', start_date: '', end_date: '' };
    setFilters(blank);
    await refresh(blank);
  }

  return h('div', { className: 'app-shell' },
    h('header', { className: 'hero' },
      h('div', null,
        h('p', { className: 'eyebrow' }, 'PERSONAL FINANCE'),
        h('h1', null, 'Expense Tracker'),
        h('p', { className: 'subtitle' }, 'Record transactions, filter spending, and review category totals in one place.')
      )
    ),

    error && h('div', { className: 'alert', role: 'alert' }, error),

    h('section', { className: 'summary-grid', 'aria-label': 'Spending summary' },
      metric('Total spending', currency.format(summary.total_spending)),
      metric('Expenses', String(summary.expense_count)),
      metric('Average expense', currency.format(summary.average_expense))
    ),

    h('main', { className: 'content-grid' },
      h('section', { className: 'card' },
        h('h2', null, editingId ? 'Edit expense' : 'Add expense'),
        h('form', { onSubmit: submitForm, className: 'expense-form' },
          field('Description', 'description', h('input', { name: 'description', value: form.description, onChange: changeForm, maxLength: 120, required: true, placeholder: 'e.g., Groceries' })),
          h('div', { className: 'two-column' },
            field('Amount', 'amount', h('input', { name: 'amount', type: 'number', min: '0.01', step: '0.01', value: form.amount, onChange: changeForm, required: true, placeholder: '0.00' })),
            field('Date', 'expense_date', h('input', { name: 'expense_date', type: 'date', value: form.expense_date, onChange: changeForm, required: true }))
          ),
          field('Category', 'category_id', h('select', { name: 'category_id', value: form.category_id, onChange: changeForm, required: true },
            categories.map((category) => h('option', { key: category.id, value: category.id }, category.name))
          )),
          field('Notes', 'notes', h('textarea', { name: 'notes', value: form.notes, onChange: changeForm, maxLength: 500, rows: 3, placeholder: 'Optional note' })),
          h('div', { className: 'button-row' },
            h('button', { className: 'primary', type: 'submit' }, editingId ? 'Save changes' : 'Add expense'),
            editingId && h('button', { className: 'secondary', type: 'button', onClick: cancelEdit }, 'Cancel')
          )
        )
      ),

      h('section', { className: 'card' },
        h('div', { className: 'section-heading' }, h('h2', null, 'Transactions'), h('span', null, `${expenses.length} shown`)),
        h('form', { className: 'filters', onSubmit: applyFilters },
          h('select', { value: filters.category_id, onChange: (e) => setFilters({ ...filters, category_id: e.target.value }), 'aria-label': 'Filter by category' },
            h('option', { value: '' }, 'All categories'),
            categories.map((category) => h('option', { key: category.id, value: category.id }, category.name))
          ),
          h('input', { type: 'date', value: filters.start_date, onChange: (e) => setFilters({ ...filters, start_date: e.target.value }), 'aria-label': 'Start date' }),
          h('input', { type: 'date', value: filters.end_date, onChange: (e) => setFilters({ ...filters, end_date: e.target.value }), 'aria-label': 'End date' }),
          h('button', { className: 'secondary', type: 'submit' }, 'Filter'),
          h('button', { className: 'text-button', type: 'button', onClick: clearFilters }, 'Clear')
        ),
        loading ? h('p', { className: 'muted' }, 'Loading expenses…') :
          expenses.length === 0 ? h('div', { className: 'empty-state' }, h('p', null, 'No expenses match the current filters.')) :
            h('div', { className: 'table-wrap' },
              h('table', null,
                h('thead', null, h('tr', null,
                  h('th', null, 'Date'), h('th', null, 'Description'), h('th', null, 'Category'), h('th', null, 'Amount'), h('th', null, 'Actions')
                )),
                h('tbody', null, expenses.map((expense) => h('tr', { key: expense.id },
                  h('td', null, expense.expense_date),
                  h('td', null, h('strong', null, expense.description), expense.notes && h('span', { className: 'note' }, expense.notes)),
                  h('td', null, h('span', { className: 'badge' }, expense.category)),
                  h('td', { className: 'amount' }, currency.format(expense.amount)),
                  h('td', null,
                    h('div', { className: 'row-actions' },
                      h('button', { className: 'text-button', type: 'button', onClick: () => beginEdit(expense) }, 'Edit'),
                      h('button', { className: 'danger-link', type: 'button', onClick: () => removeExpense(expense) }, 'Delete')
                    )
                  )
                )))
              )
            )
      )
    ),

    h('section', { className: 'card category-card' },
      h('div', { className: 'section-heading' }, h('h2', null, 'Spending by category'), h('span', null, 'All recorded expenses')),
      summary.by_category.length === 0 ? h('p', { className: 'muted' }, 'Add an expense to see category totals.') :
        h('div', { className: 'category-list' }, summary.by_category.map((item) => h('div', { className: 'category-row', key: item.category },
          h('span', null, item.category), h('strong', null, currency.format(item.total))
        )))
    )
  );
}

function metric(label, value) {
  return h('article', { className: 'metric-card' }, h('span', null, label), h('strong', null, value));
}

function field(label, name, control) {
  return h('label', { className: 'field', htmlFor: name }, h('span', null, label), React.cloneElement(control, { id: name }));
}

createRoot(document.getElementById('root')).render(h(React.StrictMode, null, h(App)));
