// jsons/context_match.js

// Recupera a partida da lista interna
var currentMatch = output._internalMatchList[output.matchIndex];

// Expõe dados básicos para o YAML
output.currentMatchName = currentMatch.match_name;

// Configura o sub-loop de Mercados
output.marketList = currentMatch.markets || [];
output.totalMarkets = output.marketList.length;
output.marketIndex = 0; // Sempre reseta ao entrar em novo jogo

console.log("--> [MATCH] Processando: " + output.currentMatchName + " (" + output.totalMarkets + " mercados)");