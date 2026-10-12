import { NavLink, Link } from "react-router-dom";
import {
  BookOpen,
  FileText,
  LayoutDashboard,
  Map,
  Gauge,
  Network,
  WandSparkles,
  Sparkles,
  PenLine,
  Settings,
  Shield,
  ScrollText,
} from "lucide-react";
import "./SideNav.css";

const ICON_PROPS = { size: 18, strokeWidth: 1.5 };

interface SideNavProps {
  projectId?: string;
  projectTitle?: string;
  onboardingComplete?: boolean;
}

export function SideNav({
  projectId,
  projectTitle,
  onboardingComplete = false,
}: SideNavProps) {
  const base = projectId ? `/projects/${projectId}` : null;

  return (
    <nav className="side-nav" aria-label="主导航">
      <Link to="/" className="side-nav__brand">
        <div className="side-nav__logo">X</div>
        <span className="side-nav__title">xsagent</span>
      </Link>

      {projectId && projectTitle && (
        <div className="side-nav__project">
          <div className="side-nav__project-label">当前项目</div>
          <div className="side-nav__project-name">{projectTitle}</div>
        </div>
      )}

      <div className="side-nav__links">
        {base ? (
          <>
            <NavLink
              to={base}
              end
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <LayoutDashboard {...ICON_PROPS} />
              概览
            </NavLink>
            <NavLink
              to={`${base}/write`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <PenLine {...ICON_PROPS} />
              写作
            </NavLink>
            <NavLink
              to={`${base}/planning`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <Map {...ICON_PROPS} />
              规划
            </NavLink>
            <NavLink
              to={`${base}/bible`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <BookOpen {...ICON_PROPS} />
              设定集
            </NavLink>
            <NavLink
              to={`${base}/onboarding`}
              className={({ isActive }) =>
                [
                  "side-nav__link",
                  isActive ? "side-nav__link--active" : "",
                  onboardingComplete ? "side-nav__link--done" : "",
                ]
                  .filter(Boolean)
                  .join(" ")
              }
            >
              <Sparkles {...ICON_PROPS} />
              <span className="side-nav__link-text">引导</span>
              {onboardingComplete && (
                <span className="side-nav__link-badge">完成</span>
              )}
            </NavLink>
            <NavLink
              to={`${base}/chapters`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <FileText {...ICON_PROPS} />
              章节
            </NavLink>
            <NavLink
              to={`${base}/supervision`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <Shield {...ICON_PROPS} />
              监督
            </NavLink>
            <NavLink
              to={`${base}/llm-logs`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <ScrollText {...ICON_PROPS} />
              LLM 日志
            </NavLink>
            <NavLink
              to={`${base}/quality`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <Gauge {...ICON_PROPS} />
              质量
            </NavLink>
            <NavLink
              to={`${base}/explore`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <WandSparkles {...ICON_PROPS} />
              探索
            </NavLink>
            <NavLink
              to={`${base}/knowledge`}
              className={({ isActive }) =>
                `side-nav__link${isActive ? " side-nav__link--active" : ""}`
              }
            >
              <Network {...ICON_PROPS} />
              图谱
            </NavLink>
          </>
        ) : (
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `side-nav__link${isActive ? " side-nav__link--active" : ""}`
            }
          >
            <LayoutDashboard {...ICON_PROPS} />
            项目列表
          </NavLink>
        )}
      </div>

      <div className="side-nav__footer">
        <Link to="/settings/llm" className="side-nav__footer-link">
          <Settings size={14} strokeWidth={1.5} />
          LLM 配置
        </Link>
        <Link to="/dev/components" className="side-nav__footer-link">
          <Settings size={14} strokeWidth={1.5} />
          组件预览
        </Link>
      </div>
    </nav>
  );
}
