from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random
import os

# Import direto do módulo backend (agora na raiz)
from backend import Base, Avaliacao, SQLALCHEMY_DATABASE_URL

# Configuração
fake = Faker('pt_BR')

# Listas de frases de avaliação (positivas, negativas e neutras)
avaliacoes_positivas = [
    "Produto excelente! Superou minhas expectativas. Recomendo muito!",
    "Entrega rápida e produto de ótima qualidade. Muito satisfeito!",
    "Adorei! Exatamente como descrito. Voltarei a comprar com certeza.",
    "Atendimento impecável e produto maravilhoso. Nota 10!",
    "Melhor compra que fiz este ano. Qualidade excepcional!",
    "Produto perfeito, entrega antes do prazo. Empresa confiável!",
    "Estou muito feliz com a compra. Produto de primeira linha!",
    "Recomendo de olhos fechados! Qualidade surpreendente!",
    "Produto incrível, embalagem caprichada. Amei tudo!",
    "Superou todas as minhas expectativas. Comprarei novamente!",
]

avaliacoes_negativas = [
    "Produto chegou com defeito. Muito decepcionado.",
    "Péssima qualidade. Não recomendo de jeito nenhum.",
    "Entrega atrasada e produto diferente do anunciado.",
    "Horrível! Dinheiro jogado fora. Nunca mais compro aqui.",
    "Atendimento péssimo e produto de baixa qualidade.",
    "Propaganda enganosa. Produto não corresponde à descrição.",
    "Muito insatisfeito. Produto veio quebrado.",
    "Não vale o preço. Qualidade muito ruim.",
    "Decepção total. Esperava muito mais pelo valor pago.",
    "Péssima experiência. Não comprem nesta loja!",
]

avaliacoes_neutras = [
    "Produto ok, nada de especial. Atende o básico.",
    "Entrega no prazo, produto razoável. Esperava mais.",
    "Produto mediano. Pelo preço, está ok.",
    "Atende o que promete, mas sem grandes destaques.",
    "Produto aceitável. Não é ruim, mas também não impressiona.",
    "Entrega demorou um pouco, mas o produto é ok.",
    "Qualidade média. Serve para o que preciso.",
    "Nada de excepcional, mas também não tenho reclamações.",
    "Produto comum, sem muitos diferenciais.",
    "Atende as expectativas básicas. Nada mais que isso.",
]

def gerar_avaliacao_aleatoria():
    """Gera uma avaliação aleatória combinando diferentes tipos."""
    tipo = random.choices(
        ['positiva', 'neutra', 'negativa'],
        weights=[0.5, 0.3, 0.2]  # 50% positivas, 30% neutras, 20% negativas
    )[0]
    
    if tipo == 'positiva':
        return random.choice(avaliacoes_positivas)
    elif tipo == 'negativa':
        return random.choice(avaliacoes_negativas)
    else:
        return random.choice(avaliacoes_neutras)

def popular_banco(num_avaliacoes=100):
    """Popula o banco com avaliações fake."""
    
    # Criar diretório data se não existir
    os.makedirs("./data", exist_ok=True)
    
    # Criar engine e sessão
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Limpar tabela existente (opcional)
        db.query(Avaliacao).delete()
        db.commit()
        
        print(f"Gerando {num_avaliacoes} avaliações...")
        
        # Gerar avaliações
        for i in range(num_avaliacoes):
            avaliacao = Avaliacao(
                texto_avaliacao=gerar_avaliacao_aleatoria(),
                nota_llm=None  # Inicialmente nulo, será preenchido pelo Ollama
            )
            db.add(avaliacao)
            
            # Commit em lotes de 100 para melhor performance
            if (i + 1) % 100 == 0:
                db.commit()
                print(f"Inseridas {i + 1} avaliações...")
        
        # Commit final
        db.commit()
        print(f"\n✅ Banco populado com sucesso! Total: {num_avaliacoes} avaliações.")
        print(f"📁 Arquivo do banco: {SQLALCHEMY_DATABASE_URL}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco(100)
