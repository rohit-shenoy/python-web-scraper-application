# Web Scraper

The incredible amount of data on the Internet is a rich resource for any field of research or personal interest.
To effectively harvest that data, you’ll need to become skilled at web scraping. Our take home test is designed
to evaluate real scenario. Dramacool (watchasian.id) is a web site which lists asian dramas and movies.
You would like to check from the command line status of dramas for year or range of years.
You can see all dramas for chosen year (example: 1996) under: https://dramacool.cy/released-in-1996.html.
Please take into account that this view displays only first 36 dramas so pagination should be taken into account.
If you go to drama details (example: first-love) https://dramacool.cy/drama-detail/first-love, you will see some
drama details like Country, Status, Released, Genre, Actors (images) and list of episodes: RAW - withouts and SUB
with english Subtitles. Each Episode has date-time of last change.

## Core requirements
1. List all dramas for chosen year and country: For example scrap.py --year 1996 -country Korea
2. List should include drama name, genre, actors and last SUB or RAW episode.
3. If there are RAW and SUB Episodes in one drama, it should show last RAW and last SUB
4. Program should list all dramas not only 36 from the first page. (Pagination)
5. Program should support date-time parameter which will list all episodes released after specified date-time.

This is how result should looks like
```
python scrap.py --year 1996 --country Korean (optional: --newer date-time)
First Love - Korean - 1996 - Romance - Bae Yong Joon (1972), Choi Ji Woo (1975), Lee Seung Yeon (1968), Choi Soo Jong (1962)
  RAW First Love Episode 65 2015-03-05 09:34:25
  SUB First Love Episode 61 2015-03-05 09:34:25
```

## Bonus points
1. Program accepts instead of year range of years for example 1990-1999: `python scrap.py --years 1990-1996 --country Korean` 
2. Program accepts additionally genre parameter to list only dramas with choosen genre
`python scrap.py --year 1996 --country Korean --genre Romance` 
3. Program supports actor/actress parameter and list all dramas with him/her
`python scrap.py --act "Bae Yong Joon"`
4. Program displays progress using eg. 'alive_progress'
5. Program displays only episodes (lines starting with SUB or RAW) ignoring Drama title, country etc
```
python scrap.py --year 1996 --country Korean --ep (optional: --newer date-time)
  RAW First Love Episode 65 2015-03-05 09:34:25
  SUB First Love Episode 61 2015-03-05 09:34:25
```

## Python

To give you more idea how it should work you can look into python code which you can use as well as a base for
further development.
Problems with current code:
- No support for pagination (example for 1996 displays only 36 results from page 1)
- No support for country (displays all dramas from choosen year)
- ugly formatting
```
27
First Love https://watchasian.id/drama-detail/first-love
Bae Yong Joon (1972)
Choi Ji Woo (1975)
Lee Seung Yeon (1968)
Choi Soo Jong (1962)
SUB

First Love Episode 66
2015-03-05 09:34:25
SUB

First Love Episode 65
```

- displays all episodes not only the last one
- no support for RAW, SUB
- no support for date-time episodes

### Setup

```
# Create virtual environment
python -m venv venv
# Activate Virtual Environment
source venv/bin/activate
# Install dependencies
python -m pip install requests beautifulsoup4
...
# Example run for 1996
python scrap.py 1996
...
# Exit from virtual Environment
deactivate
```
## 📝 Candidate instructions
1. Create a private [GitHub](https://help.github.com/en/articles/create-a-repo) repository containing the content of this repository
2. Complete the [Task](#task) :tada:
3. [Invite](https://help.github.com/en/articles/inviting-collaborators-to-a-personal-repository) me to your private repo
4. Let me know you've completed the exercise
