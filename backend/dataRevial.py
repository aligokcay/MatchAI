import requests
import json
from bs4 import BeautifulSoup

def get_team_market_value(team_url):
    """Takımın Transfermarkt sayfasından piyasa değerini çeker."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(team_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    market_value_element = soup.find("a", class_="data-header__market-value-wrapper")
    market_value = market_value_element.find("span", class_="waehrung").previous_sibling.strip()

    if market_value:
        return market_value.strip()
    return "Bilinmiyor"

def get_team_urls():
    """Fenerbahçe'nin fikstür sayfasından rakip takım URL'lerini çeker ve piyasa değerlerini alır."""
    url = "https://www.transfermarkt.com.tr/fenerbahce-istanbul/spielplandatum/verein/36"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    team_data = {}
    matches = soup.find_all("tr")
    
    for match in matches:
        team_link = match.find("td", class_="no-border-links hauptlink")
        if team_link:
            a_tag = team_link.find("a", href=True)
            if a_tag:
                team_name = a_tag.text.strip()
                if team_name in team_data:
                    continue
                team_url = "https://www.transfermarkt.com.tr" + a_tag["href"]
                result_cell = match.find("a", title="Ön rapor")
                if result_cell:
                    break
                team_value = get_team_market_value(team_url)
                team_data[team_name] = team_value
                print(f"Rakip: {team_name} | Piyasa Değeri: {team_value}")
    
    return team_data

def get_fixtures_and_values():
    """FBRef üzerinden Fenerbahçe'nin fikstürünü çeker ve rakip takım piyasa değerleri ile eşleştirir."""
    url = "https://fbref.com/en/squads/ae1e2d7d/2024-2025/matchlogs/all_comps/schedule/Fenerbahce-Scores-and-Fixtures-All-Competitions"
    team_name_mapping = {
        "BB Bodrumspor": "Bodrum FK",   # Transfermarkt ve FBref'deki farklı isimler
        "Rizespor": "Ç. Rizespor",
        "Manchester Utd": "Man United",
        "Slavia Prague": "Slavia Prag",
        "Athletic Club": "Bilbao"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    team_values = get_team_urls()
    
    fixtures = []
    table = soup.find("table", {"id": "matchlogs_for"})
    if table:
        rows = table.find_all("tr")
        
        for row in rows[1:]:
            cols = row.find_all("td")
            if cols:
                competition = cols[1].text.strip()
                home_away = cols[4].text.strip()
                result = cols[5].text.strip()
                if result == "":
                    continue
                goals_for = cols[6].text.strip()
                goals_against = cols[7].text.strip()

                # opponent hücresindeki <a> etiketi içindeki metni al
                opponent_cell = cols[8]
                
                # Bayrakları temizle
                for span in opponent_cell.find_all("span"):
                    span.decompose()  # Bayrağı temizle
                    
                # Takım adını almak için <a> etiketini bul
                a_tag = opponent_cell.find("a", href=True)
                if a_tag:
                    opponent = a_tag.text.strip()  # sadece takım adını al
                else:
                    opponent = opponent_cell.text.strip()  # Bayraksız metin al (eğer <a> yoksa)
                
                opponent_normalized = team_name_mapping.get(opponent, opponent)
                opponent_value = team_values.get(opponent_normalized, "Bilinmiyor")
                xG = cols[9].text.strip()
                xGA = cols[10].text.strip()
                formation = cols[14].text.strip()
                opp_formation = cols[15].text.strip()

                if competition in ['Champions Lg', 'Europa Lg', 'Conf Lg']:
                    competition_type = 'European Match'
                else:
                    competition_type = 'League Match'
                
                print(f"Turnuva: {competition} | İç/Dış: {home_away} | Sonuç: {result} ({goals_for}:{goals_against}) | Rakip: {opponent} | Rakip Takımın Değeri: {opponent_value} | Formation: {formation} | Opp Formation: {opp_formation} | xG: {xG} | xGA: {xGA}")

                fixture = {
                    "competition": competition_type,
                    "home_away": home_away,
                    "opponent": opponent,
                    "opponent_market_value": opponent_value,
                    "formation": formation,
                    "opponent_formation": opp_formation,
                    "result": result,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "xG": xG,
                    "xGA": xGA                    
                }
                fixtures.append(fixture)
        with open("fixtureData.json", "w", encoding="utf-8") as f:
            json.dump(fixtures, f, ensure_ascii=False, indent=4)
    
        print("Veriler fixtures.json dosyasına kaydedildi.")        
    else:
        print("Tablo bulunamadı, URL veya HTML yapısını kontrol et.")

# Çalıştır
get_fixtures_and_values()
