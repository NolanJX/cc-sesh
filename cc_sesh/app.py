from __future__ import annotations

import os
from datetime import datetime, timezone

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, ListView, ListItem, RichLog, Static

from cc_sesh.models import SessionMeta
from cc_sesh.parser import load_messages
from cc_sesh.scanner import scan_sessions


def format_ts(ms: int | None) -> str:
    if ms is None:
        return ""
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M")


ROLE_COLORS = {
    "user": "cyan",
    "assistant": "blue",
    "tool": "magenta",
}


class SessionItem(ListItem):
    def __init__(self, session: SessionMeta) -> None:
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        title = self.session.title or self.session.session_id[:8]
        ts = format_ts(self.session.last_active_at or self.session.created_at)
        yield Static(title)
        yield Static(ts)


class ConfirmDeleteScreen(ModalScreen[bool]):
    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: thick $error;
        padding: 1 2;
        background: $surface;
    }
    #dialog-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #dialog-body {
        margin-bottom: 1;
    }
    #dialog-buttons {
        width: 100%;
        height: auto;
        align-horizontal: center;
        margin-top: 1;
    }
    """

    def __init__(self, session: SessionMeta) -> None:
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("! Delete Session", id="dialog-title")
            yield Label(
                f'Permanently delete "{self.session.title or self.session.session_id[:8]}"?\n'
                f"Session ID: {self.session.session_id[:16]}...\n\n"
                f"This action cannot be undone.",
                id="dialog-body",
            )
            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Delete", variant="error", id="delete")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "delete")


class SessionManagerApp(App):
    CSS = """
    #main {
        height: 1fr;
    }
    #list-panel {
        width: 32;
        height: 1fr;
        border-right: solid $border;
    }
    #list-header {
        padding: 0 1;
        height: 1;
        text-style: bold;
    }
    #session-list {
        height: 1fr;
    }
    #detail-panel {
        width: 1fr;
        height: 1fr;
    }
    #detail-header {
        padding: 0 1;
        height: auto;
        border-bottom: solid $border;
    }
    #detail-title {
        text-style: bold;
    }
    #detail-meta {
        color: $text-muted;
    }
    #conversation {
        height: 1fr;
    }
    #empty-detail {
        height: 1fr;
        padding: 2;
        content-align: center middle;
        color: $text-muted;
    }
    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("j,down", "list_down", "Down", show=False),
        Binding("k,up", "list_up", "Up", show=False),
        Binding("tab", "switch_panel", "Switch Panel"),
        Binding("d", "delete_session", "Delete"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="list-panel"):
                yield Label("Sessions", id="list-header")
                yield ListView(id="session-list")
            with Vertical(id="detail-panel"):
                yield Static("Select a session to view", id="empty-detail")
                yield Static(id="detail-header", classes="hidden")
                yield RichLog(id="conversation", markup=True, wrap=True, classes="hidden")
        yield Footer()

    def on_mount(self) -> None:
        sessions = scan_sessions()
        list_view = self.query_one("#session-list", ListView)
        for session in sessions:
            list_view.append(SessionItem(session))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        item: SessionItem = event.item  # type: ignore[assignment]
        self._show_session(item.session)

    def _show_session(self, session: SessionMeta) -> None:
        empty = self.query_one("#empty-detail", Static)
        header = self.query_one("#detail-header", Static)
        log = self.query_one("#conversation", RichLog)

        empty.add_class("hidden")
        header.remove_class("hidden")
        log.remove_class("hidden")

        title = session.title or session.session_id[:8]
        ts = format_ts(session.last_active_at or session.created_at)
        meta_parts = [ts]
        if session.project_dir:
            meta_parts.append(session.project_dir)
        header.update(f"[bold]{title}[/bold]\n[dim]{' | '.join(meta_parts)}[/dim]")

        log.clear()
        messages = load_messages(session.source_path)
        for msg in messages:
            color = ROLE_COLORS.get(msg.role, "white")
            ts_str = format_ts(msg.ts) if msg.ts else ""
            label = msg.role.capitalize()
            separator = f"── [{color} bold]{label}[/] {'─' * 4}"
            if ts_str:
                separator += f" {ts_str} "
            separator += "─" * 10
            log.write(separator)
            log.write(msg.content)
            log.write("")
        log.scroll_home(animate=False)

    def action_list_down(self) -> None:
        self.query_one("#session-list", ListView).action_cursor_down()

    def action_list_up(self) -> None:
        self.query_one("#session-list", ListView).action_cursor_up()

    def action_switch_panel(self) -> None:
        list_view = self.query_one("#session-list", ListView)
        conversation = self.query_one("#conversation", RichLog)
        if list_view.has_focus:
            conversation.focus()
        else:
            list_view.focus()

    def action_delete_session(self) -> None:
        list_view = self.query_one("#session-list", ListView)
        item = list_view.highlighted_child
        if item is None or not isinstance(item, SessionItem):
            return
        self.push_screen(
            ConfirmDeleteScreen(item.session),
            callback=self._handle_delete_result,
        )

    def _handle_delete_result(self, confirmed: bool) -> None:
        if not confirmed:
            return
        list_view = self.query_one("#session-list", ListView)
        item = list_view.highlighted_child
        if item is None or not isinstance(item, SessionItem):
            return
        os.remove(item.session.source_path)
        list_view.remove_items([list_view.index])
        if list_view.item_count == 0:
            self.query_one("#detail-header").add_class("hidden")
            self.query_one("#conversation").add_class("hidden")
            self.query_one("#conversation", RichLog).clear()
            self.query_one("#empty-detail").remove_class("hidden")


def main() -> None:
    app = SessionManagerApp()
    app.run()


if __name__ == "__main__":
    main()
