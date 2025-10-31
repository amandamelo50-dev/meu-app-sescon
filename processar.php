<?php
// Exemplo em PHP - você precisará instalar a biblioteca oficial do Google
require __DIR__ . '/vendor/autoload.php';

// 1. DADOS OBTIDOS APÓS O PROCESSAMENTO COMPLETO
$data_inscricao = date('d/m/Y H:i:s');
$cnpj_final = $_POST['cnpj_limpo']; 
$razao_social = $_POST['razaoSocial_api']; // Dados limpos da API CNPJ
$cpf_socio = $_POST['cpfSocio'];
$telefone_whatsapp = $_POST['telefone'];
$plano_escolhido = $_POST['plano'];
$valor_final = $_POST['valor_proporcional']; // O valor calculado no backend

// O ID da Planilha Google (URL: https://docs.google.com/spreadsheets/d/ID_AQUI/edit)
$spreadsheetId = 'SEU_ID_DA_PLANILHA_GOOGLE';

// 2. CONFIGURAÇÃO DA API
try {
    // Configura a autenticação com as credenciais JSON que você baixou
    $client = new \Google\Client();
    $client->setAuthConfig('caminho/para/seu/credentials.json');
    $client->addScope(\Google\Service\Sheets::SPREADSHEETS);
    
    // Cria o serviço da Sheets API
    $service = new \Google\Service\Sheets($client);

    // 3. PREPARAÇÃO DOS DADOS PARA INSERÇÃO
    // Garanta que a ordem dos campos seja IGUAL à ordem das colunas da Planilha!
    $values = [
        [$data_inscricao, $cnpj_final, $razao_social, $cpf_socio, $telefone_whatsapp, $plano_escolhido, $valor_final]
    ];
    
    $body = new \Google\Service\Sheets\ValueRange(['values' => $values]);
    
    // Define onde a linha será inserida (geralmente A:A para a próxima linha vazia)
    $range = 'Página1!A:G'; 
    $params = ['valueInputOption' => 'USER_ENTERED'];

    // 4. ENVIO DE DADOS PARA O GOOGLE SHEETS
    $result = $service->spreadsheets_values->append(
        $spreadsheetId, 
        $range, 
        $body, 
        $params
    );

    // Verifica se a inserção foi bem-sucedida
    if ($result->getUpdates()->getUpdatedCells() > 0) {
        // Sucesso na Planilha, agora continua para a geração do Boleto e E-mail
        // ... (Seu código de API de Boleto e Geração de PDF continua aqui)
        
        // Finaliza o processamento e redireciona o usuário:
        header("Location: agradecimento.html");
        exit;
    } else {
        // Erro na inserção da Planilha (tratar erro)
        error_log("Erro ao inserir dados no Google Sheets.");
        // Não impede o usuário de se inscrever, mas alerta o erro interno
    }

} catch (\Exception $e) {
    // Tratar erros de conexão ou autenticação da API
    error_log("Erro crítico de API do Google Sheets: " . $e->getMessage());
}

?>
