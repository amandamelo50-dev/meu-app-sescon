# main.py
import os
import base64
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pdf_utils import gerar_pdf

app = FastAPI(title="API Ficha SESCON")

# CORS liberado para desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/gerar-pdf")
async def gerar_pdf_endpoint(request: Request):
    """
    Recebe JSON com campos do formulário e 'signature' (dataURL PNG).
    Retorna o PDF gerado como attachment.
    """
    try:
        data = await request.json()
    except Exception as e:
        return JSONResponse({"erro": "JSON inválido ou inválido content-type"}, status_code=400)

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
        except Exception as e:
            # se a assinatura falhar, seguimos sem ela (o PDF terá espaço em branco)
            print("Erro ao salvar assinatura:", e)
            signature_path = None

    pdf_path = gerar_pdf(dados, signature_path)

    # limpa assinatura temporária
    if signature_path and os.path.exists(signature_path):
        try:
            os.remove(signature_path)
        except:
            pass

    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
    else:
        return JSONResponse({"erro": "Não foi possível gerar o PDF."}, status_code=500)
