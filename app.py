from flask import Flask, jsonify, request, json
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import requests
from bs4 import BeautifulSoup


#rodar o flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  #para aceitar caracteres especiais no JSON

#configurar para definir titulo e versao
app.config['SWAGGER'] = {
    'title': 'My Flask API',
    'uiversion': 3
}

#instancia Swagger(app) para habilitar documentação
#acesso a doc em /apidocs ou /flasgger
#permite anotações de rota em docstrings
swagger = Swagger(app)

#autenticação básica
auth = HTTPBasicAuth()

#dicionário users simulando "banco" de credenciais
users = {
    "user1": "password1",
    "user2": "password2"
}

#validar usuario e senha
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password: #retorna usuario correto, senao none
        return username



## PRODUÇÃO
#retorna os dados da produção do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem) e Quantidade.
@app.route('/vitibrasil/producao', methods=['GET'])
@auth.login_required #autenticação obrigatória
def vitibrasil_dados():
    """
    Retorna os dados de Produção do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem) e Quantidade.
    ---
    parameters:
      - name: ano
        in: query
        type: integer
        required: true
        description: Ano para buscar os dados (ex: 2011)
    responses:
      200:
        description: Lista de produção por tipos, produtos e quantidades do ano informado
    """
    ano = request.args.get('ano', type=int)
    if not ano:
        return jsonify({"error": "Parametro 'ano' obrigatorio"}), 400

    url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_02"
    try:
        response = requests.get(url)
        response.encoding = 'latin1'  # Define a codificação correta para o conteúdo
        # Verifica se a requisição foi bem-sucedida 
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível acessar a API"}), 500
        soup = BeautifulSoup(response.text, "html.parser") #modificado para usar response.text invés de response.content
        # Encontra a tabela com os dados de produção
        table = soup.find("table", class_="tb_base tb_dados")
        if not table:
            return jsonify({"error": "Tabela não encontrada"}), 404
        rows = table.find_all("tr")
        data = []
        tipo_atual = None
        for row in rows[1:]:
            cols = row.find_all("td")
            # Atualiza o tipo se encontrar um <td class='tb_item'>
            if len(cols) >= 1 and 'tb_item' in cols[0].get('class', []):
                tipo_atual = cols[0].get_text(strip=True)
                continue
            # Se a linha tem <td class='tb_subitem'>, pega como produto
            if len(cols) >= 2 and 'tb_subitem' in cols[0].get('class', []):
                produto = cols[0].get_text(strip=True)
                try: #tenta decodificar o produto para UTF-8
                    #se o produto contiver caracteres especiais, converte de latin1 para utf-8
                    produto = produto.encode('latin1').decode('utf-8')
                except Exception:
                    pass
                quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                if quantidade_str == '-' or not quantidade_str:
                    continue
                try:
                    quantidade = float(quantidade_str)
                except ValueError:
                    quantidade = None
                if quantidade is not None:
                    data.append({
                        "Tipo": tipo_atual,
                        "Produto": produto,
                        "Quantidade (L.)": quantidade,
                        "Ano": ano
                    })
        #print(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


## PROCESSAMENTO
#retorna os dados da tabela do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem), Quantidade, Ano e Classificação (tb_subopcao) (name='subopcao').
@app.route('/vitibrasil/processamento', methods=['GET'])
@auth.login_required #autenticação obrigatória
def vitibrasil_processamento():
    """
    Retorna todos os dados de processamento do VitiBrasil para o ano informado, para todas as classificações (subopcao).
    ---
    parameters:
      - name: ano
        in: query
        type: integer
        required: true
        description: Ano para buscar os dados (ex: 2021)
    responses:
      200:
        description: Lista de classificações, tipos, produtos e quantidades do ano informado
    """
    ano = request.args.get('ano', type=int)
    if not ano:
        return jsonify({"error": "Parâmetro 'ano' é obrigatório"}), 400

    url_base = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_03"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        #busca a página principal para pegar as subopcoes
        response = requests.get(url_base, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível acessar a API"}), 500
        soup = BeautifulSoup(response.content, "html.parser")
        btns = soup.find_all('button', class_='btn_sopt')
        subopcoes = []
        for btn in btns:
            value = btn.get('value')
            label = btn.get_text(strip=True)
            if value and label:
                subopcoes.append({"value": value, "label": label})

        if not subopcoes:
            return jsonify({"error": "Nenhuma subopcao encontrada"}), 404

        resultado = []
        #para cada subopcao, monta a url e faz o scraping dos tb_subitem
        for sub in subopcoes:
            url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_03&subopcao={sub['value']}"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                continue
            soup_sub = BeautifulSoup(resp.content, "html.parser")
            table = soup_sub.find("table", class_="tb_base tb_dados")
            if not table:
                continue
            rows = table.find_all("tr")
            tipo_atual = None
            for row in rows[1:]:
                cols = row.find_all("td")
                #atualiza o tipo se encontrar um <td class='tb_item'>
                if len(cols) >= 1 and 'tb_item' in cols[0].get('class', []):
                    tipo_atual = cols[0].get_text(strip=True)
                    continue
                #só pega tb_subitem
                if len(cols) >= 2 and 'tb_subitem' in cols[0].get('class', []):
                    produto = cols[0].get_text(strip=True)
                    quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                    #sempre inclui o produto, mesmo se quantidade for '-'
                    if quantidade_str == '-' or not quantidade_str:
                        quantidade = None  # ou 0 se preferir
                    else:
                        try:
                            quantidade = float(quantidade_str)
                        except ValueError:
                            quantidade = None
                    resultado.append({
                        "Ano": ano,
                        "Classificacao": sub['label'],
                        "Cultivar": produto,
                        "Quantidade (L.)": quantidade,
                        "Tipo": tipo_atual
                    })
        return jsonify(resultado)
    except Exception as e:     
        return jsonify({"error": str(e)}), 500

## COMERCIALIZAÇÃO
#retorna os dados da tabela do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem) e Quantidade.
@app.route('/vitibrasil/comercializacao', methods=['GET'])
@auth.login_required #autenticação obrigatória
def vitibrasil_comercializacao():
    """
    Retorna os dados de Produção do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem) e Quantidade.
    ---
    parameters:
      - name: ano
        in: query
        type: integer
        required: true
        description: Ano para buscar os dados (ex: 2011)
    responses:
      200:
        description: Lista de produção por tipos, produtos e quantidades do ano informado
    """
    ano = request.args.get('ano', type=int)
    if not ano:
        return jsonify({"error": "Parametro 'ano' obrigatorio"}), 400

    url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_04"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível acessar a API"}), 500
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", class_="tb_base tb_dados")
        if not table:
            return jsonify({"error": "Tabela não encontrada"}), 404
        rows = table.find_all("tr")
        data = []
        tipo_atual = None
        for row in rows[1:]:
            cols = row.find_all("td")
            # Atualiza o tipo se encontrar um <td class='tb_item'>
            if len(cols) >= 1 and 'tb_item' in cols[0].get('class', []):
                tipo_atual = cols[0].get_text(strip=True)
                continue
            # Se a linha tem <td class='tb_subitem'>, pega como produto
            if len(cols) >= 2 and 'tb_subitem' in cols[0].get('class', []):
                produto = cols[0].get_text(strip=True)
                quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                if quantidade_str == '-' or not quantidade_str:
                    continue
                try:
                    quantidade = float(quantidade_str)
                except ValueError:
                    quantidade = None
                if quantidade is not None:
                    data.append({
                        "Ano": ano,
                        "Produto": produto,
                        "Quantidade (L.)": quantidade,
                        "Tipo": tipo_atual
                        
                    })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

## IMPORTAÇÃO
#retorna os dados de Importação do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem), Quantidade, Ano e Classificação (tb_subopcao) (name='subopcao').
@app.route('/vitibrasil/importacao', methods=['GET'])
@auth.login_required #autenticação obrigatória
def vitibrasil_importacao():
    """
    Retorna os dados de Importação do VitiBrasil para o ano informado, trazendo Ano, Classificacao (botão), País, Quantidade (Kg.), Valor (US$).
    """
    ano = request.args.get('ano', type=int)
    if not ano:
        return jsonify({"error": "Parâmetro 'ano' é obrigatório"}), 400

    url_base = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_05"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url_base, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível acessar a API"}), 500
        soup = BeautifulSoup(response.content, "html.parser")
        btns = soup.find_all('button', class_='btn_sopt')
        resultado = []

        if btns:
            subopcoes = []
            for btn in btns:
                value = btn.get('value')
                label = btn.get_text(strip=True)
                if value and label:
                    subopcoes.append({"value": value, "label": label})

            for sub in subopcoes:
                url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_05&subopcao={sub['value']}"
                resp = requests.get(url, headers=headers)
                if resp.status_code != 200:
                    continue
                soup_sub = BeautifulSoup(resp.content, "html.parser")
                table = soup_sub.find("table", class_="tb_base tb_dados")
                if not table:
                    continue
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        pais = cols[0].get_text(strip=True)
                          # Ignora linhas de total (case insensitive, ignora espaços e o total)
                        if pais.strip().lower() == "total":
                            continue
                        quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                        valor_str = cols[2].get_text(strip=True).replace('.', '').replace(',', '.')
                        quantidade = None if quantidade_str == '-' or not quantidade_str else float(quantidade_str)
                        valor = None if valor_str == '-' or not valor_str else float(valor_str)
                        resultado.append({
                            "Ano": ano,
                            "Classificacao": sub['label'],
                            "País": pais,
                            "Quantidade (Kg.)": quantidade,
                            "Valor (US$)": valor
                        })
        else:
            # Caso não haja subopções, pega a tabela principal
            table = soup.find("table", class_="tb_base tb_dados")
            if not table:
                return jsonify({"error": "Tabela não encontrada"}), 404
            rows = table.find_all("tr")
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    pais = cols[0].get_text(strip=True)
                    quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                    valor_str = cols[2].get_text(strip=True).replace('.', '').replace(',', '.')
                    quantidade = None if quantidade_str == '-' or not quantidade_str else float(quantidade_str)
                    valor = None if valor_str == '-' or not valor_str else float(valor_str)
                    resultado.append({
                        "Ano": ano,
                        "Classificacao": None,
                        "País": pais,
                        "Quantidade (Kg.)": quantidade,
                        "Valor (US$)": valor
                    })
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


## EXPORTAÇÃO
#retorna os dados de Exportação do VitiBrasil para o ano informado, trazendo o Tipo (tb_item), Produto (tb_subitem), Quantidade, Ano e Classificação (tb_subopcao) (name='subopcao').
@app.route('/vitibrasil/exportacao', methods=['GET'])
@auth.login_required #autenticação obrigatória
def vitibrasil_exportacao():
    """
    Retorna os dados de Exportação do VitiBrasil para o ano informado, trazendo Ano, Classificacao (botão), País, Quantidade (Kg.), Valor (US$).
    """
    ano = request.args.get('ano', type=int)
    if not ano:
        return jsonify({"error": "Parâmetro 'ano' é obrigatório"}), 400

    url_base = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_05"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url_base, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível acessar a API"}), 500
        soup = BeautifulSoup(response.content, "html.parser")
        btns = soup.find_all('button', class_='btn_sopt')
        resultado = []

        if btns:
            subopcoes = []
            for btn in btns:
                value = btn.get('value')
                label = btn.get_text(strip=True)
                if value and label:
                    subopcoes.append({"value": value, "label": label})

            for sub in subopcoes:
                url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={ano}&opcao=opt_06&subopcao={sub['value']}"
                resp = requests.get(url, headers=headers)
                if resp.status_code != 200:
                    continue
                soup_sub = BeautifulSoup(resp.content, "html.parser")
                table = soup_sub.find("table", class_="tb_base tb_dados")
                if not table:
                    continue
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        pais = cols[0].get_text(strip=True)
                          # Ignora linhas de total (case insensitive, ignora espaços e o total)
                        if pais.strip().lower() == "total":
                            continue
                        quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                        valor_str = cols[2].get_text(strip=True).replace('.', '').replace(',', '.')
                        quantidade = None if quantidade_str == '-' or not quantidade_str else float(quantidade_str)
                        valor = None if valor_str == '-' or not valor_str else float(valor_str)
                        resultado.append({
                            "Ano": ano,
                            "Classificacao": sub['label'],
                            "País": pais,
                            "Quantidade (Kg.)": quantidade,
                            "Valor (US$)": valor
                        })
        else:
            # Caso não haja subopções, pega a tabela principal
            table = soup.find("table", class_="tb_base tb_dados")
            if not table:
                return jsonify({"error": "Tabela não encontrada"}), 404
            rows = table.find_all("tr")
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    pais = cols[0].get_text(strip=True)
                    quantidade_str = cols[1].get_text(strip=True).replace('.', '').replace(',', '.')
                    valor_str = cols[2].get_text(strip=True).replace('.', '').replace(',', '.')
                    quantidade = None if quantidade_str == '-' or not quantidade_str else float(quantidade_str)
                    valor = None if valor_str == '-' or not valor_str else float(valor_str)
                    resultado.append({
                        "Ano": ano,
                        "Classificacao": None,
                        "País": pais,
                        "Quantidade (Kg.)": quantidade,
                        "Valor (US$)": valor
                    })
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#rodar local
if __name__ == '__main__': 
    app.run(debug=True)



