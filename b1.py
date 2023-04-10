import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil.parser import parse
import pytz


api_key = "cb07402b474ead52cfde7bcb9b0a3493"
url = f"https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds/?apiKey={api_key}&regions=us&oddsFormat=decimal"

response = requests.get(url)
data = response.json()

html_file = "output.html"

with open(html_file, "r") as file:
    content = file.read()

soup = BeautifulSoup(content, "html.parser")
table = soup.find("table", {"id": "fights"})
table.tbody.clear()
first_event_date = None
count = 0
def round_to_factor(x, factor):
    return int(factor * round(float(x) / factor))

for event in data:
    if count >= 20:
        break
    fighters = [event["home_team"], event["away_team"]]
    date = event["commence_time"]
    local_tz = pytz.timezone('US/Eastern')
    utc_dt = parse(date).replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(local_tz)

    if first_event_date is None:
        first_event_date = local_dt.date()
    elif local_dt.date() != first_event_date:
        break

    best_odds = [0, 0]

    for bookmaker in event["bookmakers"]:
        odds = bookmaker["markets"][0]["outcomes"]

        for i in range(2):
            current_odds = float(odds[i]["price"])
            fighter_index = fighters.index(odds[i]["name"])
            if current_odds > best_odds[fighter_index]:
                best_odds[fighter_index] = current_odds

    # Determine favorite and underdog
    favorite_index = 0 if best_odds[0] < best_odds[1] else 1
    underdog_index = 1 - favorite_index

    favorite = fighters[favorite_index]
    underdog = fighters[underdog_index]

    favorite_odds = best_odds[favorite_index]
    underdog_odds = best_odds[underdog_index]

    # Convert to American odds
    if favorite_odds >= 2:
        american_favorite_odds = round_to_factor((favorite_odds - 1) * 100, 5)
    else:
        american_favorite_odds = round_to_factor(-100 / (favorite_odds - 1), 5)

    if underdog_odds >= 2:
        american_underdog_odds = round_to_factor((underdog_odds - 1) * 100, 5)
    else:
        american_underdog_odds = round_to_factor(-100 / (underdog_odds - 1), 5)

    local_tz = pytz.timezone('US/Eastern')
    utc_dt = parse(date).replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(local_tz)
    formatted_date = local_dt.strftime('%m/%d/%y - %I:%M %p ET')

    tr = soup.new_tag("tr")
    
    td_favorite = soup.new_tag("td")
    td_favorite.string = favorite
    tr.append(td_favorite)

    td_underdog = soup.new_tag("td")
    td_underdog.string = underdog
    tr.append(td_underdog)

    td_favorite_odds = soup.new_tag("td")
    td_favorite_odds.string = f"{american_favorite_odds:+}"
    tr.append(td_favorite_odds)

    td_underdog_odds = soup.new_tag("td")
    td_underdog_odds.string = f"{american_underdog_odds:+}"
    tr.append(td_underdog_odds)

    td_date = soup.new_tag("td")
    td_date.string = formatted_date
    tr.append(td_date)

    table.tbody.append(tr)

with open(html_file, "w") as file:
    file.write(str(soup))