<?php
// ==============================================================================
// FICHEIRO: processar.php
// FUNÇÃO: RECEBER DADOS DO FORMULÁRIO E REALIZAR AUTOMAÇÃO CRÍTICA
// ==============================================================================

// 1. Configuração Inicial e Inclusão de Bibliotecas
// NECESSÁRIO: Instalar o Composer e as bibliotecas do Google Sheets e API CNPJ.
// require 'vendor/autoload.php'; 

// Recebe os dados brutos do formulário
$cnpj_raw = $_POST['cnpj'] ?? '';
$plano_escolhido = $_POST['plano'] ?? '';
$cpf_socio = $_POST['cpfSocio'] ?? '';
// ... (receber todos os outros campos)

// Limpeza de dados
$cnpj_limpo = preg_replace('/[^0-9]/', '', $cnpj_raw);
$erros = []; // Array para armazenar mensagens de erro

// ==============================================================================
// 2. LÓGICA CRÍTICA: VALIDAÇÃO DE CNPJ E BASE TERRITORIAL
// ==============================================================================

// CHAMADA À API CNPJ AQUI (Ex: ReceitaWS, Serasa)
// Esta API irá retornar a Razão Social, Endereço e, PRINCIPALMENTE, a CIDADE.
$dados_api_cnpj = buscar_dados_cnpj($cnpj_limpo); // Função a ser implementada

if (empty($dados_api_cnpj) || !validar_cnpj_pela_receita($cnpj_limpo)) {
    $erros[] = "CNPJ inválido ou inativo na Receita Federal.";
} else {
    $cidade_empresa = $dados_api_cnpj['cidade']; 

    // Regra de Negócio: Bloqueio/Alerta de Base Territorial
    if (in_array(strtoupper($cidade_empresa), ['CAMPINAS', 'SANTOS', 'TUPÃ', 'ETC'])) {
        $erros[] = "Região fora da base territorial do SESCON-SP. Sua inscrição será analisada pela AESCON-SP ou pela Regional correspondente.";
        // O código pode continuar, mas marcando o registro com um aviso especial.
    }
}

// Se houver erros, parar o processo e notificar o usuário (redirecionar para uma página de erro)
if (!empty($erros)) {
    // Redirecionar para uma página de erro mostrando $erros.
    die(implode("<br>", $erros)); 
}

// ==============================================================================
// 3. LÓGICA CRÍTICA: CÁLCULO DE VALOR PROPORCIONAL
// ==============================================================================

// Implementar a lógica de cálculo (anuidade / 12 * meses restantes)
$valor_final_a_cobrar = calcular_valor_proporcional($plano_escolhido); // Função a ser implementada

// ==============================================================================
// 4. AUTOMAÇÃO: ENVIAR DADOS PARA O GOOGLE SHEETS (Etapa 1 e 2 Concluídas!)
// ==============================================================================

$data_para_planilha = [
    date('d/m/Y H:i:s'), 
    $cnpj_limpo, 
    $dados_api_cnpj['razao_social'], 
    $cpf_socio,
    $plano_escolhido,
    'R$ ' . number_format($valor_final_a_cobrar, 2, ',', '.')
    // ... (todos os outros campos)
];

// O código de integração da Google Sheets API deve ser inserido aqui.
// Ele usa o ID da planilha e o arquivo credentials.json que você configurou.
// ... (código que insere $data_para_planilha na planilha)

// ==============================================================================
// 5. AUTOMAÇÃO: GERAÇÃO DE PDF E COBRANÇA
// ==============================================================================

// 5.1. Chamar a API de Boleto (Banco ou Gateway) para gerar o link de pagamento.
$link_boleto = gerar_boleto($valor_final_a_cobrar); // Função a ser implementada

// 5.2. Gerar o PDF da Ficha de Inscrição preenchida.
$pdf_path = gerar_ficha_pdf($dados_api_cnpj, $cpf_socio, $plano_escolhido, $valor_final_a_cobrar); // Função a ser implementada

// 5.3. Enviar e-mail de confirmação ao novo associado com o boleto e o PDF anexo.
enviar_email_confirmacao($dados_api_cnpj['email'], $link_boleto, $pdf_path); // Função a ser implementada

// ==============================================================================
// 6. FINALIZAÇÃO: REDIRECIONAR O USUÁRIO
// ==============================================================================

header("Location: agradecimento.html?status=sucesso");
exit;

// O desenvolvedor deve criar todas as funções (buscar_dados_cnpj, gerar_boleto, etc.)

?>
