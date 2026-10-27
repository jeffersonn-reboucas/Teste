# Integração com PDFs do Dicionário Capovilla

## 📚 Novidades

O sistema agora integra diretamente com os PDFs do dicionário de Libras, permitindo:

1. **Busca Inteligente no Dicionário Capovilla** (2847 páginas)
2. **Extração Automática de Parâmetros** dos sinais
3. **Descrições Anatômicas Detalhadas** das configurações de mão

---

## 🔧 Configuração

### PDFs Necessários

Coloque os seguintes arquivos na pasta `Downloads`:

1. **Dicionário Capovilla Completo** (212 MB)
   - Caminho: `C:\Users\Jeffe\Downloads\Dicionario capovilla completo.pdf`
   - Novo Deit-Libras (2847 páginas)

2. **Configurações de Mão** (33 MB)
   - Caminho: `C:\Users\Jeffe\Downloads\configuraçao de mao.pdf`
   - Dicionário de Configurações das Mãos em Libras

---

## 🚀 Como Usar

### Na Interface (Coluna 1 - Item A)

Você verá **duas abas**:

#### 📤 Upload Manual
- Funciona como antes: faça upload de uma imagem

#### 🔍 Buscar no Dicionário (PDF)
- **Buscar por Termo**: Digite "CASA", "OBRIGADO", etc.
  - O sistema busca no PDF completo
  - Retorna até 10 resultados
  - Renderiza a página selecionada
  
- **Ir para Página**: Navegue direto para uma página específica (1-2847)

### Extração Automática de Parâmetros

Quando você busca ou carrega uma página, o sistema:

1. ✅ Extrai o texto entre parênteses (descrição anatômica do sinal)
2. ✅ Identifica automaticamente:
   - Configuração de Mão (ex: "Mão em B")
   - Orientação (ex: "palma para frente")
   - Ponto de Articulação (ex: "testa", "peito")
   - Movimento (ex: "circular", "para cima")
3. ✅ Preenche os campos automaticamente
4. ✅ Você pode editar os valores sugeridos

### Exemplo de Descrição Extraída

```
Texto do PDF:
"(Mão em B horizontal, palma para frente, dedos inclinados para a direita. 
Movê-la ligeiramente para a direita.)"

Parâmetros Extraídos:
- Configuração: Mão em B
- Orientação: Palma para frente
- Ponto de Articulação: Espaço neutro
- Movimento: Para direita
```

---

## 🧠 Detalhes Anatômicos para IA

O `prompt_engine.py` agora inclui descrições anatômicas detalhadas:

```python
"Mão em B": "Mão aberta com dedos juntos e estendidos, polegar cruzado sobre a palma."
"Mão em C": "Mão em formato de 'C', com todos os dedos curvados e separados do polegar."
"Mão em L": "Indicador e polegar formando 'L', demais dedos fechados."
```

Isso evita que a IA "alucine" posições incorretas dos dedos!

---

## 📖 Módulo `pdf_extractor.py`

### Classes Principais

#### `PDFCapovillaExtractor`
```python
# Abrir o dicionário
extractor = PDFCapovillaExtractor()

# Buscar termo
resultados = extractor.buscar_termo("CASA", max_resultados=10)

# Renderizar página
imagem = extractor.renderizar_pagina(num_pagina=150, dpi=150)

# Extrair parâmetros
texto = extractor.extrair_texto_pagina(150)
params = extractor.extrair_parametros_sinal(texto)
```

#### `PDFConfiguracaoMaoExtractor`
```python
# Abrir PDF de configurações
extractor = PDFConfiguracaoMaoExtractor()

# Buscar configuração específica
info = extractor.extrair_configuracao(letra="B")
imagem = extractor.renderizar_pagina_configuracao(letra="B")
```

---

## 🎯 Vantagens

✅ **Lazy Loading**: Só carrega páginas sob demanda (não estoura memória)  
✅ **Regex Inteligente**: Extrai descrições entre parênteses automaticamente  
✅ **Preenchimento Automático**: Economiza tempo de digitação  
✅ **Descrições Anatômicas**: Melhora precisão da IA generativa  
✅ **Navegação Rápida**: 2847 páginas acessíveis instantaneamente  

---

## ⚡ Performance

- **Busca por termo**: ~5-30 segundos (depende de onde está o termo)
- **Renderizar página**: ~1-2 segundos (DPI 150)
- **Extração de texto**: ~0.5 segundos
- **Memória**: Apenas a página atual fica na RAM

---

## 🔍 Regex de Extração

O sistema usa os seguintes padrões:

```python
# Configuração de Mão
r'[Mm]ão(?:s)?\s+em\s+([A-Z])\b'  # "Mão em B", "Mãos em A"

# Orientação
"palma para cima", "palma para frente", etc.

# Ponto de Articulação
"testa", "boca", "peito", "espaço neutro", etc.

# Movimento
"para frente", "circular", "para cima", etc.
```

---

## 💡 Dicas

1. **Recorte Manual**: Após renderizar a página, você pode recortar apenas a ilustração do sinal usando um editor externo
2. **Edição de Parâmetros**: Os valores extraídos são sugestões - sempre revise e ajuste
3. **Limpar Cache**: Use o botão "🔄 Limpar Parâmetros Extraídos" para resetar
4. **Múltiplos Resultados**: Se a busca retornar vários resultados, escolha o mais relevante

---

## 🐛 Troubleshooting

**"PDF não encontrado"**
- Verifique se o arquivo está em `C:\Users\Jeffe\Downloads\`
- O nome deve ser exatamente: `Dicionario capovilla completo.pdf`

**"Parâmetros não extraídos"**
- Nem todas as páginas têm a descrição entre parênteses
- Você pode preencher manualmente

**"Renderização lenta"**
- Reduza o DPI (padrão: 150)
- Aguarde - PDFs grandes levam alguns segundos

---

**Desenvolvido para otimizar o fluxo de trabalho de criação de materiais pedagógicos de Libras! 🤟**
