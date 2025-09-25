import os
import base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from pdf_utils import gerar_pdf, segmentar, consultar_cnpj, get_plano_info

app = FastAPI(title="API Ficha SESCON")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/consultar-cnpj/{cnpj}")
async def consultar_cnpj_endpoint(cnpj: str):
    """
    Consulta os dados de uma empresa a partir do CNPJ e sugere um plano.
    """
    dados_empresa = consultar_cnpj(cnpj)
    if not dados_empresa:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado ou inválido.")

    cnae = dados_empresa.get("cnae_fiscal")
    cidade = dados_empresa.get("municipio")
    uf = dados_empresa.get("uf")
    
    plano_sugerido_nome = segmentar(cnae, cidade, uf)
    plano_info = get_plano_info(plano_sugerido_nome)
    
    socios = dados_empresa.get("qsa", [])
    
    response_data = {
        "razao_social": dados_empresa.get("razao_social"),
        "endereco": f"{dados_empresa.get('logradouro', '')}, {dados_empresa.get('numero', '')}, {dados_empresa.get('bairro', '')} - {cidade}/{uf}",
        "cnae": cnae,
        "plano_sugerido": plano_sugerido_nome,
        "valor_a_vista": plano_info.get('valor_a_vista'),
        "valor_parcelado": plano_info.get('valor_parcelado'),
        "socios": socios
    }
    
    return JSONResponse(response_data)

@app.post("/gerar-pdf")
async def gerar_pdf_endpoint(request: Request):
    """
    Recebe JSON com campos do formulário e 'signature' (dataURL PNG).
    Retorna o PDF gerado como attachment.
    """
    try:
        data = await request.json()
    except Exception as e:
        return JSONResponse({"erro": "JSON inválido ou content-type inválido"}, status_code=400)

    # Verifica se o plano sugerido é válido antes de prosseguir
    plano_sugerido = data.get("plano", "")
    if "Fora" in plano_sugerido or "CNAE fora" in plano_sugerido:
        return JSONResponse({"erro": "Empresa não qualificada para a associação."}, status_code=400)
    
    dados = {
        "CNPJ": data.get("cnpj",""),
        "Razão Social": data.get("razao",""),
        "Contato Empresa": data.get("email",""),
        "Telefone Empresa": data.get("telefone",""),
        "Endereço": data.get("endereco",""),
        "Plano": plano_sugerido,
        "Serviços de Interesse": ", ".join(data.get("servicos_interesse", [])),
        "Nome Socio PDF": data.get("nome_socio",""),
        "CPF Socio PDF": data.get("cpf_socio",""),
        "Forma Pagamento": data.get("forma_pagamento",""),
        "Termo Aceite": "Sim" if data.get("termo_aceite", False) else "Não"
    }

    signature_data_url = data.get("signature", None)
    signature_path = None
    if signature_data_url:
        try:
            header, encoded = signature_data_url.split(",", 1)
            binary = base64.b64decode(encoded)
            signature_path = "/tmp/signature.png"
            with open(signature_path, "wb") as f:
                f.write(binary)
        except Exception as e:
            print("Erro ao salvar assinatura:", e)
            signature_path = None

    pdf_path = gerar_pdf(dados, signature_path)

    if signature_path and os.path.exists(signature_path):
        try:
            os.remove(signature_path)
        except:
            pass

    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
    else:
        return JSONResponse({"erro": "Não foi possível gerar o PDF."}, status_code=500)
