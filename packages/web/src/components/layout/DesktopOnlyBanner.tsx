import "./DesktopOnlyBanner.css";

export function DesktopOnlyBanner() {
  return (
    <div className="desktop-banner" role="alert">
      <h2>请使用桌面端访问</h2>
      <p>xsagent 当前针对 1280px 及以上宽屏优化，请在桌面浏览器中打开。</p>
    </div>
  );
}
