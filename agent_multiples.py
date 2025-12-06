matches = get_all_matches_with_stats_and_odds()
high_confidence_picks = []

for match in matches:
    # 1. Analisa Prioridade 1: Gols
    stats = json.loads(match.home_team_form)
    avg_goals = stats['goalsScoredPerMatch'] + stats['goalsConcededPerMatch']
    
    # Se a média de gols for altíssima (> 3.0), o Over 1.5 é "Safe Bet"
    if avg_goals > 3.0:
        # Pega a odd no banco (provavelmente vai ser baixa, tipo 1.25)
        odd_over_1_5 = get_odd_from_db(match.id, "Total", "Over 1.5") 
        
        pick = {
            "match": match.name,
            "market": "Over 1.5 Gols",
            "odd_estimated": odd_over_1_5 or 1.25, # Fallback se não tiver odd
            "confidence": 0.9
        }
        high_confidence_picks.append(pick)

# 2. Montagem das Múltiplas (Combinatória)
# Precisamos combinar picks para que (Odd A * Odd B) esteja entre 1.70 e 2.50

batch_bets = []
sorted_picks = sorted(high_confidence_picks, key=lambda x: x['confidence'], reverse=True)

# Pega o melhor pick e tenta casar com o segundo melhor
while len(sorted_picks) >= 2:
    pick_a = sorted_picks.pop(0)
    pick_b = sorted_picks.pop(0)
    
    total_odd = pick_a['odd_estimated'] * pick_b['odd_estimated']
    
    if 1.70 <= total_odd <= 2.50:
        print(f"🚀 Múltipla Criada: {pick_a['match']} + {pick_b['match']} (Odd Total: {total_odd:.2f})")
        # Adiciona ao JSON de envio...
    else:
        # Se não deu a odd, devolve pra fila ou tenta com o próximo
        pass