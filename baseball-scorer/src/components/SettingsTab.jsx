import React, { useState } from 'react';
import { useStore } from '../state/store.jsx';

export default function SettingsTab() {
  const { state, dispatch } = useStore();
  const [newName, setNewName] = useState('');
  const [newNumber, setNewNumber] = useState('');

  const addPlayer = () => {
    if (!newName.trim()) return;
    dispatch({ type: 'ADD_PLAYER', name: newName.trim(), number: newNumber.trim() });
    setNewName('');
    setNewNumber('');
  };

  return (
    <div>
      <div className="card">
        <h2>チーム設定</h2>
        <label className="small dim">チーム名</label>
        <input
          value={state.settings.teamName}
          onChange={(e) => dispatch({ type: 'UPDATE_SETTINGS', patch: { teamName: e.target.value } })}
          placeholder="マイチーム"
        />
      </div>

      <div className="card">
        <h2>選手登録 ({state.players.length}人)</h2>
        <div className="flex">
          <input className="grow" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="選手名" />
          <input style={{ width: 70 }} value={newNumber} onChange={(e) => setNewNumber(e.target.value)} placeholder="背番号" inputMode="numeric" />
          <button className="primary" onClick={addPlayer}>追加</button>
        </div>
        <div className="mt12">
          {state.players.map((p) => (
            <div className="row" key={p.id}>
              <span className="pill">{p.number || '-'}</span>
              <span className="grow">{p.name}</span>
              <button className="small danger ghost" onClick={() => dispatch({ type: 'DELETE_PLAYER', id: p.id })}>削除</button>
            </div>
          ))}
          {state.players.length === 0 && <div className="dim small mt8">選手が未登録です。デモデータでも試せます。</div>}
        </div>
      </div>

      <div className="card">
        <h2>デモデータ</h2>
        <p className="small dim" style={{ marginBottom: 10 }}>
          ダミーの選手12人と3試合分の記録を投入して、ランキング表示を確認できます。
        </p>
        {state.demoLoaded ? (
          <button className="danger" onClick={() => dispatch({ type: 'CLEAR_DEMO' })}>デモデータを削除</button>
        ) : (
          <button className="primary" onClick={() => dispatch({ type: 'LOAD_DEMO' })}>デモデータを投入</button>
        )}
      </div>

      <div className="card">
        <h2>音声入力の設定</h2>
        <p className="small dim" style={{ marginBottom: 10 }}>
          音声解釈はオフラインのルールエンジンで動作します。曖昧な発話の解釈精度を上げたい場合のみ、
          外部LLM API(Anthropic)を任意で連携できます(信頼度が低いときだけ呼び出し)。
        </p>
        <div className="flex">
          <span className="grow small">LLM解釈を有効にする</span>
          <button
            className={`small ${state.settings.useLLM ? 'primary' : ''}`}
            onClick={() => dispatch({ type: 'UPDATE_SETTINGS', patch: { useLLM: !state.settings.useLLM } })}
          >
            {state.settings.useLLM ? 'ON' : 'OFF'}
          </button>
        </div>
        {state.settings.useLLM && (
          <div className="mt8">
            <label className="small dim">Anthropic APIキー (sk-ant-...)</label>
            <input
              type="password"
              value={state.settings.anthropicApiKey}
              onChange={(e) => dispatch({ type: 'UPDATE_SETTINGS', patch: { anthropicApiKey: e.target.value } })}
              placeholder="未入力の場合はオフラインエンジンのみ"
            />
            <p className="small dim mt8">⚠️ キーはこの端末のブラウザ内にのみ保存されます。</p>
          </div>
        )}
      </div>

      <div className="card">
        <h2>データ管理</h2>
        <p className="small dim">
          データはこの端末のブラウザ内(localStorage)に自動保存されます。
          クラウド共有・CSV出力は後の段階で追加されます。
        </p>
      </div>
    </div>
  );
}
