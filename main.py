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
