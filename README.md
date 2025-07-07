# Agente de Monitoramento Web

## Visão Geral

Sistema de monitoramento web containerizado que realiza testes de conectividade ICMP e HTTP em endpoints específicos. O sistema coleta métricas de latência, disponibilidade e performance, armazenando os dados em banco relacional MySQL para visualização através de dashboards Grafana.

## High Level Design

### Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SISTEMA DE MONITORAMENTO                  │
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐ │
│  │   FastAPI   │    │  Prometheus  │    │    Blackbox Exporter    │ │
│  │             │    │              │    │                         │ │
│  │  Port: 8000 │    │  Port: 9090  │    │     Port: 9115         │ │
│  └─────────────┘    └──────────────┘    └─────────────────────────┘ │
│         │                     │                           │         │
│         ▼                     ▼                           ▼         │
│  ┌─────────────┐    ┌──────────────────────────────────────────────┐ │
│  │    MySQL    │    │                Grafana                      │ │
│  │             │    │                                              │ │
│  │  Port: 3306 │    │              Port: 3000                     │ │
│  └─────────────┘    └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      TARGETS           │
                    │  • google.com          │
                    │  • youtube.com         │
                    │  • rnp.br              │
                    └─────────────────────────┘
```

### Componentes

| Componente | Tecnologia | Porta | Função |
|------------|------------|-------|---------|
| FastAPI | Python 3.9 | 8000 | Orquestração e processamento de dados |
| Prometheus | Prometheus | 9090 | Coleta e armazenamento temporário de métricas |
| Blackbox Exporter | Blackbox | 9115 | Execução de probes ICMP e HTTP |
| MySQL | MySQL 8 | 3306 | Persistência de dados |
| Grafana | Grafana | 3000 | Dashboards e visualização |

### Fluxo de Dados

```
Targets → Blackbox Exporter → Prometheus → FastAPI → MySQL → Grafana
```

1. **Blackbox Exporter** executa probes ICMP e HTTP nos targets configurados
2. **Prometheus** coleta métricas do Blackbox Exporter a cada 15 segundos
3. **FastAPI** consulta Prometheus via API REST e processa os dados
4. **MySQL** armazena dados processados em tabelas estruturadas
5. **Grafana** consulta MySQL para exibir dashboards em tempo real

### Métricas Coletadas

**ICMP (Ping)**
- RTT (Round Trip Time) em millisegundos
- Packet Loss percentual

**HTTP**
- Status Code da resposta
- Tempo de carregamento em millisegundos

### Modelo de Dados

```sql
-- Resultados de testes ICMP
CREATE TABLE ping_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    rtt_ms FLOAT,
    packet_loss FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resultados de testes HTTP
CREATE TABLE http_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    status_code INT,
    load_time_ms FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Containerização

O sistema utiliza Docker Compose com 5 containers dedicados:

- **mysql**: Banco de dados MySQL 8
- **prometheus**: Servidor Prometheus para coleta de métricas
- **blackbox_exporter**: Executor de probes ICMP/HTTP
- **fastapi**: API REST para orquestração (build customizado)
- **grafana**: Interface de visualização

Comunicação entre containers via rede bridge interna "monitoring".

## APIs Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Status da aplicação |
| `/blackbox/targets` | GET | Lista targets monitorados |
| `/blackbox/add-target` | POST | Adiciona novo target |
| `/blackbox/delete-target` | DELETE | Remove target |
| `/scrape` | GET | Executa coleta manual de métricas |

## Estrutura do Projeto

```
projeto/
├── docker-compose.yml              # Orquestração dos containers
├── prometheus.yml                  # Configuração do Prometheus
├── blackbox_exporter_config.yml    # Configuração do Blackbox Exporter
├── init.sql                        # Schema do banco MySQL
├── main.py                         # Aplicação FastAPI
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Build da aplicação FastAPI
└── grafana/
    ├── provisioning/
    │   ├── datasources/mysql.yml        # Datasource MySQL automático
    │   └── dashboards/dashboard.yml     # Provider de dashboards
    └── dashboards/
        └── monitoring-dashboard.json    # Dashboard pré-configurado
```

## Como Executar

### Pré-requisitos

- Docker
- Docker Compose
- Portas 3000, 3306, 8000, 9090, 9115 disponíveis

### Execução

```bash
# Clonar o repositório
git clone <repository-url>
cd projeto

# Subir todos os containers
docker-compose up -d

# Verificar status dos containers
docker-compose ps

# Executar primeira coleta de dados
curl http://localhost:8000/scrape
```

### Acesso às Interfaces

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API FastAPI**: http://localhost:8000
- **Blackbox Exporter**: http://localhost:9115

### Verificação do Sistema

```bash
# Testar API
curl http://localhost:8000/

# Verificar dados no banco
curl http://localhost:8000/test

# Verificar targets configurados
curl http://localhost:8000/blackbox/targets

# Executar coleta manual
curl http://localhost:8000/scrape
```

### Logs e Troubleshooting

```bash
# Ver logs de todos os containers
docker-compose logs

# Ver logs de um container específico
docker-compose logs fastapi
docker-compose logs mysql
docker-compose logs prometheus

# Parar todos os containers
docker-compose down

# Parar e remover volumes (reset completo)
docker-compose down -v
```

## Dashboards

O Grafana é configurado automaticamente com:

- Datasource MySQL pré-configurado
- Dashboard "Monitoramento de Rede" com:
  - Gráfico de latência (RTT) por host
  - Gráfico de tempo de carregamento HTTP
  - Tabela com estatísticas consolidadas

Os dashboards são provisionados automaticamente na inicialização do sistema.