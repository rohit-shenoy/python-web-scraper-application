import sys
import re
import requests
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar

# global - for displaying progress
progressBar = None


def parseInputs():
    '''
    Function to accept user passed parameters and parses them.

            Input Parameters:
                    N/A

            Returns:
                    args (Namespace): argparse.Namespace object returned
    '''

    parser = argparse.ArgumentParser(description='My asian movie scraper')

    # require one argument out of `year` or `years`
    yearGroup = parser.add_mutually_exclusive_group(required=False)
    yearGroup.add_argument(
        '--year', help='Dramas from one specific year (XXXX)')
    yearGroup.add_argument(
        '--years', help='Dramas from a range of years (XXXX-XXXX)')

    parser.add_argument('--country', type=str, required=False,
                        help='Country for the dramas')

    parser.add_argument('--genre', type=str, help='Genre for the dramas',
                        required=False)

    parser.add_argument('--act', type=str,
                        help='Actor/actress for the dramas',
                        required=('--year' not in sys.argv and '--years' not in sys.argv))

    parser.add_argument('--newer', type=str,
                        help='Date time (YYYY-MM-DD HH:MM:SS) for the dramas, display only dramas newer than this date time')

    parser.add_argument('--ep', action='store_true',
                        help='Display only episode details if passed (no drama title/country..), else display everything')

    parser.add_argument('--noact', action='store_true',
                        help='Display actors for dramas if passed, do not display actor/actresses for a drama otherwise')

    args = parser.parse_args()
    return args


def makeURL(params):
    '''
    Function to construct URL to make requests.

            Input Parameters:
                    params: Contains the user passed parameters, to be used to construct the URL
                    Type: argparse.Namespace
                    Required: Yes

            Returns:
                    URL: The URL String
                    Type: str
    '''

    URL = f""
    base_url = "https://dramacool.cy"

    # single year
    if params.year is not None:
        URL = f"{base_url}/released-in-{params.year}.html"

    # only actor URL
    elif params.act and not (params.year or params.years):
        actor_name = params.act.replace(" ", "-").lower()
        URL = f"{base_url}/star/{actor_name}"

    return URL


def findTotalDramas(URL):
    '''
    Function to find total dramas to search

            Input Parameters:
                    URL: The URL String
                    Type: str
                    Required: Yes

            Returns:
                    totalDramas: The total number of dramas to search/scrape
                    Type: int
    '''
    totalDramas = 0
    base_url_year = URL

    while URL:
        # get main page, find all child drama pages
        page = requests.get(URL)
        mainPageSoup = BeautifulSoup(page.content, "html.parser")

        detailPages = mainPageSoup.find_all(
            'a', {'class': 'img', 'href': True})
        totalDramas += len(detailPages)

        nextPage = mainPageSoup.find('li', {'class': 'next'})
        if nextPage:
            # more dramas exist
            URL = base_url_year + nextPage.a.get('href')
        else:
            # stop
            break

    return totalDramas


def getData(URL, params):
    '''
    Function to make URL requests, web scrape information & pass on to display.

            Input Parameters:
                    URL: The URL String
                    Type: str
                    Required: Yes

                    params: User passed parameters
                    Type: argparse.Namespace
                    Required: Yes

                    totalDramas: Total number of dramas to search
                    Type: int
                    Required: Yes

            Returns:
                    N/A
    '''

    base_url = "https://dramacool.cy"
    base_url_year = URL

    while URL:
        page = requests.get(URL)

        # get main page, find all child drama pages
        mainPageSoup = BeautifulSoup(page.content, "html.parser")
        detailPages = mainPageSoup.find_all(
            'a', {'class': 'img', 'href': True})

        # iterate and get drama details for all child drama page(s) - with alive progress
        # for dp in alive_it(detailPages, enrich_print=False, elapsed=True, stats=True, disable=False):
        for dp in detailPages:
            dramaTitle, country, year, genre, actors, episodeRAW, episodeSUB = "", "", "", "", "", "", ""
            detailPageUrl = base_url + dp['href']

            detailPage = requests.get(detailPageUrl)
            detailPageSoup = BeautifulSoup(detailPage.content, "html.parser")

            # Starting to searching drama, updating progress bar
            global progressBar
            progressBar()

            # details info block for each drama
            infoBlock = detailPageSoup.find('div', {'class': 'info'})
            dramaTitle = infoBlock.h1.text

            # scrape country
            countryBlock = infoBlock.find(
                'a', href=re.compile("/country/"))
            country = countryBlock.text

            # if country filter given and doesn't match, skip drama
            if params.country is not None and country.strip().lower() != params.country.strip().lower():
                continue

            # scrape year
            yearBlock = infoBlock.find(
                'a', href=re.compile("/released-in"))
            year = yearBlock.text

            # scrape genre (genres can be multiple)
            genres = infoBlock.find_all(
                'a', href=re.compile("/genre/"))
            for g in genres:
                genre += g.text + ", "
            genre = genre[:len(genre) - 2] if genre else ""

            # if genre filter given and doesn't match, skip drama
            if params.genre is not None and params.genre.strip().lower() not in [g.strip().lower() for g in genre.split(", ")]:
                continue

            # scrape actors (actors can be multiple)
            actors = ""

            actorLinks = detailPageSoup.find_all(
                'a', {'class': 'img'}, href=re.compile("/star/"))
            for ac in actorLinks:
                actors += ac.h3.text + ", "
            actors = actors[:len(actors)] if actors else ""

            # if actor filter given and doesn't match, skip drama
            if params.act is not None and params.act.lower() not in [a.lower()[:len(a) - 7] for a in actors.split(", ")]:
                continue

            # scrape episodes
            episodeLinks = detailPageSoup.find_all(
                'a', {'class': 'img'}, href=re.compile("-episode-"))

            lastRawFound, lastSubFound = False, False

            if params.newer:
                newerDateTime = datetime.strptime(
                    params.newer.strip(), '%Y-%m-%d %H:%M:%S')

            # iterate all episodes for drama
            for ep in episodeLinks:

                # if newer episodes not set, then only display last SUB and last RAW
                if not params.newer and (lastRawFound and lastSubFound):
                    break

                # extract episode info & check if RAW or SUB
                if ep:
                    # get episode, name, type, time
                    epType = ep.find('span', class_=re.compile("type "))
                    epName = ep.find('h3', {'class': 'title'}).text
                    epTime = ep.find('span', {'class': 'time'}).text

                    # compute episode datetime
                    epDateTime = datetime.strptime(
                        epTime.strip(), '%Y-%m-%d %H:%M:%S')

                    # if newer filter given and episode is before newer, skip episode
                    if params.newer is not None and epDateTime < newerDateTime:
                        continue

                    # get only last RAW episode(s) - and construct display string for RAW episodes
                    if epType.text == "RAW":
                        if lastRawFound:
                            continue

                        episodeRAW += "RAW" + " " + epName + " " + epTime + "\n\t"

                        # if newer is set, need all episodes, not just last (so never set lastFound)
                        if not params.newer:
                            lastRawFound = True

                    # get only last SUB episode - and construct display string for SUB episodes
                    elif epType.text == "SUB":
                        if lastSubFound:
                            continue

                        episodeSUB += "SUB" + " " + epName + " " + epTime + "\n\t"

                        # if newer is set, need all episodes, not just last (so never set lastFound)
                        if not params.newer:
                            lastSubFound = True

            # Format and display one drama
            displayDrama(dramaTitle=dramaTitle,
                         country=country,
                         year=year,
                         genre=genre,
                         actors=actors,
                         episodeRAW=episodeRAW,
                         episodeSUB=episodeSUB,
                         params=params)

        # Get next page from current page - stop when no next pages: PAGINATION
        nextPage = mainPageSoup.find('li', {'class': 'next'})
        if nextPage:
            # more dramas exist
            URL = base_url_year + nextPage.a.get('href')
        else:
            # stop
            break


def displayDrama(dramaTitle, country, year, genre, actors, episodeRAW, episodeSUB, params):
    '''
    Function to format and display a Drama.

            Input Parameters:
                    dramaTitle: The drama title string
                    Type: str
                    Required: Yes

                    country: The drama country string
                    Type: str
                    Required: Yes

                    year: The drama year string
                    Type: str
                    Required: Yes

                    genre: The drama genre string
                    Type: str
                    Required: Yes

                    actors: The drama actors/actresses string
                    Type: str
                    Required: Yes

                    episodeRAW: The RAW episodes string
                    Type: str
                    Required: Yes

                    episodeSUB: The SUB episodes string
                    Type: str
                    Required: Yes

                    params: User passed parameters
                    Type: argparse.Namespace
                    Required: Yes

            Returns:
                    N/A
    '''
    # display drama episode block
    episodeString = ""

    # both RAW and SUB episodes
    if episodeRAW and episodeSUB:
        episodeString += "\t" + episodeRAW.rstrip() + "\n\t" + episodeSUB.rstrip()

        # block of RAW episodes only
    elif episodeRAW and not episodeSUB:
        # strip last episode of newline & tab
        episodeRAW = episodeRAW.rstrip()
        episodeString += "\t" + episodeRAW

    # block of SUB episodes only
    elif episodeSUB and not episodeRAW:
        # strip last episode of newline & tab
        episodeSUB = episodeSUB.rstrip()
        episodeString += "\t" + episodeSUB

    # display everything if --ep parameter is True
    if not params.ep:

        # display drama title & info, don't add actor info
        if params.noact:
            dramaString = " - ".join([dramaTitle,
                                     country, year, genre])
            dramaString = dramaString[:len(dramaString)] + "\n"

        # display drama title & info, add actor info
        else:
            dramaString = " - ".join([dramaTitle,
                                     country, year, genre, actors])
            dramaString = dramaString[:len(dramaString) - 2] + "\n"

        if episodeString:
            print(dramaString + episodeString)
        else:
            # diplay only dramas that have episodes newer than date-time when newer is set
            if not params.newer:
                print(dramaString + "\n")

    # only display drama title and details if --ep parameter is False
    if params.ep:
        if episodeString:
            print(episodeString)


def main():

    global progressBar

    try:
        # parse inputs
        params = parseInputs()

        print("\nWelcome to the rohit-shenoy/scripting-interview Web Scraper!!!")
        print("----------------------------------------------------------------")

        # One Year
        if params.year:
            # make URL
            URL = makeURL(params)

            # find total dramas
            totalDramas = findTotalDramas(URL)

            # progress bar
            with alive_bar(totalDramas, enrich_print=False, title="Searching your dramas for year: " +
                           str(params.year) + ", hang tight!") as progressBar:

                # make request
                getData(URL, params)

        # Range of Years
        elif params.years:
            startYear = int(params.years.split("-")[0])
            endYear = int(params.years.split("-")[1])

            # iterate years and search dramas for all years
            for year in range(startYear, endYear + 1):
                params.year = year

                # make URL
                URL = makeURL(params)

                # find total dramas
                totalDramas = findTotalDramas(URL)

                # initialize progress bar
                with alive_bar(totalDramas, enrich_print=False, title="Searching year: " +
                               str(params.year) + ", hang tight!") as progressBar:

                    # make request
                    getData(URL, params)

        # Only actor
        elif params.act and not (params.year or params.years):
            # make URL
            URL = makeURL(params)

            # find total dramas
            totalDramas = findTotalDramas(URL)

            # progress bar
            with alive_bar(totalDramas, enrich_print=False, title="Searching actor: " +
                           str(params.act) + ", hang tight!") as progressBar:

                # make request
                getData(URL, params)

    except Exception as e:
        print("Something went wrong, hang tight! " + str(e))


if __name__ == "__main__":
    main()
