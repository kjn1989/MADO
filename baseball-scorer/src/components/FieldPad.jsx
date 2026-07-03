import React from 'react';
import { DIRECTIONS } from '../lib/model.js';

// 打球方向の選択を野球フィールド型のビジュアルで行うパッド
// 外野の芝・内野の土・ファウルラインを描き、守備位置に対応する場所にボタンを配置する。
// クラス名 .dir-pad を維持して既存のE2Eセレクタとも互換。
const POSITIONS = {
  LF: { left: '18%', top: '28%' },
  CF: { left: '50%', top: '17%' },
  RF: { left: '82%', top: '28%' },
  '3B': { left: '21%', top: '62%' },
  SS: { left: '36%', top: '48%' },
  '2B': { left: '64%', top: '48%' },
  '1B': { left: '79%', top: '62%' },
  P: { left: '50%', top: '68%' },
  C: { left: '50%', top: '89%' },
};

export default function FieldPad({ value, onChange }) {
  return (
    <div className="dir-pad field-pad">
      {/* 内野の土(ひし形) と ファウルライン */}
      <div className="field-dirt" />
      <div className="field-line left" />
      <div className="field-line right" />
      {Object.entries(DIRECTIONS).map(([key, label]) => (
        <button
          key={key}
          className={`field-pos${value === key ? ' sel' : ''}`}
          style={POSITIONS[key]}
          onClick={() => onChange(key)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
