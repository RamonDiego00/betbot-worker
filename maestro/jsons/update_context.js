// Arquivo: jsons/update_context.js

// Recupera a partida da lista interna (carregada pelo loader.js)
var currentMatch = output._internalMatchList[output.matchIndex];

// Atualiza as variáveis GLOBAIS que o YAML vai consumir
output.currentMatchName = currentMatch.match_name;

// Prepara dados dos mercados (para o loop interno)
output.marketList = currentMatch.markets || [];
output.totalMarkets = output.marketList.length;
output.marketIndex = 0;

// Log para confirmar que o script rodou
console.log("[Context Update] Jogo Atualizado: " + output.currentMatchName);