// jsons/context_market.js

var currentMarket = output.marketList[output.marketIndex];
output.currentMarketName = currentMarket.market_name;

// Lógica de Seleção (Pega a primeira disponível)
var selection = currentMarket.selections ? currentMarket.selections[0] : null;

if (selection) {
    output.targetValue = selection.visual_target;
    output.previousTargetValue = selection.previous_visual_target;
    output.targetColumn = selection.column_index;
    output.isValidBet = true;
    console.log("    -> [MARKET] Seleção: " + output.targetValue +"| Anterior: "+ output.previousTargetValue  +" | Coluna: " + output.targetColumn);
} else {
    output.isValidBet = false;
    output.targetValue = null;
    output.previousTargetValue = null;
    output.targetColumn = null;
    console.log("    -> [MARKET] Aviso: Nenhuma seleção válida encontrada.");
}