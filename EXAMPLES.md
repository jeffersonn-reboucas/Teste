# Exemplos de uso do Libras Visual Builder

## Uso via Interface Streamlit

Execute:
```bash
streamlit run src/app.py
```

## Uso via Código Python

### Exemplo 1: Geração simples

```python
from src.prompt_engine import PromptEngine
from src.ai_generator import AIGenerator

# Configurar
engine = PromptEngine()
generator = AIGenerator(provider="openai", api_key="sua-key-aqui")

# Gerar prompt
prompt = engine.gerar_prompt_completo(
    termo="OBRIGADO",
    configuracao_mao=["Mão aberta"],
    ponto_articulacao="Boca",
    movimento=["Para frente"],
    orientacao="Palma para cima",
    expressao=["Sorriso"]
)

# Gerar imagem
sucesso, msg, caminho = generator.gerar_imagem(
    prompt=prompt,
    imagem_referencia_a="assets/referencias/obrigado.png",
    imagem_personagem_b="assets/personagens/personagem1.png",
    nome_arquivo="obrigado_gerado.png"
)

print(f"Status: {msg}")
print(f"Arquivo: {caminho}")
```

### Exemplo 2: Adicionar ao catálogo

```python
from src.catalog import CatalogoSinais
from src.models import Sinal

# Inicializar catálogo
catalogo = CatalogoSinais()

# Criar novo sinal
sinal = Sinal(
    termo="OBRIGADO",
    categoria="Verbos",
    configuracao_mao=["Mão aberta"],
    ponto_articulacao="Boca",
    movimento=["Para frente"],
    orientacao="Palma para cima",
    expressao=["Sorriso"],
    caminho_imagem="output/obrigado_gerado.png",
    tags=["gratidão", "cortesia"],
    observacoes="Sinal comum em contextos sociais"
)

# Adicionar ao catálogo
if catalogo.adicionar_sinal(sinal):
    print("✅ Sinal adicionado ao catálogo!")
else:
    print("⚠️ Sinal já existe")
```

### Exemplo 3: Buscar e filtrar

```python
from src.catalog import CatalogoSinais

catalogo = CatalogoSinais()

# Buscar por categoria
sinais_verbos = catalogo.filtrar_por_categoria("Verbos")
print(f"Total de verbos: {len(sinais_verbos)}")

# Buscar por parâmetro específico
sinais_rosto = catalogo.buscar_por_parametro(ponto_articulacao="Rosto")
print(f"Sinais articulados no rosto: {len(sinais_rosto)}")

# Buscar sinal específico
sinal = catalogo.buscar_sinal("OBRIGADO")
if sinal:
    print(f"Configuração: {sinal.configuracao_mao}")
    print(f"Imagem: {sinal.caminho_imagem}")
```

### Exemplo 4: Geração em lote

```python
from src.prompt_engine import PromptEngine
from src.ai_generator import AIGenerator

sinais_para_gerar = [
    {
        "termo": "OLÁ",
        "configuracao_mao": ["Mão aberta"],
        "ponto_articulacao": "Cabeça",
        "movimento": ["Balançar"],
        "orientacao": "Palma para frente",
        "expressao": ["Sorriso"]
    },
    {
        "termo": "CASA",
        "configuracao_mao": ["Mão em C"],
        "ponto_articulacao": "Espaço neutro",
        "movimento": ["Para cima", "Para baixo"],
        "orientacao": "Palma para dentro",
        "expressao": ["Neutra"]
    }
]

engine = PromptEngine()
generator = AIGenerator(provider="openai", api_key="sua-key")

for config in sinais_para_gerar:
    prompt = engine.gerar_prompt_completo(**config)
    
    sucesso, msg, caminho = generator.gerar_imagem(
        prompt=prompt,
        imagem_referencia_a=f"assets/referencias/{config['termo'].lower()}.png",
        imagem_personagem_b="assets/personagens/personagem_padrao.png",
        nome_arquivo=f"{config['termo'].lower()}_gerado.png"
    )
    
    print(f"{config['termo']}: {msg}")
```

### Exemplo 5: Refinamento de imagem

```python
from src.prompt_engine import PromptEngine
from src.ai_generator import AIGenerator

engine = PromptEngine()

# Criar prompt de refinamento
prompt_refinamento = engine.gerar_prompt_refinamento(
    problema="A configuração da mão está imprecisa",
    ajuste_solicitado="Corrigir a mão para formato em 'L' com dedos mais definidos"
)

print(prompt_refinamento)
# Use este prompt para gerar uma nova versão corrigida
```

### Exemplo 6: Exportar catálogo

```python
from src.catalog import CatalogoSinais

catalogo = CatalogoSinais()

# Exportar para CSV
catalogo.exportar_para_csv("meu_catalogo_libras.csv")

# Ver estatísticas
stats = catalogo.estatisticas()
print(f"Total de sinais: {stats['total_sinais']}")
print(f"Categorias: {stats['categorias']}")
```
