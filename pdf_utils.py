import os
import requests
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import pytz
# A biblioteca PIL/Image é necessária para a função gerar_pdf, então mantemos a importação
try:
    from PIL import Image
except ImportError:
    # Apenas para garantir que o script não quebre se o ambiente não tiver a biblioteca
    print("A biblioteca PIL (Pillow) não está instalada. A inserção da imagem da assinatura pode falhar.")
    pass 

# -------------------- CONFIGURAÇÃO E CONSTANTES --------------------
# Atualizado para incluir o Plano Ouro que estava faltando no mapa
CNPJ_SESCON = "62.638.168/0001-84"
CNPJ_AESCON = "62.636.675/0001-89"

cnaes_ouro = {"6920601", "6920602"}
cnaes_prata = {
    "0230600", "5229002", "5229099", "5240101", "5250804", "5250805", "6461100", "6462000", "6463800",
    "6611801", "6611802", "6611803", "6611804", "6612605", "6613400", "6619302", "6619303", "6619399",
    "6621501", "6621502", "6629100", "6630400", "6911702", "6911703", "7020400", "7119701", "7119702",
    "7119703", "7119704", "7120100", "7120100", "7210000", "7220700", "7319004", "7319002", "7420002", "7420005",
    "7490101", "7490103", "7490104", "7490105", "7490199", "8020000", "8211300", "8219999", "8550302",
    "8599604", "8660700", "9411100", "9412000", "9430800", "9491000", "9499500" ,"8299799","7320300"
}

cidades_tupa = {"adamantina","bastos","dracena","flora rica","florida paulista","irapuru","junqueiropolis",
"lucelia","mariapolis","monte castelo","nova guataporanga","osvaldo cruz","ouro verde","pacaembu","parapua",
"pauliceia","pedreira","rinopolis","sagres","salmourao","sao joao do pau d alho","santa mercedes","tupa","tupi paulista",
"herculandia","piacatu","queiros","quintana","luziania"}

cidades_campinas = {"americana","arthur nogueira","cosmopolis","engenheiro coelho","holambra","indaiatuba",
"itatiba","jaguariuna","monte mor","nova odessa","paulinia","santo antonio de posse","sumare",
"valinhos","vinhedro","campinas"}

cidades_santos = {"mongagua","sao vicente","bertioga","praia grande","itariri","guaruja","itanhaem","cubata",
"peruibe","santos"}

links_planos = {
    "Plano Ouro Premium": "https://testeamandaestatestanto.my.canva.site/ouro-premium",
    "Plano Prata": "https://testeamandaestatestanto.my.canva.site/prata",
    "Plano Ouro": "https://link-plano-ouro.com", # Adicionado link para Plano Ouro (existente no select do HTML)
    "Prata Aescon": "https://www.canva.com/design/DAGqEt4Cmb8/wbIcg1Pg825iVmWQvRaurQ/view?utm_content=DAGqEt4Cmb8&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h93a130898d"
}

# Assumindo que o "Plano Ouro" utiliza a mesma tabela de preços do "Plano Prata" (ou ajuste se for diferente)
prata_pricing = {
    1: {"total": 720.00, "parcelas": 12, "valor_parcela": 60.00, "a_vista": 660.00},
    2: {"total": 660.00, "parcelas": 11, "valor_parcela": 60.00, "a_vista": 607.00},
    3: {"total": 600.00, "parcelas": 10, "valor_parcela": 60.00, "a_vista": 552.00},
    4: {"total": 540.00, "parcelas": 9, "valor_parcela": 60.00, "a_vista": 497.00},
    5: {"total": 480.00, "parcelas": 8, "valor_parcela": 60.00, "a_vista": 442.00},
    6: {"total": 420.00, "parcelas": 7, "valor_parcela": 60.00, "a_vista": 386.00},
    7: {"total": 360.00, "parcelas": 6, "valor_parcela": 60.00, "a_vista": 331.00},
    8: {"total": 300.00, "parcelas": 5, "valor_parcela": 60.00, "a_vista": 276.00},
    9: {"total": 240.00, "parcelas": 4, "valor_parcela": 60.00, "a_vista": 221.00},
    10: {"total": 180.00, "parcelas": 3, "valor_parcela": 60.00, "a_vista": 166.00},
    11: {"total": 120.00, "parcelas": 2, "valor_parcela": 60.00, "a_vista": 110.00},
    12: {"total": 60.00, "parcelas": 1, "valor_parcela": 60.00, "a_vista": 60.00},
}
# Plano Ouro (novo select) usa a mesma tabela
ouro_pricing = prata_pricing 

ouro_premium_pricing = {
    1: {"total": 1140.00, "parcelas": 12, "valor_parcela": 95.00, "a_vista": 1046.00},
    2: {"total": 1045.00, "parcelas": 11, "valor_parcela": 95.00, "a_vista": 961.00},
    3: {"total": 950.00, "parcelas": 10, "valor_parcela": 95.00, "a_vista": 874.00},
    4: {"total": 855.00, "parcelas": 9, "valor_parcela": 95.00, "a_vista": 787.00},
    5: {"total": 760.00, "parcelas": 8, "valor_parcela": 95.00, "a_vista": 700.00},
    6: {"total": 665.00, "parcelas": 7, "valor_parcela": 95.00, "a_vista": 611.00},
    7: {"total": 570.00, "parcelas": 6, "valor_parcela": 95.00, "a_vista": 524.00},
    8: {"total": 475.00, "parcelas": 5, "valor_parcela": 95.00, "a_vista": 437.00},
    9: {"total": 380.00, "parcelas": 4, "valor_parcela": 95.00, "a_vista": 350.00},
    10: {"total": 285.00, "parcelas": 3, "valor_parcela": 95.00, "a_vista": 263.00},
    11: {"total": 190.00, "parcelas": 2, "valor_parcela": 95.00, "a_vista": 175.00},
    12: {"total": 95.00, "parcelas": 1, "valor_parcela": 95.00, "a_vista": 95.00},
}

prata_aescon_pricing = {
    1: {"total": 420.00, "parcelas": 12, "valor_parcela": 35.00, "a_vista": 386.00},
    2: {"total": 385.00, "parcelas": 11, "valor_parcela": 35.00, "a_vista": 354.00},
    3: {"total": 350.00, "parcelas": 10, "valor_parcela": 35.00, "a_vista": 322.00},
    4: {"total": 315.00, "parcelas": 9, "valor_parcela": 35.00, "a_vista": 290.00},
    5: {"total": 280.00, "parcelas": 8, "valor_parcela": 35.00, "a_vista": 258.00},
    6: {"total": 245.00, "parcelas": 7, "valor_parcela": 35.00, "a_vista": 225.00},
    7: {"total": 210.00, "parcelas": 6, "valor_parcela": 35.00, "a_vista": 193.00},
    8: {"total": 175.00, "parcelas": 5, "valor_parcela": 35.00, "a_vista": 161.00},
    9: {"total": 140.00, "parcelas": 4, "valor_parcela": 35.00, "a_vista": 129.00},
    10: {"total": 105.00, "parcelas": 3, "valor_parcela": 35.00, "a_vista": 97.00},
    11: {"total": 70.00, "parcelas": 2, "valor_parcela": 35.00, "a_vista": 65.00},
    12: {"total": 35.00, "parcelas": 1, "valor_parcela": 35.00, "a_vista": 35.00},
}

# Mapeamento dos valores do select do HTML para o nome completo do plano
PLANO_MAP_REVERSE = {
    "ouroPremium": "Plano Ouro Premium",
    "planoPrata": "Plano Prata",
    "ouro": "Plano Ouro"
}

# -------------------- FUNÇÕES DE BACKEND (DO SEU CÓDIGO) --------------------

def consultar_cnpj(cnpj):
    """Consulta dados de CNPJ via BrasilAPI."""
    cnpj = "".join(filter(str.isdigit, str(cnpj)))
    try:
        resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        print("Erro ao consultar BrasilAPI:", e)
        return None

def get_plano_info(plano):
    """Retorna os valores de anuidade proporcionais para o mês atual."""
    mes_atual = datetime.now().month
    tabela = {}
    if plano == "Plano Prata":
        tabela = prata_pricing
    elif plano == "Plano Ouro":
        tabela = ouro_pricing # Usa a mesma tabela Prata
    elif plano == "Plano Ouro Premium":
        tabela = ouro_premium_pricing
    elif plano == "Prata Aescon":
        tabela = prata_aescon_pricing
    else:
        # Retorna N/A se o plano não for encontrado (ex: plano de erro)
        return {"valor_a_vista": "N/A", "valor_parcelado": "N/A"}

    valores = tabela.get(mes_atual, {})
    a_vista = valores.get('a_vista', 0.0)
    total = valores.get('total', 0.0)
    parcelas = valores.get('parcelas', 0)
    valor_parcela = valores.get('valor_parcela', 0.0)
    
    # Formatação do valor parcelado
    valor_parcelado = f"R$ {total:.2f} em {parcelas}x de R$ {valor_parcela:.2f}"
    
    return {
        "valor_a_vista": f"R$ {a_vista:.2f}".replace('.', ','),
        "valor_parcelado": valor_parcelado.replace('.', ','),
    }

def segmentar(cnae, cidade, uf):
    """Determina o plano sugerido com base no CNAE e localidade."""
    cnae = str(cnae)
    cidade = (cidade or "").strip().lower()
    uf = (uf or "").strip().upper()

    if uf != "SP":
        return "Fora de SP – Não podemos associar."

    if cnae in cnaes_ouro and (cidade in cidades_tupa or cidade in cidades_campinas or cidade in cidades_santos):
        return "Prata Aescon" # Apenas AESCON

    if cidade in cidades_tupa:
        return "Fora da região (Tupã). E-mail: sescontupan@unisite.com.br"
    if cidade in cidades_campinas:
        return "Fora da região (Campinas). E-mail: sesconcampinas@sesconcampinas.org.br"
    if cidade in cidades_santos:
        return "Fora da região (Santos). E-mail: sheron@sesconbs.org.br"

    if cnae in cnaes_ouro:
        return "Plano Ouro Premium" # Ouro Premium (SESCON + AESCON)
    if cnae in cnaes_prata:
        return "Plano Prata" # Plano Prata (SESCON)

    return "CNAE fora do escopo. Contate Fecomércio: (11) 3254-1700"

def get_logo_path_and_cnpj_footer(plano):
    """Determina o caminho do logo e quais CNPJs incluir no rodapé com base no plano."""
    # Como não temos acesso aos seus arquivos locais, usaremos placeholders para simular
    # o caminho para um diretório temporário ou que o logo já está no ambiente do PHP/servidor
    
    # OBSERVAÇÃO: MANTIVE A LÓGICA DO SEU CÓDIGO. PARA PRODUÇÃO, o `base` deve ser ajustado
    # para o local onde as imagens estão salvas.
    base = "/tmp" 
    logo_file_name = None
    cnpj_footer = []
    
    # Simulação de arquivos de logo (O usuário deve garantir que esses arquivos estão no /tmp ou no caminho correto)
    if plano == "Plano Ouro Premium":
        logo_file_name = "logo_sescon_aescon.png.png"
        cnpj_footer = [CNPJ_SESCON, CNPJ_AESCON]
    elif plano == "Plano Prata" or plano == "Plano Ouro":
        logo_file_name = "sescon_sp_logo.png.png"
        cnpj_footer = [CNPJ_SESCON]
    elif plano == "Prata Aescon":
        logo_file_name = "logo_aescon.png.png"
        cnpj_footer = [CNPJ_AESCON]
    else:
        return None, []
        
    logo_path = os.path.join(base, logo_file_name)
    
    # Nesta simulação, retornamos apenas o nome do arquivo, pois o ambiente real não tem os arquivos
    return (logo_file_name if os.path.exists(logo_path) else None), cnpj_footer

def gerar_pdf(dados, signature_img_path=None):
    """Gera o arquivo PDF com os dados da inscrição."""
    plano = dados.get("Plano", "")
    logo_path, cnpjs_to_show = get_logo_path_and_cnpj_footer(plano)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Inserção do Logo (Simulação)
    if logo_path:
        # Se o logo for acessível, ele será inserido aqui.
        pass # Lógica de inserção de imagem omitida para evitar dependências de arquivos não acessíveis.

    pdf.set_font("helvetica", "B", 13)
    pdf.set_y(15)
    pdf.cell(0, 8, "Ficha de Inscrição - Associação SESCON-SP / AESCON-SP", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    # DADOS DA EMPRESA
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "DADOS DA EMPRESA", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Razão Social: {dados.get('Razão Social','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"CNPJ: {dados.get('CNPJ','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Endereço Completo (inclui complemento, cidade e UF)
    endereco_completo = f"{dados.get('Endereço','')}, {dados.get('Complemento','')}, {dados.get('Cidade','')}/{dados.get('UF','')}"
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 7, f"Endereço: {endereco_completo}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 7, f"E-mail: {dados.get('Contato Empresa','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Telefone: {dados.get('Telefone Empresa','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Novos campos do HTML
    pdf.cell(0, 6, f"CRC da Empresa: {dados.get('CRC Empresa','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Segmento da Empresa: {dados.get('Segmento','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.cell(0, 6, f"Serviços de Interesse: {dados.get('Serviços de Interesse','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # DADOS DO SÓCIO/RESPONSÁVEL
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "DADOS DO SÓCIO/RESPONSÁVEL PELO PREENCHIMENTO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Nome Completo do Sócio: {dados.get('Nome Socio PDF','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"CPF do Sócio: {dados.get('CPF Socio PDF','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # PLANO SUGERIDO
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "PLANO SUGERIDO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 7, f"Plano Sugerido: {plano}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if plano == "Plano Ouro Premium":
        pdf.cell(0, 6, "Este plano inclui associação ao SESCON-SP e AESCON-SP + Contribuição Representativa.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    elif plano == "Plano Prata" or plano == "Plano Ouro":
        pdf.cell(0, 6, "Este plano inclui associação ao SESCON-SP.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    elif plano == "Prata Aescon":
        pdf.cell(0, 6, "Este plano inclui associação ao AESCON-SP.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # FORMA DE PAGAMENTO SUGERIDA E VALORES
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "VALORES DA ANUIDADE PROPORCIONAL", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 10)
    
    # Obtém os valores calculados pelo backend
    plano_info = get_plano_info(plano)
    valor_a_vista = plano_info.get("valor_a_vista", "N/A")
    valor_parcelado = plano_info.get("valor_parcelado", "N/A")

    # A Forma de Pagamento não está no HTML atual, usa default
    pdf.cell(0, 6, f"Forma de Pagamento (Desejada): {dados.get('Forma Pagamento','Não Informada')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Valor À Vista: {valor_a_vista}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Valor Parcelado: {valor_parcelado}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Textos Legais
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0,5, "A anuidade informada refere-se ao valor proporcional aos meses restantes do ano corrente. No próximo ciclo de renovação, o valor será referente à anuidade integral.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.multi_cell(0,5, "Declaro estar de acordo com as políticas de associação do SESCON-SP e solicito análise para me tornar associado. Ao enviar esta ficha assinada, para associados@sescon.org.br, estou ciente e de acordo com o processo de associação.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # Dados de Preenchimento
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
    pdf.cell(0,6, f"Empresa: {dados.get('Razão Social','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0,6, f"Data do Preenchimento: {now.strftime('%d/%m/%Y %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # Assinatura (Simulação)
    pdf.ln(20)
    pdf.cell(0,6, "_"*60, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0,6, "Assinatura do Sócio da Empresa", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Rodapé CNPJs
    pdf.set_font("helvetica", "I", 9)
    for cnpj_text in cnpjs_to_show:
        pdf.cell(0,5, f"CNPJ: {cnpj_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Output do Arquivo
    safe_name = "".join(c for c in dados.get("Razão Social","empresa") if c.isalnum() or c.isspace()).replace(" ","_")
    out_path = os.path.join("/tmp", f"ficha_associacao_{safe_name}.pdf")
    try:
        pdf.output(out_path)
        return out_path
    except Exception as e:
        print("Erro ao gerar PDF:", e)
        return None

# -------------------- FUNÇÃO PRINCIPAL DE INTEGRAÇÃO COM O HTML --------------------

def processar_inscricao(
    cnpj, 
    crcEmpresa,
    razaoSocial, # Preenchido pelo JS
    endereco, # Preenchido pelo JS
    complemento, # Preenchido pelo JS
    segmento,
    nomeSocio,
    cpfSocio,
    telefone,
    email,
    plano, # Valor do select (e.g., 'ouroPremium')
    valorProporcional, # Valor proporcional simulado pelo JS
    
    # Campos que não estão no seu HTML atual, mas são esperados pelo PDF.
    servicos_interesse=None, # Deve ser adicionado ao HTML.
    forma_pagamento=None # Deve ser adicionado ao HTML (Radio/Select).
):
    """
    Função de alto nível que simula o processamento do formulário de inscrição.
    """
    
    # 1. Consulta CNPJ (para obter dados de cidade/UF e CNAE)
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    dados_cnpj = consultar_cnpj(cnpj_clean)

    if not dados_cnpj:
        return {"status": "error", "message": "CNPJ inválido ou consulta falhou.", "plan_name": None}

    razao = dados_cnpj.get("razao_social", razaoSocial or "N/A")
    cidade = dados_cnpj.get("municipio", "N/A")
    uf = dados_cnpj.get("uf", "N/A")
    cnae = str(dados_cnpj.get("cnae_fiscal", ""))
    
    # Garante que o endereço usado é o preenchido no formulário (via JS ou manual)
    endereco_final = f"{endereco} - {dados_cnpj.get('bairro', '')}" if endereco else "N/A"

    # 2. Segmentação de Plano
    plano_segmentado = segmentar(cnae, cidade, uf)
    
    # Se o plano segmentado for um plano de associação (e não uma mensagem de erro/contato), 
    # ele será comparado com a seleção do usuário. 
    # Priorizamos a seleção do usuário se estiver dentro dos planos válidos, 
    # caso contrário, usamos o segmentado (especialmente para erros).
    
    plano_selecionado_completo = PLANO_MAP_REVERSE.get(plano, "Plano Prata") # Pega o nome completo do plano escolhido
    
    planos_validos = ["Plano Ouro Premium", "Plano Prata", "Plano Ouro", "Prata Aescon"]
    
    if plano_segmentado in planos_validos:
        plano_final = plano_segmentado # Força a sugestão do backend (regra de negócio)
    elif plano_selecionado_completo in planos_validos:
        plano_final = plano_selecionado_completo
    else:
        # Se for um plano de erro/contato, usamos ele.
        plano_final = plano_segmentado 
        
    # 3. Construção do Dicionário para o PDF
    pdf_dados = {
        "CNPJ": cnpj,
        "Razão Social": razao,
        "Endereço": endereco_final,
        "Complemento": complemento or "",
        "Cidade": cidade,
        "UF": uf,
        "Contato Empresa": email,
        "Telefone Empresa": telefone,
        "CRC Empresa": crcEmpresa or "N/A",
        "Segmento": segmento or "N/A",
        "Serviços de Interesse": servicos_interesse or "Não Informado", 
        
        "Nome Socio PDF": nomeSocio,
        "CPF Socio PDF": cpfSocio,
        
        "Plano": plano_final,
        "Forma Pagamento": forma_pagamento or "Não Informada"
    }

    # 4. Geração do PDF
    pdf_path = gerar_pdf(pdf_dados)

    # 5. Retorno
    if pdf_path:
        link_do_plano = links_planos.get(plano_final, "https://www.sesconsp.org.br/fale-conosco")
        return {
            "status": "success",
            "message": f"Ficha gerada com sucesso! Seu plano sugerido é: **{plano_final}**",
            "plan_name": plano_final,
            "pdf_path": pdf_path,
            "plan_link": link_do_plano,
            "plano_info": get_plano_info(plano_final)
        }
    else:
        return {"status": "error", "message": "Erro ao gerar PDF.", "plan_name": plano_final}

# -------------------- EXEMPLO DE USO --------------------
# Para testar:
# resultado = processar_inscricao(
#     cnpj="09.043.954/0001-56", 
#     crcEmpresa="SP-123456/O-1",
#     razaoSocial="BIU CONTA PRO MAX LTDA",
#     endereco="AV PAULISTA, 1471",
#     complemento="ANDAR 10",
#     segmento="Serviços Legais e Contábeis",
#     nomeSocio="EDSON LUIZ CANDIDO",
#     cpfSocio="111.111.111-11",
#     telefone="(11) 99999-9999",
#     email="contato@empresa.com.br",
#     plano="ouroPremium",
#     valorProporcional="R$ 380,00"
# )
# print(resultado)
