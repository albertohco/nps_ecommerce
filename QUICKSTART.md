# 🚀 Guia Rápido - E-commerce NPS

## Estrutura Simplificada

```
ecommerce_nps/
├── backend.py          # API FastAPI
├── frontend.py         # Dashboard Streamlit  
├── fake_data.py        # Gera 1000 avaliações
├── requirements.txt    # Dependências
└── data/              # Banco SQLite (criado automaticamente)
```

## Comandos Rápidos

### 1. Popular o Banco
```bash
python fake_data.py
```

### 2. Iniciar Backend
```bash
uvicorn backend:app --reload
```
API: http://localhost:8000

### 3. Iniciar Frontend (novo terminal)
```bash
streamlit run frontend.py
```
Dashboard: http://localhost:8501

## Pré-requisitos

### Ollama (para análise de sentimento)
```bash
# Instalar
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar serviço
ollama serve

# Baixar modelo otimizado (novo terminal)
ollama pull gemma:2b
```

## Uso

1. Abra o dashboard Streamlit
2. Clique em "🤖 Rodar Análise de Sentimento (Ollama)"
3. Aguarde o processamento
4. Visualize o NPS e os gráficos!

---

**Tudo na raiz = mais simples! 🎯**
