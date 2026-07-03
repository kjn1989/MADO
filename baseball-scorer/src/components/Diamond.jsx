import React from 'react';
import { usePlayerName } from '../state/store.jsx';

// 走者ダイヤモンド: リアル風フィールド(芝＋土＋ファウルライン)の上に塁を配置。
// 塁タップで走者イベントシートを開く。クラス名(.base.b1等)はE2E互換のため維持。
export default function Diamond({ game, onBaseTap }) {
  const nameOf = usePlayerName();

  const label = (base) => {
    const r = game.runners[base];
    if (!r) return base === 1 ? '一塁' : base === 2 ? '二塁' : '三塁';
    return r.playerId ? nameOf(r.playerId) : '走者';
  };

  return (
    <div className="field-diamond">
      <div className="field-dirt fd" />
      <div className="field-line left" />
      <div className="field-line right" />
      {[2, 3, 1].map((b) => (
        <div
          key={b}
          className={`base b${b}${game.runners[b] ? ' occupied' : ''}`}
          onClick={() => onBaseTap?.(b)}
          role="button"
        >
          <span>{label(b)}</span>
        </div>
      ))}
      <div className="base home">
        <span>本塁</span>
      </div>
    </div>
  );
}
