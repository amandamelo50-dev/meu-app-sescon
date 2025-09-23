# main.py - ADICIONAR ESTAS FUNÇÕES NO INÍCIO
import requests
from fastapi import HTTPException

async def consultar_cnpj_automatico(cnpj: str):
    """Consulta CNPJ na Receita Federal/BrasilAPI"""
    cnpj_limpo = "".join(filter(str.isdigit, cnpj))
    
    if len(cnpj_limpo) != 14:
        return None
        
    try:
        response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}", timeout=10)
        if response.status_code == 200:
            dados = response.json()
            return {
                'razao_social': dados.get('razao_social', ''),
                'endereco': f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
                'cidade': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cnae': dados.get('cnae_fiscal', '')
            }
    except Exception as e:
        print(f"Erro na consulta CNPJ: {e}")
    
    return None

# ADICIONAR ESTA NOVA ROTA NO main.py (antes da rota /gerar-pdf)
@app.get("/consultar-cnpj/{cnpj}")
async def consultar_cnpj_endpoint(cnpj: str):
    """
    Consulta CNPJ na Receita Federal e retorna dados automáticos
    """
    dados = await consultar_cnpj_automatico(cnpj)
    if dados:
        return dados
    else:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado ou inválido")
        # main.py - ADICIONAR ESTAS FUNÇÕES

@app.get("/calcular-valores/{plano}")
async def calcular_valores_endpoint(plano: str):
    """
    Retorna os valores do plano para o mês atual
    """
    from datetime import datetime
    from pdf_utils import prata_pricing, ouro_premium_pricing, prata_aescon_pricing
    
    mes_atual = datetime.now().month
    
    if plano == "Plano Prata":
        tabela = prata_pricing
    elif plano == "Plano Ouro Premium":
        tabela = ouro_premium_pricing
    elif plano == "Prata Aescon":
        tabela = prata_aescon_pricing
    else:
        return {"error": "Plano não encontrado"}
    
    valores = tabela.get(mes_atual, {})
    return {
        "a_vista": f"R$ {valores.get('a_vista', 0):.2f}",
        "parcelado": f"R$ {valores.get('total', 0):.2f} em {valores.get('parcelas', 0)}x de R$ {valores.get('valor_parcela', 0):.2f}",
        "mes": mes_atual
    }

@app.get("/sugerir-plano/{cnpj}")
async def sugerir_plano_endpoint(cnpj: str):
    """
    Sugere o plano baseado no CNPJ (CNAE e cidade)
    """
    dados = await consultar_cnpj_automatico(cnpj)
    if not dados:
        return {"plano": "Não foi possível determinar", "error": "CNPJ não encontrado"}
    
    from pdf_utils import segmentar
    plano = segmentar(dados['cnae'], dados['cidade'], dados['uf'])
    
    return {
        "plano": plano,
        "cnae": dados['cnae'],
        "cidade": dados['cidade'],
        "uf": dados['uf']
    }
