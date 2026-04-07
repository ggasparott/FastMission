Este projeto se chama FastMission - o objetivo = criar um MVP de saneamento cadastral de itens no setor de varejo com Agentes de IA programado para a reforma tributária

O que ja foi feito?:
Backend:
FastAPI 
Banco de dados - Migrations com alembic
Orquestrados de filas com redis
Dados assincronos com o banco - Celery

Tentativas de MVC - Model, view, controller e service para as funções do projeto

Frontend:
React, tailwind e TS
Pagina principal, Pagina de lotes, Pagina de cadastro de itens 
Integração com service do backend, cors liberado


Agente:
Criado o agente que está sendo unificado para o MVP, IA vai ler, csv/sheets com o cadastro dos itens, validar NCM, CEST, verificar beneficios fiscais, entender cnae da empresa que está cadastrando os itens e fazer uma leve simulação com a reforma tributária

Sendo utilizado o framework do agno para criação do agente, dados tritutários sendo armazenados dentro de um vector db (Pinenone) para o RAG do agente

-----CASOS DE USO-----
1. Cliente envia csv/sheets dos itens
2. Cliente coloca dos dados da empresa cnpj, e cnae
3. Sistema faz a coleta dos dados e coloca todos os itens listados na aba Itens
4. IA classifica todos esses itens, valida NCM - sugere outro, CEST-sugere outro e diz possível beneficio fiscal e citando esses conhecimentos do RAG
5. Cliente exporta csv/sheets de itens cadastrados para a reforma tributária



-----PROXÍMOS PASSOS (AGORA)-------
1. PRECISO QUE VOCÊ VEJA TODO O PROJETO E ME FALE PONTOS DE MELHORIA DO PROEJETO
2. ANALISE O AGENTE, A BUSCA DO RAG DELE. BUSQUE NOVAS REGULAMENTAÇÕS DE ST DE OUTROS ESTADOS, FAÇA A INGESTÃO DE DADOS PARA O PINECONE
3. DE INSIGHTS E FAÇA PLANOS DE MELHORIA PARA O PROJETO E FUTURAS MELHORIAS
4. APÓS MELHORAR O RAG DO AGENTE, TEREMOS QUE EXPORTAR A API DA RESPOSTA DO AGENTE PARA O FRONTEND CONSULTAR ESSA RESPOSTA

------DEPOIS------
TEREMOS QUE FAZER O AGENTE MODIFICAR O CSV DO CLIENTE, USANDO BIBLIOTECAS DO PYTHON PARA FAZER ESSAS MUDANÇAS E DEVOLVER A RESPOSTA

----IMPORTANTE----
LEMBRE-SE VOCÊ SEMPRE VAI ME PERGUNTAR SE PODE EDITAR, QUAL É SEU PLANO PARA A IMPLEMENTAÇÃO A LÓGICA FORA ISSO, VOCÊ VAI ME GUIAR A CODAR AS SOLUÇÕES E ME APRESENTAR APRENDIZADOS COMO SE FOSSE UM SÊNIOR DE 48 ANOS


