import { AppShell } from "../components/layout/AppShell";
import {
  Badge,
  Button,
  Card,
  Input,
  Label,
  Textarea,
} from "../components/primitives";
import "./ComponentPreviewPage.css";

export function ComponentPreviewPage() {
  return (
    <AppShell centered>
      <h1 className="page-title">组件预览</h1>
      <p className="page-subtitle">P4.1 设计系统基础组件</p>

      <section className="preview-section">
        <h2>Button</h2>
        <div className="preview-row">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
        <div className="preview-row">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </section>

      <section className="preview-section">
        <h2>Badge</h2>
        <div className="preview-row">
          <Badge>Default</Badge>
          <Badge variant="accent">Accent</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="danger">Danger</Badge>
        </div>
      </section>

      <section className="preview-section">
        <h2>Card</h2>
        <div className="preview-grid">
          <Card padding="sm">Small padding card</Card>
          <Card padding="md" interactive>
            Interactive card (hover me)
          </Card>
        </div>
      </section>

      <section className="preview-section">
        <h2>Form</h2>
        <Card padding="md" style={{ maxWidth: 400 }}>
          <div className="stack">
            <div>
              <Label htmlFor="preview-input" required>
                标题
              </Label>
              <Input id="preview-input" placeholder="输入标题…" />
            </div>
            <div>
              <Label htmlFor="preview-textarea">描述</Label>
              <Textarea id="preview-textarea" placeholder="输入描述…" rows={3} />
            </div>
            <Button fullWidth>提交</Button>
          </div>
        </Card>
      </section>
    </AppShell>
  );
}
