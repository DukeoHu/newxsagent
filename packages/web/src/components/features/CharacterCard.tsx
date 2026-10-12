import { Badge, Card } from "../primitives";
import type { CharacterItem } from "../../api/types";
import "./CharacterCard.css";

interface CharacterCardProps {
  character: CharacterItem;
}

export function CharacterCard({ character }: CharacterCardProps) {
  const name = String(character.name ?? "未命名角色");
  const role = character.role ? String(character.role) : "未定义";
  const description = character.description
    ? String(character.description)
    : "暂无角色描述。";

  return (
    <Card padding="md">
      <h3 className="character-card__name">{name}</h3>
      <div className="character-card__meta">
        <Badge variant="accent">{role}</Badge>
      </div>
      <p className="character-card__description">{description}</p>
      <div className="character-card__grid">
        <div className="character-card__field">
          <strong>目标：</strong>
          {String(character.goal ?? "未填写")}
        </div>
        <div className="character-card__field">
          <strong>成长线：</strong>
          {String(character.arc ?? "未填写")}
        </div>
      </div>
    </Card>
  );
}
