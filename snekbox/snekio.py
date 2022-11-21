"""I/O Operations for sending / receiving files from the sandbox."""
from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T", str, bytes)


class AttachmentError(ValueError):
    """Raised when an attachment is invalid."""


class ParsingError(AttachmentError):
    """Raised when an incoming file cannot be parsed."""


class IllegalPathError(AttachmentError):
    """Raised when an attachment has an illegal path."""


@dataclass
class FileAttachment(Generic[T]):
    """A file attachment."""

    path: str
    content: T

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> FileAttachment[bytes]:
        """Convert a dict to an attachment."""
        name = data["name"]
        path = Path(name)
        parts = path.parts

        if path.is_absolute() or set(parts[0]) & {"\\", "/"}:
            raise IllegalPathError(f"File path '{name}' must be relative")

        if any(set(part) == {"."} for part in parts):
            raise IllegalPathError(f"File path '{name}' may not use traversal ('..')")

        content = b64decode(data.get("content", ""))
        return cls(name, content)

    @classmethod
    def from_path(cls, file: Path) -> FileAttachment[bytes]:
        """Create an attachment from a file path."""
        return cls(file.name, file.read_bytes())

    @property
    def size(self) -> int:
        """Size of the attachment."""
        return len(self.content)

    def as_bytes(self) -> bytes:
        """Return the attachment as bytes."""
        if isinstance(self.content, bytes):
            return self.content
        return self.content.encode("utf-8")

    def save_to(self, directory: Path | str) -> None:
        """Save the attachment to a path directory."""
        file = Path(directory, self.path)
        # Create directories if they don't exist
        file.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(self.content, str):
            file.write_text(self.content, encoding="utf-8")
        else:
            file.write_bytes(self.content)

    def to_dict(self) -> dict[str, str]:
        """Convert the attachment to a dict."""
        content = b64encode(self.as_bytes()).decode("ascii")
        return {
            "path": self.path,
            "size": self.size,
            "content": content,
        }
