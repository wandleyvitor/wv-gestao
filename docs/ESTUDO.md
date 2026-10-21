# Primeira etapa para estudar

Comece pelo fluxo de uma venda, não por todas as telas ao mesmo tempo.

1. Em `schemas.py`, veja por que quantidade precisa ser um inteiro positivo.
2. Em `services.py`, localize `create_sale`. Identifique de onde vem o preço e onde o total é calculado.
3. Em `db.py`, veja o bloco `writing`: tudo é confirmado junto ou desfeito em caso de erro.
4. Em `tests/test_business.py`, leia `test_insufficient_has_no_partial_write` e explique por que uma falha no segundo produto não baixa o primeiro.

Exercício no papel: dois produtos de R$ 12,34 e um de R$ 89,90. O backend calcula `2 × 1234 + 1 × 8990 = 11458` centavos, ou R$ 114,58. O cancelamento cria entradas; não apaga a venda.

Para demonstrar seu trabalho de análise, explique também a diferença entre faturamento e lucro e por que vendas canceladas ficam fora dos indicadores.
