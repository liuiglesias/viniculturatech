# API ViniculturaTech
Este é um projeto de API desenvolvido com Flask para o Tech Challenge Fase 1 5MLET da FIAP, com o objetivo de capturar os dados do Banco de dados de uva, vinho e derivados na Embrapa para facilitação de acompanhamento de comercialização, importação e exportação de uvas processadas no Rio Grande do Sul.



<b>Funcionalidades:</b>
- Autenticação Básica: para maior proteção das rotas sensíveis, usando HTTP. Dados de acesso:
   - user1: <i>password1</i>
   - user2: <i>password2</i>
- Permite ler itens do site http://vitibrasil.cnpuv.embrapa.br/, extraindo dados de páginas web usando BeatifulSoup, especificamente das páginas, usando como pârametro o <b>ano</b> desejado:
   - <b>Produção:</b> Produto, Quantidade e Tipo. Ex>
   - <b>Processamento:</b> Classificação, Cultivar, Quantidade e Tipo
   - <b>Comercialização:</b> Produto, Quantidade e Tipo
   - <b>Importação:</b> Classificação, País, Quantidade e Valor
   - <b>Exportação:</b> Classificação, País, Quantidade e Valor



<b> Estrutura do Projeto </b>
- <b>venv:</b> Ambiente Virtual do Projeto (não-obrigatório, só utilizar as instruções abaixo para criação do ambiente virtual).
- <b>app.py:</b> Aplicação principal.
- <b>README.md:</b> Documentação do projeto.



<b> Como Executar o Projeto </b>  

1. Clonar o repositório:
   
    <i>git clone https://github.com/liuiglesias/viniculturatech</i>
    
    <i>cd my_flask_app</i>

3. Caso não deseje clonar o projeto completo, somente a aplicação. Crie um ambiente virtual:
   
    <i>python -m venv venv</i>
    
    <i>source venv/bin/activate  # No Windows: venv\Scripts\activate</i>

4. Instale as dependências abaixo:

    <i>pip install -r requirements.txt</i> 

5. Execute o Aplicativo

   <i>python app.py</i>

6. Para Acessar:
   - <b>Produção:</b> http://127.0.0.1:5000/vitibrasil/producao?ano={ano}
   - <b>Processamento:</b> http://127.0.0.1:5000/vitibrasil/processamento?ano={ano}
   - <b>Comercialização:</b> http://127.0.0.1:5000/vitibrasil/comercializacao?ano={ano}
   - <b>Importação:</b> http://127.0.0.1:5000/vitibrasil/importacao?ano={ano}
   - <b>Exportação:</b> http://127.0.0.1:5000/vitibrasil/exportacao?ano={ano}

   
