# Validação — 21/10/2026

## Verificado
- Python 3.14.2; Node.js 24.19.0; pnpm 11.25.0.
- Ambiente virtual próprio e dependências congeladas em `backend/requirements.txt`; `pip check` sem conflitos.
- Migração `001` executada em um banco novo da demonstração e em bancos temporários de cada teste.
- Seed explícito: seis produtos e 28 vendas fictícias, uma cancelada. Segunda chamada recusada, preservando dados.
- `python -m pytest -q`: **15 testes aprovados**. Cobertura de venda com vários itens, centavos exatos, falha sem baixa parcial, vendas simultâneas, devolução única, preços e categorias históricos, indicadores sem cancelamentos, quantidades inválidas, produtos inativos, código único, valores negativos, horários, saídas retroativas, CSV e CORS.
- `pnpm run build`: TypeScript e build de produção concluídos.
- HTTP 200 na API local e interface servida localmente pela versão compilada.
- Iniciador `iniciar.py` executado de ponta a ponta: backend e frontend responderam HTTP 200. As quatro exportações CSV reais responderam HTTP 200 com BOM UTF-8. Após cancelar a venda de teste de 11458 centavos, a API confirmou o saldo de dez unidades restaurado no produto `DEMO-UI`.
- Navegador: quatro telas, cadastro de produto fictício `DEMO-UI`, estoque inicial de dez unidades, venda com dois produtos no total de R$ 114,58 e cancelamento com confirmação de devolução.
- Layout inspecionado em 1440×1000 e 390×844. Na conferência móvel, a largura do conteúdo foi de 375px dentro do viewport de 390px, sem overflow horizontal da página.
- Capturas: `dashboard-desktop.jpg` e `dashboard-mobile.jpg`. Os gráficos usam dados do backend, sem números fixos no frontend.

## Limitações observadas
- O modo de desenvolvimento do Vite encontrou restrição de acesso ao usar o otimizador no sandbox Windows. A configuração usa `--configLoader runner`, e a versão compilada com `vite preview` foi testada visualmente. Não se afirma que o modo dev foi validado neste ambiente.
- Build informa um chunk maior que 500kB (aproximadamente 636kB antes da compressão), principalmente pela biblioteca de gráficos. Build foi concluído; divisão de código é melhoria futura.
- Starlette avisa que seu adaptador de testes com `httpx` está depreciado. Os testes passaram; migração para o adaptador futuro é pendência de manutenção.
- Scripts PowerShell estão bloqueados pela política local. O iniciador Python/`.cmd` foi incluído para não exigir mudança dessa política.
- Não foram realizados teste de carga de produção, auditoria de segurança completa, teste com leitores de tela ou validação com usuários reais.
- A inspeção de navegador usou dados fictícios e acrescentou um produto e uma venda de teste cancelada. Esses registros foram preservados no histórico; nenhum dado foi apagado.

## Como repetir
No backend: `.\.venv\Scripts\python.exe -m pytest -q`. No frontend: `npx --yes pnpm@11.25.0 run build`. Para executar a apresentação, siga o README.
