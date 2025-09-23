# main.py - BACKEND COMPLETO COM CONSULTA CNPJ
import os
import base64
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pdf_utils import gerar_pdf

app = FastAPI(title="API Ficha SESCON")

# CORS liberado para desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== FUNÇÃO DE CONSULTA CNPJ ==========
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
                'endereco': f"{dados.get('logradouro', '')}, {dados.get('numero', '')} - {dados.get('bairro', '')}",
                'cidade': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cnae': str(dados.get('cnae_fiscal', ''))
            }
        else:
            print(f"Erro na API Brasil: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro na consulta CNPJ: {e}")
        return None

# ========== ROTA DE CONSULTA CNPJ ==========
@app.get("/consultar-cnpj/{cnpj}")
async def consultar_cnpj_endpoint(cnpj: str):
    """
    Consulta CNPJ na Receita Federal e retorna dados automáticos
    """
    print(f"Consultando CNPJ: {cnpj}")
    dados = await consultar_cnpj_automatico(cnpj)
    if dados:
        print(f"Dados encontrados: {dados}")
        return dados
    else:
        print("CNPJ não encontrado")
        raise HTTPException(status_code=404, detail="CNPJ não encontrado ou inválido")

# ========== ROTA DE CÁLCULO DE VALORES ==========
@app.get("/calcular-valores/{plano}")
async def calcular_valores_endpoint(plano: str):
    """
    Retorna os valores do plano para o mês atual
    """
    from datetime import datetime
    from pdf_utils import prata_pricing, ouro_premium_pricing, prata_aescon_pricing
    
    mes_atual = datetime.now().month
    print(f"Calculando valores para {plano} - mês {mes_atual}")
    
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

# ========== ROTA DE SUGESTÃO DE PLANO ==========
@app.get("/sugerir-plano/{cnpj}")
async def sugerir_plano_endpoint(cnpj: str):
    """
    Sugere o plano baseado no CNPJ (CNAE e cidade)
    """
    print(f"Sugerindo plano para CNPJ: {cnpj}")
    dados = await consultar_cnpj_automatico(cnpj)
    if not dados:
        return {"plano": "Não foi possível determinar", "error": "CNPJ não encontrado"}
    
    from pdf_utils import segmentar
    plano = segmentar(dados['cnae'], dados['cidade'], dados['uf'])
    
    print(f"Plano sugerido: {plano} para CNAE {dados['cnae']} em {dados['cidade']}/{dados['uf']}")
    
    return {
        "plano": plano,
        "cnae": dados['cnae'],
        "cidade": dados['cidade'],
        "uf": dados['uf']
    }

# ========== ROTA PRINCIPAL DE GERAÇÃO DE PDF ==========
@app.post("/gerar-pdf")
async def gerar_pdf_endpoint(request: Request):
    """
    Recebe JSON com campos do formulário e 'signature' (dataURL PNG).
    Retorna o PDF gerado como attachment.
    """
    try:
        data = await request.json()
        print("Dados recebidos para gerar PDF")
    except Exception as e:
        print(f"Erro no JSON: {e}")
        return JSONResponse({"erro": "JSON inválido"}, status_code=400)

    # Mapear campos para o dicionário que gerar_pdf espera
    dados = {
        "CNPJ": data.get("cnpj",""),
        "Razão Social": data.get("razao",""),
        "Contato Empresa": data.get("email",""),
        "Telefone Empresa": data.get("telefone",""),
        "Endereço": data.get("endereco",""),
        "Plano": data.get("plano",""),
        "Serviço": data.get("servico",""),
        "Tipo Responsavel": data.get("tipo_resp",""),
        "Nome Socio PDF": data.get("nome_socio",""),
        "CPF Socio PDF": data.get("cpf_socio",""),
        "Nome Outro Responsavel": data.get("nome_outro",""),
        "Contato Outro Responsavel": data.get("contato_outro",""),
        "CNAE Fiscal": data.get("cnae",""),
        "Cidade": data.get("cidade",""),
        "UF": data.get("uf",""),
        "Forma Pagamento": data.get("forma_pagamento",""),
        "Termo Aceite": "Sim" if data.get("termo_aceite", False) else "Não"
    }

    print(f"Gerando PDF para: {dados['Razão Social']}")

    # signature espera "data:image/png;base64,...."
    signature_data_url = data.get("signature", None)
    signature_path = None
    if signature_data_url:
        try:
            header, encoded = signature_data_url.split(",", 1)
            binary = base64.b64decode(encoded)
            signature_path = "/tmp/signature.png"
            with open(signature_path, "wb") as f:
                f.write(binary)
            print("Assinatura salva temporariamente")
        except Exception as e:
            print(f"Erro ao salvar assinatura: {e}")
            signature_path = None

    pdf_path = gerar_pdf(dados, signature_path)

    # limpa assinatura temporária
    if signature_path and os.path.exists(signature_path):
        try:
            os.remove(signature_path)
            print("Assinatura temporária removida")
        except:
            pass

    if pdf_path and os.path.exists(pdf_path):
        print(f"PDF gerado com sucesso: {pdf_path}")
        return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
    else:
        print("Erro ao gerar PDF")
        return JSONResponse({"erro": "Não foi possível gerar o PDF."}, status_code=500)

# ========== ROTA DE HEALTH CHECK ==========
@app.get("/")
async def root():
    return {"message": "API Ficha SESCON está funcionando!", "status": "online"}

# ========== INICIAR SERVIDOR ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
