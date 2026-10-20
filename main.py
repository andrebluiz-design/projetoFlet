"""
To-Do App evoluído em Flet + SQLite
===================================
Recursos:
  - Persistência local com sqlite3 (criar, editar, concluir, apagar)
  - Prioridade (Baixa/Média/Alta) e Categoria por tarefa
  - Busca em tempo real (nome ou categoria)
  - Abas de filtro (Todas / Pendentes / Concluídas)
  - Modo escuro/claro no cabeçalho
  - Rodapé com contador de pendentes e botão "Limpar concluídas"

Requisitos:  pip install -U flet      (Flet 1.x, sintaxe @ft.control)
Executar:    flet run main.py
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import field
from pathlib import Path
from typing import Callable

import flet as ft

# ----------------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------------
DB_PATH = Path(__file__).with_name("todo.db")

PRIORITIES = ["Baixa", "Média", "Alta"]
CATEGORIES = ["Trabalho", "Pessoal", "Estudos", "Outros"]

PRIORITY_COLORS = {
    "Baixa": ft.Colors.GREEN_600,
    "Média": ft.Colors.ORANGE_600,
    "Alta": ft.Colors.RED_600,
}


# ----------------------------------------------------------------------------
# Camada de dados (SQLite)
# ----------------------------------------------------------------------------
class DatabaseError(Exception):
    """Erro amigável para a interface exibir ao usuário."""


class TaskRepository:
    """Encapsula todo o acesso ao banco SQLite."""

    def __init__(self, path: Path = DB_PATH):
        self.path = str(path)
        self._create_table()

    @contextmanager
    def _connect(self):
        """Abre uma conexão, faz commit/rollback e sempre fecha."""
        conn = None
        try:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Erro no banco de dados: {exc}") from exc
        finally:
            if conn:
                conn.close()

    def _create_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT    NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    priority  TEXT    NOT NULL DEFAULT 'Média',
                    category  TEXT    NOT NULL DEFAULT 'Outros'
                )
                """
            )

    def get_all(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()

    def add(self, name: str, priority: str, category: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (name, priority, category) VALUES (?, ?, ?)",
                (name, priority, category),
            )
            return cur.lastrowid

    def update(self, task_id: int, name: str, completed: bool, priority: str, category: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE tasks SET name=?, completed=?, priority=?, category=? WHERE id=?",
                (name, int(completed), priority, category, task_id),
            )

    def delete(self, task_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def delete_completed(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE completed=1")


# ----------------------------------------------------------------------------
# Helpers de UI
# ----------------------------------------------------------------------------
def make_dropdown(options: list[str], value: str, label: str, width: int = 130) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        value=value,
        width=width,
        dense=True,
        options=[ft.DropdownOption(key=o, text=o) for o in options],
    )


def make_badge(text: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(text, size=11, color=ft.Colors.WHITE),
        bgcolor=color,
        border_radius=10,
        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
    )


# ----------------------------------------------------------------------------
# Componente reutilizável: Task
# ----------------------------------------------------------------------------
@ft.control
class Task(ft.Column):
    """Uma tarefa com modo de visualização e modo de edição."""

    task_id: int = 0
    task_name: str = ""
    completed: bool = False
    priority: str = "Média"
    category: str = "Outros"
    # Callbacks fornecidos pelo TodoApp
    on_change: Callable = field(default=lambda task: None)
    on_delete: Callable = field(default=lambda task: None)

    def init(self):
        # ---- Modo de visualização ----
        self.checkbox = ft.Checkbox(
            value=self.completed,
            label=self.task_name,
            label_style=self._label_style(),
            expand=True,
            on_change=self.status_changed,
        )
        self.priority_badge = make_badge(self.priority, PRIORITY_COLORS[self.priority])
        self.category_badge = make_badge(self.category, ft.Colors.BLUE_GREY_500)

        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.checkbox,
                self.priority_badge,
                self.category_badge,
                ft.IconButton(
                    icon=ft.Icons.CREATE_OUTLINED,
                    tooltip="Editar",
                    on_click=self.edit_clicked,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Apagar",
                    icon_color=ft.Colors.RED_400,
                    on_click=lambda e: self.on_delete(self),
                ),
            ],
        )

        # ---- Modo de edição ----
        self.edit_name = ft.TextField(
            value=self.task_name, expand=True, dense=True, on_submit=self.save_clicked
        )
        self.edit_priority = make_dropdown(PRIORITIES, self.priority, "Prioridade")
        self.edit_category = make_dropdown(CATEGORIES, self.category, "Categoria")

        self.edit_view = ft.Row(
            visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.edit_name,
                self.edit_priority,
                self.edit_category,
                ft.IconButton(
                    icon=ft.Icons.DONE_OUTLINE,
                    icon_color=ft.Colors.GREEN_600,
                    tooltip="Salvar",
                    on_click=self.save_clicked,
                ),
            ],
        )

        self.controls = [self.display_view, self.edit_view]

    # ---- Utilidades internas ----
    def _label_style(self) -> ft.TextStyle:
        return ft.TextStyle(
            decoration=ft.TextDecoration.LINE_THROUGH
            if self.completed
            else ft.TextDecoration.NONE
        )

    # ---- Eventos ----
    def status_changed(self, e):
        self.completed = self.checkbox.value
        self.checkbox.label_style = self._label_style()
        self.checkbox.update()
        self.on_change(self)

    def edit_clicked(self, e):
        self.edit_name.value = self.task_name
        self.edit_priority.value = self.priority
        self.edit_category.value = self.category
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        new_name = (self.edit_name.value or "").strip()
        if not new_name:
            self.edit_name.error_text = "Digite um nome"
            self.edit_name.update()
            return
        self.edit_name.error_text = None

        self.task_name = new_name
        self.priority = self.edit_priority.value or "Média"
        self.category = self.edit_category.value or "Outros"

        # Atualiza a visualização
        self.checkbox.label = self.task_name
        self.priority_badge.content.value = self.priority
        self.priority_badge.bgcolor = PRIORITY_COLORS[self.priority]
        self.category_badge.content.value = self.category

        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()
        self.on_change(self)


# ----------------------------------------------------------------------------
# Aplicativo principal: TodoApp
# ----------------------------------------------------------------------------
@ft.control
class TodoApp(ft.Column):
    """Controle raiz: cabeçalho, entrada, busca, abas, lista e rodapé."""

    def init(self):
        self.width = 760
        self.spacing = 14
        self.repo = TaskRepository()

        # ---- Cabeçalho ----
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            tooltip="Alternar tema",
            on_click=self.toggle_theme,
        )
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Minhas Tarefas", size=28, weight=ft.FontWeight.BOLD),
                self.theme_button,
            ],
        )

        # ---- Nova tarefa ----
        self.new_task = ft.TextField(
            hint_text="O que precisa ser feito?",
            expand=True,  # ocupa o espaço restante da linha (Row sem wrap)
            dense=True,
            on_submit=self.add_clicked,
        )
        self.new_priority = make_dropdown(PRIORITIES, "Média", "Prioridade")
        self.new_category = make_dropdown(CATEGORIES, "Pessoal", "Categoria")
        add_row = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.new_task,
                self.new_priority,
                self.new_category,
                ft.Button("Adicionar", icon=ft.Icons.ADD, on_click=self.add_clicked),
            ],
        )

        # ---- Busca ----
        self.search = ft.TextField(
            hint_text="Buscar por palavra-chave ou categoria...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            on_change=lambda e: self.apply_filters(),
        )

        # ---- Abas ----
        self.filter_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            on_change=lambda e: self.apply_filters(),
            content=ft.TabBar(
                tabs=[
                    ft.Tab(label="Todas"),
                    ft.Tab(label="Pendentes"),
                    ft.Tab(label="Concluídas"),
                ]
            ),
        )

        # ---- Lista de tarefas ----
        self.tasks = ft.Column(spacing=2)
        self.empty_text = ft.Text(
            "Nenhuma tarefa encontrada.", italic=True, color=ft.Colors.GREY_600, visible=False
        )

        # ---- Rodapé ----
        self.counter = ft.Text("0 tarefas pendentes")
        footer = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.counter,
                ft.OutlinedButton(
                    "Limpar concluídas",
                    icon=ft.Icons.CLEANING_SERVICES_OUTLINED,
                    on_click=self.clear_completed,
                ),
            ],
        )

        self.controls = [
            header,
            add_row,
            self.search,
            self.filter_tabs,
            self.tasks,
            self.empty_text,
            ft.Divider(),
            footer,
        ]

        # Carrega as tarefas salvas (ainda sem update, pois não está montado)
        self.load_tasks()

    def did_mount(self):
        # Já montado na página: aplica filtros e atualiza contador/ícone do tema
        self._sync_theme_icon()
        self.apply_filters()

    # ---- Banco de dados / mensagens ----
    def notify(self, message: str):
        """Mostra um SnackBar (ignora silenciosamente se ainda não montado)."""
        try:
            self.page.show_dialog(ft.SnackBar(ft.Text(message)))
        except Exception:
            print(message)

    def load_tasks(self):
        try:
            rows = self.repo.get_all()
        except DatabaseError as exc:
            print(exc)
            rows = []
        for row in rows:
            self.tasks.controls.append(self._build_task(row))

    def _build_task(self, row) -> Task:
        return Task(
            task_id=row["id"],
            task_name=row["name"],
            completed=bool(row["completed"]),
            priority=row["priority"],
            category=row["category"],
            on_change=self.task_changed,
            on_delete=self.task_deleted,
        )

    # ---- Eventos ----
    def add_clicked(self, e):
        name = (self.new_task.value or "").strip()
        if not name:
            self.new_task.error_text = "Digite uma tarefa"
            self.new_task.update()
            return
        self.new_task.error_text = None

        priority = self.new_priority.value or "Média"
        category = self.new_category.value or "Outros"
        try:
            new_id = self.repo.add(name, priority, category)
        except DatabaseError as exc:
            self.notify(str(exc))
            return

        self.tasks.controls.append(
            self._build_task(
                {"id": new_id, "name": name, "completed": 0,
                 "priority": priority, "category": category}
            )
        )
        self.new_task.value = ""
        self.apply_filters()
        self.new_task.focus()

    def task_changed(self, task: Task):
        """Chamado quando uma tarefa é editada ou marcada/desmarcada."""
        try:
            self.repo.update(
                task.task_id, task.task_name, task.completed, task.priority, task.category
            )
        except DatabaseError as exc:
            self.notify(str(exc))
        self.apply_filters()

    def task_deleted(self, task: Task):
        try:
            self.repo.delete(task.task_id)
        except DatabaseError as exc:
            self.notify(str(exc))
            return
        self.tasks.controls.remove(task)
        self.apply_filters()

    def clear_completed(self, e):
        try:
            self.repo.delete_completed()
        except DatabaseError as exc:
            self.notify(str(exc))
            return
        self.tasks.controls = [t for t in self.tasks.controls if not t.completed]
        self.apply_filters()

    def toggle_theme(self, e):
        self.page.theme_mode = (
            ft.ThemeMode.DARK
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self._sync_theme_icon()
        self.page.update()

    def _sync_theme_icon(self):
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self.theme_button.icon = ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE

    # ---- Filtros + estatísticas ----
    def apply_filters(self):
        status = self.filter_tabs.selected_index  # 0=todas, 1=pendentes, 2=concluídas
        query = (self.search.value or "").strip().lower()

        visible_count = 0
        for task in self.tasks.controls:
            match_status = (
                status == 0
                or (status == 1 and not task.completed)
                or (status == 2 and task.completed)
            )
            match_query = (
                not query
                or query in task.task_name.lower()
                or query in task.category.lower()
            )
            task.visible = match_status and match_query
            visible_count += int(task.visible)

        pending = sum(1 for t in self.tasks.controls if not t.completed)
        self.counter.value = f"{pending} tarefa{'s' if pending != 1 else ''} pendente{'s' if pending != 1 else ''}"
        self.empty_text.visible = visible_count == 0
        self.update()


# ----------------------------------------------------------------------------
# Ponto de entrada
# ----------------------------------------------------------------------------
def main(page: ft.Page):
    page.title = "To-Do App com SQLite"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 24

    page.add(TodoApp())


ft.run(main)
