import "./ForeshadowingBoard.css";

interface ForeshadowingBoardProps {
  setup: string[];
  progress: string[];
  payoff: string[];
}

function renderList(items: string[]) {
  if (items.length === 0) {
    return <p className="foreshadowing-board__empty">暂无内容</p>;
  }
  return items.map((item, index) => (
    <div key={`${item}-${index}`} className="foreshadowing-board__item">
      {item}
    </div>
  ));
}

export function ForeshadowingBoard({
  setup,
  progress,
  payoff,
}: ForeshadowingBoardProps) {
  return (
    <div className="foreshadowing-board">
      <section className="foreshadowing-board__column">
        <h4 className="foreshadowing-board__title">埋设</h4>
        {renderList(setup)}
      </section>
      <section className="foreshadowing-board__column">
        <h4 className="foreshadowing-board__title">推进</h4>
        {renderList(progress)}
      </section>
      <section className="foreshadowing-board__column">
        <h4 className="foreshadowing-board__title">回收</h4>
        {renderList(payoff)}
      </section>
    </div>
  );
}
