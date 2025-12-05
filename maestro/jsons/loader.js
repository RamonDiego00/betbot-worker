
        // ARQUIVO GERADO PELO PYTHON
        output.jsonData = {
  "batch_id": "1",
  "global_stake": 0.5,
  "matches": [
    {
      "match_name": "Leeds v Chelsea",
      "markets": [
        {
          "market_name": "Total de Gols",
          "selections": [
            {
              "visual_target": "1 Gols",
              "previous_visual_target": "0 Gols",
              "column_index": 0,
              "description": "Mais de 1 gol(Coluna 1)"
            }
          ]
        },
        {
          "market_name": "Escanteios",
          "selections": [
            {
              "visual_target": "7 Escanteios",
              "previous_visual_target": "6 Escanteios",
              "column_index": 0,
              "description": "Mais de 7 Escanteios"
            }
          ]
        }
      ]
    },
    {
      "match_name": "Arsenal v Brentford",
      "markets": [
        {
          "market_name": "Total de Gols",
          "selections": [
            {
              "visual_target": "1 Gols",
              "previous_visual_target": "0 Gols",
              "column_index": 0,
              "description": "Mais de 1 gol(Coluna 1)"
            }
          ]
        },
        {
          "market_name": "Escanteios",
          "selections": [
            {
              "visual_target": "7 Escanteios",
              "previous_visual_target": "6 Escanteios",
              "column_index": 0,
              "description": "Mais de 7 Escanteios"
            }
          ]
        }
      ]
    }
  ]
};

        if (!output.jsonData || !output.jsonData.matches) {
            throw new Error("CRÍTICO: JSON vazio.");
        }
        output._internalMatchList = output.jsonData.matches;
        output.totalMatches = output._internalMatchList.length;
        output.matchIndex = 0;
        