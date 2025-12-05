// iterator.js

// Simulação do carregamento do JSON (em produção, você pode ler de um arquivo ou variável de ambiente)
// O objeto 'json_input' representa o payload que você forneceu.
var data = json_input; 

// Inicializa contadores se não existirem
if (typeof output.matchIndex === 'undefined') output.matchIndex = 0;

// Lógica para recuperar dados do JOGO ATUAL
if (output.matchIndex < data.matches.length) {
    var currentMatch = data.matches[output.matchIndex];
    output.currentMatchName = currentMatch.match_name;
    output.hasMoreMatches = true;

    // Inicializa contador de mercados para este jogo se não existir
    if (typeof output.marketIndex === 'undefined') output.marketIndex = 0;

    // Lógica para recuperar dados do MERCADO ATUAL
    if (output.marketIndex < currentMatch.markets.length) {
        var currentMarket = currentMatch.markets[output.marketIndex];
        
        output.currentMarketName = currentMarket.market_name;
        output.currentSelections = JSON.stringify(currentMarket.selections); // Passa como string para o subfluxo
        output.hasMoreMarkets = true;
        
        // Define qual subfluxo chamar baseado no nome do mercado
        if (currentMarket.market_name.includes("Jogador")) {
            output.subFlowToRun = "players_lines.yaml";
        } else {
            output.subFlowToRun = "team_lines.yaml";
        }
    } else {
        output.hasMoreMarkets = false;
        output.subFlowToRun = null;
    }
} else {
    output.hasMoreMatches = false;
}

// Passa dados globais
output.globalStake = data.global_stake;