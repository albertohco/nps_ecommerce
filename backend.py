from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
import ollama
import os

# Configuração do SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/ecommerce_nps.db"

# Criar diretório data se não existir
os.makedirs("./data", exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos SQLAlchemy (ORM)
class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    texto_avaliacao = Column(String, nullable=False)
    nota_llm = Column(Integer, nullable=True)  # 0-10, pode ser nulo

# Criar tabelas
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

# Modelos Pydantic
class AvaliacaoBase(BaseModel):
    texto_avaliacao: str
    nota_llm: Optional[int] = None

class AvaliacaoSchema(AvaliacaoBase):
    id: int
    
    class Config:
        from_attributes = True

class NPSResult(BaseModel):
    nps_score: float
    total_avaliacoes: int
    promotores: int
    neutros: int
    detratores: int
    percentual_promotores: float
    percentual_neutros: float
    percentual_detratores: float

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função de Integração com Ollama
def get_ollama_sentiment_score(texto: str, model: str = "gemma:2b") -> int:
    """
    Integração real com Ollama para análise de sentimento.
    Retorna uma nota de 0 a 10 baseada no sentimento do texto.
    Usa modelo leve (gemma:2b) para melhor performance.
    """
    try:
        # Prompt simplificado para resposta mais rápida
        prompt = f"""Avalie esta opinião de 0 a 10 (0=péssimo, 10=excelente). Responda APENAS o número.

Opinião: "{texto}"

Nota:"""

        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0,  # Respostas mais consistentes
                'num_predict': 5,  # Limitar tokens de resposta
            }
        )
        
        # Extrair a resposta e fazer parsing
        resposta_texto = response['message']['content'].strip()
        
        # Tentar extrair apenas o número
        import re
        numeros = re.findall(r'\d+', resposta_texto)
        if numeros:
            nota = int(numeros[0])
            # Garantir que está no range 0-10
            nota = max(0, min(10, nota))
            return nota
        else:
            # Fallback: retornar 5 (neutro) se não conseguir extrair
            return 5
            
    except Exception as e:
        print(f"Erro ao conectar com Ollama: {e}")
        print("Certifique-se de que o Ollama está rodando e o modelo está instalado.")
        raise HTTPException(
            status_code=503,
            detail=f"Serviço Ollama indisponível: {str(e)}"
        )

# FastAPI App
app = FastAPI(title="E-commerce NPS API")

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Rotas
@app.get("/api/avaliacoes", response_model=List[AvaliacaoSchema])
def get_avaliacoes(db: Session = Depends(get_db)):
    """Retorna todas as avaliações do banco."""
    avaliacoes = db.query(Avaliacao).all()
    return avaliacoes

@app.get("/api/nps", response_model=NPSResult)
def get_nps(db: Session = Depends(get_db)):
    """Calcula e retorna o NPS baseado nas notas LLM."""
    avaliacoes = db.query(Avaliacao).filter(Avaliacao.nota_llm.isnot(None)).all()
    
    if not avaliacoes:
        return NPSResult(
            nps_score=0.0,
            total_avaliacoes=0,
            promotores=0,
            neutros=0,
            detratores=0,
            percentual_promotores=0.0,
            percentual_neutros=0.0,
            percentual_detratores=0.0
        )
    
    total = len(avaliacoes)
    promotores = sum(1 for a in avaliacoes if a.nota_llm >= 9)
    neutros = sum(1 for a in avaliacoes if 7 <= a.nota_llm <= 8)
    detratores = sum(1 for a in avaliacoes if a.nota_llm <= 6)
    
    # Cálculo do NPS: (% Promotores - % Detratores)
    percentual_promotores = (promotores / total) * 100
    percentual_detratores = (detratores / total) * 100
    percentual_neutros = (neutros / total) * 100
    
    nps_score = percentual_promotores - percentual_detratores
    
    return NPSResult(
        nps_score=round(nps_score, 2),
        total_avaliacoes=total,
        promotores=promotores,
        neutros=neutros,
        detratores=detratores,
        percentual_promotores=round(percentual_promotores, 2),
        percentual_neutros=round(percentual_neutros, 2),
        percentual_detratores=round(percentual_detratores, 2)
    )

@app.post("/api/processar_avaliacoes")
def processar_avaliacoes(limit: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Processa avaliações sem nota_llm usando Ollama.
    
    Args:
        limit: Número máximo de avaliações a processar (None = todas)
    """
    # Buscar avaliações sem nota
    query = db.query(Avaliacao).filter(Avaliacao.nota_llm.is_(None))
    
    if limit:
        avaliacoes_pendentes = query.limit(limit).all()
    else:
        avaliacoes_pendentes = query.all()
    
    total_pendentes_inicial = db.query(Avaliacao).filter(Avaliacao.nota_llm.is_(None)).count()
    total_processadas = 0
    erros = 0
    
    for avaliacao in avaliacoes_pendentes:
        try:
            # Chamar Ollama para análise de sentimento
            nota = get_ollama_sentiment_score(avaliacao.texto_avaliacao)
            
            # Atualizar no banco
            avaliacao.nota_llm = nota
            db.commit()
            
            total_processadas += 1
            print(f"Processada avaliação {avaliacao.id}: nota {nota}")
            
        except Exception as e:
            db.rollback()
            erros += 1
            print(f"Erro ao processar avaliação {avaliacao.id}: {e}")
            # Continuar com as próximas mesmo se uma falhar
            continue
    
    total_pendentes_restantes = db.query(Avaliacao).filter(Avaliacao.nota_llm.is_(None)).count()
    
    return {
        "total_processadas": total_processadas,
        "total_pendentes_inicial": total_pendentes_inicial,
        "total_pendentes_restantes": total_pendentes_restantes,
        "erros": erros,
        "concluido": total_pendentes_restantes == 0
    }

@app.get("/")
def root():
    return {
        "message": "API NPS E-commerce",
        "endpoints": [
            "/api/avaliacoes",
            "/api/nps",
            "/api/processar_avaliacoes"
        ]
    }
