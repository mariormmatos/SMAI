
---

## `instrucoes.md`

```md
# Instruções de desenvolvimento (Codex + VS Code)

Este ficheiro define como trabalhar no projeto SMAI usando o Codex no terminal do VS Code.
O objetivo é gerar alterações consistentes, testáveis e com boa legibilidade.

---

## 1) Como usar o Codex no terminal
Quando precisares de uma alteração, escreve no terminal como um pedido de tarefa, por exemplo:

- “Codex: refatora os charts para um módulo separado e mantém compatibilidade com app.py”
- “Codex: adiciona caching (st.cache_data) para yfinance + fallback se falhar”
- “Codex: cria requirements.txt e atualiza README com comandos”

### Pedidos que devem incluir sempre
- **Contexto:** em que ficheiro(s) mexer
- **Objetivo:** o comportamento esperado
- **Critérios de aceitação:** como validar que ficou certo
- **Restrições:** sem quebrar UI, manter tabs, manter tema dark, etc.

---

## 2) Regras técnicas obrigatórias
### UI & UX
- Tema dark consistente (evitar backgrounds brancos).
- Contraste elevado para legibilidade.
- KPIs em cards dark; texto em branco; cores semânticas (verde/vermelho) apenas para variações.
- Gráficos sempre interativos com **hover** e **markers**.

### Dados
- Fonte base: `yfinance`.
- Implementar fallback e mensagens claras quando faltam campos.
- NUNCA assumir que uma coluna existe: validar e degradar graciosamente.
- Usar `st.cache_data` com TTL para reduzir latência.

### Performance
- Evitar downloads repetidos: cache por ticker/timeframe.
- Evitar loops de tickers sem progress/limites (no screener usar batching e `st.progress`).

### Qualidade de código
- Funções pequenas e focadas.
- Sem duplicação: criar helpers (`formatting.py`, `charts.py`).
- Tratamento de erros: try/except com fallback e `st.warning` contextual.
- Logging leve (opcional) via prints controlados ou `st.status`.

---

## 3) Padrões de nomenclatura e organização
- `snake_case` para funções e variáveis.
- `PascalCase` apenas para dataclasses/classes.
- Separar responsabilidades:
  - `core/` = dados, cálculos, scoring, DCF, sentiment
  - `ui/` = CSS/tema, components, charts, pages

---

## 4) Dependências
Manter atualizado:
- `requirements.txt` com versões (idealmente travadas) quando o projeto estabilizar.

Exemplo:
- streamlit
- yfinance
- pandas
- numpy
- plotly
- requests
- textblob (opcional)

---

## 5) Checklist antes de commit (manual)
- [ ] A app abre sem erros: `python -m streamlit run SMAI/app.py`
- [ ] Tabs principais aparecem e navegam.
- [ ] Charts com hover e eixos legíveis (~s).
- [ ] Sem caixas brancas inesperadas.
- [ ] Falhas de API não crasham a app (mostram aviso + continuam).
- [ ] Screener funciona com universo default e CSV.

---

## 6) Como pedir alterações ao Codex (template)
Copiar/colar e preencher:

**Tarefa:**
- O que preciso mudar?

**Ficheiros:**
- Em que ficheiros mexer?

**Comportamento esperado:**
- O que deve acontecer no UI?

**Critérios de aceitação:**
- Como valido que ficou correto?

**Notas/Restrições:**
- Não quebrar tabs, manter estilo dark, manter hover nos charts, etc.
