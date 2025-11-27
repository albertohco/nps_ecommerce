# 🚀 Otimizações de Performance

## Modelo Ollama Otimizado

O sistema agora usa o modelo **gemma:2b** para melhor performance:

### Instalar o modelo otimizado:
```bash
ollama pull gemma:2b
```

### Por que gemma:2b?
- **Mais rápido**: ~2-3x mais rápido que phi3
- **Menor**: ~1.7GB vs ~2.3GB do phi3
- **Eficiente**: Ótimo para tarefas de classificação simples

### Comparação de modelos:

| Modelo | Tamanho | Velocidade | Qualidade |
|--------|---------|------------|-----------|
| gemma:2b | 1.7GB | ⚡⚡⚡ Rápido | ✅ Boa |
| phi3 | 2.3GB | ⚡⚡ Médio | ✅✅ Muito boa |
| llama2 | 3.8GB | ⚡ Lento | ✅✅✅ Excelente |

### Outras otimizações implementadas:

1. **Processamento unitário**: 1 avaliação por vez para feedback instantâneo
2. **Prompt simplificado**: Resposta mais direta e rápida
3. **Temperature=0**: Respostas consistentes e rápidas
4. **Limite de tokens**: Apenas 5 tokens de resposta
5. **Sem delays**: Processamento contínuo sem pausas

### Trocar de modelo (se necessário):

Edite `backend.py` linha 65:
```python
def get_ollama_sentiment_score(texto: str, model: str = "gemma:2b"):
```

Modelos disponíveis:
- `gemma:2b` - Recomendado (rápido)
- `phi3` - Balanceado
- `llama2` - Mais preciso (lento)
- `mistral` - Alternativa rápida
