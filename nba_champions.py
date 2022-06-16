
from bs4 import BeautifulSoup
import requests

url = "https://www.landofbasketball.com/championships/year_by_year.htm"
teams_url = "https://www.landofbasketball.com/nba_teams.htm"


def champions_yby():
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')

    main_tables = soup.find_all('div', class_ = "color-alt a-center max-0")

    # extracted the nba champions year by year data ; complete
    lst = []
    for i in range(1,len(main_tables)):
        main_table = main_tables[i]
        
        tags = main_table.find_all('div', class_ ="pad-5 clearfix")
        for i in range(len(tags)):
            yearly_lst = []
            tag = tags[i]
            text = tag.find_all("a")
            for i in range(len(text)):
                yearly_lst.append(text[i].string)
            score = tag.find('div', class_ = "rd-100 margen-r5").string
            yearly_lst.insert(2,score)
            lst.append(yearly_lst)
    
    return lst  # returning list of lists comprised of [year, winner, score, loser, Finals MVP, Season MVP]


print(champions_yby())