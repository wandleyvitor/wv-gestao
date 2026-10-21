# Entenda o WV Gestão

## Em uma frase
O WV Gestão registra o que entra e sai do estoque, conecta cada venda às suas movimentações e usa esse histórico para apresentar indicadores. É uma demonstração local de portfólio, com dados fictícios.

## As três partes
| Parte | Função | Neste projeto |
|---|---|---|
| Frontend | A tela com que a pessoa interage | React e TypeScript: formulários, navegação, tabelas e gráficos. Vite prepara os arquivos para o navegador. |
| Backend | Confere pedidos e aplica regras | Python e FastAPI: valida quantidades, confere estoque, calcula totais, salva dados e devolve respostas. |
| Banco de dados | Guarda o histórico mesmo depois de fechar a aplicação | SQLite: arquivo local com produtos, vendas, itens de venda e movimentações. |

O frontend conversa com o backend pela API HTTP. O backend acessa o banco usando SQLAlchemy. As migrações do Alembic preparam e versionam a estrutura das tabelas.

## Exemplo: vender dois mouses
1. Você cadastra um mouse com preço de R$ 89,90.
2. Registra uma entrada inicial de dez unidades no estoque.
3. Na tela Vendas, escolhe o mouse e informa duas unidades.
4. A tela envia o ID do produto e a quantidade para o backend.
5. O backend confere se o produto está ativo e se há estoque, consulta o preço e calcula `2 × 8990 = 17980` centavos.
6. Grava a venda de R$ 179,80, seu item e uma movimentação de saída de duas unidades, na mesma transação.
7. O estoque passa a oito unidades e o dashboard considera a venda no período correspondente.

Se a venda tiver mais itens e um deles não tiver saldo, a operação inteira é recusada. Não existe uma venda pela metade.

## Por que não guardar só um número de estoque?
Um saldo isolado informa quantas unidades existem, mas não explica como chegaram ali. O histórico permite conferir entradas, saídas, vendas e devoluções. Neste projeto, o saldo é a soma das movimentações. Cancelar uma venda cria entradas de devolução e preserva o registro original.

## Por que guardar o preço em cada item vendido?
Se o mouse custava R$ 89,90 ontem e custa R$ 99,90 hoje, a venda de ontem precisa continuar valendo R$ 89,90 por unidade. O item da venda guarda o preço praticado, assim como nome e categoria daquele momento.

## O que é uma transação?
É um conjunto de alterações que precisa dar certo por inteiro. A venda e a baixa de estoque são confirmadas juntas. Se algo falhar, as alterações são desfeitas. No SQLite, o bloqueio de escrita também faz uma venda esperar a outra antes de conferir o saldo.

## Onde entra a análise de dados?
- **Definir indicadores:** faturamento é receita de vendas válidas; não é lucro.
- **Definir o recorte:** as datas são interpretadas no horário de Brasília.
- **Conferir qualidade:** cancelamentos ficam fora dos indicadores; preços históricos são preservados.
- **Comparar:** identificar produtos com mais unidades vendidas e categorias com mais receita.
- **Interpretar:** um produto pode vender muitas unidades e gerar menos receita que outro de preço maior.
- **Comunicar limites:** não há custos, impostos ou despesas suficientes para calcular lucro.

## O que significa full stack aqui?
O projeto tem trabalho nas telas, nas regras do servidor e na persistência dos dados. Conseguir navegar entre essas partes ajuda a entender a aplicação completa. Ter o código pronto não significa dominar todas essas tecnologias: estude cada etapa antes de afirmar esse domínio em entrevistas.

## Como comprovar que as regras funcionam?
Os testes automatizados criam bancos temporários e verificam cenários como falta de estoque, vendas simultâneas e cancelamento repetido. O build verifica o TypeScript e gera os arquivos da interface. A conferência visual verifica se a pessoa consegue usar as telas. São verificações diferentes; nenhuma substitui uma auditoria de produção.

## Roteiro de estudo
1. Abra a aplicação e cadastre um produto fictício.
2. Registre dez unidades e venda duas. Explique por que restam oito.
3. Leia `backend/app/schemas.py`: o que é aceito nos pedidos?
4. Leia `backend/app/services.py`, começando em `create_sale`: onde está cada regra?
5. Leia `backend/tests/test_business.py`: como o comportamento é conferido?
6. Veja `frontend/src/api.ts` e procure a chamada de venda em `App.tsx`: o que a tela envia?
7. Cancele a venda e confira a devolução e a mudança no dashboard.

## Como apresentar com transparência
“Desenvolvi um projeto de portfólio com assistência de IA para estudar um fluxo de vendas e estoque. Estou aprendendo a conectar React, uma API em Python e um banco SQLite. A versão local tem dados fictícios e regras testadas para preservar o histórico e evitar estoque negativo.”

Esta explicação não deve ser usada para afirmar que o sistema já atende clientes. Antes de uso na internet, são necessárias autenticação, permissões e revisão de segurança, entre outras melhorias descritas no README.
