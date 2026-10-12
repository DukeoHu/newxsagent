/** 长篇规模推导：章节数上限与分卷策略 */

/** 单次应用蓝图时的硬上限（约 500 万字 / 3000 字每章） */
export const MAX_PLANNING_CHAPTERS = 2000;

/** 超过此值显示性能提示，但不阻止应用 */
export const PLANNING_CHAPTERS_WARN = 500;

/** 每卷目标章数（网文常见 20–40 章/卷） */
export const CHAPTERS_PER_VOLUME_TARGET = 30;

/** 应用蓝图时每批并发请求数 */
export const SCALE_APPLY_BATCH_SIZE = 40;

export function inferScalePlan(targetWords: number, avgChapterWords: number) {
  const safeTargetWords = Math.max(10_000, Number(targetWords) || 10_000);
  const safeAvgChapterWords = Math.max(1_000, Number(avgChapterWords) || 1_000);
  const totalChapters = Math.max(
    1,
    Math.ceil(safeTargetWords / safeAvgChapterWords),
  );
  const volumeCount = Math.max(
    1,
    Math.ceil(totalChapters / CHAPTERS_PER_VOLUME_TARGET),
  );
  const chaptersPerVolume = Math.max(
    1,
    Math.ceil(totalChapters / volumeCount),
  );

  return {
    safeTargetWords,
    safeAvgChapterWords,
    totalChapters,
    volumeCount,
    chaptersPerVolume,
    exceedsHardLimit: totalChapters > MAX_PLANNING_CHAPTERS,
    showPerformanceWarning: totalChapters > PLANNING_CHAPTERS_WARN,
  };
}

export function chapterId(no: number) {
  return `ch_${String(no).padStart(3, "0")}`;
}

export function volumeId(index: number) {
  return `vol_${String(index + 1).padStart(2, "0")}`;
}
