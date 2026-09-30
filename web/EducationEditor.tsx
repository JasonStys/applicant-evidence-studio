// Purpose: explicit, editable transfer/degree chronology; it never infers credentials or ranking features.
// Index: Education@3, EducationEditor@6, records@7, onChange@8, records@11, changes@14, index@14, update@14, position@15, record@15, index@23, record@23, event@31, event@39, event@46, status@48, event@61, event@69, _@74, position@74
import type { Education } from './types';

/** Edit education facts through clear fields; all changes still need an explicit parent save. */
export default function EducationEditor({
  records,
  onChange,
}: {
  records: Education[];
  onChange: (records: Education[]) => void;
}) {
  /** Replace one record without mutating source state. */
  function update(index: number, changes: Partial<Education>) {
    onChange(records.map((record, position) => (position === index ? { ...record, ...changes } : record)));
  }
  return (
    <div>
      <p>
        Enter only explicit facts. A transfer is neither a degree nor a failure. Unknown outcomes stay
        unclear.
      </p>
      {records.map((record, index) => (
        <article className="evidence" key={index}>
          <div className="form-grid">
            <label>
              Institution {index + 1}
              <input
                maxLength={240}
                value={record.institution}
                onChange={(event) => update(index, { institution: event.target.value })}
              />
            </label>
            <label>
              Program / major {index + 1}
              <input
                maxLength={240}
                value={record.program}
                onChange={(event) => update(index, { program: event.target.value })}
              />
            </label>
            <label>
              Education outcome {index + 1}
              <select
                value={record.status}
                onChange={(event) => update(index, { status: event.target.value as Education['status'] })}
              >
                {['unclear', 'transferred', 'in_progress', 'coursework_only', 'completed'].map((status) => (
                  <option key={status} value={status}>
                    {status.replaceAll('_', ' ')}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Transfer destination {index + 1}
            <input
              maxLength={240}
              value={record.transferred_to}
              onChange={(event) => update(index, { transferred_to: event.target.value })}
            />
          </label>
          <label>
            Chronology / major change / degree notes {index + 1}
            <textarea
              maxLength={1200}
              value={record.notes}
              onChange={(event) => update(index, { notes: event.target.value })}
            />
          </label>
          <button
            className="secondary"
            onClick={() => onChange(records.filter((_, position) => position !== index))}
          >
            Remove unsaved education row {index + 1}
          </button>
        </article>
      ))}
      <button
        className="secondary"
        disabled={records.length >= 20}
        onClick={() =>
          onChange([
            ...records,
            { institution: '', program: '', status: 'unclear', transferred_to: '', notes: '' },
          ])
        }
      >
        Add education / transfer record
      </button>
    </div>
  );
}
