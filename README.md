# 🔮 Ritual Bot

Bot RPG para Discord desenvolvido em Python, utilizando Discord.py e PostgreSQL, com foco em economia, progressão, cassino, mercado, pactos e sistemas interativos entre jogadores.

---

## ✨ Funcionalidades

### 💰 Economia
- Sistema de saldo persistente
- Transferência de moedas entre usuários
- Recompensa diária com `/daily`
- Ranking dos jogadores mais ricos

### 🎰 Cassino
- Painel principal do cassino
- Sistema de roleta
- Apostas com moedas do servidor
- Mecânicas de risco e recompensa

### 📈 Progressão
- Sistema de níveis
- Ranking de exorcistas
- Evolução dos jogadores por atividade

### 🏪 Comércio
- Loja de Feiticeiros
- Loja de Maldições
- Mercado Amaldiçoado
- Sistema de leilões

### 📜 Pactos e Maldições
- Sistema de pactos especiais
- Maldições com efeitos próprios
- Mecânicas inspiradas em RPG

### ⚔️ Sistema de Abates
- Registro de abates
- Competição entre jogadores
- Estatísticas de desempenho

---

## 🧾 Comandos

| Comando | Descrição |
|---|---|
| `/daily` | Recebe a recompensa diária do cassino |
| `/painel_cassino` | Envia o painel principal do Cassino do Diabo |
| `/pay` | Envia moedas para outro membro |
| `/ranking` | Mostra os membros mais ricos |
| `/ranking_exorcistas` | Mostra o ranking dos maiores exorcistas |
| `/roleta` | Gira a Roleta Amaldiçoada |
| `/saldo` | Mostra seu saldo de moedas |

---

## 🛠 Tecnologias Utilizadas

- Python 3.12
- Discord.py
- PostgreSQL
- GitHub Actions
- Slash Commands
- Cogs
- Variáveis de ambiente

---

## 🏗 Arquitetura

O projeto utiliza uma estrutura modular baseada em Cogs, separando cada sistema em arquivos independentes.

```text
game-rpg-discord/
│
├── .github/
│   └── workflows/
│       └── discord-updates.yml
│
├── ritualbot/
│   ├── cogs/
│   │   ├── abate.py
│   │   ├── economia.py
│   │   ├── leilao.py
│   │   ├── levels.py
│   │   ├── loja_feiticeiros.py
│   │   ├── loja_maldicoes.py
│   │   ├── maldicoes.py
│   │   ├── mercado_amaldicoado.py
│   │   ├── pactos.py
│   │   ├── painel_cassino.py
│   │   └── roleta.py
│   │
│   ├── utils/
│   ├── main.py
│   ├── requirements.txt
│   ├── runtime.txt
│   └── Procfile
```

---

## 📦 Principais Módulos

| Módulo | Função |
|---|---|
| `economia.py` | Gerencia saldo, transferências, ranking e recompensas |
| `painel_cassino.py` | Controla o painel principal do cassino |
| `roleta.py` | Sistema de roleta e apostas |
| `levels.py` | Sistema de experiência e níveis |
| `leilao.py` | Sistema de leilões |
| `mercado_amaldicoado.py` | Mercado entre jogadores |
| `loja_feiticeiros.py` | Loja de itens de feiticeiros |
| `loja_maldicoes.py` | Loja relacionada às maldições |
| `pactos.py` | Sistema de pactos especiais |
| `maldicoes.py` | Sistema de maldições |
| `abate.py` | Sistema de abates e estatísticas |

---

## 🚀 Como Executar

Clone o repositório:

```bash
git clone https://github.com/eusants01/game-rpg-discord.git
```

Entre na pasta do projeto:

```bash
cd game-rpg-discord/ritualbot
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente:

```env
DISCORD_TOKEN=seu_token_aqui
DATABASE_URL=sua_url_postgresql
```

Execute o bot:

```bash
python main.py
```

---

## 🔐 Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `DISCORD_TOKEN` | Token do bot no Discord |
| `DATABASE_URL` | URL de conexão com o PostgreSQL |

---

## 📊 Status do Projeto

✅ Em desenvolvimento ativo

- +100 commits
- Banco de dados PostgreSQL
- Arquitetura modular com Cogs
- Sistemas RPG integrados
- Deploy automatizado

---

## 🎯 Objetivo do Projeto

O Ritual Bot foi criado para transformar servidores Discord em uma experiência RPG interativa, com sistemas de economia, apostas, progressão, comércio e competição entre usuários.

Além do uso em comunidades, o projeto também serve como prática de desenvolvimento backend com Python, banco de dados relacional e arquitetura modular.

---

## 👨‍💻 Desenvolvedor

**Daniel / Sants**

Estudante de Engenharia de Software, com foco em desenvolvimento Python e backend.

GitHub: `@eusants01`

---

## ⭐ Destaque

Este projeto demonstra conhecimentos em:

- Desenvolvimento backend com Python
- Integração com APIs externas
- Banco de dados PostgreSQL
- Organização modular de código
- Controle de versão com Git/GitHub
- Deploy e automação
- Criação de sistemas com regras de negócio
