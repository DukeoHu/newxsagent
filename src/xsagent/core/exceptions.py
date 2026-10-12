class XSAgentError(Exception):
    """Base application error."""


class ProjectNotFoundError(XSAgentError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project not found: {project_id}")
        self.project_id = project_id


class ProjectAlreadyExistsError(XSAgentError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project already exists: {project_id}")
        self.project_id = project_id


class BibleSectionNotFoundError(XSAgentError):
    def __init__(self, section: str) -> None:
        super().__init__(f"Invalid bible section: {section}")
        self.section = section


class FieldLockedError(XSAgentError):
    def __init__(self, field_path: str) -> None:
        super().__init__(f"Field is locked and cannot be modified: {field_path}")
        self.field_path = field_path


class ChapterNotFoundError(XSAgentError):
    def __init__(self, project_id: str, chapter_id: str) -> None:
        super().__init__(f"Chapter not found: {project_id}/{chapter_id}")
        self.project_id = project_id
        self.chapter_id = chapter_id


class ChapterAlreadyExistsError(XSAgentError):
    def __init__(self, chapter_id: str) -> None:
        super().__init__(f"Chapter already exists: {chapter_id}")
        self.chapter_id = chapter_id


class OutlineNotFoundError(XSAgentError):
    def __init__(self, resource: str) -> None:
        super().__init__(f"Outline resource not found: {resource}")
        self.resource = resource


class SnapshotNotFoundError(XSAgentError):
    def __init__(self, snapshot_id: str) -> None:
        super().__init__(f"Snapshot not found: {snapshot_id}")
        self.snapshot_id = snapshot_id

