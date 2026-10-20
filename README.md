# 📝 To-Do App com Flet + SQLite

Aplicativo de lista de tarefas para desktop feito em **Python** com o framework **[Flet](https://flet.dev)**. As tarefas são salvas em um banco **SQLite** local, então continuam lá depois que você fecha e abre o app.

O projeto foi escrito com orientação a objetos e componentes reutilizáveis (`@ft.control`), como exemplo de uma aplicação Flet organizada, mas ainda contida em um único arquivo.

---

## ✨ Funcionalidades

| Recurso | Descrição |
|---|---|
| **Persistência** | Criar, editar, concluir e apagar tarefas; tudo é salvo automaticamente no SQLite e carregado ao abrir o app. |
| **Prioridade** | Cada tarefa tem prioridade **Baixa**, **Média** ou **Alta**, mostrada em um selo colorido (verde, laranja, vermelho). |
| **Categoria** | **Trabalho**, **Pessoal**, **Estudos** ou **Outros**. |
| **Busca em tempo real** | Filtra a lista enquanto você digita, pelo nome ou pela categoria da tarefa. |
| **Abas de filtro** | **Todas**, **Pendentes** e **Concluídas**. A busca e as abas funcionam juntas. |
| **Tema claro/escuro** | Botão no cabeçalho alterna o tema do app em tempo real. |
| **Rodapé de estatísticas** | Mostra quantas tarefas estão pendentes e tem o botão **Limpar concluídas**. |
| **Tratamento de erros** | Falhas no banco viram uma mensagem na tela em vez de derrubar o app. |

---

## 🧰 Tecnologias

- **Python** 3.12 ou 3.13 (recomendado)
- **Flet** 1.x (interface baseada em Flutter)
- **sqlite3** (biblioteca padrão do Python; não precisa instalar nada)

---

## 📁 Estrutura do projeto

```
projetoFlet/
├── main.py            # Todo o código do app
├── requirements.txt   # Dependências
└── todo.db            # Banco SQLite (criado automaticamente na primeira execução)
```

---

## 🚀 Como rodar

### 1. Pré-requisitos

- Python 3.12 ou 3.13 instalado (no Windows, marque **Add Python to PATH** no instalador)
- Conexão com a internet na primeira execução, porque o Flet baixa o componente de desktop

### 2. Clonar o repositório

```bash
git clone https://github.com/andrebluiz-design/projetoFlet.git
cd projetoFlet
```

### 3. Criar o ambiente virtual e instalar o Flet

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install "flet[all]"
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flet[all]"
```

> O `flet[all]` instala o Flet junto com o comando `flet run` e o app de desktop. Só `pip install flet` pode deixar de fora o CLI.

### 4. Executar

**Windows:**

```powershell
.venv\Scripts\flet.exe run main.py
```

**Linux / macOS:**

```bash
flet run main.py
```

Com `flet run`, o app **recarrega sozinho** quando você salva o `main.py`. Para abrir no navegador em vez de uma janela, use `flet run -w main.py`. Também dá para rodar direto com `python main.py`, sem o recarregamento automático.

---

## 🏗️ Como o código funciona

O `main.py` é dividido em três camadas:

### `TaskRepository` — acesso ao banco

Concentra todo o SQL. Nenhuma outra parte do app fala com o SQLite diretamente.

- Cria a tabela `tasks` se ela não existir.
- Expõe `get_all`, `add`, `update`, `delete` e `delete_completed`.
- Cada operação abre uma conexão, faz **commit** em caso de sucesso, **rollback** em caso de erro e sempre fecha a conexão (via *context manager*).
- Erros do `sqlite3` são convertidos em `DatabaseError`, que a interface mostra ao usuário.
- Usa consultas parametrizadas (`?`), o que evita SQL injection.

Estrutura da tabela:

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | INTEGER | Chave primária, autoincremento |
| `name` | TEXT | Nome da tarefa (obrigatório) |
| `completed` | INTEGER | 0 = pendente, 1 = concluída |
| `priority` | TEXT | `Baixa`, `Média` ou `Alta` |
| `category` | TEXT | `Trabalho`, `Pessoal`, `Estudos` ou `Outros` |

### `Task` — componente de uma tarefa

Controle reutilizável (`@ft.control`, herda de `ft.Column`) que representa uma linha da lista. Tem dois modos:

- **Visualização:** checkbox com o nome (riscado quando concluída), selos de prioridade e categoria, e botões de editar e apagar.
- **Edição:** campo de texto e seletores de prioridade e categoria, com botão de salvar.

A `Task` não conhece o banco. Ela avisa o app pelos callbacks `on_change` e `on_delete`, e quem salva é o `TodoApp`. Isso mantém o componente simples e reaproveitável.

### `TodoApp` — tela principal

Controle raiz que monta e coordena tudo: cabeçalho com o botão de tema, linha para criar tarefas, busca, abas, lista e rodapé.

O método `apply_filters()` é o centro da tela. A cada mudança (digitar na busca, trocar de aba, marcar, apagar ou adicionar) ele decide quais tarefas ficam visíveis, atualiza o contador de pendentes e mostra o aviso "Nenhuma tarefa encontrada" quando for o caso.

---

## 🧪 Como usar

1. Digite a tarefa, escolha prioridade e categoria e clique em **Adicionar** (ou aperte Enter).
2. Marque o checkbox para concluir. Clique no lápis para editar e na lixeira para apagar.
3. Use a busca para filtrar e as abas para ver só pendentes ou concluídas.
4. Clique no ícone de sol/lua no topo para trocar o tema.
5. **Limpar concluídas** apaga de uma vez todas as tarefas concluídas.

---

## 🛠️ Solução de problemas

| Problema | Solução |
|---|---|
| `flet` não é reconhecido como comando | Use o executável do venv: `.venv\Scripts\flet.exe run main.py`. |
| `Activate.ps1` bloqueado no PowerShell | Não precisa ativar o venv; use os caminhos completos dos comandos acima. Para ativar mesmo assim: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. |
| `No module named flet.__main__` | `python -m flet` não existe no Flet 1.x. Use `flet run` ou `python main.py`. |
| Falha ao instalar o Flet | O Python 3.14 pode ainda não ter pacotes prontos. Recrie o venv com Python 3.12 ou 3.13. |
| Erro de controle ao abrir o app | Confirme que está no Flet 1.x: `pip install -U "flet[all]"`. |

---

## 🔭 Ideias para evoluir

- Versão **Kanban** com colunas "A Fazer", "Em Progresso" e "Concluído"
- Backend com **FastAPI**, separando a interface da API
- Data de vencimento e ordenação por prioridade
- Empacotar como executável com `flet build windows`

---

## 📄 Licença

Projeto de estudo. Use e modifique à vontade.
