// ============================================================
// スタッツ集計エンジン
// games(対象試合の配列) から選手別に集計する。
// 「試合単位/シーズン通算」の切替は呼び出し側が games を絞って渡す。
// ============================================================
import { RESULTS, formatIP } from './model.js';

// ---- 打者: 足し算カウントスタッツ(タイトル系) ----
export function aggregateBatting(games) {
  const map = {}; // playerId -> stats
  const get = (pid) => {
    if (!map[pid]) {
      map[pid] = {
        playerId: pid,
        pa: 0, ab: 0, h: 0, single: 0, double: 0, triple: 0, hr: 0,
        rbi: 0, runs: 0, sb: 0, bb: 0, hbp: 0, so: 0,
        sacBunt: 0, sacFly: 0, interference: 0, error: 0, tb: 0,
        // 詳細メトリクス用
        rispAB: 0, rispH: 0,
        advChance: 0, advSuccess: 0,
        totalPitches: 0,
        clutch: 0,
        firstPitchSwings: 0, firstPitchHits: 0,
      };
    }
    return map[pid];
  };

  for (const g of games) {
    for (const ab of g.atBats || []) {
      if (!ab.result) continue; // 未確定打席は除外
      const s = get(ab.playerId);
      const def = RESULTS[ab.result];
      if (!def) continue;

      s.pa += 1;
      if (def.ab) s.ab += 1;
      if (def.hit) {
        s.h += 1;
        s.tb += def.bases;
        if (ab.result === 'single') s.single += 1;
        if (ab.result === 'double') s.double += 1;
        if (ab.result === 'triple') s.triple += 1;
        if (ab.result === 'hr') s.hr += 1;
      }
      if (ab.result === 'bb') s.bb += 1;
      if (ab.result === 'hbp') s.hbp += 1;
      if (ab.result === 'so') s.so += 1;
      if (ab.result === 'sacBunt') s.sacBunt += 1;
      if (ab.result === 'sacFly') s.sacFly += 1;
      if (ab.result === 'interference') s.interference += 1;
      if (ab.result === 'error') s.error += 1;
      s.rbi += ab.rbi || 0;

      // RISP: 打席開始時に走者二塁or三塁
      const snap = ab.snapshot || {};
      const risp = snap.runners && (snap.runners[2] || snap.runners[3]);
      if (risp && def.ab) {
        s.rispAB += 1;
        if (def.hit) s.rispH += 1;
      }

      // 進塁打: 走者あり凡打(三振除く)が対象
      if (ab.advSuccess !== null && ab.advSuccess !== undefined) {
        s.advChance += 1;
        if (ab.advSuccess) s.advSuccess += 1;
      }

      // PPA用
      s.totalPitches += ab.pitchCount || 0;

      // クラッチ
      if (ab.clutch) s.clutch += 1;

      // 初球打ち
      if (ab.firstPitch === 'inplay') {
        s.firstPitchSwings += 1;
        if (ab.firstPitchHit) s.firstPitchHits += 1;
      }
    }
    // 得点・盗塁は PlayLog から拾う(打席レコード外の事象のため)
    for (const log of g.playLogs || []) {
      if (log.kind === 'run' && log.payload?.playerId) get(log.payload.playerId).runs += 1;
      if (log.kind === 'sb' && log.payload?.playerId) get(log.payload.playerId).sb += 1;
    }
  }
  return map;
}

// ---- 投手: カウントスタッツ ----
export function aggregatePitching(games) {
  const map = {}; // playerId -> stats
  const get = (pid) => {
    if (!map[pid]) {
      map[pid] = {
        playerId: pid,
        outsRecorded: 0, runs: 0, earnedRuns: 0, hitsAllowed: 0,
        walks: 0, hitByPitch: 0, strikeouts: 0, pitches: 0,
        wins: 0, saves: 0, games: 0,
      };
    }
    return map[pid];
  };
  for (const g of games) {
    for (const pr of g.pitchingRecords || []) {
      const s = get(pr.playerId);
      s.games += 1;
      s.outsRecorded += pr.outsRecorded || 0;
      s.runs += pr.runs || 0;
      s.earnedRuns += pr.earnedRuns || 0;
      s.hitsAllowed += pr.hitsAllowed || 0;
      s.walks += pr.walks || 0;
      s.hitByPitch += pr.hitByPitch || 0;
      s.strikeouts += pr.strikeouts || 0;
      s.pitches += pr.pitches || 0;
      if (pr.win) s.wins += 1;
      if (pr.save) s.saves += 1;
    }
  }
  return map;
}

// ---- タイトル系ランキング(同数は同順位で全員返す) ----
export const BATTING_TITLES = [
  { key: 'h', label: '安打', crown: '安打王' },
  { key: 'rbi', label: '打点', crown: '打点王' },
  { key: 'runs', label: '得点', crown: '得点王' },
  { key: 'hr', label: '本塁打', crown: '本塁打王' },
  { key: 'double', label: '二塁打', crown: '二塁打王' },
  { key: 'triple', label: '三塁打', crown: '三塁打王' },
  { key: 'sb', label: '盗塁', crown: '盗塁王' },
  { key: 'bbhbp', label: '四死球', crown: '選球眼王' },
  { key: 'tb', label: '塁打', crown: '塁打王' },
];

export const PITCHING_TITLES = [
  { key: 'wins', label: '勝利', crown: '最多勝' },
  { key: 'strikeouts', label: '奪三振', crown: '奪三振王' },
  { key: 'saves', label: 'セーブ', crown: 'セーブ王' },
  { key: 'ip', label: '投球回', crown: 'イニング王' },
];

// stats map からタイトルのトップ(同数同順位)を返す
export function titleLeaders(statsMap, key) {
  const rows = Object.values(statsMap).map((s) => {
    let v;
    if (key === 'bbhbp') v = s.bb + s.hbp;
    else if (key === 'ip') v = s.outsRecorded; // 内部はアウト数で比較
    else v = s[key] ?? 0;
    return { playerId: s.playerId, value: v };
  });
  const max = Math.max(0, ...rows.map((r) => r.value));
  if (max <= 0) return { leaders: [], value: 0, display: '0' };
  const leaders = rows.filter((r) => r.value === max).map((r) => r.playerId);
  const display = key === 'ip' ? formatIP(max) : String(max);
  return { leaders, value: max, display };
}

// 値の降順で順位付け(同数同順位)したランキング行を返す
export function rankRows(rows) {
  const sorted = [...rows].sort((a, b) => b.sortValue - a.sortValue);
  let rank = 0;
  let prev = null;
  return sorted.map((r, i) => {
    if (prev === null || r.sortValue !== prev) rank = i + 1;
    prev = r.sortValue;
    return { ...r, rank };
  });
}
